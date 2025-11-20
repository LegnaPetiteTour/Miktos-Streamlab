# Miktos Hub - Architecture Foundation

## 🎯 What is Miktos Hub?

Miktos Hub is the central orchestrator for the Miktos Streamlab platform. It provides a modular, engine-agnostic foundation that coordinates:

- **Multiple Cameras** (phones, webcams, IP cameras, NDI sources)
- **Multiple Engines** (OBS, Epiphan Pearl, vMix, ATEM - via adapters)
- **Multiple Platforms** (YouTube, Facebook, Twitter, custom RTMP/SRT)
- **Processing Pipelines** (audio/video enhancement)
- **Sessions** (complete show lifecycle management)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      MIKTOS HUB                              │
│                 (The Central Orchestrator)                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  LAYER 1: Core Foundation Services (Base Plate)             │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Device     │  │   Stream     │  │   Session    │      │
│  │  Registry   │  │   Router     │  │   Manager    │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐                         │
│  │ Processing  │  │   Event      │                         │
│  │  Pipeline   │  │    Bus       │                         │
│  └─────────────┘  └──────────────┘                         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  LAYER 2: Services (Wrappers Around Existing Modules)       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Transcription │  │   Quality    │  │ Enhancement  │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Export     │  │   Network    │                        │
│  │   Service    │  │   Service    │                        │
│  └──────────────┘  └──────────────┘                        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  LAYER 3: Feature Modules (Lego Bricks)                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Multi-Camera │  │     OBS      │  │Multi-Platform│     │
│  │   Manager    │  │ Orchestrator │  │  Streaming   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  LAYER 4: Adapters (Engine Abstraction)                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     OBS      │  │   Epiphan    │  │    vMix      │     │
│  │   Adapter    │  │   Adapter    │  │   Adapter    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  LAYER 5: API (Unified Control Interface)                   │
│                                                              │
│  FastAPI Server  +  WebSocket  +  REST Endpoints            │
└──────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
Miktos Hub/
├── models/              # Data structures
│   ├── __init__.py
│   ├── camera.py        # CameraDevice, CameraHealth, etc.
│   ├── destination.py   # StreamDestination, platforms
│   ├── scene.py         # Scene composition models
│   ├── session.py       # Session lifecycle models
│   └── processing.py    # Processor models
│
├── core/                # Foundation services
│   ├── __init__.py
│   ├── device_registry.py    # Camera registration & tracking
│   ├── stream_router.py      # Routing: cameras → scenes → outputs
│   ├── session_manager.py    # Session lifecycle management
│   ├── processing_pipeline.py # Audio/video processor chains
│   ├── event_bus.py          # Pub/sub event system
│   └── interfaces.py         # Protocol definitions
│
├── services/            # Wrappers for existing backend modules
│   ├── __init__.py
│   ├── transcription_service.py   # Wraps core/transcription.py
│   ├── quality_service.py         # Wraps core/quality_analyzer.py
│   ├── enhancement_service.py     # Wraps core/enhancement_engine.py
│   ├── export_service.py          # Wraps editing/export logic
│   └── network_service.py         # Wraps core/network.py
│
├── modules/             # Feature modules
│   ├── __init__.py
│   ├── multi_camera_manager.py    # Phone discovery, control
│   ├── multi_platform_streaming.py # Wraps egress_v2.py
│   └── obs_orchestrator.py        # OBS scene automation
│
├── adapters/            # Engine adapters
│   ├── __init__.py
│   ├── obs_engine.py    # OBS WebSocket adapter
│   ├── epiphan_adapter.py (future)
│   └── vmix_adapter.py (future)
│
├── api/                 # REST + WebSocket API
│   ├── __init__.py
│   ├── server.py        # FastAPI application
│   ├── routes/
│   │   ├── sessions.py  # Session endpoints
│   │   ├── cameras.py   # Camera endpoints
│   │   ├── scenes.py    # Scene endpoints
│   │   └── health.py    # Health monitoring
│   └── websocket/
│       └── handlers.py  # WebSocket handlers
│
├── config/              # Configuration management
│   ├── __init__.py
│   └── settings.py
│
└── tests/               # Test suite
    ├── __init__.py
    ├── test_device_registry.py
    ├── test_stream_router.py
    ├── test_session_manager.py
    └── test_integration.py
