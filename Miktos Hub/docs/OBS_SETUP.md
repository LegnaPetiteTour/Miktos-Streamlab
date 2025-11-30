# OBS Studio Setup Guide

Complete guide for configuring OBS Studio to work with Miktos Hub.

## Prerequisites

- OBS Studio 30.0 or higher
- WebSocket Server plugin (included in OBS 28+)
- Miktos Hub installed

## Part 1: Basic OBS Configuration

### 1. Enable WebSocket Server

1. Open OBS Studio
2. Navigate to **Tools → WebSocket Server Settings**
3. **Enable WebSocket server** (check the box)
4. Configure settings:
   - **Server Port**: `4455` (default, recommended)
   - **Enable Authentication**: Check this for security
   - **Password**: Set a strong password (save it for later)
5. Click **Apply** then **OK**

### 2. Update Miktos Hub Configuration

Edit `config/settings.py` in your Miktos Hub directory:

```python
class OBSConfig:
    host = "localhost"  # Use "localhost" for same machine
    port = 4455  # Match OBS WebSocket port
    password = "your_password_here"  # Password from step 1
    timeout = 5  # Connection timeout in seconds
    
    # Auto-reconnect settings
    reconnect_enabled = True
    reconnect_delay = 5
    max_reconnect_attempts = 3
```

### 3. Verify Connection

Start Miktos Hub and check the health endpoint:

```bash
curl http://localhost:8000/api/health
```

Look for OBS Engine status:

```json
{
  "name": "OBS Engine",
  "status": "healthy",
  "message": "Connected to OBS WebSocket"
}
```

## Part 2: Scene Setup

### Creating Scenes for Multi-Camera Streaming

#### Scene 1: Main Camera (Full Screen)

1. **Create Scene**
   - Click **+** in Scenes panel
   - Name it `Sony_Main`

2. **Add Video Source**
   - In Sources panel, click **+**
   - Select **Video Capture Device**
   - Name it `Sony a7 IV`
   - Device: **Imaging Edge Webcam**
   - Resolution: **1920x1080** or **3840x2160**
   - FPS: **30** (match camera setting)
   - Click **OK**

3. **Position Source**
   - Right-click source → **Transform → Fit to screen**
   - Or manually resize to fill canvas

#### Scene 2: Picture-in-Picture (PIP)

1. **Create Scene**
   - Name it `Sony_PIP`

2. **Add Main Feed** (full screen background)
   - Add **Video Capture Device**
   - Name: `Sony Main BG`
   - Device: **Imaging Edge Webcam**
   - Fit to screen

3. **Add PIP Overlay** (smaller window)
   - Add another **Video Capture Device** or **Scene** source
   - Name: `PIP Overlay`
   - Position in corner (typically top-right or bottom-right)
   - Resize to ~25% of screen
   - Optional: Add border effect

4. **Add Border** (optional)
   - Right-click PIP source → **Filters**
   - Click **+** → **Color Correction**
   - Adjust to create border effect

#### Scene 3: Intro/Branding Scene

1. **Create Scene**
   - Name it `Intro Scene`

2. **Add Background**
   - Image Source or Color Source
   - Your logo/branding

3. **Add Text**
   - Text (GDI+) or Text (FreeType 2)
   - Stream title, schedule, etc.

4. **Add Animation** (optional)
   - Use Move Transition plugin
   - Fade in/out effects

### Scene Collection Best Practices

**Naming Convention**:

- Use clear, descriptive names
- Prefix by camera: `Sony_Main`, `Sony_PIP`
- Suffix by purpose: `_Intro`, `_Outro`, `_BRB`

**Organization**:

- Group related scenes
- Keep scene count manageable (8-12 scenes recommended)
- Delete unused scenes

## Part 3: Streaming Configuration

### RTMP Streaming Setup

#### For Local Testing (MediaMTX)

1. **Configure Stream Settings**
   - Settings → **Stream**
   - Service: **Custom**
   - Server: `rtmp://localhost:1935/live`
   - Stream Key: `test_stream`

2. **Configure Output**
   - Settings → **Output**
   - Output Mode: **Advanced**
   - Streaming Tab:
     - Encoder: **Hardware (H.264)** or **x264**
     - Rate Control: **CBR**
     - Bitrate: **2500-6000 Kbps** (adjust based on upload speed)
     - Keyframe Interval: **2** seconds
     - Preset: **veryfast** to **medium**

3. **Configure Video**
   - Settings → **Video**
   - Base (Canvas) Resolution: **1920x1080**
   - Output (Scaled) Resolution: **1920x1080**
   - Downscale Filter: **Lanczos**
   - FPS: **30** (or **60** for high motion)

#### For YouTube Streaming

1. **Get Stream Key**
   - Go to YouTube Studio
   - **Go Live** → **Stream**
   - Copy **Stream key**

2. **Configure OBS**
   - Settings → **Stream**
   - Service: **YouTube - RTMPS**
   - Server: **Primary YouTube ingest server**
   - Stream Key: Paste your key

3. **Recommended Settings**
   - Bitrate: **4500-6000 Kbps** (1080p30)
   - Keyframe Interval: **2** seconds
   - Encoder: **Hardware (NVENC)** if available

#### For Twitch Streaming

1. **Get Stream Key**
   - Twitch Dashboard → **Settings → Stream**
   - Copy **Primary Stream key**

