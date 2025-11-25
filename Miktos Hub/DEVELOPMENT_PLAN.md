# Miktos Hub - 4-Week Development Plan

## 📅 TIMELINE OVERVIEW

| Week | Focus | Deliverable | Status |

|------|-------|-------------|--------|
| 1 | Services Layer | All backend wrappers complete | 🚧 10% |

| 2 | Modules Layer | Camera manager + OBS orchestrator | ❌ 0% |
| 3 | API Layer | REST + WebSocket interface | ❌ 0% |

| 4 | Integration & Testing | End-to-end workflow | ❌ 0% |

---

## 🔨 WEEK 1: SERVICES LAYER

**Goal**: Wrap all existing backend modules with clean service interfaces

### Day 1 (Monday): Quality & Enhancement Services

#### Morning: QualityService (4 hours)
**File**: `services/quality_service.py`

**Requirements**:

- Wrap `Desktop/Backend/core/quality_analyzer.py`
- Analyze video quality (exposure, focus, noise, color)
- Provide recommendations for improvement
- Support batch analysis of multiple cameras

**Implementation Checklist**:

```python
class QualityService:
    ✓ __init__() - Initialize with config
    ✓ analyze_frame(frame_data) -> QualityAnalysis
    ✓ analyze_stream(camera_id, duration=5) -> QualityReport
    ✓ get_recommendations(analysis) -> List[Recommendation]
    ✓ compare_cameras(camera_ids) -> ComparisonReport

```text

**Test**:

```python

# Test with sample frame
service = QualityService()
analysis = await service.analyze_frame(test_frame)
assert analysis.overall_score > 0
assert len(analysis.issues) >= 0

```text

#### Afternoon: EnhancementService (4 hours)
**File**: `services/enhancement_service.py`

**Requirements**:

- Wrap `Desktop/Backend/core/enhancement_engine.py`
- Apply audio/video enhancement presets
- Create custom enhancement profiles
- Real-time processing pipeline integration

**Implementation Checklist**:

```python
class EnhancementService:
    ✓ __init__() - Initialize with config
    ✓ list_presets() -> List[PresetInfo]
    ✓ apply_preset(camera_id, preset_name) -> bool
    ✓ create_profile(name, config) -> Profile
    ✓ enable_enhancement(camera_id, profile_id) -> bool
    ✓ disable_enhancement(camera_id) -> bool

```text

**Test**:

```python
service = EnhancementService()
presets = service.list_presets()
assert "broadcast" in [p.name for p in presets]

```text

---

### Day 2 (Tuesday): Network & Recording Services

#### Morning: NetworkService (4 hours)
**File**: `services/network_service.py`

**Requirements**:

- Wrap `Desktop/Backend/core/network.py`
- Pre-flight bandwidth testing
- Real-time network monitoring
- Jitter, packet loss, RTT measurement

**Implementation Checklist**:

```python
class NetworkService:
    ✓ __init__() - Initialize with config
    ✓ test_bandwidth(target_bitrate) -> BandwidthTestResult
    ✓ start_monitoring(camera_id) -> MonitoringSession
    ✓ stop_monitoring(camera_id) -> None
    ✓ get_metrics(camera_id) -> NetworkMetrics
    ✓ predict_stability(metrics) -> PredictionResult

```text

**Test**:

```python
service = NetworkService()
result = await service.test_bandwidth(6000)  # 6 Mbps
assert result.achieved_bitrate_kbps > 0
assert result.is_sufficient == True

```text

#### Afternoon: RecordingService (4 hours)
**File**: `services/recording_service.py`

**Requirements**:

- Wrap `Desktop/Backend/core/iso_recording.py`
- Start/stop session recording
- ISO recording (each camera separately)
- Recording status and file management

**Implementation Checklist**:

```python
class RecordingService:
    ✓ __init__() - Initialize with config
    ✓ start_recording(session_id, config) -> RecordingHandle
    ✓ stop_recording(recording_id) -> RecordingInfo
    ✓ start_iso_recording(camera_ids) -> List[RecordingHandle]
    ✓ get_recording_status(recording_id) -> RecordingStatus
    ✓ list_recordings(session_id) -> List[RecordingInfo]

```text

**Test**:

```python
service = RecordingService()
handle = await service.start_recording(session_id, config)
assert handle.recording_id is not None
assert handle.output_path.exists()

```text

---

### Day 3-4 (Wed-Thu): Export Service

**File**: `services/export_service.py`

**Requirements**:

- FFmpeg-based video editing
- Cut clips from recordings
- Resize to multiple aspect ratios (16:9, 9:16, 1:1, 4:5)
- Burn captions into video
- Render queue management

**Implementation Checklist**:

