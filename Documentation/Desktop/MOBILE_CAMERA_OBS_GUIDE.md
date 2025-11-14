# 📱 Mobile Camera → OBS Integration Guide
## Week 1 MVP - Getting Your Phone Into OBS

This guide shows you how to get your phone's camera feed into OBS Studio using the StreamLab mobile camera system.

---

## 🎯 What You're Building

```
iPhone Camera  →  SRT Stream  →  Desktop Receiver  →  OBS Studio
   (H.264)          (WiFi)         (FFmpeg)          (Window/Virtual Cam)
```

**End Goal**: Your phone appears as a camera source in OBS with <300ms latency.

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Start Desktop Receiver

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab"
./quick_test_mobile_camera.sh
```

This will:
- ✅ Check prerequisites (FFmpeg, Python, SRT support)
- ✅ Display your desktop IP address
- ✅ Start SRT receiver on port 9001
- ✅ Show instructions for mobile app

### Step 2: Configure Mobile App

1. Open **StreamLab Camera** app on your iPhone
2. Enter **Desktop IP** (shown in terminal)
3. Enter **Port**: `9001`
4. Press **START STREAMING**

### Step 3: Add to OBS

The receiver creates a window titled **"StreamLab Camera (Port 9001)"**

In OBS Studio:
1. Click **+ (Add Source)**
2. Select **Window Capture**
3. Name it: "Mobile Camera 1"
4. Select window: **"StreamLab Camera (Port 9001)"**
5. Click **OK**

✅ **Done!** Your phone is now in OBS.

---

## 🔧 Integration Methods

There are 3 ways to get the mobile stream into OBS:

### Method 1: Window Capture (✅ Recommended for Week 1)

**Pros:**
- ✅ Works immediately on macOS and Linux
- ✅ No additional software needed
- ✅ Reliable and simple

**Cons:**
- ❌ Window must stay visible
- ❌ Captures window border (can crop)
- ❌ Can't use multiple cameras easily

**Setup:**
```bash
# Start receiver in window mode (default)
python3 -m src.mobile.srt_receiver --port 9001 --output window
```

In OBS:
- Add → Window Capture → Select "StreamLab Camera" window
- Use ALT+drag to crop window border if needed

---

### Method 2: Virtual Camera (Linux)

**Pros:**
- ✅ Appears as real camera in OBS
- ✅ Can hide receiver window
- ✅ Supports multiple cameras

**Cons:**
- ❌ Requires v4l2loopback setup
- ❌ Linux only (macOS needs OBS Virtual Camera plugin)

**Setup (Linux):**
```bash
# Install v4l2loopback
sudo apt-get install v4l2loopback-dkms

# Load kernel module
sudo modprobe v4l2loopback devices=4 video_nr=10,11,12,13

# Start receiver in virtual camera mode
python3 -m src.mobile.srt_receiver --port 9001 --output virtual_camera
```

In OBS:
- Add → Video Capture Device → Select "/dev/video10"

---

### Method 3: Browser Source (Future)

**Pros:**
- ✅ Most flexible
- ✅ Can add custom overlays easily
- ✅ Works cross-platform

**Cons:**
- ❌ Requires local web server
- ❌ More complex setup
- ❌ Not implemented in Week 1

**Status:** Planned for Week 3

---

## 🎬 Multi-Camera Setup

Want to use 2-3 phones simultaneously?

### Start Multiple Receivers

Each phone needs its own port:

```bash
# Terminal 1: Camera 1
python3 -m src.mobile.srt_receiver --port 9001 --output window

# Terminal 2: Camera 2  
python3 -m src.mobile.srt_receiver --port 9002 --output window

# Terminal 3: Camera 3
python3 -m src.mobile.srt_receiver --port 9003 --output window
```

### Configure Mobile Apps

- Phone 1: IP = `192.168.1.100`, Port = `9001`
- Phone 2: IP = `192.168.1.100`, Port = `9002`  
- Phone 3: IP = `192.168.1.100`, Port = `9003`

### Add to OBS

1. Add Window Capture: "StreamLab Camera (Port 9001)" → Name "Phone 1"
2. Add Window Capture: "StreamLab Camera (Port 9002)" → Name "Phone 2"
3. Add Window Capture: "StreamLab Camera (Port 9003)" → Name "Phone 3"

✅ All 3 phones now available in OBS!

---

## 📊 Monitoring & Quality

### Check Stream Stats

The receiver logs:
- ✅ Connection status
- ✅ Bitrate
- ✅ Resolution
- ✅ Dropped frames

Watch the terminal for issues:
```
INFO - FFmpeg process started (PID: 12345)
INFO - Waiting for mobile phone to connect...
INFO - Stream connected from 192.168.1.150
INFO - Receiving 1080p30 @ 5.2 Mbps
```

### Latency Test

To measure end-to-end latency:

1. **On Phone**: Display a timer app
2. **In OBS**: Record the scene with phone source
3. **Compare**: Original timer vs OBS output

**Target**: <300ms (acceptable for Week 1 MVP)

---

## ⚙️ Advanced Options

### Adjust SRT Latency

Default is 120ms. Increase for unstable WiFi:

```bash
python3 -m src.mobile.srt_receiver --port 9001 --latency 200
```

**Guidelines:**
- Local WiFi: 80-120ms
- Congested network: 150-200ms
- Remote/Internet: 300-500ms

### Change Output Resolution

Edit the FFmpeg command in `srt_receiver.py`:

```python
# Scale to 720p (lower bandwidth)
'-vf', 'scale=1280:720',
```

### Record Streams Directly

Capture the SRT stream to disk:

```bash
ffmpeg -i srt://0.0.0.0:9001?mode=listener -c copy output.mp4
```

---

## 🔥 Troubleshooting

### Problem: No video in receiver window

**Check:**
- ✅ Phone app shows "Streaming to..."
- ✅ Desktop firewall allows port 9001
- ✅ Both devices on same WiFi network
- ✅ FFmpeg shows "Stream connected"

**Solution:**
```bash
# Check if port is listening
lsof -i :9001

