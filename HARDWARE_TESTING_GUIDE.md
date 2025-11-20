# Hardware Integration Testing Guide
**Date:** November 20, 2025  
**Status:** Ready for Day 2 Testing

---

## 🎯 Testing Objectives

1. ✅ Verify OBS Studio connection
2. ✅ Test scene creation and switching
3. ✅ Validate camera discovery from Android phones
4. ✅ Test end-to-end streaming workflow
5. ✅ Monitor system health and fix runtime issues

---

## 📋 Pre-Testing Checklist

### Server Status
- [x] Miktos Hub server running on `http://127.0.0.1:8000`
- [x] API docs accessible at `http://127.0.0.1:8000/docs`
- [x] Health metrics endpoint responding
- [x] Camera discovery active

### Software Requirements
- [x] OBS Studio installed at `/Applications/OBS.app`
- [ ] OBS WebSocket plugin installed (v5.x required)
- [ ] Android app built and installed on phone
- [ ] Phone and Mac on same WiFi network

### Network Setup
- [ ] Mac WiFi IP address: `_____________`
- [ ] Phone WiFi IP address: `_____________`
- [ ] Firewall allows incoming connections on port 8888 (SRT)
- [ ] mDNS/Bonjour enabled on network

---

## 🔧 STEP 1: OBS Studio Connection Test

### 1.1 Configure OBS WebSocket

**If OBS WebSocket is not installed:**
1. Open OBS Studio
2. Go to `Tools` → `WebSocket Server Settings`
3. If option doesn't exist, install obs-websocket:
   ```bash
   # Download from: https://github.com/obsproject/obs-websocket/releases
   # Install the .pkg file for macOS
   ```

**Configure WebSocket:**
1. Enable WebSocket Server
2. Set Server Port: `4455` (default)
3. Set Password: Leave blank or use simple password
4. Click "Apply" and "OK"

### 1.2 Start OBS Studio

```bash
# Launch OBS from terminal to see logs
open -a OBS
```

**Initial Setup (if first time):**
- Choose "Optimize for streaming"
- Canvas resolution: 1920x1080
- FPS: 30
- Click through wizard

### 1.3 Test Connection from Miktos Hub

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub"
source ../.venv/bin/activate

# Run OBS connection test
python << 'EOF'
import asyncio
from adapters.obs_engine import OBSEngine
from config.settings import Settings

async def test_obs_connection():
    settings = Settings()
    obs = OBSEngine(settings.obs)
    
    print("🔌 Testing OBS connection...")
    try:
        await obs.connect()
        print("✅ OBS Connected!")
        
        # Get version info
        version = await obs._client.get_version()
        print(f"📺 OBS Studio version: {version.obs_version}")
        print(f"🔌 WebSocket version: {version.obs_web_socket_version}")
        
        # List existing scenes
        scenes = await obs._client.get_scene_list()
        print(f"\n📋 Existing scenes ({len(scenes.scenes)}):")
        for scene in scenes.scenes:
            print(f"   - {scene['sceneName']}")
        
        await obs.disconnect()
        print("\n✅ OBS test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure OBS Studio is running")
        print("2. Check WebSocket is enabled in Tools → WebSocket Server Settings")
        print("3. Verify port 4455 is correct")
        print("4. Try restarting OBS Studio")

asyncio.run(test_obs_connection())
EOF
```

**Expected Output:**
```
🔌 Testing OBS connection...
✅ OBS Connected!
📺 OBS Studio version: 30.x.x
🔌 WebSocket version: 5.x.x

📋 Existing scenes (1):
   - Scene

✅ OBS test complete!
```

### 1.4 Test Scene Creation

```bash
# Test creating a scene via API
python << 'EOF'
import requests
import json

print("\n🎬 Testing Scene Creation...")

# Create a new scene
response = requests.post('http://127.0.0.1:8000/api/scenes', json={
    "name": "Test Multi-Camera Scene",
    "layout": "grid_2x2",
    "description": "Testing scene creation from API"
})

if response.status_code == 200:
    scene = response.json()
    print(f"✅ Scene created: {scene.get('name')}")
    print(f"   ID: {scene.get('scene_id')}")
    print(f"   Layout: {scene.get('layout')}")
else:
    print(f"❌ Failed: {response.status_code}")
    print(f"   {response.text}")

# List all scenes
print("\n📋 All Scenes:")
response = requests.get('http://127.0.0.1:8000/api/scenes')
if response.status_code == 200:
    scenes = response.json()
    for scene in scenes:
        print(f"   - {scene['name']} ({scene['layout']})")
EOF
```

---

## 📱 STEP 2: Android Phone Setup

### 2.1 Build and Install Android App

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Mobile/Android"

# Check if Android Studio is set up
echo "Android SDK location:"
echo $ANDROID_HOME

# Build the app (if not already built)
./gradlew assembleDebug

# The APK will be in:
# app/build/outputs/apk/debug/app-debug.apk
```

**Install on Phone:**
1. Enable Developer Mode on phone:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
   - Go back to Settings → Developer Options
   - Enable "USB Debugging"

2. Connect phone via USB

3. Install APK:
```bash
adb devices  # Verify phone is connected
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

**OR use wireless installation:**
1. Upload APK to cloud (Google Drive, Dropbox)
2. Download on phone
3. Install (may need to allow "Install from Unknown Sources")

### 2.2 Configure Phone App

**On the phone:**
1. Open "Miktos StreamLab" app
2. Go to Settings
3. Enter Hub IP address: `192.168.x.x` (your Mac's IP)
4. Default Hub port: `8000`
5. Camera name: "Phone-1" (or custom name)
6. Enable "Auto-discover Hub"
7. Save settings

**Find your Mac's IP:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
```

