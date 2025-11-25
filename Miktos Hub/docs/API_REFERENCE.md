# API Reference

Complete API documentation for Miktos Hub.

**Base URL:** `http://localhost:8000`

**Interactive Docs:** `/docs` (Swagger UI) | `/redoc` (ReDoc)

---

## Authentication

Currently, no authentication is required. Future versions will support:

- API Keys
- OAuth 2.0
- JWT tokens

---

## Sessions

Manage streaming sessions.

### Create Session

```http
POST /api/sessions/

```

**Request Body:**

```json
{
  "name": "My Stream",
  "description": "Optional description"
}

```

**Response:** `201 Created`

```json
{
  "session_id": "uuid",
  "name": "My Stream",
  "state": "preparing",
  "created_at": "2025-11-24T12:00:00Z"
}

```

### List Sessions

```http
GET /api/sessions/

```

**Response:** `200 OK`

```json
[
  {
    "id": "uuid",
    "name": "My Stream",
    "state": "preparing",
    "created_at": "2025-11-24T12:00:00Z"
  }
]

```

### Get Session

```http
GET /api/sessions/{session_id}

```

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "name": "My Stream",
  "description": "...",
  "state": "active",
  "created_at": "2025-11-24T12:00:00Z",
  "cameras": [],
  "scenes": []
}

```

### Delete Session

```http
DELETE /api/sessions/{session_id}

```

**Response:** `204 No Content`

---

## Cameras

Manage camera devices.

### List Cameras

```http
GET /api/cameras/

```

**Response:** `200 OK`

```json
[
  {
    "id": "camera-1",
    "name": "iPhone 13 Pro",
    "status": "connected",
    "stream_url": "rtmp://...",
    "resolution": "1920x1080",
    "fps": 30
  }
]

```

### Register Camera

```http
POST /api/cameras/register

```

**Request Body:**

```json
{
  "device_id": "camera-1",
  "name": "iPhone 13 Pro",
  "stream_url": "rtmp://192.168.1.100:1935/live"
}

```

**Response:** `201 Created`

### Get Camera

```http
GET /api/cameras/{camera_id}

```

**Response:** `200 OK`

### Remove Camera

```http
DELETE /api/cameras/{camera_id}

```

**Response:** `204 No Content`

---

## Scenes

Manage OBS scenes (session-based).

### List Scenes

```http
GET /api/scenes/?session_id={session_id}

```

**Response:** `200 OK`

```json
[
  {
    "id": "scene-1",
    "name": "Main Camera",
    "layout": "fullscreen",
    "cameras": ["camera-1"],
    "is_active": true
  }
]

```

### Switch Scene

```http
POST /api/scenes/switch

```

**Request Body:**

```json
{
  "session_id": "uuid",
  "scene_id": "scene-1"
}

```

**Response:** `200 OK`

---

## OBS Control

Direct OBS Studio control (independent of sessions).

### Get OBS Status

```http
GET /api/obs/status

```

**Response:** `200 OK`

```json
{
  "connected": true,
  "version": "32.0.2",
  "websocket_version": "5.x",
  "recording": false,
  "streaming": false,
  "current_scene": "Scene 1"
}

```

### List OBS Scenes

```http
GET /api/obs/scenes

```

**Response:** `200 OK`

```json
{
  "scenes": [
    {
      "name": "Scene 1",
      "is_active": true,
      "index": 0
    },
    {
      "name": "Scene 2",
      "is_active": false,
      "index": 1
    }
  ],
  "total": 2,
  "current_scene": "Scene 1"
}

```

### Activate Scene (Path Parameter)

```http
POST /api/obs/scenes/{scene_name}/activate

```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Switched to scene: Scene 1",
  "scene_name": "Scene 1"
}

```

### Activate Scene (Request Body)

```http
POST /api/obs/scenes/switch

```

**Request Body:**

```json
{
  "scene_name": "Scene 1"
}

```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Switched to scene: Scene 1",
  "scene_name": "Scene 1"
}

```

---

## Streaming

Control streaming to destinations.

### Start Streaming

```http
POST /api/streaming/start

```

**Request Body:**

```json
{
  "session_id": "uuid",
  "destinations": ["youtube", "twitch"]
}

```

**Response:** `200 OK`

### Stop Streaming

```http
POST /api/streaming/stop

```

**Request Body:**

```json
{
  "session_id": "uuid"
}

```

**Response:** `200 OK`

### Get Streaming Status

```http
GET /api/streaming/status?session_id={session_id}

