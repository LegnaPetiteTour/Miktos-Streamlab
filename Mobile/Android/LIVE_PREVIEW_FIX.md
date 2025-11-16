# 🎬 Live Preview Fix - Quick Guide

## Problem

- ✅ Streaming works (data is being received)
- ❌ No live preview on Mac
- ❌ No camera preview on phone

## Solution

### Option 1: Use New Receiver with ffplay (RECOMMENDED)

This will show the live video on your Mac!

#### Step 1: Stop Current Receiver

In the Terminal where the receiver is running:

- Press `Ctrl+C` to stop it

#### Step 2: Check if ffplay is installed

```bash
which ffplay
```

**If you see a path** (like `/opt/homebrew/bin/ffplay`): ✅ You have it!

**If you see nothing:** Install ffmpeg:

```bash
brew install ffmpeg
```

(This takes 2-3 minutes)

#### Step 3: Start New Receiver with Live Preview

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab"
source .venv/bin/activate
python3 tcp_h264_receiver_with_preview.py
```

#### Step 4: Restart Streaming on Phone

1. On phone, tap "STOP STREAMING"
2. Wait 2 seconds
3. Tap "START STREAMING" again

**You should now see:**

- 📺 A new window opens on Mac showing live video!
- 📊 Terminal shows stats (FPS, bitrate, etc.)

---

### What You'll See

**On Mac:**

```text
🎥 Miktos StreamLab Camera - TCP H.264 Receiver
============================================================
📺 Live preview enabled (press Q in preview window to close)

🎥 TCP H.264 Receiver with Live Preview
📡 Listening on 0.0.0.0:8554
============================================================
Waiting for Android StreamLab Camera connection...

✅ Connected to 192.168.2.27:39418 at 2025-11-15 19:01:01
🚀 Starting live preview window...
🎬 Preview window opened (PID: 12345)
📊 P-Frame | Frames: 30 | FPS: 30.1 | Bitrate: 6.12 Mbps | Total: 2.3 MB
```

**A video window will pop up showing whatever your phone camera sees!**

---

### Commands

**Start with preview (default):**

```bash
python3 tcp_h264_receiver_with_preview.py
```

**Stats only (no preview window):**

```bash
python3 tcp_h264_receiver_with_preview.py --no-preview
```

**Use different port:**

```bash
python3 tcp_h264_receiver_with_preview.py 9000
```

**Stop receiver:**

- Press `Ctrl+C` in Terminal, or
- Press `Q` in the video preview window

---

### Troubleshooting

#### "ffplay: command not found"

```bash
brew install ffmpeg
```

#### Preview window appears but is black

- Give it 2-3 seconds to start
- Check phone is actually streaming (look for "STOP STREAMING" button)
- Try stopping and restarting the stream on phone

#### Preview is laggy

- This is normal for first few seconds
- Should stabilize at 30 FPS after ~5 seconds
- Check Wi-Fi signal strength

#### No preview window at all

- Check Terminal for errors
- Make sure ffplay installed: `which ffplay`
- Try `--no-preview` mode to verify data is received

---

## Phone Camera Preview (Coming Soon)

The Android app has a PreviewView but it's not currently connected to show what the camera sees. This is a known limitation - you can still stream successfully, you just won't see the preview on the phone screen.

**Workaround:** Use the Mac's live preview window to see what you're filming!

---

## Quick Test

1. **Stop old receiver** (Ctrl+C)
2. **Start new receiver:**

   ```bash
   python3 tcp_h264_receiver_with_preview.py
   ```

3. **On phone:** Stop then Start streaming
4. **Watch for preview window to pop up!**

You should see live video from your phone camera on your Mac screen!

---

## Success Checklist

- [ ] ffplay installed (`brew install ffmpeg`)
- [ ] New receiver script running
- [ ] Phone streaming (red STOP button visible)
- [ ] Terminal shows "Preview window opened"
- [ ] Video preview window appears on Mac
- [ ] Can see live video from phone camera

---

**Press Q in the preview window or Ctrl+C in Terminal to stop!**
