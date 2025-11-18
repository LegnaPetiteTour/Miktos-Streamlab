# Week 1 Testing Procedure: Studio Mode + Remote Control

**Date**: November 17, 2025  
**Build Status**: ✅ **APK Installed**  
**Server Status**: ✅ **WebSocket Server Running**  
**Ready for Testing**: YES

---

## Pre-Test Checklist

- ✅ APK built successfully (app-debug.apk)
- ✅ APK installed on Android device
- ✅ WebSocket server running on desktop (ports 9000/9001)
- ✅ Python websockets library installed
- ⏳ Desktop receiver ready (tcp_h264_receiver.py or VLC)
- ⏳ Android device charged >80%
- ⏳ WiFi network stable

---

## Test 1: Studio Mode Basic Function (30 minutes)

### Objective

Verify that Studio Mode provides a minimal black overlay that allows continuous streaming while preventing accidental touches.

### Prerequisites

- Android device charged >80%
- Desktop receiver running (VLC or Python receiver)
- WiFi connection stable

### Test Steps

1. **Start Normal Streaming**

```text
   - Open StreamLab Camera app
   - Enter server IP: [your desktop IP]
   - Tap START button
   - Verify streaming starts successfully
   - Verify video appears on desktop receiver
   ```

2. **Enter Studio Mode**

```text
   - Tap "📺 ENTER STUDIO MODE" button
   - Expected: Screen goes black immediately
   - Expected: Small red dot appears in center
   - Expected: Red dot pulses (fade 30% → 100% → repeat)
   - Expected: Screen brightness dims to ~5%
   ```

3. **Verify Status Display**

```text
   - Check top-right corner for status text
   - Expected format: "[network] [battery]% [thermal]"
   - Network icons:
     * 📶 = WiFi with internet
     * 📱 = LTE/Cellular
     * ❓ = Unknown/LAN WiFi
     * 📵 = Offline
   - Battery: percentage + ⚡ if charging
   - Thermal: (blank = OK), 🌡️ = WARM, 🔥 = HOT, ☠️ = CRITICAL
   ```

4. **Verify Exit Hint**

```text
   - Check bottom center for "Hold 3s to exit"
   - Expected: Dimmed gray text
   ```

5. **Test Touch Prevention**

```text
   - Tap screen randomly multiple times
   - Expected: No UI changes, no menus, no dialogs
   - Expected: Stream continues uninterrupted
   ```

6. **Test Long-Press Exit**

```text
   - Touch and hold screen for exactly 3 seconds
   - Expected: Returns to MainActivity
   - Expected: Screen brightness restored
   - Expected: Stream still running (visible on desktop)
   ```

7. **Re-Enter Studio Mode**

```text
   - Tap "📺 ENTER STUDIO MODE" again
   - Expected: Black overlay returns
   - Expected: Red dot animation restarts
   ```

8. **30-Minute Continuous Test**

```text
   - Leave in Studio Mode for 30 minutes
   - Check desktop receiver every 5 minutes
   - Expected: Video stream continuous, no freezes
   - Expected: No app crashes
   - Expected: No thermal warnings (unless ambient temp high)
   ```

9. **Exit and Stop**

```text
   - Long-press to exit Studio Mode
   - Tap STOP button
   - Expected: Clean shutdown
   ```

### Success Criteria

- ✅ Studio Mode activates instantly
- ✅ Red dot animation smooth and continuous
- ✅ Status display shows correct battery/network/thermal
- ✅ Touch events blocked (no accidental UI interactions)
- ✅ Long-press exit works reliably
- ✅ Stream continues uninterrupted for full 30 minutes
- ✅ Screen brightness properly dimmed
- ✅ No crashes or errors

### Data to Record

```text
Test Start Time: __________
Test End Time: __________
Total Duration: __________
Battery at Start: __________
Battery at End: __________
Battery Drain: __________
Thermal State at 5min: __________
Thermal State at 15min: __________
Thermal State at 30min: __________
Stream Interruptions: __________
Crashes: __________
```

---

## Test 2: Remote Control - Basic Commands

### Objective

Verify WebSocket communication between Android app and desktop server, and test remote command execution.

### Prerequisites

- WebSocket server running on desktop (already started)
- Desktop IP address: `[your IP]`
- Android device on same network

### Test Steps

#### 2A: Manual Remote Control Integration

Since the app doesn't have auto-connect yet, we need to add remote control manually:

