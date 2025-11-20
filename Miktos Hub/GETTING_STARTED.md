# Miktos Hub - Getting Started

## 🚀 Quick Start Guide

### Prerequisites

**Python 3.10+** required. Your existing Miktos Streamlab backend should be at:
```
/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend
```

### Installation

1. **Navigate to Hub directory**:
```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub"
```

2. **Install dependencies** (if needed):
```bash
pip install -r requirements.txt  # Create this file with your backend dependencies
```

### Basic Usage

#### Example 1: Register a Camera

```python
from core import DeviceRegistry
from models import CameraDevice, TransportType, CameraCapability

# Initialize registry
registry = DeviceRegistry()

# Create camera device
phone = CameraDevice(
    id="phone-001",
    label="Wide Shot (Phone 1)",
    transport=TransportType.SRT,
    url="srt://192.168.1.100:8888",
    capabilities=[
        CameraCapability.VIDEO,
        CameraCapability.AUDIO,
        CameraCapability.REMOTE_CONTROL,
    ]
)

# Register it
registry.register(phone)

# Verify
camera = registry.get("phone-001")
print(f"Registered: {camera.label}")
print(f"Connected: {camera.is_healthy()}")
```

#### Example 2: Create a Session

```python
from core import SessionManager, DeviceRegistry, StreamRouter
from models import SessionConfig, SessionState

# Initialize core services
registry = DeviceRegistry()
router = StreamRouter()
session_manager = SessionManager(registry, router)

# Create session
config = SessionConfig(
    name="City Council Meeting",
    camera_ids=[],
    destination_ids=[],
)

session = session_manager.create_session(config)
print(f"Created session: {session.id}")
print(f"State: {session.state}")
```

#### Example 3: Route a Camera to a Scene

```python
from core import StreamRouter
from models import CameraDevice, Scene, SceneLayout, TransportType

# Initialize router
router = StreamRouter()

# Create camera
camera = CameraDevice(
    id="phone-001",
    label="Wide Shot",
    transport=TransportType.SRT,
    url="srt://192.168.1.100:8888",
)

# Create scene
scene = Scene(
    id="scene-main",
    name="Main Scene",
    layout=SceneLayout.SINGLE_FULL,
)

# Route camera to scene
route = router.attach_camera_to_scene(camera, scene)
print(f"Created route: {route.id}")
print(f"State: {route.state}")
```

#### Example 4: Use Event Bus

```python
from core import EventBus, Event, EventPriority

# Get event bus
event_bus = EventBus()

# Subscribe to events
def on_camera_connected(event: Event):
    camera_id = event.data.get("camera_id")
    print(f"Camera connected: {camera_id}")

event_bus.subscribe("camera_connected", on_camera_connected)

# Emit event
event_bus.emit_sync(Event(
    type="camera_connected",
    data={"camera_id": "phone-001"},
    source="device_registry",
))
```

#### Example 5: Use Transcription Service

```python
from services import TranscriptionService

# Initialize service
transcription = TranscriptionService()

# Transcribe a file
transcript = await transcription.transcribe_file(
    file_path="/path/to/recording.mp4",
    languages=["en", "fr"],
    output_format="json",
)

print(f"Transcribed: {transcript['text']}")

# Export as SRT
srt_path = await transcription.export_transcript(
    transcript=transcript,
    format="srt",
    output_path="/path/to/output.srt",
)

print(f"Exported SRT: {srt_path}")
```

### Configuration

Create a `.env` file in the Hub directory:

```bash
# OBS Settings
OBS_HOST=localhost
OBS_PORT=4455
OBS_PASSWORD=your-password

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# General
HUB_LOG_LEVEL=INFO
HUB_DEBUG=false
```

Load configuration:

```python
from config import get_config

config = get_config()
print(f"OBS Host: {config.obs.host}")
print(f"API Port: {config.api.port}")
```

### Testing Your Setup

Create a test script `test_hub.py`:

```python
#!/usr/bin/env python3
"""
Test Miktos Hub Foundation
"""

import asyncio
from core import DeviceRegistry, StreamRouter, SessionManager
from models import CameraDevice, TransportType, SessionConfig


async def test_foundation():
    print("Testing Miktos Hub Foundation...")
    
    # Test 1: Device Registry
    print("\n1. Testing Device Registry...")
    registry = DeviceRegistry()
    
    phone = CameraDevice(
        id="test-phone",
        label="Test Phone",
        transport=TransportType.SRT,
        url="srt://localhost:8888",
    )
    
    registry.register(phone)
    assert registry.get("test-phone") is not None
    print("✅ Device Registry works!")
    
    # Test 2: Stream Router
    print("\n2. Testing Stream Router...")
    router = StreamRouter()
    
    from models import Scene, SceneLayout
    scene = Scene(name="Test Scene", layout=SceneLayout.SINGLE_FULL)
    
    route = router.attach_camera_to_scene(phone, scene)
    assert route is not None
    print("✅ Stream Router works!")
    
    # Test 3: Session Manager
    print("\n3. Testing Session Manager...")
    session_manager = SessionManager(registry, router)
    
    config = SessionConfig(name="Test Session")
    session = session_manager.create_session(config)
    assert session.id is not None
    print("✅ Session Manager works!")
    
    # Test 4: Event Bus
    print("\n4. Testing Event Bus...")
    from core import EventBus, Event
    
    event_bus = EventBus()
    
    received = []
    def handler(event):
        received.append(event)
    
    event_bus.subscribe("test_event", handler)
    await event_bus.emit(Event(
        type="test_event",
        data={"message": "hello"},
        source="test",
    ))
    
    assert len(received) == 1
    print("✅ Event Bus works!")
    
    print("\n🎉 All foundation tests passed!")


if __name__ == "__main__":
    asyncio.run(test_foundation())
```

Run it:

```bash
python test_hub.py
```

### Next Steps

1. **Read STATUS.md** - Understand what's complete and what's next
2. **Try examples** - Test the foundation services
3. **Continue building** - Follow the 4-week roadmap in STATUS.md

### Directory Structure

```
Miktos Hub/
├── models/           # ✅ Data structures
├── core/             # ✅ Foundation services
├── config/           # ✅ Configuration
├── services/         # 🚧 Backend wrappers (10% done)
├── modules/          # ❌ Feature modules (0% done)
├── adapters/         # 🚧 Engine adapters (40% done)
├── api/              # ❌ REST + WebSocket (0% done)
├── tests/            # ❌ Test suite (0% done)
├── README.md         # Architecture overview
├── STATUS.md         # Current progress & roadmap
└── GETTING_STARTED.md # This file
```

### Troubleshooting

**Import errors?**
- Make sure you're in the Hub directory
- Check that Python can find the modules: `python -c "from core import DeviceRegistry"`

**Backend not found?**
- Verify path in `config/settings.py`
- Should point to: `/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend`

**Can't import transcription?**
- Check that backend has `core/transcription.py`
- May need to install Whisper dependencies

### Support

Questions? Check:
1. `README.md` - Architecture overview
2. `STATUS.md` - What's built, what's next
3. Individual module docstrings
4. Example code in this guide

---

**Ready to build more?** Say: **"Continue building services"**