# Test SRT connection manually
ffplay srt://0.0.0.0:9001?mode=listener
```

### Problem: High latency (>500ms)

**Causes:**
- Weak WiFi signal
- Network congestion
- Phone overheating
- Too high bitrate

**Solutions:**
1. Move phone closer to router
2. Use 5GHz WiFi band
3. Reduce video quality in app
4. Increase SRT latency parameter

### Problem: Choppy video in OBS

**Check:**
1. OBS encoder settings (use NVENC if available)
2. Desktop CPU usage (<70%)
3. Network packet loss (should be <1%)

**Solution:**
```bash
# Use lower resolution receiver
python3 -m src.mobile.srt_receiver --port 9001 --output window --latency 150
```

### Problem: Window border visible in OBS

**Solution:**
1. In OBS, select the Window Capture source
2. Hold ALT and drag edges to crop border
3. Or: Use Transform → Edit Transform → Crop

---

## 🎯 Week 1 MVP Checklist

By end of Week 1, you should have:

- [ ] ✅ Mobile app builds and runs on iPhone
- [ ] ✅ Desktop receiver starts without errors
- [ ] ✅ Phone connects and streams to desktop
- [ ] ✅ Video appears in receiver window
- [ ] ✅ OBS shows phone camera as source
- [ ] ✅ Latency is <300ms
- [ ] ✅ Stream is stable for >5 minutes
- [ ] ✅ Can use 1-2 phones simultaneously
- [ ] ✅ Demo video recorded

---

## 📹 Creating Your Demo Video

Show off your mobile camera system:

### What to Record

1. **Setup (30 seconds)**:
   - Show mobile app UI
   - Enter IP and port
   - Press "Start Streaming"

2. **Desktop (30 seconds)**:
   - Show terminal with receiver logs
   - Show receiver window with video

3. **OBS (60 seconds)**:
   - Show OBS with mobile camera source
   - Switch between scenes
   - Show latency test with timer
   - Show 2-3 phones if available

4. **Final Shot (30 seconds)**:
   - Show final stream output
   - Mention "Week 1 MVP Complete"

### Recording Tips

```bash
# Record OBS output
OBS → File → Start Recording

# Or use QuickTime (macOS)
QuickTime → File → New Screen Recording
```

---

## 🚀 Next Steps (Week 2)

After Week 1 MVP is complete:

### Week 2: Optimize Latency
- [ ] Reduce to <150ms target
- [ ] Add network quality monitoring
- [ ] Implement automatic bitrate adjustment

### Week 2-3: Professional Features
- [ ] QR code pairing (no manual IP entry)
- [ ] Tally feedback (on-air indicator)
- [ ] Studio Mode (DND, thermal management)
- [ ] Multi-camera director controls

### Week 3-4: Polish
- [ ] Beautiful mobile app UI
- [ ] Desktop control panel
- [ ] One-click setup wizard

---

## 📚 Additional Resources

### react-native-vision-camera
- Docs: https://react-native-vision-camera.com/
- Examples: https://github.com/mrousavy/react-native-vision-camera/tree/main/example

### SRT Protocol
- Specification: https://github.com/Haivision/srt
- FFmpeg SRT: https://ffmpeg.org/ffmpeg-protocols.html#srt

### OBS Studio
- Forum: https://obsproject.com/forum/
- Plugins: https://obsproject.com/forum/resources/

---

## 💡 Pro Tips

1. **WiFi Optimization**:
   - Use dedicated 5GHz network for cameras
   - Router close to phones
   - Reduce other WiFi traffic during streaming

2. **Phone Management**:
   - Keep phones charged (or on power)
   - Lock exposure and white balance
   - Use airplane mode + WiFi (disable cellular)

3. **OBS Setup**:
   - Create scene collection for mobile cameras
   - Use Studio Mode for preview
   - Set up hotkeys for camera switching

4. **Testing**:
   - Test with 1 phone first
   - Add more cameras one at a time
   - Always have wired camera as backup

---

**Status**: Week 1 MVP Integration Guide  
**Last Updated**: 2025-11-10  
**Next**: Complete Week 1 testing and create demo video
