"""
Pytest Configuration and Shared Fixtures

This module provides test fixtures and configuration for the entire test suite.
"""
import pytest
import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import DeviceRegistry, SessionManager, StreamRouter, EventBus
from models import CameraDevice, Session, TransportType, SessionState
from services import (
    TranscriptionService,
    QualityService,
    EnhancementService,
    NetworkService,
    RecordingService,
    ExportService
)
# Temporarily disabled due to model mismatches - will fix after core tests pass
# from modules import MultiCameraManager, MultiPlatformStreaming, OBSOrchestrator


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interaction"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )
    config.addinivalue_line(
        "markers", "requires_obs: Tests that require OBS connection"
    )
    config.addinivalue_line(
        "markers", "requires_hardware: Tests that require real hardware"
    )


# ============================================================================
# EVENT LOOP FIXTURE
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# CORE SERVICE FIXTURES
# ============================================================================

@pytest.fixture
def device_registry() -> DeviceRegistry:
    """Provide a fresh DeviceRegistry instance"""
    return DeviceRegistry()


@pytest.fixture
def stream_router() -> StreamRouter:
    """Provide a fresh StreamRouter instance"""
    return StreamRouter()


@pytest.fixture
def event_bus() -> EventBus:
    """Provide a fresh EventBus instance"""
    return EventBus()


@pytest.fixture
def session_manager(device_registry, stream_router) -> SessionManager:
    """Provide a configured SessionManager instance"""
    return SessionManager(device_registry, stream_router)


# ============================================================================
# MOCK CAMERA FIXTURES
# ============================================================================

@pytest.fixture
def mock_camera() -> CameraDevice:
    """Provide a mock camera device"""
    return CameraDevice(
        id="test-camera-1",
        label="Test Camera 1",
        transport=TransportType.SRT,
        url="srt://192.168.1.100:9000",
        capabilities=["video", "audio"]
    )


@pytest.fixture
def mock_cameras() -> list[CameraDevice]:
    """Provide multiple mock camera devices"""
    return [
        CameraDevice(
            id=f"test-camera-{i}",
            label=f"Test Camera {i}",
            transport=TransportType.SRT,
            url=f"srt://192.168.1.{100+i}:9000",
            capabilities=["video", "audio"]
        )
        for i in range(1, 4)
    ]


# ============================================================================
# MOCK SESSION FIXTURES
# ============================================================================

@pytest.fixture
def mock_session() -> Session:
    """Provide a mock session"""
    return Session(
        id="test-session-1",
        name="Test Session",
        description="Test session for unit tests",
        state=SessionState.READY,
        camera_ids=[],
        scene_ids=[],
        destination_ids=[]
    )


# ============================================================================
# SERVICE FIXTURES (WITH MOCKS)
# ============================================================================

@pytest.fixture
def mock_transcription_service() -> Mock:
    """Provide a mock TranscriptionService"""
    service = Mock(spec=TranscriptionService)
    service.transcribe_live = AsyncMock(return_value={"text": "Test transcription"})
    service.transcribe_file = AsyncMock(return_value={"text": "Test transcription"})
    return service


@pytest.fixture
def mock_quality_service() -> Mock:
    """Provide a mock QualityService"""
    service = Mock(spec=QualityService)
    service.analyze_frame = AsyncMock(return_value={
        "overall_score": 85,
        "issues": [],
        "recommendations": []
    })
    return service


@pytest.fixture
def mock_enhancement_service() -> Mock:
    """Provide a mock EnhancementService"""
    service = Mock(spec=EnhancementService)
    service.apply_preset = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_network_service() -> Mock:
    """Provide a mock NetworkService"""
    service = Mock(spec=NetworkService)
    service.run_preflight_test = AsyncMock(return_value={
        "success": True,
        "bandwidth_mbps": 10.0,
        "jitter_ms": 5.0
    })
    return service


@pytest.fixture
def mock_recording_service() -> Mock:
    """Provide a mock RecordingService"""
    service = Mock(spec=RecordingService)
    service.start_recording = AsyncMock(return_value=True)
    service.stop_recording = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_export_service() -> Mock:
    """Provide a mock ExportService"""
    service = Mock(spec=ExportService)
    service.cut_clip = AsyncMock(return_value="/path/to/clip.mp4")
    return service


# ============================================================================
# MODULE FIXTURES (WITH MOCKS)
# ============================================================================

@pytest.fixture
def mock_camera_manager(device_registry, event_bus) -> Mock:
    """Provide a mock MultiCameraManager"""
    manager = Mock(spec=MultiCameraManager)
    manager._registry = device_registry
    manager._event_bus = event_bus
    manager.start_discovery = AsyncMock()
    manager.stop_discovery = AsyncMock()
    manager.get_discovered_cameras = Mock(return_value=[])
    manager.get_camera_health = AsyncMock(return_value={
        "battery_percent": 80,
        "temperature_celsius": 35.0,
        "network_quality": "excellent"
    })
    return manager


@pytest.fixture
def mock_streaming_module(session_manager, event_bus) -> Mock:
    """Provide a mock MultiPlatformStreaming"""
    streaming = Mock(spec=MultiPlatformStreaming)
    streaming._session_manager = session_manager
    streaming._event_bus = event_bus
    streaming.configure_destinations = AsyncMock()
    streaming.start_stream = AsyncMock()
    streaming.stop_stream = AsyncMock()
    streaming.get_health = AsyncMock(return_value={
        "overall_status": "healthy",
        "healthy_destinations": 2,
        "total_destinations": 2
    })
    return streaming


@pytest.fixture
def mock_obs_orchestrator(device_registry, stream_router, event_bus) -> Mock:
    """Provide a mock OBSOrchestrator"""
    obs = Mock(spec=OBSOrchestrator)
    obs._registry = device_registry
    obs._router = stream_router
    obs._event_bus = event_bus
    obs.connect = AsyncMock()
    obs.disconnect = AsyncMock()
    obs.is_connected = AsyncMock(return_value=True)
    obs.create_scene_for_camera = AsyncMock()
    obs.switch_scene = AsyncMock()
    return obs


# ============================================================================
# OBS MOCK FIXTURE
# ============================================================================

@pytest.fixture
def mock_obs_client():
    """Provide a mock OBS WebSocket client"""
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.call = AsyncMock(return_value={"status": "ok"})
    client.is_identified = Mock(return_value=True)
    return client


# ============================================================================
# API TEST FIXTURES
# ============================================================================

@pytest.fixture
async def test_client():
    """Provide an HTTP test client for API testing"""
    from httpx import AsyncClient
    from api.server import create_app
    
    app = create_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def api_headers():
    """Provide common API headers"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test(device_registry, session_manager):
    """Cleanup after each test"""
    yield
    
    # Clear all registered devices
    for device_id in list(device_registry._devices.keys()):
        device_registry.remove(device_id)
    
    # Clear all sessions
    for session_id in list(session_manager._sessions.keys()):
        try:
            session_manager.delete_session(session_id)
        except:
            pass


# ============================================================================
# TEMPORARY DIRECTORY FIXTURE
# ============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for file operations"""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    return test_dir


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def sample_video_metadata():
    """Provide sample video metadata for testing"""
    return {
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "bitrate": 5000000,
        "codec": "h264",
        "duration": 60.0
    }


@pytest.fixture
def sample_audio_metadata():
    """Provide sample audio metadata for testing"""
    return {
        "sample_rate": 48000,
        "channels": 2,
        "bitrate": 192000,
        "codec": "aac"
    }
