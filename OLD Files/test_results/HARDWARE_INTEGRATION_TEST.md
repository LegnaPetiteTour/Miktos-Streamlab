# Hardware Integration Test - Live Session

**Date:** November 20, 2025  
**Tester:** [Your Name]  
**Duration:** 1-2 hours  
**Status:** 🔄 In Progress

---

## 🎯 Test Objectives

1. ✅ Build and install Android app on physical device
2. ✅ Start Desktop Control Panel
3. ✅ Connect phone to WebSocket server
4. ✅ Test all remote control commands
5. ✅ Verify end-to-end streaming workflow
6. ✅ Document all findings

---

## 📋 Pre-Test Checklist

### Environment Setup

- [ ] Mac WiFi IP address: `_____________`
- [ ] Phone WiFi IP address: `_____________`
- [ ] Both devices on same network
- [ ] Firewall allows incoming connections
- [ ] Virtual environment activated

### Software Verification

```bash
# Check Python environment
cd "/Users/atorrella/Desktop/Miktos Streamlab"
source .venv/bin/activate
python --version  # Should be 3.10+

# Check Android SDK
echo $ANDROID_HOME  # Should show SDK path
```

---

## 🔧 Test Procedure

### PART 1: Android App Build & Installation (20 min)

#### Step 1.1: Build the APK

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Mobile/Android"

# Clean previous builds
./gradlew clean

# Build debug APK
./gradlew assembleDebug
```

**Expected output:**
```text
BUILD SUCCESSFUL in 30s
```

**APK location:** `app/build/outputs/apk/debug/app-debug.apk`

**Result:** ⬜ Pass / ⬜ Fail  
**Notes:** ___________________________________________

#### Step 1.2: Install on Phone

**Option A: USB Installation**

```bash
# Enable USB debugging on phone:
# Settings → About Phone → Tap "Build Number" 7 times
# Settings → Developer Options → Enable "USB Debugging"

# Connect phone via USB
adb devices  # Should show your device

# Install APK
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

**Option B: Wireless Installation**

```bash
# Find your Mac's IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Upload APK to cloud or use:
adb connect <phone-ip>:5555
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

**Result:** ⬜ Pass / ⬜ Fail  
**Installation Time:** _____ seconds  
**Notes:** ___________________________________________

---

### PART 2: Desktop Control Panel Setup (10 min)

#### Step 2.1: Start Control Panel

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend/remote_control"

# Start both servers
./start_control_panel.sh
```

**Expected output:**
```text
================================================
  Miktos StreamLab - Remote Control System
================================================

📦 Activating virtual environment...
✅ Dependencies OK

Starting servers...
🎥 WebSocket server started (port 9000-9001)
🌐 Web control panel started (port 5000)

Open your browser to: http://localhost:5000
```

**Result:** ⬜ Pass / ⬜ Fail  
**WebSocket Port:** _____ (should be 9000-9001)  
**Web Panel Port:** _____ (should be 5000)  
**Notes:** ___________________________________________

#### Step 2.2: Verify Web Interface

1. Open browser: `http://localhost:5000`
2. Verify page loads with header "Miktos StreamLab - Remote Camera Control Panel"
3. Check status bar shows: "Connected: 0, Streaming: 0, Paused: 0"

**Result:** ⬜ Pass / ⬜ Fail  
**Screenshot:** ___________________________________________

---

### PART 3: Camera Connection Test (15 min)

#### Step 3.1: Configure Android App

**On the phone:**