1. **Add Remote Control to CameraStreamService**

   Edit `/Mobile/Android/app/src/main/java/com/miktos/streamlabcamera/CameraStreamService.kt`:

   Find the `onStartCommand()` method and add after streaming starts:

   ```kotlin
   // Enable remote control
   streamer?.enableRemoteControl("[YOUR_DESKTOP_IP]", 9000)
   ```

   Or create a Settings menu in MainActivity to enable it.

2. **Rebuild and Install**

   ```bash
   cd "/Users/atorrella/Desktop/Miktos Streamlab/Mobile/Android"
   ./gradlew assembleDebug
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```

#### 2B: Verify WebSocket Connection

1. **Start App with Streaming**

```text
   - Open StreamLab Camera app
   - Enter server IP
   - Tap START
   - Wait 5 seconds
   ```

2. **Check Desktop Server Logs**

```text
   Expected output:
   "📱 Camera registered: [device-id]"
   "📊 Broadcasting camera list to X controller(s)"
   ```

3. **Verify Status Updates**

```text
   Expected every 5 seconds:
   "📊 Status from [device-id]: {...}"
   ```

#### 2C: Test Remote Commands (Python Controller)

Create a simple test controller:

```python
# test_controller.py
import asyncio
import websockets
import json

async def test_commands():
    uri = "ws://localhost:9001"  # Controller port
    
    async with websockets.connect(uri) as websocket:
        # Wait for camera list
        msg = await websocket.recv()
        data = json.loads(msg)
        print(f"Received: {data}")
        
        if data["type"] == "camera_list" and len(data["cameras"]) > 0:
            camera_id = data["cameras"][0]
            print(f"\nTesting commands for camera: {camera_id}\n")
            
            # Test GET_STATUS
            cmd = {
                "type": "command",
                "camera_id": camera_id,
                "command": "GET_STATUS",
                "params": {}
            }
            await websocket.send(json.dumps(cmd))
            print("✅ Sent GET_STATUS command")
            await asyncio.sleep(2)
            
            # Test ENTER_STUDIO_MODE
            cmd["command"] = "ENTER_STUDIO_MODE"
            await websocket.send(json.dumps(cmd))
            print("✅ Sent ENTER_STUDIO_MODE command")
            await asyncio.sleep(5)
            
            # Test EXIT_STUDIO_MODE
            cmd["command"] = "EXIT_STUDIO_MODE"
            await websocket.send(json.dumps(cmd))
            print("✅ Sent EXIT_STUDIO_MODE command")
            await asyncio.sleep(2)
            
            # Test STOP
            cmd["command"] = "STOP"
            await websocket.send(json.dumps(cmd))
            print("✅ Sent STOP command")
            await asyncio.sleep(2)
            
            # Test START
            cmd["command"] = "START"
            cmd["params"] = {
                "server_ip": "192.168.1.100",  # Your desktop IP
                "server_port": 8554
            }
            await websocket.send(json.dumps(cmd))
            print("✅ Sent START command")
        else:
            print("❌ No cameras connected")

asyncio.run(test_commands())
```

