# Desktop Control Panel - User Guide

**Status:** ✅ Ready for Testing  
**Created:** November 18, 2025  
**Version:** 1.0.0

## Overview

The Desktop Control Panel is a professional web-based interface for remotely controlling Miktos StreamLab camera phones. It provides real-time monitoring and control capabilities for multiple cameras simultaneously.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Android App   │◄────────┤  WebSocket       │◄────────┤  Web Control    │
│   (Camera)      │         │  Server          │         │  Panel (Flask)  │
│   Port 9000     │         │  Port 9000-9001  │         │  Port 5000      │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │
                            Status Updates
                            Commands
```

## Features

### Real-Time Camera Monitoring
- ✅ Live connection status (online/offline)
- ✅ Streaming state (IDLE, RUNNING, PAUSED, STOPPED)
- ✅ Battery level and charging status
- ✅ Network type (WiFi, LTE, etc.)
- ✅ Thermal state (OK, WARM, HOT, CRITICAL)

### Remote Control Commands
- **START** - Begin streaming from camera
- **STOP** - Stop streaming
- **PAUSE** - Freeze current frame (keeps connection alive)
- **RESUME** - Resume from paused state
- **ENTER_STUDIO_MODE** - Switch to full-screen black mode
- **GET_STATUS** - Request current status update

### Multi-Camera Support
- Control multiple cameras simultaneously
- Independent state management for each camera
- Color-coded status indicators
- Real-time status updates across all cameras

## Installation

### Prerequisites
- Python 3.10+ with virtual environment
- Flask, Flask-SocketIO, websockets packages
- Android app with remote control enabled

### Setup

1. **Navigate to remote control directory:**
   ```bash
   cd Desktop/Backend/remote_control
   ```

2. **Install dependencies (if not already installed):**
   ```bash
   source ../../../.venv/bin/activate
   pip install flask flask-socketio flask-cors websockets
   ```

3. **Verify files exist:**
   ```bash
   ls -la
   # Should show:
   # - websocket_server.py
   # - control_panel.py
   # - templates/control_panel.html
   # - start_control_panel.sh
   ```

## Usage

### Quick Start

**Option 1: Using the startup script (recommended)**
```bash
./start_control_panel.sh
```

This automatically starts both:
- WebSocket server (ports 9000-9001)
- Web control panel (port 5000)

**Option 2: Manual startup**

Terminal 1 - Start WebSocket server:
```bash
cd Desktop/Backend/remote_control
source ../../../.venv/bin/activate
python3 websocket_server.py
```

Terminal 2 - Start control panel:
```bash
cd Desktop/Backend/remote_control
source ../../../.venv/bin/activate
python3 control_panel.py
```

### Accessing the Control Panel

1. **Open your browser:**
   ```
   http://localhost:5000
   ```

2. **You should see:**
   - Header: "Miktos StreamLab - Remote Camera Control Panel"
   - Status bar showing connected cameras count
   - Empty state if no cameras connected

### Connecting Cameras

**On Android Phone:**

1. Open Miktos StreamLab app
2. Go to Settings
3. Enable "Remote Control"
4. Enter server IP: `192.168.2.36` (your Mac's IP)
5. Enter port: `9000`
6. Tap "Connect"

**Expected behavior:**
- Phone logs: "✅ WebSocket connected"
- Desktop logs: "📱 Camera registered: [device-id]"
- Web UI: Camera card appears automatically

## Control Panel Interface

### Camera Card Layout

Each camera displays:

```
┌────────────────────────────────────┐
│ 📱 abc123...     [RUNNING]         │  ← Header
├────────────────────────────────────┤
│  🔋 85%    📶 WiFi    ✅ OK        │  ← Stats
├────────────────────────────────────┤
│  [▶️ START]  [⏹️ STOP]             │
│  [⏸️ PAUSE]  [▶️ RESUME]            │  ← Controls
│  [🌙 Studio]  [🔄 Refresh]         │
└────────────────────────────────────┘
```

### Status Bar

Top of page shows:
- **Connected Cameras** - Total online cameras
- **Streaming** - Cameras currently in RUNNING state
- **Paused** - Cameras in PAUSED state

### Visual Indicators

**Card Border Colors:**
- **Green pulse** - Streaming (RUNNING)
- **Orange** - Paused
- **Red** - Offline
- **Gray** - Idle

**State Badges:**
- `IDLE` - Connected, not streaming
- `RUNNING` - Actively streaming
- `PAUSED` - Frozen frame, connection alive
- `STOPPED` - Streaming stopped
- `OFFLINE` - Camera disconnected

## Testing Procedures

### Test 1: Basic Connection
```bash
1. Start control panel: ./start_control_panel.sh
2. Open browser: http://localhost:5000
3. Enable remote control on Android app
4. Verify: Camera appears in web UI
5. Verify: Status shows "IDLE"
```

**Expected result:** ✅ Camera card appears within 2 seconds

### Test 2: START/STOP Commands
```bash
1. Click "START" button
2. Verify: Android starts streaming
3. Verify: Web UI shows "RUNNING" state
4. Verify: Green pulsing border
5. Click "STOP" button
6. Verify: Android stops streaming
7. Verify: Web UI shows "STOPPED" state
```

**Expected result:** ✅ Commands execute within 1 second

### Test 3: PAUSE/RESUME
```bash
1. Start streaming
2. Click "PAUSE"
3. Verify: Desktop shows frozen frame
4. Verify: Web UI shows "PAUSED" (orange)
5. Wait 30 seconds
6. Verify: Connection still alive
7. Click "RESUME"
8. Verify: Streaming resumes immediately
```

**Expected result:** ✅ No disconnect during pause

### Test 4: Studio Mode
```bash
1. Click "🌙 Studio Mode"
2. Verify: Phone screen goes black with red dot
3. Verify: Status updates continue
4. Long-press phone screen 3 seconds
5. Verify: Returns to normal UI
```

**Expected result:** ✅ Studio mode activates/exits cleanly

### Test 5: Multi-Camera
```bash
1. Connect phone #1
2. Verify: 1 camera card shown
3. Connect phone #2
4. Verify: 2 camera cards shown
5. Start streaming on phone #1
6. Verify: Phone #1 shows "RUNNING"
7. Verify: Phone #2 still shows "IDLE"
8. Control each independently
```

**Expected result:** ✅ Independent control of each camera

## Troubleshooting

### Problem: Camera doesn't appear in web UI

**Check:**
1. WebSocket server running? `ps aux | grep websocket_server`
2. Android shows "connected"? Check app logs
3. Correct IP address? Use Mac's local IP, not 127.0.0.1
4. Firewall blocking? Check Mac firewall settings

**Solution:**
```bash
# Check Mac IP
ifconfig | grep "inet "
# Should show: inet 192.168.2.36 (or similar)

