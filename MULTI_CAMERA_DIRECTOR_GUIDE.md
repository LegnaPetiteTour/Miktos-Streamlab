# Multi-Camera Director System - Complete Guide

## Overview

The StreamLab Multi-Camera Director System provides production-ready multi-camera streaming with intelligent thermal management, instant camera switching, and comprehensive health monitoring.

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    DESKTOP SYSTEM                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Multi-Camera Director UI (Port 9001)                 │  │
│  │  • Camera tiles with health indicators                │  │
│  │  • Remote control buttons                             │  │
│  │  • Active camera switching                            │  │
│  │  • Thermal alerts                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Multi-Camera Receiver (Ports 8554-8556)             │  │
│  │  • Accept 3 simultaneous camera streams              │  │
│  │  • Detect PAUSE state (< 2 fps)                      │  │
│  │  • Live preview for active camera                    │  │
│  │  • Switch cameras instantly                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Remote Control Server (Ports 9000-9001)             │  │
│  │  • WebSocket communication                            │  │
│  │  • Command relay to phones                           │  │
│  │  • Status aggregation                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                  ╔════════╪════════╗
                  ║   WiFi Network  ║
                  ╚════════╪════════╝
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐        ┌────▼────┐       ┌────▼────┐
   │ Phone 1 │        │ Phone 2 │       │ Phone 3 │
   │ Port    │        │ Port    │       │ Port    │
   │ 8554    │        │ 8555    │       │ 8556    │
   └─────────┘        └─────────┘       └─────────┘
```

## Features

### ✅ Priority 1: Thermal Response Actions (IMPLEMENTED)

**Automated Quality Protection:**

- **OK**: Normal operation at 6 Mbps
- **WARM**: Auto-reduce to 4 Mbps
- **HOT**: Auto-reduce to 3 Mbps + force Studio Mode
- **CRITICAL**: Send alert to desktop (desktop should auto-cut)

**Implementation:**

```kotlin
// In CameraStreamer.kt
when (thermalState) {
    OK -> restoreBitrate(6_000_000)
    WARM -> reduceBitrate(4_000_000)
    HOT -> {
        reduceBitrate(3_000_000)
        enterStudioMode()
    }
    CRITICAL -> sendCriticalAlert()
}
```

**Benefits:**

- 🔥 Prevents device overheating
- 🎥 Maintains stream quality as long as possible
- ⚡ No manual intervention required
- 📊 Desktop receives thermal state in status updates

### ✅ Priority 2: Desktop Multi-Camera Director UI (IMPLEMENTED)

**Features:**

- 📱 Individual tiles for each camera
- 🟢 Live status indicators (LIVE/PAUSED/STOPPED)
- 🔋 Battery level + charging status
- 🌡️ Thermal badges (WARM/HOT/CRITICAL)
- 📶 Network type (WiFi/LTE)
- 📊 Current bitrate display
- ⏱️ Streaming uptime
- 🎮 Control buttons per camera:
  - ▶ START / ⏹ STOP
  - ⏸ PAUSE / ▶ RESUME
  - 🌙 Studio Mode ON/OFF
  - ✨ MAKE ACTIVE

**Usage:**

```bash
# Start the director UI
cd Desktop/Backend/remote_control
python3 multi_camera_director.py
```

**Director Workflow:**

1. Launch app - connects to WebSocket server
2. Camera tiles appear as phones connect
3. Click ▶ START on each camera
4. Click ✨ MAKE ACTIVE to switch cameras
   - Automatically PAUSES other cameras
   - RESUMES selected camera
5. Monitor health indicators
6. Respond to thermal alerts

### ✅ Priority 3: Multi-Stream Receiver (IMPLEMENTED)

**Features:**

- 🎬 Accept 3 simultaneous camera connections
- 🟡 Detect PAUSE state (frame rate < 2 fps)
- 🟢 Detect LIVE state (frame rate ≥ 2 fps)
- 🖥️ Live preview for active camera
- 📊 Real-time FPS and bitrate monitoring
- 🔄 Automatic state transitions
- 📈 Per-camera statistics

**Usage:**

```bash
# Start multi-camera receiver (ports 8554-8556 for 3 cameras)
python3 multi_camera_receiver.py

