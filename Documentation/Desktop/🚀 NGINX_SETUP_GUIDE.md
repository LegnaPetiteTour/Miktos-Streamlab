# Week 5 Phase 2: NGINX RTMP Setup

Quick Start Guide for Dual-Path Streaming

## Status

- ✅ Phase 1: RTMP Dual-Output Code Complete (egress_v2.py)
- 🎯 Phase 2: NGINX RTMP Setup (Current)
- 📋 Phase 3: Live Testing & SRT Backup (Planned)

## Prerequisites Completed

✅ EgressManagerV2 created with dual-destination support  
✅ 22 tests passing (89% coverage)  
✅ .env.example configured  
✅ Documentation complete (500+ lines)  

## Next Steps

### 1. Install NGINX RTMP Module

```bash
brew install nginx-full --with-rtmp-module
```

### 2. Locate nginx.conf

```bash
# Usually at:
/usr/local/etc/nginx/nginx.conf

# Or find it:
nginx -t
```

### 3. Configure NGINX for Dual-Output

Add this RTMP section to nginx.conf:

```nginx
rtmp {
    server {
        listen 1935;
        chunk_size 4096;
        
        application live {
            live on;
            record off;
            
            # Push to YouTube EN
            push rtmp://a.rtmp.youtube.com/live2/YOUR_EN_STREAM_KEY;
            
            # Push to YouTube FR  
            push rtmp://a.rtmp.youtube.com/live2/YOUR_FR_STREAM_KEY;
        }
    }
}
```

**Note**: Replace `YOUR_EN_STREAM_KEY` and `YOUR_FR_STREAM_KEY` with actual keys from YouTube Studio.

### 4. Add Stats Page (Optional)

Add this HTTP section:

```nginx
http {
    server {
        listen 8080;
        
        location /stat {
            rtmp_stat all;
            rtmp_stat_stylesheet stat.xsl;
        }
    }
}
```

### 5. Start NGINX

```bash
# Start service
brew services start nginx-full

# Or run manually
nginx

# Verify running
lsof -i :1935
```

### 6. Configure OBS Studio

**Settings → Stream:**

- Service: Custom
- Server: `rtmp://localhost/live`
- Stream Key: `streamlab` (or any identifier)

**Settings → Output:**

- Output Mode: Advanced
- Encoder: x264 (or Hardware H264)
- Rate Control: CBR
- Bitrate: 5000 Kbps
- Keyframe Interval: 2
- Preset: veryfast

### 7. Get YouTube Stream Keys

1. Go to <https://studio.youtube.com>
2. Select your channel
3. Click "Go Live" or "Create" → "Go Live"
4. Copy the Stream Key (format: xxxx-xxxx-xxxx-xxxx)
5. Repeat for both EN and FR channels

### 8. Update .env File

```bash
# Copy example
cp .env.example .env

# Edit .env and add:
YOUTUBE_EN_STREAM_KEY=xxxx-xxxx-xxxx-xxxx
YOUTUBE_FR_STREAM_KEY=yyyy-yyyy-yyyy-yyyy
```

### 9. Test the Setup

**Start OBS Streaming:**

1. Open OBS Studio
2. Click "Start Streaming"
3. OBS should connect to `rtmp://localhost/live`

**Verify NGINX Relay:**

```bash
# Check NGINX stats
open http://localhost:8080/stat

# Should show:
# - 1 incoming stream (from OBS)
# - 2 outgoing streams (to YouTube EN + FR)
```

**Check YouTube Studio:**

1. Open YouTube Studio for each channel
2. Go to "Go Live" or "Stream"
3. You should see "Stream is Live" indicator
4. Video should appear in 1-2 minutes

### 10. Monitor Health

**Using EgressManagerV2:**

```python
import asyncio
from src.obs_controller import OBSController
from src.core.egress_v2 import EgressManagerV2

async def monitor():
    obs = OBSController(host="localhost", port=4455, password="YOUR_PASSWORD")
    await obs.connect()
    
    egress = EgressManagerV2(obs_controller=obs)
    
    # Start streaming
    await egress.start_streaming()
    
    # Monitor health every 10 seconds
    while egress.is_streaming():
        health = await egress.get_health()
        for dest in health['destinations']:
            print(f"{dest['name']}: {dest['bitrate_kbps']:.1f} Kbps, {dest['drop_percentage']:.2f}% dropped")
        await asyncio.sleep(10)

asyncio.run(monitor())
```

## Troubleshooting

### NGINX Won't Start

```bash
# Check error log
tail -f /usr/local/var/log/nginx/error.log

# Check if port is in use
lsof -i :1935

# Test configuration
nginx -t
```

### OBS Won't Connect

1. Verify NGINX is running: `lsof -i :1935`
2. Check OBS logs: Help → Log Files → View Current Log
3. Verify server URL: `rtmp://localhost/live`

### YouTube Not Receiving Stream

1. Check stream keys are correct in nginx.conf
2. Verify YouTube Studio shows "Waiting for stream"
3. Check NGINX stats: <http://localhost:8080/stat>
4. Look for outgoing connections in stats

### High Dropped Frames

1. Reduce bitrate in OBS (try 3000 Kbps)
2. Use hardware encoder (NVENC/H264)
3. Check upload speed: `speedtest-cli`
4. Close bandwidth-heavy applications

## Expected Performance

- **Bitrate**: 5000 Kbps per destination (10 Mbps total upload)
- **CPU**: ~25% (1080p30, x264 veryfast)
- **RAM**: ~500MB
- **Drop Rate**: <0.1% on good connection
- **Latency**: 1-3 seconds RTMP delay

## Success Criteria

✅ NGINX running on port 1935  
✅ OBS connected to localhost RTMP  
✅ Both YouTube channels receiving stream  
✅ Health monitoring showing <1% drop rate  
✅ Stable streaming for 5+ minutes  

## Files to Reference

- `docs/week-5-6-dual-egress.md` - Complete documentation
- `src/core/egress_v2.py` - Egress manager implementation
- `tests/test_dual_output.py` - Test suite with examples
- `.env.example` - Configuration template

## Next Phase (Phase 3)

After successful NGINX setup:

1. Install SRT: `brew install srt`
2. Create SRTDestination class
3. Add SRT backup to egress_v2.py
4. Test automatic failover
5. Document complete Week 5-6 completion