### 2.3 Test Camera Discovery

**Start discovery on Hub:**
```bash
python << 'EOF'
import requests

print("🔍 Starting camera discovery...")
response = requests.post('http://127.0.0.1:8000/api/discovery/start')
print(f"Status: {response.status_code}")

# Check discovery status
import time
time.sleep(5)

response = requests.get('http://127.0.0.1:8000/api/discovery/status')
status = response.json()
print(f"\n📡 Discovery Status:")
print(f"   Active: {status['active']}")
print(f"   Method: {status['discovery_method']}")
print(f"   Cameras discovered: {status['cameras_discovered']}")
print(f"   Cameras registered: {status['cameras_registered']}")
EOF
```

**On the phone:**
1. Launch Miktos StreamLab app
2. Tap "Connect to Hub"
3. Should see "Discovering..." then "Connected"
4. Camera should start streaming

**Verify on Hub:**
```bash
# List discovered cameras
curl http://127.0.0.1:8000/api/cameras
```

---

## 🎥 STEP 3: End-to-End Streaming Test

### 3.1 Create a Streaming Session

```bash
python << 'EOF'
import requests
import json

print("📺 Creating streaming session...")

# Create session
session = requests.post('http://127.0.0.1:8000/api/', json={
    "name": "Hardware Test Stream",
    "description": "Testing complete workflow with real devices"
}).json()

session_id = session['session_id']
print(f"✅ Session created: {session_id}")
print(f"   Name: {session['name']}")
print(f"   State: {session['state']}")

# Start the session
print(f"\n▶️  Starting session...")
response = requests.post(f'http://127.0.0.1:8000/api/{session_id}/start')
if response.status_code == 200:
    print("✅ Session started!")
else:
    print(f"❌ Failed: {response.text}")

print(f"\n🔗 Monitor at: http://127.0.0.1:8000/docs")
EOF
```

### 3.2 Add Camera to Scene

```bash
python << 'EOF'
import requests

# Get list of cameras
cameras = requests.get('http://127.0.0.1:8000/api/cameras').json()
if cameras:
    camera_id = cameras[0]['id']
    print(f"📱 Found camera: {cameras[0]['name']}")
    
    # Get list of scenes
    scenes = requests.get('http://127.0.0.1:8000/api/scenes').json()
    if scenes:
        scene_id = scenes[0]['scene_id']
        print(f"🎬 Using scene: {scenes[0]['name']}")
        
        # Add camera to scene would go here
        # (This endpoint may need to be implemented)
        print("\n⚠️  Camera-to-scene assignment needs API endpoint")
else:
    print("❌ No cameras found. Ensure phone app is connected.")
EOF
```

### 3.3 Monitor Stream Health

**Watch server logs:**
```bash
tail -f /tmp/miktos_server.log | grep -E "(ERROR|camera|scene|stream)"
```

**Check metrics:**
```bash
# Run in another terminal
watch -n 2 'curl -s http://127.0.0.1:8000/api/health/metrics | python -m json.tool'
```

---

## 🔍 STEP 4: Troubleshooting

### Common Issues

#### OBS Won't Connect
```bash
# Check if OBS is running
ps aux | grep OBS

# Check if WebSocket port is open
lsof -i :4455

# Try with password
# Edit config/settings.py and add OBS password
```

#### Camera Not Discovered
```bash
# Check mDNS is working
dns-sd -B _miktos-camera._tcp

# Check firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Verify phone and Mac on same network
ping <phone-ip>
```

#### Stream Quality Issues
```bash
# Check network stats
netstat -i

# Monitor SRT connection
# (Install srt-live-server for testing)
```

### Debug Commands

```bash
# Check all active connections
lsof -i -P | grep LISTEN

# View detailed server logs
tail -100 /tmp/miktos_server.log

# Test API endpoints
curl http://127.0.0.1:8000/api/health/diagnostics

# Check Python dependencies
pip list | grep -E "obs|websocket|srt"
```

---

## ✅ Success Criteria

- [ ] OBS connects successfully
- [ ] Can create scenes via API
- [ ] Can switch between scenes
- [ ] Phone discovers Hub via mDNS
- [ ] Phone streams video to Hub
- [ ] Hub receives and processes stream
- [ ] OBS shows phone camera feed
- [ ] No dropped frames (<1%)
- [ ] Latency under 500ms
- [ ] System stable for 5+ minutes

---

## 📝 Test Results Log

### Test Run: ___________

**OBS Connection:**
- Status: ⬜ Pass / ⬜ Fail
- Notes: _________________________________

**Camera Discovery:**
- Cameras found: _____
- Registration time: _____ seconds
- Status: ⬜ Pass / ⬜ Fail
- Notes: _________________________________

**Scene Management:**
- Scenes created: _____
- Scene switches: _____
- Status: ⬜ Pass / ⬜ Fail
- Notes: _________________________________

**Streaming Quality:**
- Bitrate: _____ kbps
- Frame rate: _____ fps
- Dropped frames: _____ %
- Latency: _____ ms
- Status: ⬜ Pass / ⬜ Fail

**Issues Found:**
1. _________________________________
2. _________________________________
3. _________________________________

**Overall Result:** ⬜ Pass / ⬜ Needs Work

---

## 🚀 Next Steps After Testing

1. Document all issues found
2. Fix critical bugs blocking workflow
3. Optimize performance bottlenecks
4. Test with multiple phones (2-3 cameras)
5. Test longer streaming sessions (30+ minutes)
6. Validate failover and reconnection
7. Production readiness assessment