2. **Configure OBS**
   - Settings → **Stream**
   - Service: **Twitch**
   - Server: **Auto** (or select closest server)
   - Stream Key: Paste your key

3. **Recommended Settings**
   - Bitrate: **3000-6000 Kbps**
   - Keyframe Interval: **2** seconds
   - Audio: **160 Kbps**, **44.1kHz**

## Part 4: Audio Configuration

### Setting Up Audio Sources

1. **Desktop Audio**
   - Settings → **Audio**
   - Desktop Audio: Select your audio output device
   - Use for system sounds, music, etc.

2. **Microphone**
   - Mic/Auxiliary Audio: Select your microphone
   - Add **Noise Suppression** filter
   - Add **Compressor** for consistent levels

3. **Camera Audio** (Sony a7 IV)
   - If using camera microphone via Imaging Edge
   - May need separate audio interface for better quality

### Audio Filters (Recommended)

For microphone audio:

1. **Noise Suppression**
   - RNNoise or NVIDIA Noise Removal
   - Helps reduce background noise

2. **Gain**
   - Adjust if mic is too quiet
   - Typically +5 to +15 dB

3. **Compressor**
   - Evens out volume levels
   - Ratio: 3:1 to 6:1
   - Threshold: -20 to -10 dB

4. **Limiter**
   - Prevents audio clipping
   - Threshold: -6 dB
   - Release: 60ms

## Part 5: Advanced Features

### Transitions

1. **Configure Scene Transitions**
   - Right-click scene → **Transition Override**
   - Choose transition type:
     - **Fade**: Smooth, professional
     - **Cut**: Instant, no transition
     - **Stinger**: Custom video transition
   - Set duration: **300-500ms** recommended

### Hotkeys

Set up keyboard shortcuts for quick control:

1. **Settings → Hotkeys**
2. Assign keys for:
   - Start/Stop Streaming: `F1`
   - Start/Stop Recording: `F2`
   - Scene switches: `F3`, `F4`, `F5`, etc.
   - Mute/Unmute Mic: `F6`
   - Enable/Disable sources

### Studio Mode

Enable for safer live switching:

1. Click **Studio Mode** in OBS
2. Left side: **Preview** (what you're preparing)
3. Right side: **Program** (what's live)
4. Edit scenes in Preview before going live
5. Click **Transition** when ready

## Part 6: Integration with Miktos Hub

### Scene Control via API

Once OBS is configured, Miktos Hub can control it programmatically:

```python
# Example: Switch scenes via API
import httpx

# Create session
response = httpx.post("http://localhost:8000/api/sessions/", json={
    "name": "My Stream",
    "description": "Live streaming session"
})
session_id = response.json()["session_id"]

# Switch to Sony_Main scene
httpx.post(
    f"http://localhost:8000/api/sessions/{session_id}/scenes/Sony_Main/activate"
)

# Start streaming
httpx.post(
    f"http://localhost:8000/api/sessions/{session_id}/streaming/start"
)
```

See [API_EXAMPLES.md](API_EXAMPLES.md) for more examples.

### Automated Scene Switching

You can create workflows that automatically switch scenes:

```python
# Example: Automated intro sequence
scenes = ["Intro Scene", "Sony_Main", "Sony_PIP"]
for scene in scenes:
    switch_scene(session_id, scene)
    time.sleep(10)  # Show each scene for 10 seconds
```

## Troubleshooting

### Connection Issues

**Problem**: "OBS Engine: unhealthy - Connection failed"

**Solutions**:

1. Verify OBS WebSocket is enabled
2. Check port number matches (4455)
3. Verify password is correct
4. Check firewall settings
5. Restart OBS Studio

### Scene Not Found

**Problem**: API returns "Scene not found"

**Solutions**:

1. Verify scene name matches exactly (case-sensitive)
2. List scenes via API: `GET /api/sessions/{id}/scenes`
3. Check scene exists in OBS

### Stream Won't Start

**Problem**: Stream fails to start via API

**Solutions**:

1. Verify RTMP server is running (for local streaming)
2. Check stream key/server settings in OBS
3. Ensure internet connection is stable
4. Try starting stream manually in OBS first

### Performance Issues

**Problem**: Dropped frames, lag, stuttering

**Solutions**:

1. Lower output resolution (1080p → 720p)
2. Reduce bitrate
3. Use hardware encoder if available
4. Close unnecessary applications
5. Check CPU/GPU usage
6. Use faster encoder preset

## Best Practices

1. **Test before going live**
   - Do a test stream to verify everything works
   - Check audio levels
   - Test scene transitions

2. **Monitor performance**
   - Watch OBS stats (bottom right)
   - CPU usage should be < 80%
   - Dropped frames should be 0% or < 0.1%

3. **Have backups**
   - Save multiple scene collections
   - Export OBS profile
   - Document your setup

4. **Keep it simple**
   - Start with basic scenes
   - Add complexity gradually
   - Don't overcomplicate your workflow

## Next Steps

- 📷 [Camera Pairing Guide](CAMERA_PAIRING.md) - Set up multiple cameras
- 🔧 [API Examples](API_EXAMPLES.md) - Control OBS via API
- 🐛 [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

**Need help?** Check the [Troubleshooting Guide](TROUBLESHOOTING.md) or open an issue on GitHub.
