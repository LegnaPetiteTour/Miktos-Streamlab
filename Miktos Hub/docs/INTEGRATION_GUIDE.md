# Miktos Hub ↔ Backend Integration Guide

**Date**: November 27, 2025  
**Purpose**: Complete guide to integrating Hub with existing Backend modules

## 📋 Current Architecture

### Directory Structure

```text
/Users/atorrella/Desktop/Miktos Streamlab/
├── Desktop/Backend/           # Existing production backend
│   ├── core/                  # Core modules (385 passing tests)
│   │   ├── transcription.py
│   │   ├── quality_analyzer.py
│   │   ├── enhancement_engine.py
│   │   ├── network.py
│   │   ├── iso_recording.py
│   │   ├── egress_v2.py
│   │   └── ...
│   ├── api/
│   ├── requirements.txt       # Backend dependencies
│   └── ...
│
└── Miktos Hub/                # New Hub architecture
    ├── services/              # Wrappers for Backend modules
    ├── modules/               # Feature modules
    ├── core/                  # Hub core (DeviceRegistry, etc)
    ├── hub_api/               # Hub REST API
    ├── requirements-test.txt  # Test dependencies only
    └── ...
```

### Integration Pattern

Hub services **wrap** Backend modules using this pattern:

```python
# Example: services/transcription_service.py
import sys
from pathlib import Path

# Add Backend to Python path
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

try:
    from core.transcription import TranscriptionEngine
    TRANSCRIPTION_AVAILABLE = True
except ImportError as e:
    TranscriptionEngine = None
    TRANSCRIPTION_AVAILABLE = False
    logging.warning(f"Transcription module not available: {e}")

class TranscriptionService:
    """Wraps Backend TranscriptionEngine with Hub-friendly API"""
    def __init__(self):
        if not TRANSCRIPTION_AVAILABLE:
            raise RuntimeError("Backend transcription not available")
        self.engine = TranscriptionEngine()
```

### Graceful Degradation

When Backend modules aren't available:

- ✅ Hub core functions work (DeviceRegistry, SessionManager, EventBus)
- ✅ API server starts successfully
- ✅ OBS integration works
- ⚠️ Advanced features disabled (transcription, quality analysis, enhancement)
- 📊 Warnings logged but no crashes

## 🔧 Integration Options

### Option A: Shared Backend (Recommended for Development)

Install Backend dependencies in Hub virtualenv:

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub"
source venv/bin/activate

# Install Backend dependencies
pip install -r ../Desktop/Backend/requirements.txt

# Test Backend imports
python -c "
import sys
sys.path.insert(0, '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend')
from core.transcription import TranscriptionEngine
from core.quality_analyzer import QualityAnalyzer
print('✓ Backend modules importable')
"
```

**Pros**:

- Single virtualenv to manage
- Easy development workflow
- Full feature access

**Cons**:

- Larger virtualenv (more dependencies)
- Backend changes might affect Hub

### Option B: Separate Backend Installation (Production)

Run Backend as separate service:

```bash
# Terminal 1: Start Backend API
cd "/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend"
source venv/bin/activate
uvicorn api.server:app --port 8001

# Terminal 2: Start Hub API
cd "/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub"
source venv/bin/activate
uvicorn hub_api.server:create_app --factory --port 8000
```

Hub services call Backend via HTTP:

```python
# services/transcription_service.py (HTTP version)
import httpx

class TranscriptionService:
    def __init__(self, backend_url="http://localhost:8001"):
        self.backend_url = backend_url
        self.client = httpx.AsyncClient()
    
    async def transcribe_file(self, path, languages):
        response = await self.client.post(
            f"{self.backend_url}/transcription/transcribe",
            json={"path": path, "languages": languages}
        )
        return response.json()
```

**Pros**:

- Clean separation
- Services can scale independently
- Backend can be deployed separately

**Cons**:

- More complex setup
- Network latency for local calls
- Need to manage two processes

### Option C: Monorepo with Shared Dependencies

Create unified requirements.txt:

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub"

# Create requirements.txt
cat > requirements.txt << 'EOF'
# Miktos Hub + Backend Dependencies

# ============================================================================
# Core Hub Dependencies
# ============================================================================
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
websockets>=12.0
python-multipart>=0.0.6

# ============================================================================
# Backend Integration Dependencies
# ============================================================================
obs-websocket-py==1.0
python-dotenv==1.0.0
cryptography>=41.0.0
speedtest-cli==2.1.3
psutil>=5.9.0
ffmpeg-python>=0.2.0
pysrt>=1.1.2

# ============================================================================
# Optional: AI Features (only if using transcription/enhancement)
# ============================================================================
# openai-whisper>=20231117  # Uncomment for transcription
# torch>=2.0.0  # Uncomment for GPU acceleration
# numpy>=1.24.0  # Uncomment for image processing

# ============================================================================
# Development/Testing
# ============================================================================
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0
EOF

# Install
pip install -r requirements.txt
```

**Pros**:

- Unified dependency management
- Simple deployment
- Clear dependency list

**Cons**:

- Larger install size
- Might install unused dependencies

## 🎯 Recommended Setup (Quick Start)

### Step 1: Install Backend Dependencies

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub"
source venv/bin/activate

# Install core Backend dependencies (without AI features)
pip install \
    obs-websocket-py==1.0 \
    python-dotenv==1.0.0 \
    cryptography>=41.0.0 \
    speedtest-cli==2.1.3 \
    psutil>=5.9.0 \
    ffmpeg-python>=0.2.0 \
    pysrt>=1.1.2
```

### Step 2: Verify Backend Integration

```bash
# Test Backend imports
python test_server_imports.py

