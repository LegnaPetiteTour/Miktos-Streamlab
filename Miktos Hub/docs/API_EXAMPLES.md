# API Request/Response Examples

Quick reference guide for common Miktos Hub API flows.

## Sessions

### Create a new session

**POST** `/api/sessions/`

Request:

```json
{
  "name": "Sunday Morning Show",
  "description": "Test stream for camera integration"
}
```

Response (200):

```json
{
  "session_id": "sess_012345",
  "name": "Sunday Morning Show",
  "state": "preparing",
  "created_at": "2025-11-26T12:00:00Z"
}
```

### List all sessions

**GET** `/api/sessions/`

Response (200):

```json
{
  "sessions": [
    {
      "id": "sess_012345",
      "name": "Sunday Morning Show",
      "description": "Test stream for camera integration",
      "state": "preparing",
      "created_at": "2025-11-26T12:00:00Z",
      "started_at": null,
      "ended_at": null,
      "camera_ids": [],
      "scene_ids": [],
      "destination_ids": []
    }
  ],
  "total": 1
}
```

### Start a session

**POST** `/api/sessions/{session_id}/start`

Request:

```json
{
  "start_streaming": true,
  "start_recording": false
}
```

Response (200):

```json
{
  "session_id": "sess_012345",
  "state": "live",
  "streaming_started": true,
  "recording_started": false,
  "message": "Streaming started to 1 destinations"
}
```

### Stop a session

**POST** `/api/sessions/{session_id}/stop`

Response (200):

```json
{
  "success": true,
  "message": "Session stopped successfully"
}
```

## Cameras

### List all cameras

**GET** `/api/cameras/`

Response (200):

```json
{
  "cameras": [
    {
      "camera_id": "cam_abcd1234",
      "label": "Sony a7 IV",
      "status": "discovered",
      "transport": "imaging_edge",
      "connection_url": "http://192.168.1.100:8080",
      "capabilities": ["video_stream", "remote_control"],
      "is_connected": false,
      "battery_percent": null,
      "temperature_celsius": null,
      "network_quality": null,
      "metadata": {}
    }
  ],
  "total": 1,
  "discovered_count": 1,
  "registered_count": 0
}
```

### Register a camera

**POST** `/api/cameras/register`

Request:

```json
{
  "camera_id": "cam_abcd1234"
}
```

Response (200):

```json
{
  "camera_id": "cam_abcd1234",
  "registered": true,
  "message": "Camera registered successfully"
}
```

### Get camera health

**GET** `/api/cameras/{camera_id}/health`

Response (200):

```json
{
  "camera_id": "cam_abcd1234",
  "overall_status": "healthy",
  "is_connected": true,
  "battery_percent": 85,
  "temperature_celsius": 42.5,
  "network_quality": "excellent",
  "last_seen": "2025-11-26T12:05:00Z",
  "uptime_seconds": 3600.5
}
```

## Streaming

### Configure streaming destinations

**POST** `/api/streaming/destinations`

Request:

```json
{
  "session_id": "sess_012345",
  "destinations": [
    {
      "platform": "youtube",
      "stream_key": "abcd-efgh-ijkl",
      "stream_url": null,
      "label": "YouTube - Test",
      "enabled": true
    },
    {
      "platform": "twitch",
      "stream_key": "live_xyz_987654",
      "stream_url": null,
      "label": "Twitch Backup",
      "enabled": true
    }
  ]
}
```

Response (200):

```json
{
  "success": true,
  "message": "Configured 2 streaming destinations",
  "data": {
    "session_id": "sess_012345",
    "destination_count": 2
  }
}
```

### Start streaming

**POST** `/api/streaming/start`

Request:

```json
{
  "session_id": "sess_012345",
  "start_recording": false
}
```

Response (200):

```json
{
  "success": true,
  "message": "Streaming started for session sess_012345",
  "data": {
    "session_id": "sess_012345",
    "recording": false
  }
}
```

### Stop streaming

**POST** `/api/streaming/stop`

Request:

```json
{
  "session_id": "sess_012345",
  "stop_recording": true
}
```

Response (200):

```json
{
  "success": true,
  "message": "Streaming stopped for session sess_012345",
  "data": {
    "session_id": "sess_012345"
  }
}
```

### Get streaming health

**GET** `/api/streaming/health?session_id=sess_012345`

Response (200):

```json
{
  "session_id": "sess_012345",
  "overall_status": "healthy",
  "is_streaming": true,
  "destinations": [
    {
      "destination_id": "sess_012345_youtube_0",
      "platform": "youtube",
      "label": "YouTube - Test",
      "status": "healthy",
      "bitrate_kbps": 6500.0,
      "fps": 59.94,
      "dropped_frames": 12,
      "total_frames": 108000,
      "uptime_seconds": 1800.0,
      "last_error": null,
      "using_backup": false
    }
  ],
  "total_destinations": 1,
  "healthy_destinations": 1,
  "degraded_destinations": 0,
  "failed_destinations": 0,
  "avg_bitrate_kbps": 6500.0,
  "avg_fps": 59.94,
  "total_dropped_frames": 12,
  "uptime_seconds": 1800.0
}
```

## Health & Status

### System health

**GET** `/api/health`

Response (200):

```json
{
  "status": "healthy",
  "obs_connected": true,
  "cameras_registered": 1,
  "cameras_healthy": 1,
  "active_sessions": 1,
  "streaming_sessions": 1,
  "cpu_percent": 35.2,
  "memory_percent": 42.8,
  "disk_usage_percent": 65.0,
  "network_quality": "excellent",
  "timestamp": "2025-11-26T12:10:00Z"
}
```

## Error Responses

All endpoints may return error responses in the following format:

### 404 Not Found

```json
{
  "detail": "Session not found"
}
```

### 422 Validation Error

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

### 500 Internal Server Error

```json
{
  "error": "InternalServerError",
  "message": "Failed to start session",
  "timestamp": "2025-11-26T12:15:00Z"
}
```

## Common Workflows

### Complete live streaming workflow

1. **Create a session**

   ```bash
   POST /api/sessions/
   {"name": "Sunday Morning Show", "description": "Test stream"}
   ```

2. **List discovered cameras**

   ```bash
   GET /api/cameras/
   ```

3. **Register a camera**

   ```bash
   POST /api/cameras/register
   {"camera_id": "cam_abcd1234"}
   ```

4. **Configure streaming destinations**

   ```bash
   POST /api/streaming/destinations
   {
     "session_id": "sess_012345",
     "destinations": [{"platform": "youtube", "stream_key": "...", "label": "YouTube - Test", "enabled": true}]
   }
   ```

5. **Start the session**

   ```bash
   POST /api/sessions/sess_012345/start
   {"start_streaming": true, "start_recording": false}
   ```

6. **Monitor health**

   ```bash
   GET /api/streaming/health?session_id=sess_012345
   ```

7. **Stop the session**

   ```bash
   POST /api/sessions/sess_012345/stop
   ```

## Using the Swagger UI

Interactive API documentation is available at <http://127.0.0.1:8000/docs> when the server is running.

- Click **Try it out** on any endpoint
- Fill in the request body using examples above
- Click **Execute** to send the request
- View the response inline
