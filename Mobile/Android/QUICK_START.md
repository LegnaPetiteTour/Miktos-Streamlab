# 🚀 Quick Start Card - Android Streaming Test

## ⚡ 5-Minute Setup

### 1️⃣ Enable Developer Mode (One-time setup)

```text
Phone Settings → About Phone → Tap "Build number" 7 times
Settings → Developer Options → Enable "USB debugging"
```

### 2️⃣ Connect Phone to Mac

```bash
# Connect USB cable, approve popup on phone
adb devices    # Verify connection
```

### 3️⃣ Install App

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Mobile/Android"
./gradlew installDebug
```

### 4️⃣ Start Mac Receiver

```bash
# Terminal Window 1:
cd "/Users/atorrella/Desktop/Miktos Streamlab"
source .venv/bin/activate
python3 tcp_h264_receiver.py
```

### 5️⃣ Get Mac IP

```bash
# Terminal Window 2:
ifconfig | grep "inet " | grep -v 127.0.0.1
# Note the IP (e.g., 192.168.2.36)
```

### 6️⃣ Stream from Phone

```text
1. Open "Miktos Camera" app
2. Grant all permissions (camera/audio/notification)
3. Enter Mac IP: 192.168.2.36 (use YOUR IP)
4. Port: 8554
5. Tap "START STREAMING"
```

## ✅ Success Indicators

**On Phone:**

- Red "STOP STREAMING" button
- "✅ LIVE: Streaming to..." status
- Notification: "📹 Streaming to Mac..."

**On Mac Terminal:**

- "✅ Connected to..."
- "📊 Receiving stream... X.X MB/s"

## ⚠️ Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| `adb devices` empty | Reconnect USB, approve popup on phone |
| Connection refused | Check Wi-Fi (same network), verify IP |
| App crashes | Grant all 3 permissions |
| No stream data | Check lighting, move closer to Wi-Fi router |

## 📝 Your Details

**Your Mac IP:** _________________ (from step 5)

**Port:** 8554 (don't change)

**Wi-Fi Network:** _________________ (same for both devices)

---

**Full Guide:** See `TESTING_GUIDE.md` for detailed instructions
