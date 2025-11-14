# SRT Implementation Guide

## Overview

This document describes the complete SRT (Secure Reliable Transport) integration for Miktos StreamLab, providing professional-grade low-latency streaming with automatic error recovery and comprehensive monitoring.

## Features

### Core SRT Capabilities

- **Native Integration**: FFmpeg with libsrt support for real SRT protocol implementation
- **Low Latency**: Configurable latency down to 500ms for live broadcasting
- **Encryption**: Support for AES128/192/256 encryption with passphrase protection
- **Error Recovery**: Automatic retransmission and forward error correction
- **Adaptive Bitrate**: Dynamic adjustment based on network conditions
- **Health Monitoring**: Real-time statistics and connection quality assessment

### Professional Features

- **Dual-Path Egress**: Integration with YouTube EN/FR streaming system
- **Automatic Failover**: Seamless switching between primary and backup streams
- **Slate Management**: Professional transitions during connection issues
- **Statistics API**: Comprehensive performance metrics and health scoring
- **Configuration Management**: Flexible YAML-based configuration system

## Architecture

### Core Components

```text
SRT Integration Layer
├── srt_integration.py       # Core SRT implementation
│   ├── SRTConnection        # Individual SRT connection management
│   ├── SRTServer           # SRT server for receiving streams
│   ├── SRTConfig           # Configuration management
│   └── SRTStats            # Statistics and health monitoring
│
├── egress.py               # Integration with egress system
│   └── SRTDestination      # SRT destination implementation
│
└── youtube_dual_stream.py  # Dual-streaming integration
    └── SRT backup support  # SRT as backup for YouTube streams
```

### Data Flow

```text
Input Source → FFmpeg → SRT Protocol → Destination
     ↓              ↓         ↓           ↓
   Camera        Encoding  Network    Receiver
   RTMP          H.264     UDP/SRT    Server
   File          Audio     Encrypted  CDN
```

## Configuration

### Basic SRT Configuration

```yaml
srt_destinations:
  primary_relay:
    host: "srt-relay.example.com"
    port: 9999
    latency_ms: 2000
    encryption: "aes256"
    passphrase: "secure_streaming_2024"
    
  backup_relay:
    host: "backup.example.com"  
    port: 9999
    latency_ms: 3000
    encryption: "none"
```

### Advanced Configuration

```yaml
srt_advanced:
  connection:
    mode: "caller"              # caller, listener, rendezvous
    connection_timeout: 3000    # milliseconds
    packet_size: 1316          # UDP packet size
    
  performance:
    max_bandwidth: 0           # 0 = unlimited
    buffer_size: 25600000      # receive buffer size
    congestion_control: "live" # live or file
    
  monitoring:
    stats_interval: 5          # seconds
    health_threshold: 80       # minimum health score
    
  custom_options:
    streamid: "publisher/live/stream1"
    transtype: "live"
```

## Integration with Dual-Path Egress

### Configuration Example

```yaml
egress:
  destinations:
    # Primary YouTube streams
    - name: "youtube_en"
      type: "youtube" 
      url: "rtmp://a.rtmp.youtube.com/live2/YOUR_KEY_EN"
      
    - name: "youtube_fr"
      type: "youtube"
      url: "rtmp://a.rtmp.youtube.com/live2/YOUR_KEY_FR"
      
    # SRT backup
    - name: "srt_backup"
      type: "srt"
      url: "srt://relay.example.com:9999?latency=2000&pbkeylen=aes256&passphrase=secure123"
      
  failover:
    enabled: true
    slate_display: true
    recovery_attempts: 3
    
  thresholds:
    rtt_warning: 100           # ms
    rtt_critical: 300          # ms  
    packet_loss_warning: 1.0   # %
    packet_loss_critical: 3.0  # %
```

## API Usage

### Basic SRT Connection

```python
from Desktop.Backend.core.srt_integration import SRTConnection, create_srt_config

# Create configuration
config = create_srt_config(
    host="srt-server.example.com",
    port=9999,
    latency_ms=2000,
    encryption="aes256", 
    passphrase="secure_key"
)

# Create and connect
srt = SRTConnection(config)
success = await srt.connect()

if success:
    # Start streaming
    await srt.start_streaming("rtmp://input.example.com/live/stream")
    
    # Monitor health
    stats = srt.get_stats()
    print(f"Health: {stats.get_health_score()}/100")
    
    # Stop and disconnect
    await srt.stop_streaming()
    await srt.disconnect()
```

### Statistics Monitoring

```python
def on_stats_update(stats):
    print(f"RTT: {stats.rtt_ms:.1f}ms")
    print(f"Packet Loss: {stats.packet_loss_pct:.2f}%")
    print(f"Bitrate: {stats.bitrate_mbps:.1f}Mbps")
    print(f"Health Score: {stats.get_health_score():.1f}/100")

srt.set_stats_callback(on_stats_update)
```

### Integration with Egress Manager

```python
from Desktop.Backend.core.egress import SRTDestination

# Create SRT destination
srt_dest = SRTDestination(
    name="backup_srt",
    url="srt://relay.example.com:9999?latency=2000"
)

# Use with egress manager
egress_manager.add_destination(srt_dest)
await egress_manager.start_streaming()
```

## Health Monitoring

### Health Score Calculation

The SRT health score (0-100) is calculated based on:

- **Connection Status** (50 points): Connected vs disconnected
- **RTT Performance** (25 points):
  - Excellent: <50ms (25 points)
  - Good: 50-100ms (20 points)
  - Fair: 100-200ms (15 points)
  - Poor: >200ms (0-10 points)
- **Packet Loss** (25 points):
  - Excellent: 0% (25 points)
  - Good: <0.1% (20 points)
  - Fair: 0.1-1% (15 points)
  - Poor: >1% (0-10 points)

