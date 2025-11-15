# Architecture Documentation - Miktos StreamLab

**Version**: 1.0  
**Last Updated**: Week 2  
**Status**: Living Document

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Core Modules](#core-modules)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Core Modules](#core-modules)
7. [Integration Points](#integration-points)
8. [Security Architecture](#security-architecture)
9. [Performance Considerations](#performance-considerations)
10. [Failure Modes & Recovery](#failure-modes--recovery)

---

## System Overview

### High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface (Future)                   │
│                    (PyQt6/Electron Dashboard)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     Core Application Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Config     │  │    Logger    │  │   Network    │         │
│  │  Management  │  │   System     │  │  Monitoring  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Production Control Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Egress     │  │    ISO       │  │    Scene     │         │
│  │   Manager    │  │  Recording   │  │ Automation   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Image     │  │   Stream     │  │   Camera     │         │
│  │   Quality    │  │   Health     │  │   Manager    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      AI Processing Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │Transcription │  │  Translation │  │     Clip     │         │
│  │   Engine     │  │    Engine    │  │  Generator   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │    Image     │  │     ROI      │                            │
│  │   Quality    │  │   Tracking   │                            │
│  └──────────────┘  └──────────────┘                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Integration Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │     OBS      │  │    NVIDIA    │  │   Platform   │         │
│  │  WebSocket   │  │  Broadcast   │  │     APIs     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │     Chat     │  │    Remote    │  │    Social    │         │
│  │ Aggregation  │  │    Guests    │  │   Platforms  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     Transport Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │     RTMP     │  │     SRT      │  │    WHIP      │         │
│  │   Streaming  │  │    Relay     │  │   (Future)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────────────────────────────────────────────┘
```

---

## Architecture Principles

### 1. Reliability First

- **Dual-path egress**: Never rely on single connection
- **Graceful degradation**: System continues with reduced features
- **Automatic recovery**: Self-healing on failures
- **Comprehensive logging**: Every failure is captured

### 2. Modularity & Extensibility

- **Loose coupling**: Modules communicate via well-defined interfaces
- **Plugin architecture**: Easy to add new platforms, features
- **Configuration-driven**: Behavior changed without code changes
- **Type-safe**: Strong typing throughout for maintainability

### 3. Performance & Efficiency

- **Async-first**: Non-blocking I/O for all operations
- **Resource monitoring**: Track CPU, GPU, memory, disk
- **Adaptive behavior**: Auto-adjust based on available resources
- **Efficient processing**: Minimal overhead on stream quality

### 4. Security & Privacy

- **Encrypted credentials**: Never store keys in plaintext
- **Secure communications**: TLS/SSL for all external connections
- **Data isolation**: User data stays local
- **Audit logging**: Track all security-relevant operations

### 5. Production-Grade Quality

- **Comprehensive testing**: Unit, integration, system tests
- **Error handling**: Every function handles failures
- **Documentation**: Code is self-documenting
- **Monitoring**: Real-time health metrics

---

## Core Modules

### Foundation Modules ✅ (Phase 1)

#### 1. Configuration Management (`src/core/config.py`)

**Purpose**: Centralized, type-safe configuration with encryption

**Responsibilities**:

- Load/save configuration from files
- Encrypt sensitive credentials (Fernet)
- Validate configuration integrity
- Provide type-safe access to settings
- Support multiple profiles

**Key Classes**:


```python
@dataclass
class AppConfig:

    obs: OBSConfig
    streaming: StreamConfig
    transcription: TranscriptionConfig
    network: NetworkConfig
    
class ConfigManager:

    def load_config(path: str) -> AppConfig
    def save_config(config: AppConfig, path: str)
    def encrypt_credential(value: str) -> str
    def decrypt_credential(encrypted: str) -> str
```

**Dependencies**: `cryptography`, `python-dotenv`

---

#### 2. Logging System (`src/core/logger.py`)

**Purpose**: Structured, multi-target logging with rotation

**Responsibilities**:

- JSON-structured logging for machine parsing
- Colored console output for humans
- Automatic log rotation (10MB files, 5 backups)
- Separate error logs
- Stream event tracking

**Key Functions**:


```python
def setup_logging(log_dir: str, level: str)
def get_logger(name: str) -> logging.Logger
def log_stream_event(event_type: str, data: dict)
```

**Log Levels**:

- `DEBUG`: Detailed diagnostic info
- `INFO`: General operational events
- `WARNING`: Potential issues
- `ERROR`: Failures that don't stop operation
- `CRITICAL`: Failures that require immediate attention

---

#### 3. Network Monitoring (`src/core/network.py`)

**Purpose**: Real-time network quality assessment

**Responsibilities**:

- Speed testing (upload/download)
- Latency and jitter measurement
- 5-level status assessment (Excellent → Critical)
- Bitrate recommendations
- Pre-stream readiness checks

**Key Classes**:


```python
@dataclass
class NetworkStatus:

    download_mbps: float
    upload_mbps: float
    latency_ms: float
    jitter_ms: float
    packet_loss_pct: float
    status: NetworkQuality
    recommended_bitrate: int
    
class NetworkMonitor:

    async def run_speed_test() -> SpeedTestResult
    async def check_latency() -> LatencyResult
    def assess_quality(results) -> NetworkStatus
    def get_recommendations() -> BitrateRecommendations
```

**Status Levels**:

1. **Excellent**: >50 Mbps up, <30ms latency, 0% loss
2. **Good**: 25-50 Mbps up, 30-50ms latency, <0.5% loss
3. **Fair**: 10-25 Mbps up, 50-100ms latency, 0.5-1% loss
4. **Poor**: 5-10 Mbps up, 100-200ms latency, 1-3% loss
5. **Critical**: <5 Mbps up, >200ms latency, >3% loss

---

#### 4. AI Transcription (`src/core/transcription.py`)

**Purpose**: Real-time and post-stream transcription with translation

**Responsibilities**:

- OpenAI Whisper integration
- Bilingual support (EN/FR automatic detection)
- Multiple export formats (SRT, VTT, TXT)
- Timestamp-synchronized subtitles
- Language filtering

**Key Classes**:


```python
class TranscriptionEngine:

    async def transcribe_audio(audio_path: str) -> Transcription
    def detect_language(audio_chunk) -> str
    def export_srt(transcription) -> str
    def export_vtt(transcription) -> str
    def filter_by_language(transcription, lang) -> Transcription
```

**Supported Formats**:

- **SRT**: Standard subtitle format
- **VTT**: Web-based captions
- **TXT**: Plain text with timestamps
- **JSON**: Structured data for processing

---

#### 5. OBS Controller (`src/obs_controller.py`)

**Purpose**: Complete OBS WebSocket API wrapper

**Responsibilities**:

- Scene and source management
- Streaming control (start/stop/status)
- Recording management
- Source filter control
- Connection health monitoring

**Key Classes**:


```python
class OBSController:

    async def connect(host: str, port: int, password: str)
    async def disconnect()
    
    # Streaming
    async def start_streaming()
    async def stop_streaming()
    async def get_stream_status() -> StreamStatus
    
    # Scenes
    async def get_scenes() -> List[Scene]
    async def set_current_scene(scene_name: str)
    async def create_scene(scene_name: str)
    
    # Sources
    async def get_sources() -> List[Source]
    async def set_source_visibility(source: str, visible: bool)
    async def apply_filter(source: str, filter: Filter)
    
    # Recording
    async def start_recording()
    async def stop_recording()
    async def get_recording_status() -> RecordingStatus
```

---

### Production Control Modules 🔜 (Phase 2-3)

#### 6. Egress Manager (`src/core/egress.py`) 🔜 Week 2-3

**Purpose**: Multi-destination streaming with automatic failover

**Architecture**:


```python
class EgressDestination(ABC):

    """Abstract base for streaming destinations"""
    @abstractmethod
    async def connect() -> bool
    @abstractmethod
    async def send_frame(frame: Frame)
    @abstractmethod
    async def disconnect()
    @abstractmethod
    def get_health() -> DestinationHealth

class RTMPDestination(EgressDestination):

    """YouTube, Twitch, Facebook via RTMP"""
    def __init__(self, url: str, key: str)
    # Implementation via FFmpeg

class SRTDestination(EgressDestination):

    """SRT relay for failover"""
    def __init__(self, url: str, latency_ms: int)
    # Implementation via libsrt

class EgressManager:

    """Orchestrates multiple destinations with failover"""
    def __init__(self):
        self.primary: EgressDestination
        self.backup: Optional[EgressDestination]
        self.failover_active: bool = False
    
    async def start_streaming(destinations: List[EgressDestination]):
        """Start all destinations, monitor health"""
        
    async def monitor_health(self):
        """Continuous health checking"""
        while self.streaming:
            health = await self.primary.get_health()
            if health.is_failing:
                await self.initiate_failover()
    
    async def initiate_failover(self):
        """Switch to backup, show slate, attempt recovery"""
        self.failover_active = True
        await self.show_slate()
        await self.backup.connect()
        await self.attempt_primary_recovery()
```

**Failover Logic**:

1. Monitor primary connection health (packet loss, RTT)
2. On failure detection (>5% loss or >500ms RTT for 10s):
   - Switch OBS output to backup destination
   - Display "Technical Difficulties" slate on primary
   - Log failure event

3. Attempt primary reconnection every 30 seconds
4. On primary recovery:
   - Fade out slate
   - Switch back to primary
   - Mark failover complete

**Configuration**:

```yaml
egress:

  primary:
    type: rtmp
    url: rtmp://a.rtmp.youtube.com/live2
    key: ${YOUTUBE_STREAM_KEY}
    
  backup:
    type: srt
    url: srt://relay.example.com:9998
    latency_ms: 2000
    
  failover:
    trigger_packet_loss_pct: 5.0
    trigger_rtt_ms: 500
    trigger_duration_sec: 10
    retry_interval_sec: 30
```

---

#### 7. Stream Health Monitor (`src/core/health.py`) 🔜 Week 3-4

**Purpose**: Real-time stream quality metrics and alerts

**Architecture**:

```python
@dataclass
class StreamHealth:

    timestamp: datetime
    
    # Network metrics
    bitrate_mbps: float
    dropped_frames: int
    network_jitter_ms: float
    
    # System metrics
    cpu_usage_pct: float
    gpu_usage_pct: float
    memory_usage_mb: float
    disk_space_gb: float
    
    # Stream metrics (per destination)
    destinations: Dict[str, DestinationHealth]
    
    # Overall status
    status: HealthStatus  # Healthy, Warning, Critical
    issues: List[HealthIssue]
    
@dataclass
class DestinationHealth:

    name: str
    connected: bool
    bitrate_actual: float
    bitrate_target: float
    dropped_frames: int
    rtt_ms: float
    packet_loss_pct: float

class StreamHealthMonitor:

    def __init__(self, obs: OBSController, egress: EgressManager):
        self.obs = obs
        self.egress = egress
        self.history: List[StreamHealth] = []
        
    async def get_current_health(self) -> StreamHealth:
        """Gather all current metrics"""
        
    async def monitor_continuously(self, interval_sec: float = 1.0):
        """Continuous monitoring loop"""
        while self.monitoring:
            health = await self.get_current_health()
            self.history.append(health)
            
            if health.status == HealthStatus.CRITICAL:
                await self.alert_critical(health)
            elif health.status == HealthStatus.WARNING:
                await self.alert_warning(health)
            
            await asyncio.sleep(interval_sec)
    
    def export_health_log(self, start: datetime, end: datetime) -> str:
        """Export health metrics as JSON for analysis"""
```

**Alert Thresholds**:

```python
class HealthThresholds:

    # Warning thresholds
    WARN_DROPPED_FRAMES = 10  # per second
    WARN_CPU_USAGE = 80  # percent
    WARN_GPU_USAGE = 85  # percent
    WARN_DISK_SPACE_GB = 10
    WARN_BITRATE_VARIANCE = 20  # percent from target
    
    # Critical thresholds
    CRIT_DROPPED_FRAMES = 30  # per second
    CRIT_CPU_USAGE = 95  # percent
    CRIT_GPU_USAGE = 98  # percent
    CRIT_DISK_SPACE_GB = 2
    CRIT_BITRATE_VARIANCE = 40  # percent from target
    CRIT_PACKET_LOSS = 5  # percent
```

---

#### 8. ISO Recording System (`src/core/iso_recording.py`) 🔜 Week 5-6

**Purpose**: Multi-track recording for backup and editing

**Architecture**:

```python
@dataclass
class RecordingTrack:

    name: str
    source_type: str  # 'program', 'camera', 'microphone', 'screen'
    output_path: Path
    format: str  # 'mp4', 'mkv', 'mov'
    codec: str  # 'h264', 'h265', 'prores'
    audio_buses: List[int]  # Which audio tracks to include

class ISORecorder:

    def __init__(self, obs: OBSController, storage_path: Path):
        self.obs = obs
        self.storage_path = storage_path
        self.tracks: Dict[str, RecordingTrack] = {}
        self.recording_active: bool = False
        
    async def start_recording(self, tracks: List[RecordingTrack]):
        """Start recording all specified tracks"""
        for track in tracks:
            await self._start_track_recording(track)
        self.recording_active = True
        
    async def stop_recording(self) -> RecordingManifest:
        """Stop all recordings, return manifest"""
        files = []
        for track_name, track in self.tracks.items():
            await self._stop_track_recording(track)
            files.append(track.output_path)
        
        return RecordingManifest(
            started_at=self.start_time,
            ended_at=datetime.now(),
            duration_sec=(datetime.now() - self.start_time).total_seconds(),
            tracks=files,
            disk_usage_mb=self._calculate_disk_usage(files)
        )
    
    async def get_replay_buffer(self, duration_sec: float) -> Path:
        """Save last N seconds from buffer"""
```

**Storage Management**:

```python
class StorageManager:

    def __init__(self, base_path: Path, retention_hours: int = 168):
        self.base_path = base_path
        self.retention_hours = retention_hours
        
    def check_available_space(self) -> float:
        """Return available space in GB"""
        
    def cleanup_old_recordings(self):
        """Delete recordings older than retention period"""
        
    def estimate_recording_duration(self, bitrate_mbps: float) -> float:
        """Estimate how long we can record with available space"""
```

---

## Data Flow

### Streaming Data Flow

```text
┌──────────┐
│   OBS    │ ← User configures scenes, sources
│ Sources  │
└────┬─────┘
     │
     ▼
┌──────────────────┐
│  OBS Compositor  │ ← Mixes video/audio
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  OBS Encoder     │ ← H.264/HEVC encoding
└────┬─────────────┘
     │
     ├──────────────┐
     │              │
     ▼              ▼
┌─────────┐   ┌─────────────┐
│ RTMP    │   │     ISO     │
│ Primary │   │  Recorder   │
└────┬────┘   └─────────────┘
     │
     ▼
┌─────────────────┐
│ Egress Manager  │ ← Our code monitors health
└────┬────────────┘
     │
     ├──────────────┐
     │              │
     ▼              ▼
┌─────────┐   ┌─────────┐
│ YouTube │   │   SRT   │
│  RTMP   │   │  Relay  │
└─────────┘   └─────────┘
     │              │
     └──────┬───────┘
            │
            ▼
      ┌─────────┐
      │ Viewers │
      └─────────┘
```

### Transcription Data Flow

```text
┌────────────┐
│    OBS     │
│   Audio    │
│   Output   │
└─────┬──────┘
      │
      ▼
┌────────────────┐
│ Audio Capture  │ ← Record chunks (30s intervals)
└─────┬──────────┘
      │
      ▼
┌────────────────┐
│ Whisper API    │ ← Transcribe chunk
└─────┬──────────┘
      │
      ▼
┌────────────────────┐
│ Language Detection │ ← Identify EN/FR
└─────┬──────────────┘
      │
      ▼
┌─────────────────┐
│ Transcription   │ ← Store with timestamps
│   Storage       │
└─────┬───────────┘
      │
      ├──────────────┬──────────────┐
      │              │              │
      ▼              ▼              ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│   SRT   │    │   VTT   │    │   TXT   │
│  Export │    │  Export │    │  Export │
└─────────┘    └─────────┘    └─────────┘
```

---

## Technology Stack

### Core Technologies

**Language**: Python 3.11+

- Type hints throughout
- Async/await for concurrency
- Dataclasses for structured data

**OBS Integration**:

- `obs-websocket-py` - WebSocket API client
- OBS Studio 28+ required

**Video/Audio Processing**:

- `ffmpeg-python` - FFmpeg wrapper for encoding
- `opencv-python` - Image processing, face detection
- `libsrt` - SRT protocol support

**AI/ML**:

- `openai` - Whisper transcription API
- `whisper` (optional) - Local Whisper model
- `numpy` - Numerical processing

**Networking**:

- `aiohttp` - Async HTTP client
- `speedtest-cli` - Network speed testing
- `websockets` - WebSocket communication

**Security**:

- `cryptography` - Fernet encryption for credentials
- `python-dotenv` - Environment variable management

**UI (Future)**:

- `PyQt6` or `Electron` - Desktop interface
- `matplotlib` / `plotly` - Metrics visualization

**Testing**:

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage
- `pytest-mock` - Mocking utilities

**Development**:

- `black` - Code formatting
- `mypy` - Static type checking
- `pylint` - Linting
- `pre-commit` - Git hooks

---

## Integration Points

### External Services

#### 1. OBS Studio

- **Protocol**: WebSocket (ws://localhost:4455)
- **Authentication**: Password-based
- **API Version**: 5.0+
- **Rate Limiting**: None (local)

#### 2. YouTube Streaming

- **Protocol**: RTMP
- **URL**: `rtmp://a.rtmp.youtube.com/live2`
- **Authentication**: Stream key
- **Requirements**:
  - Keyframe interval: 2 seconds
  - Max bitrate: 51 Mbps (8K), typically 4.5-9 Mbps (1080p)
  - Audio: AAC, 128 kbps

#### 3. OpenAI Whisper

- **Protocol**: HTTPS REST API
- **Endpoint**: `https://api.openai.com/v1/audio/transcriptions`
- **Authentication**: API key (Bearer token)
- **Rate Limiting**: 50 requests/minute (free tier)
- **Max File Size**: 25 MB

#### 4. SRT Relay (Future)

- **Protocol**: SRT
- **Port**: Configurable (typically 9998)
- **Latency**: Configurable (1000-3000ms recommended)

---

## Security Architecture

### Credential Management

**Storage**:

```text
$HOME/.streamlab/
├── config.yaml          # Non-sensitive config
├── credentials.enc      # Encrypted credentials
└── .encryption_key      # Fernet key (chmod 600)
```

**Encryption**:

```python
from cryptography.fernet import Fernet

# Generate key (once)
key = Fernet.generate_key()

# Encrypt
f = Fernet(key)
encrypted = f.encrypt(b"youtube_stream_key_here")

# Decrypt
decrypted = f.decrypt(encrypted)
```

**Environment Variables** (Alternative):

```bash
# .env file (never commit)
YOUTUBE_STREAM_KEY=your-key-here
OPENAI_API_KEY=sk-...
OBS_WEBSOCKET_PASSWORD=your-password
```

### Network Security

**TLS/SSL**:

- All external APIs use HTTPS
- OBS WebSocket can use WSS (future)

**Firewall Rules**:

- Outbound: Allow RTMP (1935), SRT (9998), HTTPS (443)
- Inbound: Block all (no server component)

---

## Performance Considerations

### Resource Targets

**CPU Usage**:

- Baseline: <10% (idle)
- During stream: <30% (monitoring/transcription)
- OBS encoding: 40-60% (separate process)

**Memory Usage**:

- Baseline: ~200 MB
- During stream: ~500 MB
- Transcription buffer: ~100 MB

**Disk I/O**:

- ISO recording: ~50 MB/min per track
- Log files: ~1 MB/hour
- Transcription cache: ~10 MB/hour

**Network**:

- Upload: 5-10 Mbps (stream) + 0.1 Mbps (monitoring)
- Download: <1 Mbps (API responses)

### Optimization Strategies

1. **Async Processing**:

   - All I/O operations are async (network, disk, API calls)
   - Prevents blocking the main thread
   

2. **Batching**:

   - Transcription: Process in 30s chunks
   - Metrics collection: 1s intervals
   - Health checks: 5s intervals
   
3. **Caching**:

   - Configuration cached in memory
   - Network status cached for 10s
   - OBS status cached for 1s
   
4. **Resource Monitoring**:

   - Track CPU/GPU usage continuously
   - Auto-disable heavy features if resources constrained
   - Alert user when resources critical

---

## Failure Modes & Recovery

### Network Failures

**Scenario**: Internet connection drops

**Detection**:

- Speedtest fails
- RTMP connection drops
- API calls timeout

**Recovery**:

1. Display "Connection Lost" overlay
2. Continue ISO recording
3. Attempt reconnection every 30s
4. On recovery, resume streaming from last good frame

---

**Scenario**: High packet loss (>5%)

**Detection**:

- Monitor RTT and dropped frames
- 3 consecutive checks above threshold

**Recovery**:

1. Alert user (warning notification)
2. If primary RTMP, failover to SRT
3. Reduce bitrate recommendation
4. Log detailed network metrics for diagnosis

---

### OBS Failures

**Scenario**: OBS crashes

**Detection**:

- WebSocket connection lost
- Heartbeat timeout (10s)

**Recovery**:

1. Log crash event
2. Alert user immediately
3. Stop monitoring gracefully
4. Preserve all recordings/logs
5. Provide diagnostic information

---

**Scenario**: Encoding overload (dropped frames)

**Detection**:

- Dropped frame count increasing
- Encoding lag >100ms

**Recovery**:

1. Alert user (warning)
2. Suggest bitrate reduction
3. Identify resource-heavy sources
4. Optionally pause non-essential features (e.g., face tracking)

---

### Disk Failures

**Scenario**: Disk full during recording

**Detection**:

- Pre-flight check: <2 GB available
- During recording: <1 GB remaining

**Recovery**:

1. Alert user immediately
2. Stop ISO recording gracefully
3. Continue streaming (critical function)
4. Suggest cleanup or change recording path

---

### API Failures

**Scenario**: OpenAI API fails (transcription)

**Detection**:

- HTTP 5xx errors
- Connection timeout
- Rate limit exceeded

**Recovery**:

1. Log failure details
2. Queue audio chunk for retry
3. Continue with blank captions
4. Alert user (low priority)
5. Retry with exponential backoff

---

### Application Crashes

**Scenario**: Python exception causes crash

**Prevention**:

- Try/except blocks around all critical functions
- Comprehensive error logging
- Graceful shutdown handlers

**Recovery**:

1. Log full stack trace
2. Save current state (config, metrics)
3. Attempt to stop streams gracefully
4. Create crash report
5. Auto-restart (future feature)

---

## Testing Strategy

### Unit Tests

- Each module has comprehensive unit tests
- Mock external dependencies (OBS, APIs)
- Target: 80%+ coverage

### Integration Tests

- Test module interactions
- Use test OBS instance
- Validate end-to-end flows

### System Tests

- Full application testing
- Real streaming (to test server)
- Performance benchmarks

### Test Structure

```text
tests/
├── unit/
│   ├── test_config.py
│   ├── test_network.py
│   ├── test_transcription.py
│   ├── test_egress.py
│   ├── test_health.py
│   └── test_iso_recording.py
├── integration/
│   ├── test_obs_integration.py
│   ├── test_streaming_flow.py
│   └── test_failover.py
├── system/
│   ├── test_full_stream.py
│   └── test_performance.py
└── conftest.py  # Shared fixtures
```

---

## Deployment Architecture

### Development Environment

```text
Local Machine
├── OBS Studio (production)
├── Python virtual environment
├── Test streaming server (optional)
└── Test data files
```

### Production Environment (City of Ottawa)

```text
Production Machine
├── OBS Studio (configured)
├── Miktos StreamLab (installed)
├── Network: Reliable internet (50+ Mbps up)
├── Storage: 500+ GB for recordings
└── Backup: External drive for archives
```

---

## Future Architecture Considerations

### Scalability

- **Multiple concurrent streams**: Architecture supports this
- **Cloud deployment**: Could run on server for remote control
- **Distributed processing**: Transcription could be offloaded

### Extensibility

- **Plugin system**: For custom integrations
- **REST API**: For external control
- **WebSocket API**: For real-time updates to UI

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Week 2 | Initial architecture document |

---

## Review Schedule

- **Weekly**: During active development
- **Monthly**: During maintenance
- **Quarterly**: Major architectural reviews

