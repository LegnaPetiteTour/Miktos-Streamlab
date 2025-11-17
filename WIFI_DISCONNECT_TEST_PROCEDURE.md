# WiFi Disconnect/Reconnect Test Procedure

**Date**: November 16, 2025  
**Purpose**: Validate auto-reconnection when WiFi network disconnects and reconnects  
**Device**: Samsung S23 FE (R5CX346T71B)  
**Expected Behavior**: App should auto-reconnect when WiFi comes back online

---

## Test Overview

This test validates that the auto-reconnection feature works when the WiFi network is temporarily lost and restored, simulating real-world scenarios like:

- Moving between WiFi access points
- Temporary network outages
- Router restarts
- Network congestion causing brief disconnects

---

## Prerequisites

- [x] Phone connected to WiFi network
- [x] Receiver running on Mac (192.168.2.36:8554)
- [x] App installed with auto-reconnect feature
- [x] Ability to disable/enable WiFi on phone

---

## Test Procedure

### Step 1: Establish Baseline Streaming (2 minutes)

1. **Start streaming**
   - Open Miktos Camera app
   - Connect to 192.168.2.36:8554
   - Tap START STREAMING
   - Verify video appears in receiver

2. **Confirm stable connection**
   - Let stream run for 2 minutes
   - Verify frames are flowing (check logs)
   - Note baseline FPS and quality

**Expected**: Stable 30 FPS streaming

---

### Step 2: WiFi Disconnect Test (30 seconds)

1. **Disable WiFi on phone**
   - Swipe down notification panel
   - Tap WiFi icon to disable
   - OR: Settings → WiFi → Toggle OFF

2. **Observe behavior**
   - Check receiver window - should show "Connection lost"
   - Check app UI - should show "Reconnecting... Attempt 1/5"
   - Log disconnect time: ___________

**Expected Results:**

- ✅ Receiver detects disconnect within 8 seconds
- ✅ App UI shows "Reconnecting..." status
- ✅ App does NOT crash
- ✅ Foreground service stays active

---

### Step 3: WiFi Reconnect Test (2 minutes)

1. **Re-enable WiFi after 30 seconds**
   - Wait exactly 30 seconds with WiFi off
   - Swipe down notification panel
   - Tap WiFi icon to enable
   - Wait for WiFi to reconnect to network

2. **Observe auto-reconnection**
   - Watch app UI for reconnection attempts
   - Check receiver for incoming connection
   - Note reconnection time: ___________

**Expected Results:**

- ✅ App attempts reconnection (shows "Attempt 2/5", "3/5", etc.)
- ✅ Connection re-establishes within 16 seconds after WiFi returns
- ✅ Receiver shows video again
- ✅ App UI updates to "✅ LIVE: Streaming"
- ✅ Streaming resumes at 30 FPS

---

### Step 4: Post-Reconnection Validation (3 minutes)

1. **Verify stable streaming**
   - Let stream run for 3 minutes after reconnection
   - Check frame rate stability
   - Check for dropped frames

2. **Check quality metrics**
   - FPS should return to ~30
   - Bitrate should be consistent (~7.8 Mbps)
   - No visual artifacts

**Expected**: Streaming quality matches pre-disconnect baseline

---

### Step 5: Rapid Disconnect/Reconnect Test (Optional)

**Purpose**: Test resilience to flaky network conditions

1. **Quick WiFi toggle**
   - Disable WiFi for 5 seconds
   - Re-enable WiFi
   - Repeat 3 times

2. **Observe behavior**
   - Does app keep trying to reconnect?
   - Does it eventually succeed?
   - Any crashes or freezes?

**Expected**: App should handle rapid WiFi changes gracefully

---

## Monitoring Commands

### Terminal 1: Android Logs

```bash
adb logcat -s "CameraStreamer:I" "MainActivity:I" | tee /tmp/wifi_test_$(date +%H%M).log
```

**Watch for:**

- "Socket connection lost"
- "Reconnection attempt X/5"
- "✅ Reconnection successful"
- "❌ Max reconnection attempts reached"

### Terminal 2: Network Status

```bash
watch -n 1 'adb shell dumpsys wifi | grep "mNetworkInfo"'
```

**Shows**: WiFi connection state in real-time

---

## Success Criteria

### ✅ PASS Conditions

1. **Disconnect Detection**
   - App detects WiFi loss within 8 seconds
   - UI updates to show reconnecting status
   - No crash or app termination