1. Open "Miktos StreamLab" app
2. Tap Settings (gear icon)
3. Enable "Remote Control"
4. Enter Hub IP: `192.168.x.x` (your Mac's IP)
5. Enter Port: `9000`
6. Camera Name: "Test-Phone-1"
7. Tap "Save"
8. Tap "Connect to Hub"

**Expected behavior:**
- Phone shows: "✅ WebSocket connected"
- Desktop logs show: "📱 Camera registered: [device-id]"
- Web UI: Camera card appears automatically

**Result:** ⬜ Pass / ⬜ Fail  
**Connection Time:** _____ seconds  
**Camera ID shown:** ___________________________________________  
**Initial State:** _____ (should be IDLE)  
**Battery Level:** _____ %  
**Network Type:** ___________________________________________  
**Notes:** ___________________________________________

---

### PART 4: Remote Control Commands (30 min)

#### Test 4.1: START Command

**Steps:**
1. In web UI, click "▶️ START" button on camera card
2. Observe phone screen
3. Check desktop logs
4. Verify web UI state changes

**Expected results:**
- Phone begins streaming within 1 second
- Desktop logs: "📤 Command sent: START"
- Web UI shows state: "RUNNING" (green border)
- Status bar increments "Streaming" count

**Actual results:**
- Command sent: ⬜ Yes / ⬜ No
- Phone started streaming: ⬜ Yes / ⬜ No
- UI updated to RUNNING: ⬜ Yes / ⬜ No
- Response time: _____ ms

**Result:** ⬜ Pass / ⬜ Fail  
**Notes:** ___________________________________________

#### Test 4.2: STOP Command

**Steps:**
1. Click "⏹️ STOP" button
2. Observe phone and UI

**Expected results:**
- Phone stops streaming immediately
- UI shows state: "STOPPED"
- Green border disappears

**Result:** ⬜ Pass / ⬜ Fail  
**Response time:** _____ ms  
**Notes:** ___________________________________________

#### Test 4.3: PAUSE Command

**Steps:**
1. Click "▶️ START" to begin streaming
2. Wait 5 seconds
3. Click "⏸️ PAUSE" button
4. Wait 30 seconds
5. Check connection status

**Expected results:**
- Phone shows frozen frame
- UI shows state: "PAUSED" (orange border)
- Connection remains alive (no disconnect)
- Status bar shows "Paused: 1"

**Result:** ⬜ Pass / ⬜ Fail  
**Pause duration tested:** _____ seconds  
**Connection maintained:** ⬜ Yes / ⬜ No  
**Notes:** ___________________________________________

#### Test 4.4: RESUME Command

**Steps:**
1. From PAUSED state, click "▶️ RESUME"
2. Observe immediate response

**Expected results:**
- Streaming resumes instantly
- UI returns to "RUNNING" state
- No reconnection delay

**Result:** ⬜ Pass / ⬜ Fail  
**Resume time:** _____ ms  
**Notes:** ___________________________________________

#### Test 4.5: Studio Mode

**Steps:**
1. Click "🌙 Studio Mode" button
2. Check phone screen
3. Long-press phone screen for 3 seconds
4. Verify return to normal

**Expected results:**
- Phone screen goes full black with small red recording dot
- Status updates continue
- Long-press exits studio mode

**Result:** ⬜ Pass / ⬜ Fail  
**Screen went black:** ⬜ Yes / ⬜ No  
**Exit worked:** ⬜ Yes / ⬜ No  
**Notes:** ___________________________________________

#### Test 4.6: Refresh Status

**Steps:**
1. Click "🔄 Refresh" button
2. Observe status update

**Expected results:**
- Status updates within 1 second
- Battery, network, thermal all refresh

**Result:** ⬜ Pass / ⬜ Fail  
**Notes:** ___________________________________________

---

### PART 5: Status Monitoring (15 min)

#### Test 5.1: Real-time Updates

**Steps:**
1. Keep web UI open
2. Change phone state (start/stop streaming)
3. Plug/unplug charger
4. Move between WiFi and cellular

**Observations:**

| Action | UI Updated | Time Delay | Notes |
|--------|------------|------------|-------|
| Start streaming | ⬜ Yes / ⬜ No | _____ ms | __________ |
| Stop streaming | ⬜ Yes / ⬜ No | _____ ms | __________ |
| Plug charger | ⬜ Yes / ⬜ No | _____ ms | __________ |
| Network change | ⬜ Yes / ⬜ No | _____ ms | __________ |

**Overall Result:** ⬜ Pass / ⬜ Fail

#### Test 5.2: Disconnect/Reconnect

**Steps:**
1. Turn off phone WiFi
2. Observe UI shows "OFFLINE" (red)
3. Turn WiFi back on
4. Observe auto-reconnection

**Result:** ⬜ Pass / ⬜ Fail  
**Offline detection time:** _____ seconds  
**Reconnection time:** _____ seconds  
**Auto-recovery:** ⬜ Yes / ⬜ No  
**Notes:** ___________________________________________

---

### PART 6: End-to-End Streaming (Optional, if OBS available)

#### Test 6.1: OBS Integration

**Setup:**
```bash
# Start OBS Studio
open -a OBS

# In OBS: Tools → WebSocket Server Settings
# Enable server, port 4455, no password
```

**Steps:**
1. Configure OBS to receive SRT stream on port 8554
2. In web UI, start streaming from phone
3. Verify video appears in OBS

**Result:** ⬜ Pass / ⬜ Fail / ⬜ Skipped  
**Video quality:** ___________________________________________  
**Latency:** _____ ms  
**Notes:** ___________________________________________

---

## 📊 Test Summary

### Overall Results

**Tests Passed:** _____ / 15  
**Tests Failed:** _____  
**Tests Skipped:** _____

**Pass Rate:** _____ %

### Critical Issues Found

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Non-Critical Issues

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Performance Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Command latency | <1s | _____ ms | ⬜ Pass / ⬜ Fail |
| Status update | <2s | _____ ms | ⬜ Pass / ⬜ Fail |
| UI render | <100ms | _____ ms | ⬜ Pass / ⬜ Fail |
| Connection time | <5s | _____ s | ⬜ Pass / ⬜ Fail |
| Reconnect time | <5s | _____ s | ⬜ Pass / ⬜ Fail |

---

## 🐛 Issues Log

### Issue #1

**Severity:** ⬜ Critical / ⬜ High / ⬜ Medium / ⬜ Low  
**Component:** ___________________________________________  
**Description:** ___________________________________________  
**Steps to reproduce:** ___________________________________________  
**Expected:** ___________________________________________  
**Actual:** ___________________________________________  
**Workaround:** ___________________________________________

### Issue #2

**Severity:** ⬜ Critical / ⬜ High / ⬜ Medium / ⬜ Low  
**Component:** ___________________________________________  
**Description:** ___________________________________________

*(Add more as needed)*

---

## 📸 Screenshots/Logs

**Desktop Control Panel:**
```
[Paste screenshot or describe state]
```

**Android App:**
```
[Paste screenshot or describe state]
```

**Console Logs (first 50 lines):**
```bash
# WebSocket server logs
tail -50 /tmp/websocket_server.log

# Control panel logs
tail -50 /tmp/control_panel.log
```

---

## ✅ Sign-Off

**Tester:** ___________________________________________  
**Date:** ___________________________________________  
**Time Spent:** _____ hours _____ minutes  

**Overall Assessment:**
⬜ Ready for production  
⬜ Needs minor fixes  
⬜ Needs major work  
⬜ Blocked by critical issues

**Next Steps:**
1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

---

## 📝 Notes & Observations

*Use this section for any additional observations, suggestions, or context*

___________________________________________
___________________________________________
___________________________________________

