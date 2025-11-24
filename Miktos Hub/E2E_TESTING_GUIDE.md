# End-to-End Testing Guide

## Objective

Validate the complete Miktos Hub workflow with real cameras, OBS scenes, and streaming platforms.

## Prerequisites Checklist

- [ ] OBS Studio 32.0+ installed and running
- [ ] OBS WebSocket server enabled (port 4455)
- [ ] At least one camera available (iPhone, webcam, RTSP camera, etc.)
- [ ] Network connectivity
- [ ] Streaming platform account (YouTube, Twitch, or test RTMP server)

## Test Scenarios

### Scenario 1: Camera Discovery & Connection

**Goal**: Verify camera discovery and registration works with real hardware

**Steps**:

1. Start Miktos Hub server
2. Check camera discovery is running
3. Connect a camera to the network
4. Verify camera appears in discovered devices
5. Test camera health monitoring

**Expected Results**:

- Camera discovered within 30 seconds
- Camera metadata captured correctly
- Health status shows "healthy"
- Stream URL accessible

**Test Commands**:

```bash
# Start server
python main.py --host 0.0.0.0 --port 8000

# Check health (in another terminal)
curl http://localhost:8000/api/health | jq

# List discovered cameras
curl http://localhost:8000/api/cameras/ | jq

# Check specific camera details
curl http://localhost:8000/api/cameras/{camera_id} | jq
```

---

### Scenario 2: Session Creation with Real Camera

**Goal**: Create a production session and add real camera sources

**Steps**:

1. Create a new session via API
2. Add discovered camera to session
3. Verify session state transitions
4. Check persistence (session survives restart)

**Test Commands**:

```bash
# Create session
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E2E Test Session",
    "description": "Testing complete workflow with real camera"
  }' | jq -r '.session_id')

echo "Created session: $SESSION_ID"

# Add camera to session (replace CAMERA_ID)
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/cameras" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "YOUR_CAMERA_ID",
    "position": 0
  }' | jq

# Get session details
curl "http://localhost:8000/api/sessions/$SESSION_ID" | jq

# Check database persistence
sqlite3 ~/Desktop/Miktos\ Streamlab/data/miktos_hub.db \
  "SELECT id, name, state, created_at FROM sessions WHERE id='$SESSION_ID';"
```

---

### Scenario 3: OBS Scene Configuration

**Goal**: Configure OBS scenes with actual camera sources

**Steps**:

1. Get current OBS scenes
2. Create a new scene for the session
3. Add camera source to OBS scene
4. Test scene switching
5. Verify scene transitions work smoothly

**Test Commands**:

```bash
# List OBS scenes
curl http://localhost:8000/api/obs/scenes | jq

# Create scene for session
curl -X POST http://localhost:8000/api/obs/scenes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E2E Test Scene",
    "session_id": "'$SESSION_ID'"
  }' | jq

# Add camera source to scene (replace with your camera details)
curl -X POST http://localhost:8000/api/obs/sources \
  -H "Content-Type: application/json" \
  -d '{
    "scene_name": "E2E Test Scene",
    "source_name": "Main Camera",
    "source_type": "ffmpeg_source",
    "settings": {
      "input": "YOUR_CAMERA_STREAM_URL",
      "is_local_file": false
    }
  }' | jq

# Switch to the scene
curl -X POST http://localhost:8000/api/obs/scenes/current \
  -H "Content-Type: application/json" \
  -d '{"scene_name": "E2E Test Scene"}' | jq

# Verify current scene
curl http://localhost:8000/api/obs/scenes/current | jq
```

---

### Scenario 4: Streaming to Real Platform

**Goal**: Configure and test streaming to YouTube/Twitch/RTMP server

**Steps**:

1. Configure streaming destination
2. Start streaming
3. Verify stream health
4. Monitor for 2-5 minutes
5. Stop streaming gracefully

**Test Commands**:

