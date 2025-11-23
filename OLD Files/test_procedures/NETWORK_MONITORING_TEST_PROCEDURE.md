# Network Monitoring Fix - Test Procedure

## November 16, 2025 - Round 2

## Changes Deployed

### Build Info

- **APK**: `app-debug.apk`
- **Installed**: November 16, 2025 02:08 EST
- **Commit**: a275e97 "Implement comprehensive network monitoring and auto-reconnection"

### Key Fixes

1. ✅ TCP socket health monitoring (5 independent checks)
2. ✅ Disconnect detection (<8 seconds)
3. ✅ Auto-reconnection with exponential backoff (5 attempts: 1s, 2s, 4s, 8s, 16s)
4. ✅ UI state synchronization (explicit "NOT streaming" during reconnect)

## Test 1: 15-Minute Quick Validation

### Objective

Verify auto-reconnection works after phone lock/unlock

### Prerequisites

- ✅ Updated APK installed on Samsung S23 FE
- ✅ Receiver running: `tcp_h264_receiver_with_preview.py`
- ✅ Phone connected via USB (for logs)
- ✅ Phone battery >40%

### Procedure

1. **Start Streaming** (0:00)

   ```bash
   # On phone: Open StreamLab Camera app
   # Enter Mac IP: 192.168.2.36
   # Enter Port: 8554
   # Tap START button
   ```

   **Expected:**
   - Button changes to "STOP" (red)
   - Status: "✅ LIVE: Streaming to 192.168.2.36:8554"
   - Mac receiver shows live preview window
   - Android logs show: "💚 Health check passed"

2. **Monitor Streaming** (0:00 - 10:00)

   ```bash
   # Watch for health check logs
   adb logcat | grep -i "health check\|frame\|write error"
   ```

   **Expected:**
   - Logs show "💚 Health check passed" every ~10 seconds
   - Frame logs: "📹 Frame #300", "#600", "#900", etc.
   - No error messages
   - Receiver shows stable FPS (~30)

3. **Lock Phone** (10:00)

   ```bash
   # Press power button to lock screen
   # Note exact time: __:__:__
   ```

   **Expected:**

   - Phone screen turns off
   - Streaming continues briefly
   - Health monitoring detects disconnect within 8 seconds

4. **Monitor Auto-Reconnect** (10:00 - 10:30)

   ```bash
   # Watch for reconnection attempts
   adb logcat | grep -i "disconnect\|reconnect\|attempting"
   ```

   **Expected:**
   - Log: "❌ [Disconnect reason]"
   - Log: "🔄 Auto-reconnecting in 1s... (attempt 1/5)"
   - **Wait 1 second**
   - Log: "🚀 Attempting auto-reconnection 1/5..."
   - Log: "Reconnecting to 192.168.2.36:8554"
   - If fails: "🔄 Auto-reconnecting in 2s... (attempt 2/5)"
   - Repeats with delays: 1s, 2s, 4s, 8s, 16s

5. **Unlock Phone** (11:00)

   ```bash
   # Press power button
   # Swipe to unlock
   # Note exact time: __:__:__
   ```

   **Expected (if reconnecting):**
   - App shows: "🔄 Connection lost - Reconnecting..."
   - Button shows: "RECONNECTING (X/5)"
   - Status: "⚠️ NOT streaming - auto-reconnect in progress"

   **Expected (if reconnected):**
   - App shows: "✅ LIVE: Streaming to 192.168.2.36:8554"
   - Button shows: "STOP" (red)
   - Status: "📺 Reconnected successfully!"
   - Toast: "✅ Reconnected!"

6. **Verify Streaming Resumed** (11:00 - 15:00)

   ```bash
   # Check logs and receiver
   adb logcat | grep -i "frame\|health"
   ```

   **Expected:**
   - Mac receiver shows live preview (may have reopened)
   - Logs show: "📹 Frame #..." continuing
   - Logs show: "💚 Health check passed"
   - No manual restart required

### Success Criteria

**PASS** if:

- ✅ Auto-reconnection completed within 30 seconds of unlock
- ✅ No manual "START" button press required
- ✅ UI accurately showed "NOT streaming" during reconnect
- ✅ UI showed "Reconnected!" after success
- ✅ Streaming resumed automatically
- ✅ Total reconnection attempts ≤ 5

**FAIL** if:

- ❌ Auto-reconnection didn't happen
- ❌ Manual restart required
- ❌ UI showed "streaming" when not actually streaming
- ❌ Reconnection took >30 seconds
- ❌ App crashed

### Results Template

Test Date: ________________
Start Time:
Lock Time:
Unlock Time:

Disconnect Detection:

- Time to detect:       seconds
- Disconnect reason: _____________________

Auto-Reconnection:

- First attempt delay:       seconds
- Attempts before success: _____
- Total reconnection time:       seconds
- Successful: YES / NO

UI State Accuracy:

- Showed "NOT streaming" during reconnect: YES / NO
- Showed "RECONNECTING (X/5)": YES / NO
- Showed "Reconnected!" on success: YES / NO

Streaming Quality:

- FPS after reconnect:
- Frame continuity: SMOOTH / GAPS / FAILED

Overall Result: PASS / FAIL

Notes:
_________________________________
_________________________________

## Test 2: 60-Minute Comprehensive Test

### Test 2 Objective

Validate stability over extended period with multiple lock/unlock cycles

### Test 2 Procedure

1. **Start Streaming** (0:00)
   - Same as Test 1