### Statistics Available

```python
class SRTStats:
    # Connection
    connected: bool
    connection_time: datetime
    peer_address: str
    
    # Performance  
    bitrate_mbps: float
    rtt_ms: float
    packet_loss_pct: float
    
    # Buffers
    send_buffer_level: int
    receive_buffer_level: int
    
    # Counters
    packets_sent: int
    packets_received: int
    packets_retransmitted: int
    packets_dropped: int
    
    # Bandwidth
    bandwidth_available_mbps: float
    bandwidth_used_mbps: float
```

## Failover Scenarios

### Automatic Failover Process

1. **Detection**: Health monitoring detects degraded performance
   - RTT > 300ms for 5 seconds
   - Packet loss > 3% for 5 seconds  
   - Connection failure

2. **Slate Display**: Show "Technical Difficulties" slate to viewers

3. **Failover**: Switch to backup SRT relay
   - Establish backup connection
   - Resume streaming
   - Continue monitoring

4. **Recovery**: When primary improves
   - Test primary connection health
   - Switch back when stable
   - Log recovery event

### Manual Failover

```python
# Force failover to backup
await egress_manager.failover_to_backup("Connection issues detected")

# Return to primary when ready
await egress_manager.recover_primary()
```

## Installation & Setup

### Prerequisites

1. **FFmpeg with SRT Support**

   ```bash
   # macOS
   brew install ffmpeg --with-srt
   
   # Ubuntu/Debian  
   sudo apt update
   sudo apt install ffmpeg libsrt-dev
   
   # Verify SRT support
   ffmpeg -protocols | grep srt
   ```

2. **Python Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

### Configuration Files

1. Create `config/srt_config.yaml`:

   ```yaml
   srt:
     default_latency: 2000
     default_encryption: "aes256"
     buffer_size: 25600000
   ```

2. Update `.env` with SRT credentials:

   ```env
   SRT_PASSPHRASE=your_secure_passphrase
   SRT_PRIMARY_HOST=srt-primary.example.com
   SRT_BACKUP_HOST=srt-backup.example.com
   ```

## Testing

### Run SRT Demo

```bash
python demo_srt_implementation.py
```

This demo will test:

- Basic SRT connection
- Configuration options
- Health monitoring  
- Streaming capabilities
- Failover scenarios
- Egress integration

### Unit Tests

```bash
pytest tests/test_srt_integration.py -v
```

### Connection Testing

```python
from Desktop.Backend.core.srt_integration import test_srt_connection

# Test connection to SRT server
success = await test_srt_connection("srt-server.com", 9999)
print(f"Connection test: {'✅ Pass' if success else '❌ Fail'}")
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**

   ```text
   Error: FFmpeg not found. Please install FFmpeg with SRT support
   Solution: Install FFmpeg with libsrt support (see Installation)
   ```

2. **SRT connection timeout**

   ```text
   Error: SRT connection test failed
   Solution: Check firewall, network connectivity, server availability
   ```

3. **Encryption issues**

   ```text
   Error: SRT connection failed with encryption
   Solution: Verify passphrase, check encryption mode compatibility
   ```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger("Desktop.Backend.core.srt_integration").setLevel(logging.DEBUG)
```

### Network Testing

```bash
# Test UDP connectivity to SRT port
nc -u srt-server.com 9999

# Check firewall rules
sudo ufw status

# Test with ffmpeg directly
ffmpeg -f lavfi -i testsrc=duration=10:size=1920x1080:rate=30 \
       -f mpegts srt://srt-server.com:9999
```

## Performance Optimization

### Latency Optimization

- **Ultra-Low Latency**: 500-1000ms (gaming, interactive)
- **Low Latency**: 1000-2000ms (live events, news)
- **Standard Latency**: 2000-4000ms (general broadcasting)

### Buffer Sizing

```python
# High bandwidth, reliable networks
config.buffer_size = 12800000  # 12.8MB

# Variable networks, mobile
config.buffer_size = 25600000  # 25.6MB  

# Poor networks, maximum reliability
config.buffer_size = 51200000  # 51.2MB
```

### Encryption Performance

- **No Encryption**: Maximum performance
- **AES128**: Good security, minimal overhead
- **AES256**: Maximum security, moderate overhead

## Integration Examples

### YouTube + SRT Dual-Path

```python
# Setup dual-path streaming
youtube_config = create_youtube_dual_stream_config(
    primary_key_en="YOUR_EN_KEY",
    primary_key_fr="YOUR_FR_KEY", 
    backup_srt_url="srt://backup.com:9999"
)

# Start streaming with SRT backup
manager = YouTubeDualStreamManager(youtube_config)
await manager.start_streaming(slate_manager)
```

### Multi-SRT Configuration

```python
# Multiple SRT destinations
srt_destinations = [
    create_srt_config("primary.com", 9999, encryption="aes256"),
    create_srt_config("backup1.com", 9999, encryption="aes128"), 
    create_srt_config("backup2.com", 8080, encryption="none")
]

# Prioritized failover chain
for dest in srt_destinations:
    if await test_srt_connection(dest.host, dest.port):
        await start_streaming_to_srt(dest)
        break
```

## Conclusion

This SRT implementation provides professional-grade streaming capabilities with:

✅ **Production Ready**: Native libsrt integration via FFmpeg
✅ **Reliable**: Automatic error recovery and retransmission  
✅ **Secure**: AES encryption with passphrase protection
✅ **Monitored**: Real-time statistics and health scoring
✅ **Integrated**: Seamless integration with dual-path egress system
✅ **Tested**: Comprehensive demo and testing framework

The implementation is ready for Phase 2 deployment of the dual-path egress system, providing robust backup streaming capabilities for professional content creators worldwide.