```bash
# Configure YouTube streaming destination
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/destinations" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "youtube",
    "stream_url": "rtmp://a.rtmp.youtube.com/live2",
    "stream_key": "YOUR_STREAM_KEY",
    "quality_preset": "1080p60"
  }' | jq

# Or configure Twitch
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/destinations" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "twitch",
    "stream_url": "rtmp://live.twitch.tv/app",
    "stream_key": "YOUR_STREAM_KEY",
    "quality_preset": "1080p60"
  }' | jq

# Start streaming
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/start" | jq

# Check streaming health
curl "http://localhost:8000/api/sessions/$SESSION_ID/streaming/health" | jq

# Monitor for issues (run in loop)
for i in {1..10}; do
  echo "=== Check $i ==="
  curl -s "http://localhost:8000/api/sessions/$SESSION_ID/streaming/health" | jq '.status, .bitrate, .dropped_frames'
  sleep 30
done

# Stop streaming
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/pause" | jq
```

---

### Scenario 5: Full Production Workflow

**Goal**: Complete end-to-end workflow simulation

**Steps**:

1. Start with empty system
2. Discover cameras
3. Create session
4. Add cameras
5. Configure scenes
6. Add streaming destinations
7. Start streaming
8. Switch scenes during stream
9. Monitor health
10. End session
11. Verify persistence

**Automated Test Script**: See `scripts/e2e_test.sh`

---

### Scenario 6: Session Recovery After Restart

**Goal**: Verify persistence and recovery work in real scenario

**Steps**:

1. Create active session with cameras
2. Note session ID and state
3. Stop server gracefully
4. Restart server
5. Verify session recovered
6. Verify cameras reconnected
7. Continue streaming

**Test Commands**:

```bash
# Create and start session (use commands from Scenario 4)

# Note the session ID
echo $SESSION_ID > /tmp/e2e_session_id.txt

# Stop server
pkill -SIGTERM python

# Wait for graceful shutdown
sleep 5

# Restart server
python main.py --host 0.0.0.0 --port 8000 &

# Wait for startup
sleep 10

# Check recovery logs
tail -100 /tmp/server.log | grep -i "recovered"

# Verify session still exists
SESSION_ID=$(cat /tmp/e2e_session_id.txt)
curl "http://localhost:8000/api/sessions/$SESSION_ID" | jq

# Verify can continue streaming
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/start" | jq
```

---

## Issue Tracking

### Issues Found During Testing

| Issue # | Scenario | Description | Severity | Status |
|---------|----------|-------------|----------|--------|
| E2E-001 | Camera Discovery | ... | ... | ... |
| E2E-002 | Scene Switching | ... | ... | ... |
| E2E-003 | Streaming Health | ... | ... | ... |

### Performance Metrics

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| Camera discovery time | < 30s | ... | ... |
| Scene switch latency | < 500ms | ... | ... |
| Stream startup time | < 5s | ... | ... |
| Dropped frames | < 0.1% | ... | ... |
| Session recovery time | < 10s | ... | ... |

---

## Test Environment

**Date**: _____________  
**Tester**: _____________  
**OBS Version**: _____________  
**Python Version**: _____________  
**Camera Type**: _____________  
**Network**: WiFi / Ethernet  
**Streaming Platform**: YouTube / Twitch / RTMP  

---

## Next Steps After Testing

Based on test results:

✅ **All scenarios pass**: Move to Production Readiness  
⚠️ **Minor issues found**: Document and fix before production  
❌ **Critical issues found**: Address immediately, re-test  

---

## Quick Start Commands

```bash
# Terminal 1: Start server with logging
python main.py --host 0.0.0.0 --port 8000 2>&1 | tee /tmp/e2e_test.log

# Terminal 2: Monitor health
watch -n 5 'curl -s http://localhost:8000/api/health | jq'

# Terminal 3: Run test commands
# (Use commands from scenarios above)
```

---

## Troubleshooting

**Camera not discovered**:

- Check camera is on same network
- Verify mDNS/Bonjour is working
- Check firewall settings
- Try manual camera registration

**OBS connection fails**:

- Verify OBS WebSocket enabled
- Check password in config
- Ensure port 4455 not blocked

**Streaming fails**:

- Verify stream key is correct
- Check platform RTMP URL
- Monitor OBS output for errors
- Check network bandwidth

**Session not recovered**:

- Check database file exists
- Verify permissions on data directory
- Look for persistence errors in logs
