# E2E Critical Validation Guide

**Status**: ⚠️ CRITICAL - Hardware validation required
**Last Updated**: November 26, 2025

This guide walks through the critical end-to-end validation tasks for Miktos Hub with real hardware and streaming destinations.

---

## 🎯 Objectives

1. ✅ Camera discovery and connection (DONE)
2. ✅ Live session creation (DONE)
3. ❌ **OBS scene switching with real sources** (THIS GUIDE)
4. ❌ **Streaming to real destinations** (THIS GUIDE)
5. ❌ **Full production workflow** (THIS GUIDE)

---

## 📋 Prerequisites

### Hardware/Software Required

- **OBS Studio** (v28+ recommended)
  - Download: <https://obsproject.com/>
  - obs-websocket plugin (usually included)
- **Camera** (Sony a7 IV or any camera with RTMP output)
- **Network connectivity** for streaming
- **Streaming account** (choose one):
  - YouTube account with streaming enabled
  - Twitch account
  - Local RTMP test server (optional)

### Miktos Hub Server

```bash
# Ensure server is running
cd "/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub"
source venv/bin/activate
python main.py
```

Server should be accessible at: `http://localhost:8000`

---

## 🎬 Test 1: OBS Scene Switching with Real Sources

### Step 1.1: Configure obs-websocket

1. **Launch OBS Studio**

2. **Enable obs-websocket**:
   - Go to **Tools → obs-websocket Settings**
   - Check "Enable WebSocket server"
   - Default port: `4455`
   - Note the password (if set) or disable authentication for testing

3. **Verify Connection**:

   ```bash
   # Test OBS connection from Miktos Hub
   curl http://localhost:8000/api/obs/status
   ```

   Expected response:

   ```json
   {
     "connected": true,
     "version": "5.x.x",
     "websocket_version": "5.x.x",
     "recording": false,
     "streaming": false,
     "current_scene": "Scene Name"
   }
   ```

### Step 1.2: Create Test Scenes in OBS

Create 3 test scenes with different layouts:

#### Scene 1: "Main Camera"

- Add **Video Capture Device** source
- Configure for your main camera (Sony a7 IV / Imaging Edge / capture card)

#### Scene 2: "Picture-in-Picture"

- Add **Video Capture Device** source (main camera)
- Add **Video Capture Device** source (secondary camera/webcam)
- Position secondary as PiP overlay

#### Scene 3: "Screen Share"

- Add **Display Capture** or **Window Capture** source
- Optional: Add **Video Capture Device** in corner

### Step 1.3: Test Scene Listing via API

```bash
# List all OBS scenes
curl http://localhost:8000/api/obs/scenes

# Expected response:
# {
#   "scenes": [
#     {"name": "Main Camera", "is_active": true, "index": 0},
#     {"name": "Picture-in-Picture", "is_active": false, "index": 1},
#     {"name": "Screen Share", "is_active": false, "index": 2}
#   ],
#   "total": 3,
#   "current_scene": "Main Camera"
# }
```

### Step 1.4: Test Scene Switching

#### Method 1: Path parameter

```bash
# Switch to "Picture-in-Picture" scene
curl -X POST http://localhost:8000/api/obs/scenes/Picture-in-Picture/activate

# Verify in OBS Studio that the scene changed
```

#### Method 2: Request body

```bash
# Switch to "Screen Share" scene
curl -X POST http://localhost:8000/api/obs/scenes/switch \
  -H "Content-Type: application/json" \
  -d '{"scene_name": "Screen Share"}'
```

**Validation**:

- ✅ OBS Studio preview updates to show new scene
- ✅ API returns success response
- ✅ Subsequent `/api/obs/status` call shows correct `current_scene`

### Step 1.5: Test Scene Switching During Streaming

```bash
# 1. Start streaming in OBS Studio (manually for now)
# 2. Switch scenes while streaming
curl -X POST http://localhost:8000/api/obs/scenes/Main%20Camera/activate

# 3. Wait 5 seconds
sleep 5

# 4. Switch to another scene
curl -X POST http://localhost:8000/api/obs/scenes/Picture-in-Picture/activate

# 5. Verify stream continues without interruption
```

**✅ Success Criteria**:

- Scenes switch smoothly during live stream
- No stream interruption or buffering
- OBS Studio shows active scene correctly