```python
class ExportService:
    ✓ __init__() - Initialize with FFmpeg
    ✓ cut_clip(video_path, start, end) -> str
    ✓ resize_video(video_path, aspect) -> str
    ✓ add_captions(video_path, transcript) -> str
    ✓ render(config: RenderConfig) -> RenderJob
    ✓ get_render_status(job_id) -> RenderStatus
    ✓ list_render_queue() -> List[RenderJob]

```text

**Detailed Tasks**:

**Day 3 Morning**: Core export functions (4 hours)
- FFmpeg wrapper
- cut_clip implementation
- resize_video implementation

**Day 3 Afternoon**: Caption burning (4 hours)
- Parse SRT/VTT files
- Generate FFmpeg filter
- Burn captions into video

**Day 4 Morning**: Render queue (4 hours)
- Job queue implementation
- Progress tracking
- Error handling

**Day 4 Afternoon**: Social media presets (4 hours)
- YouTube preset (16:9, 1080p)
- TikTok/Reels preset (9:16, 1080x1920)
- Instagram preset (1:1, 1080x1080)
- Instagram Story preset (9:16)

**Test**:

```python
service = ExportService()

# Test clip cutting
clip = await service.cut_clip(
    video_path="recording.mp4",
    start=60.0,  # 1 minute
    end=120.0,   # 2 minutes
)
assert Path(clip).exists()

# Test resizing
vertical = await service.resize_video(clip, "9:16")
assert Path(vertical).exists()

# Test captions
captioned = await service.add_captions(
    video_path=vertical,
    transcript="transcript.srt",
)
assert Path(captioned).exists()

```text

---

### Day 5 (Friday): Integration & Package

**Morning**: Create `services/__init__.py` (2 hours)

```python
"""
Miktos Hub Services

Wrappers around existing backend functionality.
"""

from services.transcription_service import TranscriptionService
from services.quality_service import QualityService
from services.enhancement_service import EnhancementService
from services.network_service import NetworkService
from services.recording_service import RecordingService
from services.export_service import ExportService

__all__ = [
    "TranscriptionService",
    "QualityService",
    "EnhancementService",
    "NetworkService",
    "RecordingService",
    "ExportService",
]

```text

**Afternoon**: Test all services together (6 hours)
- Integration test script
- Error handling validation
- Documentation updates
- Fix bugs

**Integration Test**:

```python
async def test_services_integration():
    # Initialize all services
    transcription = TranscriptionService()
    quality = QualityService()
    enhancement = EnhancementService()
    network = NetworkService()
    recording = RecordingService()
    export = ExportService()
    
    # Test workflow
    print("1. Testing network...")
    bandwidth = await network.test_bandwidth(6000)
    assert bandwidth.is_sufficient
    
    print("2. Starting recording...")
    rec = await recording.start_recording(session_id, config)
    
    print("3. Analyzing quality...")
    quality_report = await quality.analyze_stream(camera_id)
    
    print("4. Applying enhancement...")
    await enhancement.apply_preset(camera_id, "broadcast")
    
    print("5. Stopping recording...")
    rec_info = await recording.stop_recording(rec.recording_id)
    
    print("6. Transcribing...")
    transcript = await transcription.transcribe_file(rec_info.path)
    
    print("7. Exporting clip...")
    clip = await export.cut_clip(rec_info.path, 0, 60)
    vertical = await export.resize_video(clip, "9:16")
    
    print("✅ All services working!")

```text

**Week 1 Deliverable**: All services implemented and tested.

---

## 🎯 WEEK 2: MODULES LAYER

**Goal**: Build high-level features using core services

### Day 1-2 (Mon-Tue): MultiCameraManager

**File**: `modules/multi_camera_manager.py`

**Requirements**:

- Auto-discover phones via mDNS
- Manual camera registration via QR code
- Health monitoring for all cameras
- Remote control interface
- Battery/thermal alerts

**Implementation Checklist**:

```python
class MultiCameraManager:
    ✓ __init__(device_registry, event_bus)
    ✓ start_discovery() -> None
    ✓ stop_discovery() -> None
    ✓ register_camera_manual(camera_info) -> CameraDevice
    ✓ get_camera_health(camera_id) -> CameraHealth
    ✓ send_remote_command(camera_id, command) -> bool
    ✓ set_camera_mode(camera_id, mode) -> bool  # STUDIO, NORMAL
    ✓ get_all_cameras() -> List[CameraDevice]

```text

**Key Features**:

- mDNS service discovery (`_miktos-camera._tcp.local.`)
- WebSocket control to phone apps
- Real-time health monitoring
- Event emission for camera events

**Test**:

```python
manager = MultiCameraManager(registry, event_bus)
await manager.start_discovery()

# Wait for cameras
await asyncio.sleep(5)

cameras = manager.get_all_cameras()
assert len(cameras) > 0

# Test remote control
success = await manager.send_remote_command(
    cameras[0].id,
    {"action": "set_mode", "mode": "STUDIO"}
)
assert success

```text

