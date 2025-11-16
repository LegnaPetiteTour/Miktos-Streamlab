# 🔄 Streaming Connection Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     ANDROID PHONE                                │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         📱 Miktos Camera App                           │     │
│  │                                                        │     │
│  │  [Mac IP: 192.168.2.36] [Port: 8554]                 │     │
│  │                                                        │     │
│  │         [🟢 START STREAMING]                          │     │
│  │                                                        │     │
│  │  Status: ✅ LIVE Streaming...                         │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           │ Captures Video                       │
│                           ▼                                      │
│                    📹 Camera Sensor                              │
│                           │                                      │
│                           │ Encodes to H.264                     │
│                           ▼                                      │
│                    🔧 Hardware Encoder                           │
│                           │                                      │
│                           │ Streams via TCP                      │
│                           ▼                                      │
│                    🌐 Wi-Fi (192.168.2.xx)                       │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            │ TCP Stream (Port 8554)
                            │ ~6 Mbps H.264 video
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                        Wi-Fi ROUTER                                │
│                    (192.168.2.1)                                   │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                      YOUR MAC                                      │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │         💻 Terminal Window                              │     │
│  │                                                          │     │
│  │  $ python3 tcp_h264_receiver.py                         │     │
│  │                                                          │     │
│  │  🎥 TCP H.264 Receiver started on 0.0.0.0:8554        │     │
│  │  Waiting for connection...                              │     │
│  │                                                          │     │
│  │  ✅ Connected to 192.168.2.151:52341                   │     │
│  │  📊 Receiving stream... 5.8 MB/s (30 fps)              │     │
│  │  📦 Total received: 145 MB                              │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                    │
│  IP Address: 192.168.2.36                                        │
│  Listening on Port: 8554                                          │
└───────────────────────────────────────────────────────────────────┘


NETWORK REQUIREMENTS:
═══════════════════════════════════════════════════════════════
 ✅ Both devices on SAME Wi-Fi network
 ✅ No VPN or guest network on phone
 ✅ Mac firewall allows incoming connections (port 8554)
 ✅ Strong Wi-Fi signal (close to router for testing)


CONNECTION FLOW:
═══════════════════════════════════════════════════════════════

1. Mac starts receiver → Listens on port 8554
   │
2. Phone app starts → Asks: "Where is the Mac?"
   │
3. You enter Mac IP (192.168.2.36) → Phone knows where to send
   │
4. Phone connects to Mac:8554 → Establishes TCP connection
   │
5. Camera captures → Encoder compresses → Sends to Mac
   │
6. Mac receives → Shows stats in terminal
   └─→ Stream continues until you stop or disconnect


DATA FLOW:
═══════════════════════════════════════════════════════════════

 Phone Camera (1080p30) 
      ↓
 H.264 Encoder (6 Mbps bitrate)
      ↓
 TCP Socket → Wi-Fi → Router → Wi-Fi → Mac
      ↓
 Mac Receiver (saves/displays stream data)


WHAT YOU'LL SEE:
═══════════════════════════════════════════════════════════════

On Phone Screen:
  - Live camera preview
  - "✅ LIVE: Streaming to 192.168.2.36:8554"
  - Red STOP button

On Phone Notification:
  - "📹 Streaming to Mac..."
  - "🟢 Connected | Bitrate: 6 Mbps"

On Mac Terminal:
  - Connection timestamp
  - Bytes/second (should be ~5-6 MB/s)
  - Total data received
  - Connection status


TROUBLESHOOTING MAP:
═══════════════════════════════════════════════════════════════

Phone Can't Connect?
 │
 ├─→ Check: Same Wi-Fi? 
 ├─→ Check: Correct IP?  (ifconfig on Mac)
 ├─→ Check: Receiver running? (Terminal shows "Waiting...")
 └─→ Check: Port 8554?  (Don't change it)

Stream Stutters?
 │
 ├─→ Move closer to Wi-Fi router
 ├─→ Close other apps on phone
 ├─→ Check Wi-Fi speed (should be >20 Mbps)
 └─→ Check: Background downloads on Mac?

App Crashes?
 │
 ├─→ Grant all permissions (Camera, Audio, Notifications)
 ├─→ Restart app
 └─→ Reinstall: ./gradlew installDebug

```