---

## 📡 Test 2: Streaming to Real Destinations

### Option A: YouTube Stream Test

#### Step 2A.1: Get YouTube Stream Key

1. Go to <https://studio.youtube.com/>
2. Click **Create → Go Live**
3. Select **Streaming software**
4. Copy your **Stream key**
5. Note the **RTMP URL**: `rtmp://a.rtmp.youtube.com/live2`

#### Step 2A.2: Configure Destination via API

```bash
curl -X POST http://localhost:8000/api/streaming/destinations \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-001",
    "destinations": [
      {
        "platform": "youtube",
        "stream_key": "YOUR_YOUTUBE_STREAM_KEY",
        "label": "YouTube Test"
      }
    ]
  }'
```

#### Step 2A.3: Start Streaming

```bash
# Start the stream
curl -X POST http://localhost:8000/api/streaming/start \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-001",
    "start_recording": false
  }'
```

#### Step 2A.4: Verify Playback

1. Go to YouTube Studio → **Go Live**
2. You should see your stream preview
3. Stream should appear in "Live" dashboard
4. Play preview to confirm video/audio quality

#### Step 2A.5: Monitor Health

```bash
# Check streaming health
curl http://localhost:8000/api/streaming/health?session_id=test-session-001

# Expected response:
# {
#   "session_id": "test-session-001",
#   "overall_status": "healthy",
#   "is_streaming": true,
#   "destinations": [
#     {
#       "destination_id": "youtube_001",
#       "platform": "youtube",
#       "status": "streaming",
#       "bitrate_kbps": 2500,
#       "fps": 30,
#       "dropped_frames": 0
#     }
#   ]
# }
```

### Option B: Twitch Stream Test

#### Step 2B.1: Get Twitch Stream Key

1. Go to <https://dashboard.twitch.tv/settings/stream>
2. Copy your **Primary Stream key**
3. Note the **RTMP URL**: `rtmp://live.twitch.tv/app`

#### Step 2B.2: Configure and Stream

```bash
# Configure Twitch destination
curl -X POST http://localhost:8000/api/streaming/destinations \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-002",
    "destinations": [
      {
        "platform": "twitch",
        "stream_key": "YOUR_TWITCH_STREAM_KEY",
        "label": "Twitch Test"
      }
    ]
  }'

# Start streaming
curl -X POST http://localhost:8000/api/streaming/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-002"}'
```

### Option C: Local RTMP Test Server

#### Step 2C.1: Set Up Local RTMP Server (Docker)

```bash
# Run nginx-rtmp server
docker run -d -p 1935:1935 --name rtmp-server tiangolo/nginx-rtmp

# Verify running
docker ps | grep rtmp-server
```

#### Step 2C.2: Configure Custom RTMP Destination

```bash
curl -X POST http://localhost:8000/api/streaming/destinations \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-003",
    "destinations": [
      {
        "platform": "custom_rtmp",
        "stream_key": "test123",
        "stream_url": "rtmp://localhost:1935/live",
        "label": "Local Test"
      }
    ]
  }'
```

#### Step 2C.3: Test Playback with VLC

1. Open VLC Media Player
2. Go to **Media → Open Network Stream**
3. Enter: `rtmp://localhost:1935/live/test123`
4. Click **Play**

**✅ Success Criteria**:

- Stream starts successfully
- Video/audio playback works
- No significant frame drops (<1%)
- Bitrate stable around configured value
- Stream runs for at least 5-10 minutes without issues

---

## 🎭 Test 3: Full Production Workflow

This test validates the complete end-to-end workflow.

### Step 3.1: Environment Setup

```bash
# 1. Ensure OBS Studio is running with scenes configured
# 2. Ensure Miktos Hub server is running
# 3. Have streaming destination credentials ready
```

### Step 3.2: Execute Complete Workflow

#### A. Start Server and Verify Health

```bash
# Check server health
curl http://localhost:8000/api/health

# Expected: overall_status = "healthy"
```

#### B. Discover Cameras

```bash
# Start camera discovery
curl -X POST http://localhost:8000/api/cameras/discovery/start \
  -H "Content-Type: application/json" \
  -d '{"timeout_seconds": 30}'

# Wait for discovery
sleep 10

# List discovered cameras
curl http://localhost:8000/api/cameras/

# Note camera IDs for next steps
```