2. **First Lock/Unlock Cycle** (30:00)
   - Lock at 30:00
   - Unlock at 31:00
   - Verify auto-reconnect
   - Continue streaming

3. **Second Lock/Unlock Cycle** (60:00)
   - Lock at 60:00 (THIS IS THE ORIGINAL BUG SCENARIO)
   - Unlock at 61:00
   - Verify auto-reconnect
   - Continue streaming

4. **Final Validation** (65:00)
   - Verify streaming still active
   - Check total frames sent
   - Check for any errors

### Test 2 Success Criteria

**PASS** if:

- ✅ Both lock/unlock cycles auto-reconnected
- ✅ No manual intervention required
- ✅ Total streaming time >60 minutes
- ✅ No crashes
- ✅ UI state accurate throughout

## Test 3: Network Stress Test

### Test 3 Objective

Verify resilience to network issues beyond simple lock/unlock

### Scenarios

1. **Wifi Toggle During Streaming**
   - Stream 5 minutes
   - Turn Wifi OFF
   - Wait 30 seconds
   - Turn Wifi ON
   - Verify auto-reconnect

2. **Receiver Restart**
   - Stream 5 minutes
   - Stop receiver (`Ctrl+C`)
   - Restart receiver
   - Verify auto-reconnect on phone

3. **Network Congestion**
   - Stream during heavy network usage
   - Download large file on same network
   - Verify streaming continues or auto-reconnects

## Monitoring Commands

### Real-Time Logs

```bash

# Health checks and frames
adb logcat | grep -i "CameraStreamer"

# Reconnection events
adb logcat | grep -i "reconnect\|disconnect"

# Frame rate tracking
adb logcat | grep "Frame #"

# Error detection
adb logcat | grep -E "❌|ERROR|FATAL"

# UI broadcasts
adb logcat | grep "com.miktos.STREAM"
### Battery Monitoring

```bash
# Current battery level
adb shell dumpsys battery | grep level

# Battery during streaming
watch -n 10 'adb shell dumpsys battery | grep level'
### Network Statistics

```bash

# App network usage
adb shell dumpsys package com.miktos.streamlabcamera | grep bytes
## Troubleshooting

### If Auto-Reconnect Fails

1. **Check Logs**

   ```bash

   adb logcat | grep -i "reconnect\|disconnect"

   - Look for: "🚀 Attempting auto-reconnection"
   - Look for: "❌ [Error message]"

2. **Check Network**
   ```bash

   adb shell ping -c 3 192.168.2.36
3. **Check Receiver**
   - Is `tcp_h264_receiver_with_preview.py` running?
   - Is it listening on port 8554?

4. **Check App State**
   ```bash

   adb shell dumpsys activity activities | grep streamlab
### If UI State Wrong

1. **Check Broadcast Receivers**
   ```bash

   adb logcat | grep "STREAM_DISCONNECTED\|STREAM_RECONNECTED\|STREAM_FAILED"
2. **Force Refresh**
   - Lock/unlock phone
   - Tap back button and reopen app

## Expected Log Sequence

### Successful Auto-Reconnect


01:00:00.123  CameraStreamer  💚 Health check passed - streaming healthy
01:10:00.456  CameraStreamer  ❌ Write error #1 - network issue: Broken pipe
01:10:00.457  CameraStreamer  Connection lost - attempting recovery (attempt 1/5)
01:10:00.458  CameraStreamer  🔄 Auto-reconnecting in 1s... (attempt 1/5)
01:10:01.460  CameraStreamer  🚀 Attempting auto-reconnection 1/5...
01:10:01.461  CameraStreamer  Reconnecting to 192.168.2.36:8554
01:10:01.462  CameraStreamer  ✅ Connected to server successfully
01:10:01.500  CameraStreamer  ✅ Reconnection successful after 1 attempts!
01:10:01.600  CameraStreamer  ✅ Sent codec config (SPS/PPS): 45 bytes
01:10:01.633  CameraStreamer  🔑 Keyframe #1: 52384 bytes
01:10:01.666  CameraStreamer  💚 Health check passed - streaming healthy
### Failed Reconnection (Max Attempts)


01:00:00.123  CameraStreamer  ❌ Socket disconnected - basic check failed
01:00:00.124  CameraStreamer  🔄 Auto-reconnecting in 1s... (attempt 1/5)
01:00:01.126  CameraStreamer  🚀 Attempting auto-reconnection 1/5...
01:00:01.127  CameraStreamer  Error starting stream: Connection refused
01:00:01.128  CameraStreamer  🔄 Auto-reconnecting in 2s... (attempt 2/5)
[... repeats ...]
01:00:31.130  CameraStreamer  🚀 Attempting auto-reconnection 5/5...
01:00:31.131  CameraStreamer  Error starting stream: Connection refused
01:00:31.132  CameraStreamer  ❌ Max reconnection attempts (5) reached - giving up
## Next Steps After Testing

### If Test 1 PASSES

- ✅ Proceed to Test 2 (60-minute comprehensive)
- Document results
- Update commercial viability assessment

### If Test 1 FAILS

- ❌ Analyze logs for failure reason
- Identify specific issue (detection, reconnection, UI)
- Implement additional fixes
- Rebuild and retest

### If All Tests PASS

- 🎉 Disconnect bug is FIXED!
- Create demo video
- Update documentation
- Prepare for OBS integration testing
- Begin beta user recruitment

---

**Ready to begin Test 1!**

When ready, say "start test 1" and follow the procedure above.
