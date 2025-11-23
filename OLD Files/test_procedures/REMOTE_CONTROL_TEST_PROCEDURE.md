# Remote Control Commands Test Procedure

**Date:** November 17, 2025
**Test Type:** Remote Control WebSocket Integration
**Objective:** Verify START/STOP/ENTER_STUDIO_MODE/EXIT_STUDIO_MODE commands work correctly

---

## Prerequisites

✅ **WebSocket Server Running:**

```text
Server: ws://192.168.2.36:9000 (cameras)
Controller: ws://192.168.2.36:9001 (desktop)
Status: RUNNING (started at 16:54:12)
```

✅ **StreamLab Camera App:**

- Version: Latest with battery fix installed
- Remote control methods: Implemented in CameraStreamer.kt
- Commands supported: START, STOP, ENTER_STUDIO_MODE, EXIT_STUDIO_MODE, STATUS

✅ **Test Client:**

- Location: `Desktop/Backend/remote_control/test_remote_control.py`
- Mode: Interactive testing

---

## Test Setup

### Step 1: Verify Server Status

Server should show:

```text
🚀 Miktos StreamLab Remote Control Server
🎥 Camera server started on ws://0.0.0.0:9000
🖥️  Controller server started on ws://0.0.0.0:9001
```

### Step 2: Enable Remote Control in App

### Option A: Via ADB (Temporary - needs UI implementation)

```bash
adb shell am broadcast -a com.miktos.ENABLE_REMOTE_CONTROL \
  --es server_ip "192.168.2.36" \
  --ei port 9000
```

### Option B: Manual Code Test (Recommended for now)

Need to add UI toggle in MainActivity to call:

```kotlin
cameraStreamer?.enableRemoteControl("192.168.2.36", 9000)
```

