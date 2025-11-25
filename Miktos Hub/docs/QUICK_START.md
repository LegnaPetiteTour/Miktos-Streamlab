# Quick Start Guide

Get Miktos Hub running in 5 minutes!

## Prerequisites

- Python 3.11 or higher
- OBS Studio (v28+ recommended)
- OBS WebSocket plugin enabled

## Installation

### 1. Clone and Setup

```bash
git clone https://github.com/LegnaPetiteTour/Miktos-Streamlab.git
cd "Miktos Hub"
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

```

### 2. Configure OBS WebSocket

1. Open OBS Studio
2. Go to **Tools → WebSocket Server Settings**

3. Enable WebSocket server
4. Note the port (default: 4455) and password
5. Update `config/settings.py`:

```python
obs:
    host: "localhost"
    port: 4455
    password: "your-password-here"

```

### 3. Start the Server

```bash
python main.py --host 0.0.0.0 --port 8000

```

You should see:

```text
MIKTOS HUB API READY
API Docs: http://localhost:8000/docs
Health Check: http://localhost:8000/api/health

```

### 4. Verify Installation

Open your browser to:

- **Swagger UI:** <http://localhost:8000/docs>
- **Health Check:** <http://localhost:8000/api/health>

## First Session

### Create a Session via API

```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Stream",
    "description": "Testing Miktos Hub"
  }'

```

### Or Use Swagger UI

1. Go to <http://localhost:8000/docs>
2. Expand **POST /api/sessions/**

3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"

## Connect a Camera

### iPhone/Android (Coming Soon)

1. Install the Miktos Camera app
2. Connect to same WiFi as hub
3. Camera will auto-discover
4. Check: `GET /api/cameras/`

### Manual Registration

```bash
curl -X POST http://localhost:8000/api/cameras/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "my-camera-1",
    "name": "iPhone 13 Pro",
    "stream_url": "rtmp://camera-ip:1935/live"
  }'

```

## Control OBS

### Check OBS Status

```bash
curl http://localhost:8000/api/obs/status

```

### List Scenes

```bash
curl http://localhost:8000/api/obs/scenes

```

### Switch Scene

```bash
curl -X POST http://localhost:8000/api/obs/scenes/MyScene/activate

```

## Next Steps

- [Camera Pairing Guide](CAMERA_PAIRING.md) - Connect multiple cameras
- [Deployment Guide](DEPLOYMENT.md) - Run as a service
- [API Reference](API_REFERENCE.md) - Full API documentation
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

## Common Issues

### OBS Not Connecting

```bash

# Check OBS WebSocket is enabled
# Verify password in config/settings.py
# Ensure OBS is running

```

### Port Already in Use

```bash

# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python main.py --port 8001

```

### Database Errors

```bash

# Reset database (WARNING: deletes all data)
rm -rf data/miktos_hub.db
python main.py  # Will recreate

```

## Help & Support

- **Issues:** <https://github.com/LegnaPetiteTour/Miktos-Streamlab/issues>
- **Documentation:** `/docs` folder
- **API Docs:** <http://localhost:8000/docs>