# Expected output:
# ✓ Config loaded
# ✓ Core services imported
# WARNING: Transcription module not available (expected if Whisper not installed)
# WARNING: Quality analyzer module not available (expected if numpy not installed)
# ✓ API server module imported
# ✓ App created
```

### Step 3: Start Hub Server

```bash
# Start server
uvicorn hub_api.server:create_app --factory --host 127.0.0.1 --port 8000 --reload

# Test endpoints
curl http://localhost:8000/api/health/ping
# {"success": true, "message": "pong"}

curl http://localhost:8000/api/health/ready
# {"ready": true, "version": "0.1.0", ...}
```

### Step 4: (Optional) Install AI Features

Only if you need transcription/enhancement:

```bash
# Install AI dependencies (large download ~2GB)
pip install openai-whisper torch numpy opencv-python
```

## 🔍 Service Integration Status

### TranscriptionService

**Backend Module**: `core/transcription.py`  
**Dependencies**: `openai-whisper`, `torch`  
**Status**: ⚠️ Optional (requires large AI models)

```python
from services import TranscriptionService

service = TranscriptionService()
if service.is_available():
    transcript = await service.transcribe_file("video.mp4", ["en", "fr"])
else:
    print("Transcription not available (Whisper not installed)")
```

### QualityService

**Backend Module**: `core/quality_analyzer.py`  
**Dependencies**: `numpy`, `opencv-python`  
**Status**: ⚠️ Optional (requires image processing libs)

```python
from services import QualityService

service = QualityService()
if service.is_available():
    analysis = await service.analyze_frame(frame_data)
else:
    print("Quality analysis not available (numpy not installed)")
```

### EnhancementService

**Backend Module**: `core/enhancement_engine.py`  
**Dependencies**: `numpy`, `opencv-python`  
**Status**: ⚠️ Optional

### NetworkService

**Backend Module**: `core/network.py`  
**Dependencies**: `speedtest-cli`, `psutil` ✅ Recommended to install  
**Status**: ✅ Ready (lightweight dependencies)

```python
from services import NetworkService

service = NetworkService()
bandwidth = await service.test_bandwidth(target_kbps=6000)
print(f"Sufficient: {bandwidth.is_sufficient}")
```

### RecordingService

**Backend Module**: `core/iso_recording.py`  
**Dependencies**: `ffmpeg-python` ✅ Recommended to install  
**Status**: ✅ Ready

### ExportService

**Backend Module**: Backend export utilities  
**Dependencies**: `ffmpeg-python`  
**Status**: ✅ Ready

## 🐛 Troubleshooting

### "No module named 'cryptography'"

```bash
pip install cryptography>=41.0.0
```

### "No module named 'core.transcription'"

This is expected. Transcription requires Whisper (~2GB download):

```bash
pip install openai-whisper torch
```

Or ignore if you don't need transcription features.

### "WARNING: Transcription module not available"

Normal behavior when Whisper not installed. Hub will work without it.

### Import Path Issues

Services already add Backend to `sys.path`:

```python
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
sys.path.insert(0, BACKEND_PATH)
```

Verify Backend location:

```bash
ls -la "/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend/core/"
# Should see: transcription.py, quality_analyzer.py, etc.
```

### Backend Modules Not Loading

Check Python path:

```python
import sys
print(sys.path)
# Should include: '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
```

## 📊 Testing Integration

### Unit Tests (Mock Backend)

```bash
# Run Hub tests with mocked Backend
pytest tests/ -v

# Tests use mock services (no Backend required)
# See tests/conftest.py for mock fixtures
```

### Integration Tests (Real Backend)

```bash
# Install Backend dependencies first
pip install cryptography speedtest-cli psutil ffmpeg-python

# Run integration tests
pytest tests/test_integration.py -v

# These tests call real Backend modules
```

### End-to-End Tests (Full Stack)

```bash
# Start OBS Studio with WebSocket enabled
# Start Hub server
uvicorn hub_api.server:create_app --factory --port 8000

# Run E2E tests
./test_e2e.sh

# Tests: server health, OBS connection, scenes, cameras, sessions
```

## 🚀 Next Steps

### Immediate (This Week)

1. ✅ Install core Backend dependencies (cryptography, psutil, etc.)
2. ✅ Verify Backend modules importable
3. ✅ Run Hub tests (should all pass with mocks)
4. ✅ Test OBS integration (requires OBS running)

### Short-term (Next 2 Weeks)

1. Create integration tests for each service
2. Decide on deployment strategy (Option A/B/C)
3. Document production deployment steps
4. Add health checks for Backend availability

### Long-term (Month 2+)

1. Consider microservices architecture
2. Add service discovery
3. Containerize with Docker
4. Create Kubernetes deployment configs

## 📞 Quick Reference

### Backend Path

```python
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
```

### Hub API Port

```text
http://localhost:8000
```

### Backend API Port (if running separately)

```text
http://localhost:8001
```

### Test Commands

```bash
# Test Hub imports
python test_server_imports.py

# Run Hub tests
pytest tests/ -v

# Start Hub server
uvicorn hub_api.server:create_app --factory --port 8000 --reload

# Test E2E
./test_e2e.sh
```

### Key Files

```text
services/transcription_service.py  # Transcription wrapper
services/quality_service.py        # Quality analysis wrapper
services/enhancement_service.py    # Enhancement wrapper
services/network_service.py        # Network monitoring wrapper
services/recording_service.py      # Recording wrapper
services/export_service.py         # Export wrapper

tests/conftest.py                  # Mock fixtures for testing
tests/test_integration.py          # Integration tests
test_server_imports.py             # Import verification script
test_e2e.sh                        # End-to-end test script
```

---

**Status**: Integration pattern established, graceful degradation working.  
**Next**: Install core Backend dependencies and verify service integration.