### Step 3: Get Desktop IP

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1
```

Expected: `192.168.2.36`

---

## Test Procedure

### Phase 1: Connection Test

1. **Start the app** on phone
2. **Check server logs** for camera registration:

```text
   📱 Camera registered: camera_001 (or similar)
   ```

1. **Run test client:**

   ```bash
   cd "/Users/atorrella/Desktop/Miktos Streamlab"
   source .venv/bin/activate
   python3 Desktop/Backend/remote_control/test_remote_control.py
   ```

### Expected Output

```text
🔌 Connecting to ws://localhost:9001...
✅ Connected to remote control server
📱 Available cameras: ['camera_001']
```

---

### Phase 2: Command Testing

Test each command in sequence:

#### Test 1: STATUS Command

**Action:** Select camera → Choose "5 - STATUS"

### Expected Result (STATUS)

- Test client: `📬 Command 'STATUS' result: {"status": "success"}`
- Phone logs: Status broadcast sent
- Server logs: Status forwarded to controllers

### Validation (STATUS)

- ✅ Command sent successfully
- ✅ Response received
- ✅ No errors

---

#### Test 2: START Command

**Action:** Select camera → Choose "1 - START"

### Expected Result (START)

- Test client: `📬 Command 'START' result: {"status": "success"}`
- Phone: Streaming should start (if IP/port configured)
- Server logs: Command delivered

### Validation (START)

- ✅ Stream starts (if configured)
- ✅ Command acknowledged
- ✅ Status updates sent

---

#### Test 3: ENTER_STUDIO_MODE Command

**Action:** Select camera → Choose "3 - ENTER_STUDIO"

### Expected Result (ENTER_STUDIO_MODE)

- Test client: `📬 Command 'ENTER_STUDIO_MODE' result: {"status": "success"}`
- Phone: Screen goes black with red pulsing dot
- Phone: Battery % and status visible
- Server logs: Studio mode activated

### Validation

- ✅ Studio Mode activated
- ✅ Screen dims to 5%
- ✅ Red dot animating
- ✅ Status display visible
- ✅ Stream continues (if running)

---

#### Test 4: STATUS in Studio Mode

**Action:** Select camera → Choose "5 - STATUS"

### Expected Result

- Test client: Receives status update
- Status should show: Studio Mode active

### Validation (STATUS in Studio)

- ✅ Status reflects Studio Mode state
- ✅ Battery level current
- ✅ Network status correct

---

#### Test 5: EXIT_STUDIO_MODE Command

**Action:** Select camera → Choose "4 - EXIT_STUDIO"

### Expected Result (EXIT_STUDIO_MODE)

- Test client: `📬 Command 'EXIT_STUDIO_MODE' result: {"status": "success"}`
- Phone: Returns to MainActivity
- Phone: Brightness restored
- Server logs: Studio mode deactivated

### Validation (EXIT_STUDIO_MODE)

- ✅ Studio Mode exits cleanly
- ✅ Returns to main UI
- ✅ Brightness restored
- ✅ Stream continues (if running)

---

#### Test 6: STOP Command

**Action:** Select camera → Choose "2 - STOP"

### Expected Result (STOP)

- Test client: `📬 Command 'STOP' result: {"status": "success"}`
- Phone: Streaming stops
- Server logs: Command delivered

### Validation (STOP)

- ✅ Stream stops cleanly
- ✅ Camera released
- ✅ UI updated

---

### Phase 3: Edge Case Testing

#### Test 7: Studio Mode While Streaming

### Sequence (Studio While Streaming)

1. START command
2. Wait for stream to connect
3. ENTER_STUDIO_MODE command
4. Verify stream continues
5. EXIT_STUDIO_MODE command
6. STOP command

### Expected

- ✅ Studio Mode works during active stream
- ✅ Stream uninterrupted
- ✅ All transitions smooth

---

#### Test 8: Multiple Commands Rapid Fire

### Sequence (Rapid Fire)

1. START → ENTER_STUDIO → EXIT_STUDIO → START → STOP
2. Send commands with 1-second intervals

### Expected (Rapid Fire)

- ✅ All commands processed
- ✅ No crashes
- ✅ State remains consistent

---

#### Test 9: Reconnection Test

### Sequence (Reconnection)

1. Enable remote control
2. Disconnect WiFi briefly
3. Reconnect WiFi
4. Send STATUS command

### Expected (Reconnection)

- ✅ Auto-reconnect works
- ✅ Commands resume
- ✅ No manual intervention needed

---

## Success Criteria

| Test | Requirement | Status |
|------|-------------|--------|
| Connection | Camera registers with server | ⏳ |
| START | Streaming initiates | ⏳ |
| STOP | Streaming stops cleanly | ⏳ |
| ENTER_STUDIO | Studio Mode activates | ⏳ |
| EXIT_STUDIO | Studio Mode exits | ⏳ |
| STATUS | Status updates received | ⏳ |
| During Stream | Studio commands work while streaming | ⏳ |
| Rapid Commands | No crashes with quick succession | ⏳ |
| Reconnection | Auto-reconnect functions | ⏳ |

**Overall Pass:** Require 100% success rate (9/9 tests)

---

## Current Limitation

⚠️ **Remote Control Not Enabled in UI**

The app has remote control implementation in `CameraStreamer.kt` but there's no UI toggle to enable it. Need to add:

1. **Toggle Switch** in MainActivity
2. **Server IP Input** field
3. **Enable/Disable Button**

For now, testing requires:

- Manual code modification, OR
- ADB broadcast command, OR
- Adding temporary code in MainActivity.onCreate()

---

## Quick Enable (Temporary Solution)

Add to `MainActivity.kt` in `startStreaming()` method:

```kotlin
private fun startStreaming() {
    // ... existing code ...
    
    // TEMPORARY: Enable remote control for testing
    cameraStreamer.enableRemoteControl("192.168.2.36", 9000)
    
    // ... rest of code ...
}
```

Then rebuild and reinstall APK.

---

## Test Commands Reference

### Test Client Commands

```bash
# Interactive mode
python3 Desktop/Backend/remote_control/test_remote_control.py

# Automated test
python3 Desktop/Backend/remote_control/test_remote_control.py auto camera_001
```

### Server Logs

```bash
# View server output
# Terminal ID: 4bf86307-6a03-482b-86e5-67ceb6901c80
```

### Phone Logs

```bash
# Monitor app logs
adb logcat | grep -E "CameraStreamer|RemoteControl|StudioMode"
```

---

## Next Steps After Testing

1. ✅ **If PASS:** Document results, add UI for remote control
2. ⚠️ **If FAIL:** Debug connection issues, check network
3. 📝 **Enhancement:** Add auto-discovery for server IP
4. 🔧 **UI Work:** Create remote control settings panel

---

## Notes

- Server IP must match network (192.168.2.x for this network)
- Port 9000 for cameras, 9001 for controllers
- WebSocket connection auto-reconnects on network change
- Commands are JSON formatted with timestamps
- Battery display update fix is independent of remote control

---

**Test Start Time:** ________________
**Tester:** ________________
**Test Result:** ⏳ PENDING