# Custom configuration
python3 multi_camera_receiver.py <base_port> <num_cameras>
# Example: python3 multi_camera_receiver.py 8600 4  # 4 cameras on ports 8600-8603
```

**State Detection:**

- **LIVE**: FPS ≥ 2.0 → 🟢 Normal streaming
- **PAUSED**: FPS < 2.0 → 🟡 Freeze frame mode
- **DISCONNECTED**: No data → ⚪ Camera offline

## Complete Workflow

### Setup (One-time)

1. **Start Remote Control Server:**

   ```bash
   cd Desktop/Backend/remote_control
   python3 websocket_server.py
   ```

2. **Start Multi-Camera Receiver:**

   ```bash
   python3 multi_camera_receiver.py 8554 3
   ```

3. **Launch Director UI:**

   ```bash
   cd Desktop/Backend/remote_control
   python3 multi_camera_director.py
   ```

4. **Configure Phones:**
   - Phone 1: Stream to `<desktop-ip>:8554`
   - Phone 2: Stream to `<desktop-ip>:8555`
   - Phone 3: Stream to `<desktop-ip>:8556`
   - Enable Remote Control (connect to port 9000)

### Live Production

1. **Pre-show:**
   - Mount all 3 phones
   - Verify all tiles appear in Director UI
   - Check battery levels (should be >80%)
   - Verify thermal state is OK

2. **Go Live:**
   - Click ▶ START on all cameras
   - Wait for all to show 🟢 LIVE
   - Cameras auto-enter Studio Mode
   - Verify preview is showing

3. **During Show:**
   - **Switch cameras**: Click ✨ MAKE ACTIVE
     - Previous camera → 🟡 PAUSED (freeze frame)
     - New camera → 🟢 LIVE (instant resume)
   - **Monitor health**:
     - Battery should stay >20%
     - Thermal should stay OK or WARM
   - **Respond to alerts**:
     - 🌡️ WARM: Already auto-reduced to 4 Mbps
     - 🔥 HOT: Already at 3 Mbps + Studio Mode
     - ☠️ CRITICAL: Switch to backup camera!

4. **Post-show:**
   - Click ⏹ STOP on all cameras
   - Phones exit Studio Mode
   - Review logs

## Thermal Management

### Automatic Actions

| State | Bitrate | Studio Mode | Alert |
|-------|---------|-------------|-------|
| OK | 6 Mbps | Optional | - |
| WARM | 4 Mbps ⬇ | Optional | 🌡️ Log only |
| HOT | 3 Mbps ⬇ | Forced ✓ | 🔥 Desktop warning |
| CRITICAL | 3 Mbps | Forced ✓ | ☠️ Desktop popup |

### Manual Override

If thermal issues persist:

1. Switch to another camera (MAKE ACTIVE)
2. Let hot phone cool (will stay PAUSED)
3. Consider stopping the hot camera entirely
4. Resume when thermal state returns to OK

## Status Information

### Desktop Receives Every 5 Seconds

```json
{
  "state": "running",
  "is_streaming": true,
  "is_paused": false,
  "battery_level": 75,
  "network_type": "LAN_WIFI",
  "thermal_state": "WARM",
  "current_bitrate_mbps": 4.0,
  "uptime_seconds": 1230,
  "frame_count": 36900
}
```

### Visual Indicators in Director UI

- **Battery**: 🔋 75% or ⚡ 85% (charging)
- **Thermal**: (blank), 🌡️ WARM, 🔥 HOT, ☠️ CRITICAL
- **Network**: 📶 WiFi, 📱 LTE, 📵 Offline
- **State**: 🟢 LIVE, 🟡 PAUSED, ⚪ STOPPED
- **Active**: ⭐ ACTIVE (highlighted border)

## Troubleshooting

### Camera Not Appearing in Director UI

- ✅ Check WebSocket server is running (port 9001)
- ✅ Check phone has Remote Control enabled
- ✅ Verify phone connected to correct server IP

### Can't START Camera

- ✅ Verify streaming destination configured on phone
- ✅ Check multi-camera receiver is running
- ✅ Ensure correct port is being used

### Camera Stuck in PAUSED

- ✅ Click ▶ RESUME button
- ✅ Or click ✨ MAKE ACTIVE to switch to it

### Thermal CRITICAL Won't Go Away

- ✅ Stop streaming on that phone
- ✅ Let it cool for 5-10 minutes
- ✅ Consider using a cooling fan
- ✅ Ensure phone not in direct sunlight

### Preview Window Not Showing

- ✅ Install ffmpeg: `brew install ffmpeg`
- ✅ Check receiver logs for errors
- ✅ Verify H.264 stream is being received

## Performance Tips

### Battery Life

- 📱 Use phones with >80% battery
- 🔌 Consider external battery packs for >1 hour streams
- 🌙 Studio Mode reduces battery drain slightly

### Heat Management

- 🌡️ Remove phone cases (improves heat dissipation)
- 💨 Use small USB fans for cooling
- 🌤️ Avoid direct sunlight
- ⏱️ For long streams (>30 min), monitor thermal state

### Network

- 📶 WiFi is preferred (6 Mbps full quality)
- 📱 LTE fallback works but reduces to 4 Mbps
- 🏠 Use 5 GHz WiFi if available
- 📡 Keep phones close to router (<20 feet)

## Next Steps

### Optional Enhancements

1. **Audio Management**: Add per-camera audio muting
2. **Recording**: Save individual camera streams
3. **Slate Graphics**: Custom "PAUSED" overlays
4. **OBS Integration**: Direct integration with OBS Studio
5. **Cloud Relay**: Remote streaming via cloud server

---

**Implementation Status**: ✅ Production Ready  
**Last Updated**: November 18, 2025  
**Version**: 2.0
