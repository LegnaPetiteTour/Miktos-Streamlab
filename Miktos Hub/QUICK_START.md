# Miktos Hub - Quick Start Guide

This guide shows how to start using Miktos Hub now that validation is complete.

## Starting the Server

```bash
# Activate virtual environment
cd "/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub"
source venv/bin/activate

# Start server
python main.py --host 0.0.0.0 --port 8000

# Or start in background
python main.py --host 0.0.0.0 --port 8000 > /tmp/miktos.log 2>&1 &
```

The server will:

- Connect to OBS (must be running on localhost:4455)
- Start camera discovery (mDNS)
- Initialize all services
- Expose API on <http://localhost:8000>

## API Documentation

Interactive API docs available at:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## Key API Endpoints

### Health & Status

```bash
# System health
curl http://localhost:8000/api/health

# Check OBS connection
curl http://localhost:8000/api/health | jq '.components[] | select(.name=="OBS Engine")'
```

### Session Management

```bash
# Create a session
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"name": "My Session", "description": "Test session"}'

# List all sessions
curl http://localhost:8000/api/sessions/

# Get specific session
curl http://localhost:8000/api/sessions/{session_id}

# Delete session
curl -X DELETE http://localhost:8000/api/sessions/{session_id}
```

### Camera Discovery

```bash
# Check discovery status
curl http://localhost:8000/api/cameras/discovery/status

# List discovered cameras
curl http://localhost:8000/api/cameras/

# Manually register a camera
curl -X POST http://localhost:8000/api/cameras/register \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "phone-001",
    "name": "iPhone 13 Pro",
    "stream_url": "rtsp://192.168.1.100:8554/stream",
    "capabilities": {
      "max_resolution": "1920x1080",
      "max_fps": 60
    }
  }'
```

### OBS Scene Management

```bash
# List scenes for a session
curl "http://localhost:8000/api/scenes/?session_id={session_id}"

# Create scene for camera
curl -X POST http://localhost:8000/api/scenes/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "{session_id}",
    "camera_id": "phone-001",
    "layout": "fullscreen"
  }'

# Switch to a scene
curl -X POST http://localhost:8000/api/scenes/switch \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "{session_id}",
    "scene_id": "{scene_id}"
  }'
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::TestHealthEndpoints::test_health_endpoint
```

## Typical Workflow

### 1. Start Prerequisites

```bash
# Make sure OBS is running
# OBS should have WebSocket server enabled on port 4455
```

### 2. Start Miktos Hub

```bash
python main.py
```

### 3. Create a Session

```bash
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"name": "My Session"}' | jq -r '.session_id')

echo "Created session: $SESSION_ID"
```

### 4. Register Cameras

If using Miktos Camera app on phones:

- Cameras will auto-discover via mDNS
- Check discovery status: `curl http://localhost:8000/api/cameras/discovery/status`

Or manually register:

```bash
curl -X POST http://localhost:8000/api/cameras/register \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "phone-001",
    "name": "iPhone",
    "stream_url": "rtsp://192.168.1.100:8554/stream"
  }'
```

### 5. Create OBS Scenes

```bash
# Create scene for single camera
curl -X POST http://localhost:8000/api/scenes/ \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"camera_id\": \"phone-001\",
    \"layout\": \"fullscreen\"
  }"

# Create multi-camera scene
curl -X POST http://localhost:8000/api/scenes/multi \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"camera_ids\": [\"phone-001\", \"phone-002\"],
    \"layout\": \"split_horizontal\"
  }"
```

### 6. Start Session

```bash
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/start"
```

### 7. Switch Scenes

```bash
curl -X POST http://localhost:8000/api/scenes/switch \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"scene_id\": \"{scene_id}\"
  }"
```

### 8. Stop Session

```bash
curl -X POST "http://localhost:8000/api/sessions/$SESSION_ID/stop"
```

## WebSocket Events

Connect to WebSocket for real-time events:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event_type, data.payload);
};
```

Event types:

- `camera.discovered` - New camera found
- `camera.connected` - Camera connected
- `camera.disconnected` - Camera lost
- `session.created` - Session created
- `session.started` - Session started
- `session.stopped` - Session ended
- `scene.switched` - Scene changed
- `streaming.started` - Streaming began
- `streaming.stopped` - Streaming ended

## Troubleshooting

### Server won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Check if OBS is running and WebSocket enabled
# OBS → Tools → WebSocket Server Settings
```

### OBS connection fails

```bash
# Check OBS WebSocket settings
# Default: localhost:4455 with password

# Update config if needed
# Edit config/settings.py or set environment variables
export OBS_HOST=localhost
export OBS_PORT=4455
export OBS_PASSWORD=your_password
```

### Cameras not discovering

```bash
# Check discovery status
curl http://localhost:8000/api/cameras/discovery/status

# Make sure devices are on same network
# Check firewall isn't blocking mDNS (port 5353)

# Try manual registration as fallback
```

## Current Limitations

### Available Features

- ✅ Session management
- ✅ Camera discovery & registration
- ✅ OBS scene creation & switching
- ✅ Health monitoring
- ✅ WebSocket events

### Not Yet Implemented

- ❌ Multi-platform streaming (requires egress_v2 module)
- ❌ AI transcription (requires transcription module)
- ❌ Video enhancement (requires enhancement module)
- ❌ ISO recording (requires recording module)
- ❌ Session persistence (Option B - planned)

## Next Steps

Choose your priority:

### Option B: Make It Stick

- Implement session persistence
- Database integration
- Session recovery

### Option C: Capture the Magic

- ISO recording
- Export management
- Playback features

---

For detailed validation results, see `VALIDATION_SUMMARY.md`.

For development plans, see `DEVELOPMENT_PLAN.md`.
