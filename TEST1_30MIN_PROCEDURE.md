# Test 1: 30-Minute Studio Mode Continuous Stream Test

**Date:** November 17, 2025
**Test Type:** Extended Stability & Battery Performance
**Duration:** 30 minutes
**Success Criteria:**

- Stream runs continuously without interruption
- Battery drain < 60% (target: 2% per minute)
- No thermal critical state
- No crashes or freezes

---

## Pre-Test Setup

### Desktop Preparation

1. **Terminal 1 - Start Video Receiver:**

   ```bash
   cd "/Users/atorrella/Desktop/Miktos Streamlab"
   source .venv/bin/activate
   python3 tcp_h264_receiver_with_preview.py 8554
   ```

2. **Terminal 2 - Start Monitoring Script:**

   ```bash
   cd "/Users/atorrella/Desktop/Miktos Streamlab"
   ./Scripts/monitor_30min_test.sh
   ```

   Wait at setup prompt - don't start yet

### Phone Preparation

1. **Check Initial State:**
   - Battery level: ****%
   - Battery charged to at least 80% recommended
   - Phone unplugged from power adapter
   - WiFi connected to same network as desktop (192.168.2.36)

2. **Start StreamLab Camera App:**
   - Open app
   - Enter server IP: `192.168.2.36`
   - Enter port: `8554`
   - Press **Connect** button
   - Verify stream appears on desktop receiver

3. **Enter Studio Mode:**
   - Press **Enter Studio Mode** button
   - Verify black screen with red pulsing dot appears
   - Verify status icons visible (battery/network/thermal)
   - Phone screen should dim to 5% brightness

---

## Test Execution

### Phase 1: Initial Capture (USB Connected)

1. **On Desktop Terminal 2:**
   - Press ENTER to start monitoring script
   - Wait for first data capture to appear (shows battery %, temp, etc.)

### Phase 2: Unplugged Test (USB Disconnected)

2. **When you see "UNPLUG USB CABLE NOW" message:**
   - **UNPLUG the USB cable from phone**
   - Leave phone in Studio Mode, undisturbed
   - Place phone in a safe location (don't touch it)
   - Monitoring will continue for 30 minutes

### Phase 3: Monitoring

3. **During the test:**
   - Desktop receiver window should show live video
   - Monitor script will print updates every minute:

```text
     [00 min] Battery: 85% | Temp: 35.2°C | Thermal: OK       | Stream: ACTIVE
     [01 min] Battery: 83% | Temp: 36.1°C | Thermal: OK       | Stream: ACTIVE
     [02 min] Battery: 81% | Temp: 37.8°C | Thermal: WARM     | Stream: ACTIVE
     ```

   - **Note any warnings or unusual behavior**
   - If stream freezes or crashes → document timestamp

### Phase 4: Completion

4. **After 30 minutes:**
   - Script will display summary automatically
   - **Reconnect USB cable** to phone
   - On phone: Press **BACK button** to exit Studio Mode
   - Press **Disconnect** in app to stop streaming
   - Record final observations

---

## Expected Results

| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| Battery Drain | < 60% | 40-60% |
| Drain Rate | 2% per minute | 1.5-2.5% per minute |
| Max Temperature | < 42°C | 35-45°C |
| Thermal State | OK or WARM | No CRITICAL |
| Stream Uptime | 100% | > 95% |
| Crashes | 0 | 0 |

---

## Data Collection

### Automatic Data

- CSV file saved to: `/Users/atorrella/Desktop/Miktos Streamlab/test_results_YYYYMMDD_HHMMSS.csv`
- Contains: Timestamp, Elapsed Minutes, Battery Level, Temperature, Thermal Status, Stream Status

### Manual Observations

**Record during test:**

- [ ] Any screen freezes (timestamp: ****__)
- [ ] Any thermal warnings on status display (timestamp: ****__)
- [ ] Any network interruptions (timestamp: ****__)
- [ ] Red dot animation smooth throughout? (Y/N)
- [ ] Status display updating correctly? (Y/N)

**Post-test questions:**

- Phone feels hot to touch? (1=Cool, 5=Very Hot): ___
- Any app crashes or unexpected exits? ___
- Video quality consistent on desktop? ___
- Any frame drops or stuttering? ___

---

## Troubleshooting

**If monitoring script can't connect to phone:**

- Reconnect USB cable temporarily
- Run: `adb devices` (should show one device)
- Restart monitoring script

**If stream disconnects:**

- Note exact timestamp
- Check desktop receiver for errors
- Check phone screen (exit Studio Mode with BACK button to see error)
- Document what happened before disconnect

**If battery drains faster than expected:**

- Check thermal state (HOT = higher drain)
- Verify brightness at 5% (shouldn't be full brightness)
- Note any background apps running

---

## Next Steps After Test

### If Test PASSES (< 60% drain, no crashes)

✅ Proceed to **Test 2: Remote Control Commands**
✅ Document results in `TEST1_STUDIO_MODE_RESULTS.md`

### If Test FAILS

❌ Analyze failure mode:

- Battery drain too high → Optimize wake lock, screen brightness, encoding settings
- Thermal issues → Review encoding parameters, add thermal throttling
- Crashes → Review logs: `adb logcat -d > crash_log.txt`

---

## Test Results

**Date:** ********___
**Start Time:** ********___
**End Time:** ********___

**Battery:**

- Initial: ****%
- Final: ****%
- Drain: ****%
- Rate: ****% per minute

**Thermal:**

- Max Temp: ****°C
- Max State: **** (OK/WARM/HOT/CRITICAL)

**Stream:**

- Uptime: ****% (****_ minutes)
- Interruptions: ****

**Overall Result:** ⬜ PASS  ⬜ FAIL

**Notes:**
---
---
---

---

**Tester Signature:** ************___
**Date:** ************___