Run the controller:

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend/remote_control"
"/Users/atorrella/Desktop/Miktos Streamlab/.venv/bin/python" test_controller.py
```

#### 2D: Verify Each Command

1. **GET_STATUS**

```text
   - Expected: Status update appears in server logs
   - Expected: Contains current state, battery, network, thermal, uptime
   ```

2. **ENTER_STUDIO_MODE**

```text
   - Expected: Android screen goes black
   - Expected: Red dot appears
   - Expected: Stream continues
   ```

3. **EXIT_STUDIO_MODE**

```text
   - Expected: Returns to MainActivity
   - Expected: Stream still running
   ```

4. **STOP**

```text
   - Expected: Stream stops on Android
   - Expected: Desktop receiver shows disconnection
   - Expected: MainActivity shows STOP button enabled
   ```

5. **START**

```text
   - Expected: Stream starts automatically
   - Expected: Desktop receiver shows video
   - Expected: MainActivity shows streaming state
   ```

### Success Criteria

- ✅ Camera registers with WebSocket server
- ✅ Status updates sent every 5 seconds
- ✅ GET_STATUS returns current state
- ✅ ENTER_STUDIO_MODE activates black overlay
- ✅ EXIT_STUDIO_MODE returns to MainActivity
- ✅ STOP command stops streaming
- ✅ START command starts streaming with correct IP/port
- ✅ No connection drops during test
- ✅ Commands execute within 1 second

### Data to Record

```text
Camera ID: __________
Connection Time: __________
Commands Tested: __________
Commands Successful: __________
Commands Failed: __________
Average Command Latency: __________
Disconnections: __________
```

---

## Test 3: Thermal Monitoring

### Objective

Verify thermal monitoring detects device temperature changes and updates Studio Mode status display.

### Prerequisites

- Android device charged >80%
- CPU-intensive app installed (e.g., CPU-Z, Geekbench, or any game)
- Streaming already running

### Test Steps

1. **Start with Cool Device**

```text
   - Let device rest for 10 minutes (cool down)
   - Start streaming
   - Enter Studio Mode
   - Check thermal status: should be blank (OK state)
   ```

2. **Increase Device Load**

```text
   - While streaming continues in background
   - Launch CPU-intensive app (benchmark or game)
   - Run for 5 minutes
   - Monitor Studio Mode status display
   ```

3. **Observe Thermal State Transitions**

```text
   Expected progression:
   - (blank) → OK state
   - 🌡️ → WARM state (PowerManager.THERMAL_STATUS_MODERATE)
   - 🔥 → HOT state (PowerManager.THERMAL_STATUS_SEVERE/CRITICAL)
   - ☠️ → CRITICAL state (PowerManager.THERMAL_STATUS_EMERGENCY/SHUTDOWN)
   ```

4. **Check Server Logs**

```text
   Expected: Status updates show changing thermal_state
   {"thermal_state": "OK"} → {"thermal_state": "WARM"} → etc.
   ```

5. **Cool Down**

```text
   - Close CPU-intensive app
   - Wait 5 minutes
   - Monitor thermal state return to OK
   ```

### Success Criteria

- ✅ Thermal monitoring detects temperature changes
- ✅ Status display updates within 5 seconds of state change
- ✅ Icons display correctly (🌡️ 🔥 ☠️)
- ✅ Thermal state included in status updates to server
- ✅ No crashes during thermal transitions
- ✅ Stream quality maintained (future: will auto-adjust)

### Data to Record

```text
Initial Thermal State: __________
Time to WARM: __________
Time to HOT: __________
Max Thermal State Reached: __________
Time to Cool Back to OK: __________
Stream Interruptions: __________
Frame Drops Observed: __________
```

---

## Week 1 Completion Checklist

After completing all 3 tests:

- [ ] Test 1: Studio Mode - PASSED
- [ ] Test 2: Remote Control - PASSED
- [ ] Test 3: Thermal Monitoring - PASSED
- [ ] No crashes during any test
- [ ] 30-minute continuous streaming achieved
- [ ] Battery drain acceptable (<2% per minute)
- [ ] WebSocket connection stable
- [ ] All commands execute successfully
- [ ] Thermal monitoring responsive

---

## Known Limitations (Week 1)

1. **No Auto-Connect**: Remote control must be manually enabled in code
2. **No Web UI**: Commands must be sent via Python script
3. **No Quality Adjustment**: Thermal states detected but don't adjust bitrate yet
4. **No Multi-Camera**: Server supports it but UI doesn't
5. **No PAUSE State**: Not implemented until Week 2

---

## Next Steps After Testing

### If All Tests Pass

- Document results in `WEEK1_TEST_RESULTS.md`
- Proceed to Week 2: PAUSE State + Advanced Remote Features
- Build web-based controller UI
- Implement quality adjustment on thermal warnings

### If Tests Fail

- Document specific failures
- Review logs for errors
- Fix critical issues before Week 2
- Re-run failed tests

---

## Support Commands

### Check if WebSocket Server is Running

```bash
lsof -i :9000
lsof -i :9001
```

### View Server Logs

```bash
# Server is already outputting to terminal
# Check the terminal where you started websocket_server.py
```

### Check Android Logs

```bash
adb logcat -d | grep -E "CameraStreamer|RemoteControlClient|StudioMode|ThermalMonitor"
```

### Kill and Restart Server

```bash
# Find process
ps aux | grep websocket_server

# Kill
kill [PID]

# Restart
cd "/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend/remote_control"
"/Users/atorrella/Desktop/Miktos Streamlab/.venv/bin/python" websocket_server.py
```

---

### Good luck with Week 1 testing! 🚀