```

**Response:** `200 OK`

```json
{
  "is_streaming": true,
  "destinations": [
    {
      "platform": "youtube",
      "status": "active",
      "viewers": 42
    }
  ],
  "duration": "00:15:30"
}

```

---

## Health

System health checks.

### Health Check

```http
GET /api/health

```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "obs": {
    "connected": true,
    "version": "32.0.2"
  },
  "database": {
    "connected": true,
    "sessions": 5
  },
  "cameras": {
    "discovered": 2,
    "connected": 1
  }
}

```

---

## WebSocket

Real-time event streaming.

### Connect

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};

```

### Events

**Camera Discovered:**

```json
{
  "event": "camera.discovered",
  "data": {
    "camera_id": "camera-1",
    "name": "iPhone 13"
  }
}

```

**Camera Connected:**

```json
{
  "event": "camera.connected",
  "data": {
    "camera_id": "camera-1"
  }
}

```

**Scene Switched:**

```json
{
  "event": "scene.switched",
  "data": {
    "session_id": "uuid",
    "scene_id": "scene-1",
    "scene_name": "Main Camera"
  }
}

```

**Streaming Started:**

```json
{
  "event": "streaming.started",
  "data": {
    "session_id": "uuid",
    "destinations": ["youtube"]
  }
}

```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message"
}

```

### Common Status Codes

| Code | Meaning | Example |

|------|---------|---------|
| `200` | Success | Request completed |

| `201` | Created | Resource created |
| `204` | No Content | Resource deleted |

| `400` | Bad Request | Invalid input |
| `404` | Not Found | Resource doesn't exist |

| `422` | Validation Error | Invalid data format |
| `500` | Server Error | Internal error |

| `503` | Service Unavailable | OBS not connected |

### Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

```

---

## Rate Limiting

**Current:** No rate limiting

**Future:**

- 100 requests/hour for unauthenticated
- 1000 requests/hour for authenticated

---

## Examples

### Complete Workflow

```bash

# 1. Create session
SESSION=$(curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"name": "My Stream"}' | jq -r '.session_id')

# 2. Check cameras
curl http://localhost:8000/api/cameras/

# 3. Check OBS
curl http://localhost:8000/api/obs/status

# 4. List scenes
curl "http://localhost:8000/api/scenes/?session_id=$SESSION"

# 5. Start streaming
curl -X POST http://localhost:8000/api/streaming/start \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION\", \"destinations\": [\"youtube\"]}"

# 6. Stop streaming
curl -X POST http://localhost:8000/api/streaming/stop \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION\"}"

# 7. Delete session
curl -X DELETE "http://localhost:8000/api/sessions/$SESSION"

```

### Python Client

```python
import requests

base_url = "http://localhost:8000"

# Create session
response = requests.post(
    f"{base_url}/api/sessions/",
    json={"name": "My Stream"}
)
session_id = response.json()["session_id"]

# Get OBS status
obs_status = requests.get(f"{base_url}/api/obs/status").json()
print(f"OBS Connected: {obs_status['connected']}")

# Switch scene
requests.post(
    f"{base_url}/api/obs/scenes/switch",
    json={"scene_name": "Main Camera"}
)

# Clean up
requests.delete(f"{base_url}/api/sessions/{session_id}")

```

### JavaScript Client

```javascript
const baseURL = 'http://localhost:8000';

// Create session
const createSession = async () => {
  const response = await fetch(`${baseURL}/api/sessions/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'My Stream' })
  });
  return await response.json();
};

// Get OBS status
const getOBSStatus = async () => {
  const response = await fetch(`${baseURL}/api/obs/status`);
  return await response.json();
};

// Switch scene
const switchScene = async (sceneName) => {
  const response = await fetch(`${baseURL}/api/obs/scenes/switch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scene_name: sceneName })
  });
  return await response.json();
};

// Usage
const session = await createSession();
const status = await getOBSStatus();
await switchScene('Main Camera');

```

---

## Changelog

### v1.0.0 (2025-11-24)

- Initial release
- Session management
- Camera discovery
- OBS integration
- Basic streaming control
- WebSocket events
- Direct OBS control endpoints

---

## Support

- **Documentation:** <https://github.com/LegnaPetiteTour/Miktos-Streamlab/tree/main/docs>
- **Issues:** <https://github.com/LegnaPetiteTour/Miktos-Streamlab/issues>
- **Swagger UI:** <http://localhost:8000/docs>
- **ReDoc:** <http://localhost:8000/redoc>
