# Sony a7 IV End-to-End Testing Guide

This guide walks you through testing the complete Miktos Hub workflow with your Sony a7 IV camera.

## Prerequisites

### 1. Sony a7 IV Setup

Choose one of these connection methods:

#### Option A: HDMI Capture Card (Recommended)
- **Hardware**: HDMI capture card (e.g., Elgato Cam Link 4K, Blackmagic Design)
- **Connection**: Sony a7 IV HDMI → Capture Card → USB to Mac
- **Advantages**: Best quality, lowest latency, no app required
- **Setup**:
  1. Connect camera HDMI output to capture card
  2. Connect capture card USB to your Mac
  3. Camera appears as USB video device

#### Option B: USB Tethering
- **Hardware**: USB-C cable
- **Software**: Sony Imaging Edge Desktop or Webcam app
- **Connection**: Sony a7 IV USB-C → Mac USB-C
- **Advantages**: Single cable solution
- **Setup**:
  1. Install [Sony Imaging Edge Webcam](https://support.d-imaging.sony.co.jp/app/webcam/en/)
  2. Connect camera via USB-C
  3. Enable USB Streaming on camera

#### Option C: Network Streaming
- **Software**: Sony Imaging Edge Mobile app
- **Connection**: WiFi (camera creates hotspot or joins your network)
- **Advantages**: Wireless, flexible positioning
- **Setup**:
  1. Install Imaging Edge Mobile on iPhone/iPad
  2. Enable WiFi on camera
  3. Connect to camera's network
  4. Use RTSP stream URL

### 2. OBS Studio

1. **Install OBS Studio**:
   ```bash
   brew install --cask obs
   ```

2. **Enable WebSocket Server**:
   - Open OBS Studio
   - Go to **Tools → WebSocket Server Settings**
   - Enable WebSocket server
   - Default port: 4455
   - No password required (for testing)

3. **Verify OBS is Running**:
   - OBS should be open before running tests
   - Create a basic scene if needed

### 3. Miktos Hub Server

1. **Start the API server**:
   ```bash
   python main.py
   ```

2. **Verify server is running**:
   - Open http://localhost:8000/docs
   - You should see the FastAPI documentation

## Running the E2E Test

### Basic Usage

```bash
python e2e_sony_a7iv_test.py
```

The script will guide you through:

1. **Server Health Check** - Verifies API is running
2. **Camera Discovery** - Detects or registers your Sony a7 IV
3. **Session Creation** - Creates a streaming session
4. **OBS Configuration** - Sets up scenes with your camera
5. **Streaming Setup** - Configures destinations (optional)
6. **Workflow Test** - Tests the complete pipeline

### Interactive Prompts

#### Camera Connection Type

When prompted, select your connection method:

```
Select connection type (1/2/3):
  1. USB Tethering (recommended for local use)
  2. Network via Imaging Edge Mobile
  3. RTSP stream URL
```

**For HDMI Capture Card**: Choose option 1 (USB)
**For Sony Webcam Utility**: Choose option 1 (USB)
**For Network Streaming**: Choose option 2 or 3

#### Streaming Destinations

```
Configure streaming destinations:
  1. YouTube
  2. Twitch
  3. Facebook Live
  4. Custom RTMP
  5. Skip this step
```

For testing, you can skip (option 5) or use a test RTMP server.

### Sample Test Run

```
============================================================
Sony a7 IV End-to-End Workflow Test
============================================================

[STEP 1] Checking server health...
✅ Server is running: healthy
ℹ️  Server version: 1.0.0

[STEP 2] Discovering Sony a7 IV camera...
ℹ️  Found 0 registered camera(s)
ℹ️  No Sony camera found. Let's register it manually.

Sony a7 IV Connection Options:
  1. USB Tethering (recommended for local use)
  2. Network via Imaging Edge Mobile
  3. RTSP stream URL

Select connection type (1/2/3): 1
ℹ️  USB connection - camera will be detected automatically
✅ Camera registered: Sony a7 IV
ℹ️  Camera ID: abc123def456...

[STEP 3] Creating streaming session...
✅ Session created: Sony a7 IV Test Session
ℹ️  Session ID: xyz789uvw012...
ℹ️  State: idle

[STEP 4] Configuring OBS scenes...
✅ OBS connected: 30.0.0
✅ Created scene: Full Frame
✅ Created scene: Picture in Picture

[STEP 5] Setting up streaming destinations...
Configure streaming destinations:
  1. YouTube
  2. Twitch
  3. Facebook Live
  4. Custom RTMP
  5. Skip this step

Select destination (1-5): 5
ℹ️  Skipping destination setup

[STEP 6] Testing workflow...
✅ Session retrieved successfully
ℹ️  Session: Sony a7 IV Test Session
ℹ️  State: idle
ℹ️  Cameras: 1
ℹ️  Scenes: 2
ℹ️  Destinations: 0

Testing scene switching...
✅ Activated scene: 1a2b3c4d...
✅ Activated scene: 5e6f7g8h...

============================================================
TEST SUMMARY
============================================================

✅ Session ID: xyz789uvw012345678901234567890
✅ Camera ID: abc123def456789012345678901234
✅ Scenes created: 2

Next steps:
  1. View session in browser: http://localhost:8000/sessions/xyz789...
  2. API documentation: http://localhost:8000/docs
  3. Start streaming via API or OBS

Cleanup:
  Delete session: curl -X DELETE http://localhost:8000/api/sessions/xyz789...

✅ E2E Test Complete!
```

## Troubleshooting

### Camera Not Detected

**USB Connection Issues**:
```bash
# Check if camera appears as USB video device
system_profiler SPCameraDataType

# Look for "Sony" or capture card name
```

**Network Connection Issues**:
```bash
# Verify camera is on network
ping <camera-ip-address>

# Check if RTSP port is accessible
nc -zv <camera-ip> 554
```

### OBS Not Connecting

1. **Check OBS is running**:
   ```bash
   ps aux | grep obs
   ```

2. **Verify WebSocket server**:
   - OBS → Tools → WebSocket Server Settings
   - Should show "Server is running on port 4455"

3. **Test WebSocket manually**:
   ```bash
   curl http://localhost:4455
   ```

### API Server Issues

1. **Check server is running**:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **View server logs**:
   - Check terminal where `python main.py` is running
   - Look for error messages

3. **Restart server**:
   ```bash
   # Stop server (Ctrl+C)
   # Start again
   python main.py
   ```

### Scene Creation Fails

- **Ensure camera is connected** before creating scenes
- **Check OBS has at least one scene** in the default profile
- **Verify camera source** is accessible in OBS

## Advanced Usage

### Manual API Testing

After running the E2E test, you can test individual endpoints:

#### Get Session Details
```bash
SESSION_ID="<your-session-id>"
curl http://localhost:8000/api/sessions/$SESSION_ID
```

#### List All Cameras
```bash
curl http://localhost:8000/api/cameras/
```

#### Activate a Scene
```bash
SCENE_ID="<your-scene-id>"
curl -X POST http://localhost:8000/api/scenes/$SCENE_ID/activate
```

#### Start Streaming
```bash
SESSION_ID="<your-session-id>"
curl -X POST http://localhost:8000/api/sessions/$SESSION_ID/start
```

### Custom Test Scenarios

You can modify `e2e_sony_a7iv_test.py` to test specific scenarios:

#### Test Multiple Cameras
```python
# Register second camera
camera_data_2 = {
    "name": "Sony a7 IV #2",
    "transport": "usb",
    "stream_url": "usb://sony-a7iv-2"
}
response = requests.post(f"{API_BASE}/cameras/", json=camera_data_2)
```

#### Test Complex Scene Layouts
```python
scene_config = {
    "name": "Multi-Cam Split",
    "layout": "split",
    "sources": [
        {
            "type": "camera",
            "camera_id": camera_id_1,
            "position": {"x": 0, "y": 0, "width": 960, "height": 1080}
        },
        {
            "type": "camera",
            "camera_id": camera_id_2,
            "position": {"x": 960, "y": 0, "width": 960, "height": 1080}
        }
    ]
}
```

## Expected Results

### Successful Test

- ✅ All 6 steps complete without errors
- ✅ Camera appears in system
- ✅ Session is created and persisted
- ✅ OBS scenes are configured
- ✅ Scene switching works

### Limitations to Note

- Camera discovery may require manual input
- OBS integration depends on WebSocket availability
- Streaming destinations need valid credentials
- Some features may be in development

## Next Steps

After successful E2E testing:

1. **Test Live Streaming**:
   - Configure YouTube/Twitch credentials
   - Start actual stream
   - Monitor stream quality

2. **Performance Testing**:
   - Test with multiple cameras
   - Measure latency
   - Check CPU/memory usage

3. **Feature Testing**:
   - Test remote camera control
   - Test audio routing
   - Test scene transitions

4. **Documentation**:
   - Document any issues found
   - Update camera compatibility list
   - Create user guides

## Support

If you encounter issues:

1. **Check logs**: Server terminal output
2. **Review errors**: E2E test error messages
3. **Verify setup**: All prerequisites met
4. **Test individually**: Break down into smaller steps

## Related Documentation

- [Sony a7 IV Manual](https://www.sony.com/electronics/support/e-mount-body-ilce-7-series/ilce-7m4/manuals)
- [OBS Studio Docs](https://obsproject.com/wiki/)
- [Miktos Hub API Docs](http://localhost:8000/docs)