```

## 🔑 Key Concepts

### 1. Device Registry
**What**: Central registry for all camera devices  
**Why**: Single source of truth for cameras  
**Example**:
```python
registry = DeviceRegistry()
registry.register(CameraDevice(
    id="phone-001",
    label="Wide Shot",
    transport=TransportType.SRT,
    url="srt://192.168.1.100:8888"
))
```

### 2. Stream Router
**What**: Routes cameras → scenes → destinations  
**Why**: Decouples inputs from composition from outputs  
**Example**:
```python
router = StreamRouter()
router.attach_camera_to_scene(camera, scene)
router.route_scene_to_output(scene, destination)
```

### 3. Session Manager
**What**: Manages complete streaming session lifecycle  
**Why**: Coordinates all components for a single show  
**Example**:
```python
manager = SessionManager(registry, router)
session = manager.create_session(SessionConfig(
    name="City Council Meeting",
    camera_ids=["phone-001", "phone-002"],
    destination_ids=["youtube-en", "youtube-fr"]
))
manager.start_session(session.id)
```

### 4. Processing Pipeline
**What**: Chains audio/video processors  
**Why**: Modular, stackable enhancement  
**Example**:
```python
pipeline = ProcessingPipeline("audio_main")
pipeline.add_processor(NoiseReductionProcessor())
pipeline.add_processor(NormalizationProcessor())
```

### 5. Event Bus
**What**: Pub/sub system for loose coupling  
**Why**: Components communicate without dependencies  
**Example**:
```python
event_bus.subscribe("camera_connected", on_camera_connected)
event_bus.emit(Event(
    type="camera_connected",
    data={"camera_id": "phone-001"},
    source="device_registry"
))
```

## 🚀 Current Status

### ✅ Completed (Foundation)
- ✅ Models (camera, destination, scene, session, processing)
- ✅ Device Registry
- ✅ Stream Router
- ✅ Session Manager
- ✅ Processing Pipeline
- ✅ Event Bus
- ✅ OBS Engine Adapter (started)

### 🚧 In Progress
- 🚧 Services Layer (wrapping existing modules)
- 🚧 Modules Layer (multi-camera manager, etc.)

### 📋 Next Steps
- [ ] Complete Service Wrappers
- [ ] Build Multi-Camera Manager
- [ ] Build Multi-Platform Streaming Module
- [ ] Build API Layer
- [ ] Write Tests
- [ ] Integration Testing

## 🔧 How to Use

### Basic Workflow

```python
# 1. Initialize core services
registry = DeviceRegistry()
router = StreamRouter()
session_manager = SessionManager(registry, router)

# 2. Register cameras
phone1 = CameraDevice(
    id="phone-001",
    label="Wide Shot",
    transport=TransportType.SRT,
    url="srt://192.168.1.100:8888"
)
registry.register(phone1)

# 3. Create session
session = session_manager.create_session(SessionConfig(
    name="My Stream",
    camera_ids=["phone-001"],
    destination_ids=["youtube-en"]
))

# 4. Setup routing
scene = Scene(name="Main", layout=SceneLayout.SINGLE_FULL)
router.attach_camera_to_scene(phone1, scene)
router.route_scene_to_output(scene, youtube_destination)

# 5. Go live
session_manager.start_session(session.id)

# 6. Monitor
health = session.health
print(f"FPS: {health.fps}, Dropped: {health.dropped_frames}")

# 7. End session
session_manager.end_session(session.id)
```

## 🎯 Design Principles

### 1. **Lego Architecture**
Components stack like Lego bricks. Foundation is built once, features snap on top.

### 2. **Engine Agnostic**
Hub doesn't care if you use OBS, Epiphan, or vMix. Adapters translate.

### 3. **Loose Coupling**
Components communicate via interfaces and events, not direct calls.

### 4. **Testability**
Every service has a Protocol interface. Easy to mock and test.

### 5. **Extensibility**
Add new cameras, engines, or platforms without modifying core code.

## 📚 Documentation

- [Models Reference](docs/models.md)
- [Core Services Reference](docs/core.md)
- [API Reference](docs/api.md)
- [Development Guide](docs/development.md)

## 🤝 Contributing

This is a personal project but follows professional standards:
- Type hints everywhere
- Comprehensive docstrings
- Unit tests for all services
- Integration tests for workflows
- Clear separation of concerns

## 📜 License

Private project for portfolio demonstration.