---

### Day 3-4 (Wed-Thu): MultiPlatformStreaming Module

**File**: `modules/multi_platform_streaming.py`

**Requirements**:

- Wrap `Desktop/Backend/core/egress_v2.py`
- Unified streaming to multiple platforms
- YouTube EN + FR dual streaming
- Automatic failover (RTMP → SRT)
- Health monitoring per destination

**Implementation Checklist**:

```python
class MultiPlatformStreaming:
    ✓ __init__(config)
    ✓ add_destination(destination) -> None
    ✓ remove_destination(destination_id) -> None
    ✓ start_streaming(session_id) -> bool
    ✓ stop_streaming(session_id) -> bool
    ✓ get_destination_health(dest_id) -> DestinationHealth
    ✓ trigger_failover(dest_id) -> bool

```text

**Key Features**:

- Simultaneous multi-destination streaming
- Per-destination health checks
- Automatic RTMP→SRT failover
- Metrics aggregation

**Test**:

```python
streaming = MultiPlatformStreaming(config)

# Add destinations
streaming.add_destination(youtube_en)
streaming.add_destination(youtube_fr)
streaming.add_destination(facebook)

# Start streaming
success = await streaming.start_streaming(session.id)
assert success

# Check health
health = streaming.get_destination_health(youtube_en.id)
assert health.is_streaming

```text

---

### Day 5 (Friday): OBS Orchestrator

**File**: `modules/obs_orchestrator.py`

**Requirements**:

- Auto-create scenes when cameras connect
- Scene switching with transitions
- Source management (positioning, cropping)
- Filter application

**Implementation Checklist**:

```python
class OBSOrchestrator:
    ✓ __init__(obs_adapter, device_registry, stream_router)
    ✓ auto_create_scene(camera) -> Scene
    ✓ switch_scene(scene_id, transition) -> bool
    ✓ update_source_position(source_id, x, y, w, h) -> bool
    ✓ apply_filter(source_id, filter_config) -> bool
    ✓ get_current_scene() -> Scene

```text

**Key Features**:

- Automatic scene generation based on camera count
- Smart layout selection (1 cam = full, 2 = split, 3+ = grid)
- Transition effects
- Real-time source updates

**Test**:

```python
orchestrator = OBSOrchestrator(obs_adapter, registry, router)

# Register camera - should auto-create scene
registry.register(phone1)
await asyncio.sleep(1)

scenes = await obs_adapter.list_scenes()
assert len(scenes) > 0

# Test scene switching
success = await orchestrator.switch_scene(
    scenes[0].id,
    transition="fade"
)
assert success

```text

**Week 2 Deliverable**: All modules implemented and tested.

---

## 🌐 WEEK 3: API LAYER

**Goal**: HTTP + WebSocket interface for control panel

### Day 1-2 (Mon-Tue): FastAPI Server + Session Routes

**Files**:

- `api/server.py`
- `api/routes/sessions.py`

**Requirements**:

- FastAPI application setup
- CORS configuration
- Session CRUD endpoints
- Session lifecycle control

**Endpoints**:

```python
POST   /api/sessions          # Create session
GET    /api/sessions          # List sessions
GET    /api/sessions/{id}     # Get session
DELETE /api/sessions/{id}     # Delete session
POST   /api/sessions/{id}/start   # Start streaming
POST   /api/sessions/{id}/pause   # Pause streaming
POST   /api/sessions/{id}/resume  # Resume streaming
POST   /api/sessions/{id}/stop    # Stop streaming

```text

**Test**:

```bash

# Create session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Stream", "camera_ids": ["phone-001"]}'

# Start streaming
curl -X POST http://localhost:8000/api/sessions/{id}/start

```text

---

### Day 3 (Wednesday): Camera & Scene Routes

**Files**:

- `api/routes/cameras.py`
- `api/routes/scenes.py`

**Requirements**:

- Camera discovery and registration
- Camera health monitoring
- Scene creation and switching

**Endpoints**:

```python
GET    /api/cameras           # List cameras
POST   /api/cameras           # Register camera
GET    /api/cameras/{id}      # Get camera
DELETE /api/cameras/{id}      # Unregister camera
GET    /api/cameras/{id}/health   # Get camera health

POST   /api/scenes            # Create scene
GET    /api/scenes            # List scenes
POST   /api/scenes/{id}/activate  # Switch to scene

```text

---

### Day 4 (Thursday): Streaming & Health Routes

**Files**:

- `api/routes/streaming.py`
- `api/routes/health.py`

**Requirements**:

- Streaming control
- Destination management
- System health monitoring

**Endpoints**:

```python
POST   /api/streaming/destinations  # Add destination
GET    /api/streaming/status        # Get streaming status
POST   /api/streaming/failover/{id} # Trigger failover

GET    /api/health                  # System health
GET    /api/health/cameras          # All camera health
GET    /api/health/destinations     # All destination health

```text

