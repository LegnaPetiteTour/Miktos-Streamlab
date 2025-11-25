# Sony a7 IV Quick Start Guide

## Pre-Flight Checklist

- [ ] Sony a7 IV connected (HDMI/USB/Network)
- [ ] OBS Studio running with WebSocket enabled (port 4455)
- [ ] Miktos Hub server running (`python main.py`)
- [ ] API accessible at <http://localhost:8000>

## Run E2E Test

```bash
python e2e_sony_a7iv_test.py
```

## Connection Methods

### HDMI Capture Card (Best Quality)

- Camera HDMI → Capture Card → USB → Mac
- Choose option **1** when prompted

### USB Tethering (Simplest)

- Install Sony Imaging Edge Webcam
- Camera USB-C → Mac USB-C
- Choose option **1** when prompted

### Network Streaming (Wireless)

- Camera WiFi → Your Network
- Get camera IP address
- Choose option **2** or **3** when prompted

## Test Flow

1. ✅ Server Health
2. 📷 Camera Discovery/Registration
3. 🎬 Session Creation
4. 🎨 OBS Scene Configuration
5. 📡 Streaming Destinations (optional)
6. 🧪 Workflow Validation

## Quick Troubleshooting

### Camera not detected

```bash
# Check USB video devices
system_profiler SPCameraDataType
```

### OBS not connecting

- Tools → WebSocket Server Settings → Enable

### Server not responding

```bash
curl http://localhost:8000/api/health
```

## After Test

View your session:

```bash
# Browser
open http://localhost:8000/sessions/<session-id>

# API
curl http://localhost:8000/api/sessions/<session-id>
```

## Clean Up

```bash
curl -X DELETE http://localhost:8000/api/sessions/<session-id>
```

## What Works

✅ Camera registration
✅ Session creation
✅ OBS scene creation
✅ Scene switching
✅ Session persistence

## What to Test Next

- [ ] Live streaming to YouTube/Twitch
- [ ] Multiple camera setup
- [ ] Remote camera control
- [ ] Audio routing
- [ ] Performance under load

## Need Help?

1. Check `E2E_TEST_GUIDE.md` for detailed instructions
2. Review server logs in terminal
3. Check OBS logs if scene issues
4. Verify camera specs match supported transports