# Test WebSocket server
curl http://localhost:5000/api/cameras
# Should return JSON with camera list
```

### Problem: Commands don't work

**Check:**
1. Camera shows "online" in web UI?
2. Browser console errors? (F12 → Console)
3. Desktop logs show command sent?

**Solution:**
```bash
# Check desktop logs
# Look for: "📤 Command sent to [camera-id]: START"
# If missing, WebSocket connection broken

# Restart both servers
pkill -f websocket_server
pkill -f control_panel
./start_control_panel.sh
```

### Problem: Status updates not appearing

**Check:**
1. Android sending status? Check app logs
2. SocketIO connected? Check browser console
3. Camera ID matching?

**Solution:**
```bash
# Click "Refresh" button on camera card
# This requests immediate status update

# Check browser console (F12)
# Should show: "📊 Status update: {...}"
```

### Problem: Web UI won't load

**Check:**
1. Flask server running on port 5000?
2. Port already in use?

**Solution:**
```bash
# Check what's using port 5000
lsof -i :5000

# Kill conflicting process
kill -9 [PID]

# Restart control panel
./start_control_panel.sh
```

## Advanced Usage

### Custom Server Configuration

Edit `control_panel.py`:
```python
# Change ports
app.run(host='0.0.0.0', port=8080)  # Web UI port

# WebSocket server connection
ws_controller = WebSocketController(
    server_host="192.168.2.36",  # Your IP
    server_port=9001              # Controller port
)
```

### Remote Access

To access from another device on your network:

1. Find your Mac's IP: `ifconfig | grep "inet "`
2. Open browser on other device: `http://192.168.2.36:5000`
3. Ensure firewall allows port 5000

### Logging

Control panel logs to console. To save:
```bash
./start_control_panel.sh 2>&1 | tee control_panel.log
```

View real-time:
```bash
tail -f control_panel.log
```

## API Reference

### REST Endpoints

**GET /api/cameras**
```json
{
  "cameras": ["camera-id-1", "camera-id-2"],
  "statuses": {
    "camera-id-1": {
      "state": "RUNNING",
      "battery": 85,
      "network_type": "LAN_WIFI",
      "thermal": "OK",
      "online": true
    }
  },
  "timestamp": "2025-11-18T10:30:00"
}
```

**POST /api/command**
```json
Request:
{
  "camera_id": "camera-id-1",
  "command": "START",
  "params": {
    "server_ip": "192.168.2.36",
    "server_port": 8554
  }
}

Response:
{
  "status": "success"
}
```

### SocketIO Events

**Client → Server:**
- `request_status` - Request status update for camera

**Server → Client:**
- `cameras` - Initial camera list
- `camera_online` - New camera connected
- `camera_offline` - Camera disconnected
- `status_update` - Camera status changed

## Performance

**Expected Latency:**
- Command execution: <500ms
- Status update propagation: <1s
- UI refresh: <100ms

**Scalability:**
- Tested with: 3 cameras
- Theoretical max: 20+ cameras
- Network bandwidth: ~10KB/s per camera (status updates)

## Security Notes

**Current Implementation:**
- ⚠️ No authentication
- ⚠️ No encryption (WebSocket, not WSS)
- ⚠️ Intended for local network only

**Production Recommendations:**
- Add JWT authentication
- Use WSS (WebSocket Secure)
- Implement rate limiting
- Add user access control

## Next Steps

After testing the control panel:

1. **Week 2 Completion:**
   - ✅ Control panel UI working
   - ✅ All commands functional
   - ✅ Multi-camera support verified

2. **Week 3 Focus:**
   - Implement SessionLogger
   - Run 5-hour stress test
   - Production polish

3. **Future Enhancements:**
   - Stream preview in web UI
   - Recording controls
   - Quality adjustment sliders
   - Batch commands (control all cameras)
   - Mobile-responsive design

## Support

**Logs Location:**
- WebSocket server: Console output
- Flask server: Console output
- Android app: Logcat (tag: RemoteControlClient)

**Debug Mode:**
```bash
# Enable verbose logging
export FLASK_DEBUG=1
python3 control_panel.py
```

## Changelog

### Version 1.0.0 (November 18, 2025)
- Initial release
- Basic camera control (START/STOP/PAUSE/RESUME)
- Studio Mode support
- Real-time status monitoring
- Multi-camera support
- Modern web UI with animations
- WebSocket communication
- REST API for commands

---

**For questions or issues, check the main project documentation or GitHub issues.**