---

### Day 5 (Friday): WebSocket Handlers

**File**: `api/websocket/handlers.py`

**Requirements**:

- Real-time health updates
- Event streaming
- Camera status updates
- Session state changes

**WebSocket Events**:

```json
// Camera health update
{
  "type": "camera_health",
  "camera_id": "phone-001",
  "data": {
    "fps": 30.0,
    "bitrate_kbps": 6000,
    "battery_level": 0.75
  }
}

// Session state change
{
  "type": "session_state",
  "session_id": "session-123",
  "state": "LIVE"
}

// Destination health
{
  "type": "destination_health",
  "destination_id": "youtube-en",
  "data": {
    "is_streaming": true,
    "fps": 30.0,
    "bitrate_kbps": 6000
  }
}

```text

**Test**:

```javascript
// JavaScript WebSocket client
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data.type, data);
};

```text

**Week 3 Deliverable**: Complete API with documentation.

---

## ✅ WEEK 4: INTEGRATION & TESTING

**Goal**: Verify everything works together

### Day 1-2 (Mon-Tue): End-to-End Integration Tests

**Test Scenarios**:

1. **Complete Streaming Workflow**:

   - Start Hub
   - Phone connects (auto-discovered)
   - OBS scene created automatically
   - Create session via API
   - Add destinations (YouTube EN/FR)
   - Start streaming
   - Monitor health for 5 minutes
   - Stop streaming

2. **Multi-Camera Switching**:

   - Connect 3 phones
   - Auto-create scenes
   - Switch between scenes via API
   - Verify transitions work

3. **Quality & Enhancement**:

   - Analyze camera quality
   - Apply enhancement preset
   - Verify improvement in metrics

4. **Transcription & Export**:

   - Record session
   - Transcribe recording
   - Cut clip
   - Resize to 9:16
   - Add captions
   - Export for social media

5. **Failover Testing**:

   - Start streaming to YouTube
   - Simulate RTMP failure
   - Verify automatic SRT failover
   - Verify recovery after fix

---

### Day 3 (Wednesday): Bug Fixes & Polish

- Fix issues found in integration tests
- Add missing error handling
- Improve logging
- Optimize performance

---

### Day 4 (Thursday): Documentation & Demo

**Documentation**:

- API documentation (OpenAPI/Swagger)
- Architecture diagrams (updated)
- User guide for control panel
- Deployment instructions

**Demo Video**:

1. System overview
2. Phone discovery
3. OBS scene creation
4. Multi-platform streaming
5. Health monitoring
6. Transcription & export

---

### Day 5 (Friday): Final Testing & Release

- Final integration test
- Performance testing (5+ hour stream)
- Load testing (stress test)
- Create v1.0 release
- Tag in git
- Deploy documentation

---

## 📊 SUCCESS METRICS

### Week 1 (Services)

- [ ] All 6 services implemented
- [ ] All services tested independently
- [ ] Integration test passes

### Week 2 (Modules)

- [ ] Camera discovery works
- [ ] OBS auto-scene creation works
- [ ] Multi-platform streaming works

### Week 3 (API)

- [ ] All endpoints functional
- [ ] WebSocket real-time updates work
- [ ] API documentation complete

### Week 4 (Integration)

- [ ] End-to-end workflow works
- [ ] Can stream for 5+ hours stable
- [ ] Demo video complete

---

## 🔥 DAILY ROUTINE

### Morning (4 hours)

1. Review previous day's work (30 min)
2. Implement new feature (3 hours)
3. Write unit tests (30 min)

### Afternoon (4 hours)

1. Continue implementation (2 hours)
2. Integration testing (1 hour)
3. Documentation (1 hour)

### Total: 8 hours/day, 5 days/week = 40 hours/week

---

## ⚠️ RISK MITIGATION

### Potential Blockers

1. **OBS Integration Issues**

   - Mitigation: Test OBS adapter early
   - Fallback: Document manual OBS setup

2. **Phone Discovery Not Working**

   - Mitigation: Implement QR code fallback
   - Test mDNS on local network early

3. **Transcription Performance**

   - Mitigation: Test with actual files
   - Consider smaller model if too slow

4. **FFmpeg Complexity**

   - Mitigation: Start with simple cuts
   - Gradually add complex features

---

## 🎯 NEXT ACTION

**Right now, continue with**:

Say: **"Continue building services"** and I'll create:
1. QualityService
2. EnhancementService
3. NetworkService
4. RecordingService
5. Complete ExportService

Then move to Week 2 (Modules).

---

**Last Updated**: November 20, 2024
**Current Week**: Week 1 - Services Layer
**Progress**: Day 1 Started (TranscriptionService complete)
