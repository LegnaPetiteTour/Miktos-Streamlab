# Sony a7 IV End-to-End Testing Guide

This guide walks you through testing the complete Miktos Hub workflow with your Sony a7 IV camera.

## Prerequisites

### Sony a7 IV Setup

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

### OBS Studio

1. **Install OBS Studio**:

```bash
brew install --cask obs
```

1. **Enable WebSocket Server**:

- Open OBS Studio
- Go to **Tools → WebSocket Server Settings**
- Enable WebSocket server
- Default port: 4455
- No password required (for testing)

1. **Verify OBS is Running**:

- OBS should be open before running tests
- Create a basic scene if needed

### Miktos Hub Server

1. **Start the API server**:

```bash
python main.py
```

1. **Verify server is running**:

- Open [http://localhost:8000/docs](http://localhost:8000/docs)
- You should see the FastAPI documentation

## Running the E2E Test

### Basic Usage

```bash
python e2e_sony_a7iv_test.py
```

The script will guide you through the following steps:

1. Server health check
1. Camera discovery / registration
1. Session creation
1. OBS configuration (scenes/sources)
1. Streaming destination setup (optional)
1. End-to-end workflow test

### Interactive Prompts (examples)

```text
Select connection type (1/2/3):
  1. USB Tethering (recommended for local use)
  2. Network via Imaging Edge Mobile
  3. RTSP stream URL
```

```text
Configure streaming destinations:
  1. YouTube
  2. Twitch
  3. Facebook Live
  4. Custom RTMP
  5. Skip this step
```

### Sample Test Output (abbreviated)

```text
[STEP 1] Checking server health... ✅
[STEP 2] Discovering Sony a7 IV camera... ✅
[STEP 3] Creating streaming session... ✅
[STEP 4] Configuring OBS scenes... ✅
[STEP 5] Setting up streaming destinations... ✅
[STEP 6] Testing workflow... ✅

TEST SUMMARY: Session created, 1 camera, 2 scenes
```

## Troubleshooting (quick)

### Camera not detected

```bash
# List connected camera devices
system_profiler SPCameraDataType
```

```bash
# Ping camera (network streaming)
ping <camera-ip-address>
# Check RTSP port
nc -zv <camera-ip> 554
```

### OBS not connecting

```bash
ps aux | grep obs
```

Verify OBS → Tools → WebSocket Server Settings (port 4455) and ensure the WebSocket server is running.

### API server issues

```bash
curl http://localhost:8000/api/health
```

Restart server if necessary:

```bash
# Stop server (Ctrl+C) then:
python main.py
```

## Advanced (short)

Get session details:

```bash
SESSION_ID="<your-session-id>"
curl http://localhost:8000/api/sessions/$SESSION_ID
```

List cameras:

```bash
curl http://localhost:8000/api/cameras/
```

## Related Documentation

- [Sony a7 IV Manual](https://www.sony.com/electronics/support/e-mount-body-ilce-7-series/ilce-7m4/manuals)
- [OBS Studio Docs](https://obsproject.com/wiki/)
- [Miktos Hub API Docs](http://localhost:8000/docs)