2. **Auto-Reconnection**
   - App attempts reconnection when WiFi returns
   - Reconnection succeeds within 5 attempts
   - Exponential backoff delays visible (1s, 2s, 4s, 8s, 16s)

3. **Stream Resumption**
   - Video streaming resumes automatically
   - Frame rate returns to 30 FPS
   - Quality matches pre-disconnect baseline

4. **UI State Sync**
   - UI shows accurate connection status throughout
   - "Reconnecting" → "LIVE: Streaming" transition works
   - No misleading status messages

### ❌ FAIL Conditions

- WiFi disconnect causes app crash
- App doesn't detect disconnect
- No reconnection attempts made
- Manual restart required
- UI shows "streaming" when not actually connected

---

## Test Results Template

### Test Execution Log

**Date**: ___________  
**Start Time**: ___________  
**Tester**: ___________

#### Baseline Streaming

- Duration: _____ minutes
- FPS: _____
- Bitrate: _____ Mbps
- Status: ☐ Stable ☐ Issues

#### WiFi Disconnect

- Disconnect Time: ___________
- Detection Time: _____ seconds
- App UI Status: ___________________
- Receiver Status: ___________________

#### WiFi Reconnect

- WiFi Re-enabled Time: ___________
- Reconnection Attempt Count: _____
- Reconnection Success Time: ___________
- Total Downtime: _____ seconds

#### Post-Reconnection

- Streaming Resumed: ☐ Yes ☐ No
- FPS After Reconnect: _____
- Quality Match: ☐ Yes ☐ No
- Stable for 3 min: ☐ Yes ☐ No

### Issues Observed

- [ ] None - perfect operation
- [ ] Slow disconnect detection (>10 seconds)
- [ ] No reconnection attempts
- [ ] Reconnection failed after max attempts
- [ ] UI state incorrect
- [ ] Stream quality degraded
- [ ] App crashed
- [ ] Other: ___________________

### Final Result

☐ **PASS** - Auto-reconnect works, WiFi disconnect handled gracefully  
☐ **PARTIAL** - Reconnects but with issues (specify above)  
☐ **FAIL** - Does not reconnect, manual intervention required

**Notes:**

---

## Expected Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Baseline | 2 min | Establish stable streaming |
| Disconnect | 30 sec | WiFi disabled, app detects |
| Reconnect | 2 min | WiFi re-enabled, auto-reconnect |
| Validation | 3 min | Verify stable post-reconnect |
| **Total** | **~8 min** | Complete test cycle |

---

## Network Scenarios to Test

### Scenario 1: Brief Disconnect (This Test)

- WiFi off for 30 seconds
- Tests: Basic auto-reconnect
- Expected: Reconnect on attempt 2-3

### Scenario 2: Extended Disconnect (Optional)

- WiFi off for 2 minutes
- Tests: Persistence of reconnect attempts
- Expected: Reconnect on attempt 4-5

### Scenario 3: Network Switch (Optional)

- Switch between WiFi networks
- Tests: Different IP handling
- Expected: Manual reconnect needed (IP changed)

---

## Troubleshooting

### If Disconnect Not Detected

**Problem**: App keeps showing "streaming" after WiFi disabled

**Check:**

- Are health checks running? (grep "Health check" in logs)
- Is write timeout working? (should fail after 8 seconds)
- Is socket state being monitored?

### If Reconnection Fails

**Problem**: WiFi returns but app doesn't reconnect

**Check:**

- Is reconnection logic triggered? (grep "Reconnection attempt" in logs)
- Are all 5 attempts exhausted?
- Is WiFi fully connected? (check IP address assigned)
- Is server still reachable? (ping 192.168.2.36)

### If Stream Doesn't Resume

**Problem**: Connection succeeds but no video

**Check:**

- Did camera reinitialize? (grep "Camera streaming to encoder")
- Are frames being encoded? (grep "Frame #")
- Is data being sent? (grep "bytes" in logs)

---

## Related Tests

- [FIELD_TEST_MANUAL_PROCEDURE.md](FIELD_TEST_MANUAL_PROCEDURE.md) - Phone lock/unlock test
- [NETWORK_MONITORING_TEST_PROCEDURE.md](NETWORK_MONITORING_TEST_PROCEDURE.md) - Comprehensive network monitoring tests

---

**Next Step**: Run this test to validate WiFi resilience!
