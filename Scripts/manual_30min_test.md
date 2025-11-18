# 30-Minute Studio Mode Test - Manual Procedure (Unplugged)

**Best approach for accurate battery drain measurement**

## Setup (5 minutes before test)

1. **Charge phone to 80-100%**
2. **Desktop: Start receiver**
   ```bash
   cd "/Users/atorrella/Desktop/Miktos Streamlab"
   source .venv/bin/activate
   python3 tcp_h264_receiver_with_preview.py 8554
   ```

3. **Phone: Start streaming**
   - Open StreamLab Camera
   - IP: `192.168.2.36`
   - Port: `8554`
   - Press **Connect**

4. **Record initial state**
   - Battery: _____%
   - Time: _____
   - Temperature (Settings > Battery): _____°C (if available)

5. **Enter Studio Mode**
   - Press **Enter Studio Mode** button
   - Black screen with red dot appears

6. **UNPLUG USB CABLE** from phone

7. **Start timer** - 30 minutes

---

## During Test (Check Every 5 Minutes)

**⚠️ DO NOT touch phone screen or press buttons during checks - just look at it**

### Minute 0 (Start)
- [ ] Battery: _____%
- [ ] Red dot pulsating: Yes / No
- [ ] Desktop receiver showing video: Yes / No

### Minute 5
- [ ] Battery: _____%
- [ ] Stream still active: Yes / No

### Minute 10
- [ ] Battery: _____%
- [ ] Stream still active: Yes / No

### Minute 15
- [ ] Battery: _____%
- [ ] Stream still active: Yes / No
- [ ] Phone temperature: Cool / Warm / Hot

### Minute 20
- [ ] Battery: _____%
- [ ] Stream still active: Yes / No

### Minute 25
- [ ] Battery: _____%
- [ ] Stream still active: Yes / No

### Minute 30 (End)
- [ ] Battery: _____%
- [ ] Stream still active: Yes / No
- [ ] Phone temperature: Cool / Warm / Hot

---

## How to Check Battery WITHOUT Exiting Studio Mode

**Option 1: Quick glance at status display**
- Studio Mode shows battery % in top-right corner
- Just look at the screen (don't touch)

**Option 2: If status not visible**
- Briefly press **BACK button** to exit Studio Mode
- Check battery in notification pulldown
- Press **Enter Studio Mode** again immediately
- (This causes ~5 second interruption)

---

## End Test

1. **Reconnect USB cable** (optional, for data transfer)
2. **Press BACK button** to exit Studio Mode
3. **Press Disconnect** in app
4. **Calculate results**:
   - Initial battery: _____%
   - Final battery: _____%
   - **Total drain: _____% in 30 minutes**
   - **Drain rate: _____% per minute**
   - **Projected 60-min drain: _____% (x2)**

---

## Success Criteria

| Metric | Target | Result |
|--------|--------|--------|
| Total drain | < 60% | ___% |
| Drain rate | ~2%/min | ___/min |
| Stream uptime | 100% | ___% |
| Crashes | 0 | ___ |

**PASS** if drain < 60% and no crashes  
**FAIL** if drain > 60% or stream disconnects

---

## Notes

**If battery drains faster than expected:**
- Check Studio Mode is active (screen should be mostly black, not showing camera UI)
- Verify screen brightness is dimmed (should be barely visible)
- Ensure no other apps running in background
- Check thermal state (overheating increases battery drain)

**If stream disconnects:**
- Note exact time: _____
- Check desktop receiver logs
- Try reconnecting and documenting issue
- This is a FAIL condition - investigate before proceeding

---

## Next Steps

**If PASS:** 
- ✅ Document results in TEST1_STUDIO_MODE_RESULTS.md
- ✅ Proceed to Test 2: Remote Control Commands

**If FAIL:**
- ❌ Analyze failure mode
- ❌ Review logs: `adb logcat -d > failure_log.txt`
- ❌ Optimize and re-test before Week 2