#### C. Create Session

```bash
# Create streaming session
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Test Stream",
    "description": "Full E2E validation test"
  }'

# Note the session_id from response
```

#### D. Configure OBS Scenes

```bash
# Create scene in Miktos Hub session
curl -X POST http://localhost:8000/api/scenes \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "name": "Main Scene",
    "layout": "single_full",
    "camera_ids": ["camera_001"]
  }'

# Create second scene
curl -X POST http://localhost:8000/api/scenes \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "name": "PiP Scene",
    "layout": "picture_in_picture",
    "camera_ids": ["camera_001", "camera_002"]
  }'
```

#### E. Configure Streaming Destination

```bash
# Configure YouTube/Twitch destination
curl -X POST http://localhost:8000/api/streaming/destinations \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "destinations": [
      {
        "platform": "youtube",
        "stream_key": "YOUR_STREAM_KEY",
        "label": "Production Test"
      }
    ]
  }'
```

#### F. Start Session and Streaming

```bash
# Start the session (begins streaming)
curl -X POST http://localhost:8000/api/sessions/YOUR_SESSION_ID/start \
  -H "Content-Type: application/json" \
  -d '{
    "start_streaming": true,
    "start_recording": false
  }'
```

#### G. Switch Scenes During Stream

```bash
# Wait for stream to stabilize
sleep 10

# Switch to PiP scene via Miktos Hub API
curl -X POST http://localhost:8000/api/scenes/switch \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "scene_id": "pip_scene_id",
    "transition": "fade",
    "transition_duration_ms": 500
  }'

# Wait and switch back
sleep 15

curl -X POST http://localhost:8000/api/scenes/switch \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "scene_id": "main_scene_id",
    "transition": "fade"
  }'
```

#### H. Monitor Streaming Health

```bash
# Check health every 30 seconds
while true; do
  curl http://localhost:8000/api/streaming/health?session_id=YOUR_SESSION_ID
  echo "\n---"
  sleep 30
done
```

#### I. Stop Streaming and Session

```bash
# Stop streaming
curl -X POST http://localhost:8000/api/streaming/stop \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID"}'

# Stop/end session
curl -X POST http://localhost:8000/api/sessions/YOUR_SESSION_ID/stop
```

### Step 3.3: Validation Checklist

**✅ Critical Success Criteria**:

- [ ] Server starts without errors
- [ ] Camera discovery finds cameras
- [ ] Session created successfully
- [ ] Scenes created in Miktos Hub
- [ ] Streaming destination configured
- [ ] Stream starts successfully
- [ ] Stream playback works on platform
- [ ] Scene switching works via API
- [ ] OBS scenes update correctly
- [ ] Stream continues during scene switches
- [ ] Health monitoring shows accurate metrics
- [ ] Stream runs for 10+ minutes without crash
- [ ] Stop commands work gracefully
- [ ] No memory leaks observed

---

## 📝 Issue Tracking

### Issues Found During Testing

| #   | Issue                            | Severity | Status | Notes                              |
| --- | -------------------------------- | -------- | ------ | ---------------------------------- |
| 1   | _Example: Scene switch lag 2s_   | Medium   | Open   | _Optimize OBS websocket commands_  |
| 2   | _Example: Stream key validation_ | Low      | Open   | _Add validation before API accept_ |

### Missing Features Identified

- [ ] Stream preview thumbnails
- [ ] Automatic bitrate adjustment
- [ ] Stream recording to local disk
- [ ] Multi-destination failover testing
- [ ] Network interruption recovery

---

## 🎯 Next Steps After Validation

1. **Fix Critical Issues**: Address any blocking bugs found
2. **Document Workarounds**: For non-blocking issues
3. **Update E2E_TEST_GUIDE.md**: Add real-world findings
4. **Performance Optimization**: Move to performance testing phase
5. **Documentation**: Create deployment and troubleshooting guides

---

## 📞 Support

If you encounter issues:

1. Check server logs: `tail -f miktos_hub.log`
2. Check OBS logs: OBS → Help → Log Files
3. Verify network connectivity: `ping youtube.com` / `ping twitch.tv`
4. Test RTMP manually in OBS first before using API

---

**Last Updated**: November 26, 2025
**Next Review**: After first E2E test completion
