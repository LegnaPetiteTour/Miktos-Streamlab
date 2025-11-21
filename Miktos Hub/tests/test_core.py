"""
Unit Tests for Core Services

Tests the foundational services: DeviceRegistry, SessionManager,
StreamRouter, EventBus
"""
import asyncio
import pytest

from core import (  # noqa: F401
    DeviceRegistry,
    SessionManager,
    StreamRouter,
    EventBus,
    Route
)
from models import CameraDevice, SessionState


# ============================================================================
# DEVICE REGISTRY TESTS
# ============================================================================

@pytest.mark.unit
class TestDeviceRegistry:
    """Test suite for DeviceRegistry"""

    def test_register_device(self, device_registry, mock_camera):
        """Test registering a new device"""
        device_registry.register(mock_camera)

        assert mock_camera.id in device_registry._devices
        retrieved = device_registry.get(mock_camera.id)
        assert retrieved.id == mock_camera.id
        assert retrieved.label == mock_camera.label

    def test_register_duplicate_device_updates(
        self,
        device_registry,
        mock_camera
    ):
        """Test that registering same device ID updates it"""
        device_registry.register(mock_camera)

        # Register again with updated label
        updated_camera = CameraDevice(
            id=mock_camera.id,
            label="Updated Label",
            transport=mock_camera.transport,
            url=mock_camera.url,
            capabilities=mock_camera.capabilities
        )
        device_registry.register(updated_camera)

        retrieved = device_registry.get(mock_camera.id)
        assert retrieved.label == "Updated Label"

    def test_get_nonexistent_device_returns_none(self, device_registry):
        """Test getting a device that doesn't exist"""
        result = device_registry.get("nonexistent-id")
        assert result is None

    def test_remove_device(self, device_registry, mock_camera):
        """Test removing a device"""
        device_registry.register(mock_camera)
        device_registry.unregister(mock_camera.id)

        assert mock_camera.id not in device_registry._devices
        assert device_registry.get(mock_camera.id) is None

    def test_remove_nonexistent_device_raises_error(self, device_registry):
        """Test removing a device that doesn't exist"""
        with pytest.raises(KeyError):
            device_registry.unregister("nonexistent-id")

    def test_list_all_devices(self, device_registry, mock_cameras):
        """Test listing all registered devices"""
        for camera in mock_cameras:
            device_registry.register(camera)

        all_devices = device_registry.list_all()
        assert len(all_devices) == len(mock_cameras)
        assert all(isinstance(d, CameraDevice) for d in all_devices)

    def test_list_all_empty(self, device_registry):
        """Test listing devices when registry is empty"""
        all_devices = device_registry.list_all()
        assert len(all_devices) == 0
        assert isinstance(all_devices, list)

    def test_thread_safety_concurrent_registration(
        self,
        device_registry,
        mock_cameras
    ):
        """Test that concurrent registrations are thread-safe"""
        import threading

        def register_device(device):
            device_registry.register(device)

        threads = [
            threading.Thread(target=register_device, args=(camera,))
            for camera in mock_cameras
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All cameras should be registered
        assert len(device_registry.list_all()) == len(mock_cameras)


# ============================================================================
# STREAM ROUTER TESTS
# ============================================================================

@pytest.mark.unit
class TestStreamRouter:
    """Test suite for StreamRouter"""

    def test_add_route(self, stream_router):
        """Test adding a new route"""
        route = Route(
            id="route-1",
            camera_id="camera-1",
            scene_id="scene-1"
        )

        stream_router.add_route(route)
        assert route.id in stream_router._routes

    def test_get_route(self, stream_router):
        """Test retrieving a route"""
        route = Route(
            id="route-1",
            camera_id="camera-1",
            scene_id="scene-1"
        )

        stream_router.add_route(route)
        retrieved = stream_router.get_route(route.id)

        assert retrieved is not None
        assert retrieved.id == route.id
        assert retrieved.camera_id == route.camera_id

    def test_get_nonexistent_route(self, stream_router):
        """Test getting a route that doesn't exist"""
        result = stream_router.get_route("nonexistent-id")
        assert result is None

    def test_remove_route(self, stream_router):
        """Test removing a route"""
        route = Route(
            id="route-1",
            camera_id="camera-1",
            scene_id="scene-1"
        )

        stream_router.add_route(route)
        stream_router.remove_route(route.id)

        assert route.id not in stream_router._routes

    def test_get_routes_for_camera(self, stream_router):
        """Test getting all routes for a specific camera"""
        routes = [
            Route(id=f"route-{i}", camera_id="camera-1", scene_id=f"scene-{i}")
            for i in range(3)
        ]

        for route in routes:
            stream_router.add_route(route)

        # Add route for different camera
        stream_router.add_route(
            Route(id="route-other", camera_id="camera-2", scene_id="scene-x")
        )

        camera_routes = stream_router.get_routes_for_camera("camera-1")
        assert len(camera_routes) == 3
        assert all(r.camera_id == "camera-1" for r in camera_routes)

    def test_get_routes_for_scene(self, stream_router):
        """Test getting all routes for a specific scene"""
        routes = [
            Route(id=f"route-{i}", camera_id=f"camera-{i}", scene_id="scene-1")
            for i in range(3)
        ]

        for route in routes:
            stream_router.add_route(route)

        scene_routes = stream_router.get_routes_for_scene("scene-1")
        assert len(scene_routes) == 3
        assert all(r.scene_id == "scene-1" for r in scene_routes)

    def test_list_all_routes(self, stream_router):
        """Test listing all routes"""
        routes = [
            Route(
                id=f"route-{i}",
                camera_id=f"camera-{i}",
                scene_id=f"scene-{i}")
            for i in range(5)
        ]

        for route in routes:
            stream_router.add_route(route)

        all_routes = stream_router.list_all()
        assert len(all_routes) == 5


# ============================================================================
# SESSION MANAGER TESTS
# ============================================================================

@pytest.mark.unit
class TestSessionManager:
    """Test suite for SessionManager"""

    def test_create_session(self, session_manager):
        """Test creating a new session"""
        session = session_manager.create_session(
            session_id="test-session",
            name="Test Session",
            description="Test description"
        )

        assert session.id == "test-session"
        assert session.name == "Test Session"
        assert session.state == SessionState.PREPARING

    def test_create_session_generates_id_if_not_provided(
            self, session_manager):
        """Test that session ID is auto-generated if not provided"""
        session = session_manager.create_session(
            name="Test Session"
        )

        assert session.id is not None
        assert len(session.id) > 0

    def test_create_duplicate_session_raises_error(self, session_manager):
        """Test that creating duplicate session ID raises error"""
        session_manager.create_session(session_id="test-1", name="Test 1")

        with pytest.raises(ValueError, match="already exists"):
            session_manager.create_session(session_id="test-1", name="Test 2")

    def test_get_session(self, session_manager):
        """Test retrieving a session"""
        created = session_manager.create_session(
            session_id="test-session",
            name="Test Session"
        )

        retrieved = session_manager.get_session("test-session")
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_nonexistent_session(self, session_manager):
        """Test getting a session that doesn't exist"""
        result = session_manager.get_session("nonexistent")
        assert result is None

    def test_list_sessions(self, session_manager):
        """Test listing all sessions"""
        for i in range(3):
            session_manager.create_session(
                session_id=f"session-{i}",
                name=f"Session {i}"
            )

        sessions = session_manager.list_sessions()
        assert len(sessions) == 3

    def test_delete_session(self, session_manager):
        """Test deleting a session"""
        session_manager.create_session(session_id="test-session", name="Test")
        session_manager.delete_session("test-session")

        assert session_manager.get_session("test-session") is None

    def test_delete_nonexistent_session_raises_error(self, session_manager):
        """Test deleting a session that doesn't exist"""
        with pytest.raises(ValueError, match="not found"):
            session_manager.delete_session("nonexistent")

    def test_update_session_state(self, session_manager):
        """Test updating session state"""
        session = session_manager.create_session(
            session_id="test-session",
            name="Test"
        )

        assert session.state == SessionState.PREPARING

        session_manager.update_session_state(
            "test-session", SessionState.READY)
        updated = session_manager.get_session("test-session")
        assert updated.state == SessionState.READY

    def test_add_camera_to_session(
        self,
        session_manager,
        device_registry,
        mock_camera
    ):
        """Test adding a camera to a session"""
        # Register camera
        device_registry.register(mock_camera)

        # Create session
        session_manager.create_session(
            session_id="test-session",
            name="Test"
        )

        # Add camera to session
        session_manager.add_camera("test-session", mock_camera.id)

        updated = session_manager.get_session("test-session")
        assert mock_camera.id in updated.camera_ids

    def test_remove_nonexistent_camera_raises_error(
        self,
        session_manager
    ):
        """Test removing a camera that doesn't exist"""
        session_manager.create_session(
            session_id="test-session",
            name="Test"
        )

        with pytest.raises(ValueError, match="not found"):
            session_manager.add_camera("test-session", "nonexistent-camera")

    def test_remove_camera_from_session(
            self, session_manager, device_registry, mock_camera):
        """Test removing a camera from a session"""
        # Register camera
        device_registry.register(mock_camera)

        # Create session and add camera
        session_manager.create_session(session_id="test-session", name="Test")
        session_manager.add_camera("test-session", mock_camera.id)

        # Remove camera
        session_manager.remove_camera("test-session", mock_camera.id)

        updated = session_manager.get_session("test-session")
        assert mock_camera.id not in updated.camera_ids


# ============================================================================
# EVENT BUS TESTS
# ============================================================================

@pytest.mark.unit
class TestEventBus:
    """Test suite for EventBus"""

    @pytest.mark.asyncio
    async def test_subscribe_and_emit(self, event_bus):
        """Test subscribing to and emitting events"""
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Subscribe
        event_bus.subscribe("test_event", handler)

        # Emit event
        await event_bus.emit("test_event", {"data": "test"})

        # Wait for async processing
        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0]["data"] == "test"

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus):
        """Test that multiple subscribers receive the same event"""
        received_1 = []
        received_2 = []

        async def handler1(event):
            received_1.append(event)

        async def handler2(event):
            received_2.append(event)

        event_bus.subscribe("test_event", handler1)
        event_bus.subscribe("test_event", handler2)

        await event_bus.emit("test_event", {"data": "test"})
        await asyncio.sleep(0.1)

        assert len(received_1) == 1
        assert len(received_2) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus):
        """Test unsubscribing from events"""
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Subscribe and unsubscribe
        event_bus.subscribe("test_event", handler)
        event_bus.unsubscribe("test_event", handler)

        # Emit event
        await event_bus.emit("test_event", {"data": "test"})
        await asyncio.sleep(0.1)

        # Should not receive event
        assert len(received_events) == 0

    @pytest.mark.asyncio
    async def test_emit_with_no_subscribers(self, event_bus):
        """Test emitting event with no subscribers doesn't crash"""
        # Should not raise an exception
        await event_bus.emit("test_event", {"data": "test"})

    @pytest.mark.asyncio
    async def test_handler_exception_doesnt_break_other_handlers(
        self,
        event_bus
    ):
        """Test that exception in one handler doesn't affect others"""
        received = []

        async def failing_handler(event):
            raise RuntimeError("Handler error")

        async def working_handler(event):
            received.append(event)

        event_bus.subscribe("test_event", failing_handler)
        event_bus.subscribe("test_event", working_handler)

        await event_bus.emit("test_event", {"data": "test"})
        await asyncio.sleep(0.1)

        # Working handler should still receive event
        assert len(received) == 1


# ============================================================================
# INTEGRATION TESTS FOR CORE SERVICES
# ============================================================================

@pytest.mark.integration
class TestCoreServicesIntegration:
    """Integration tests for core services working together"""

    def test_session_with_devices_and_routes(
        self,
        device_registry,
        session_manager,
        stream_router,
        mock_cameras
    ):
        """Test complete workflow with session, devices, and routes"""
        # Register cameras
        for camera in mock_cameras:
            device_registry.register(camera)

        # Create session
        session = session_manager.create_session(
            session_id="integration-test",
            name="Integration Test"
        )

        # Add cameras to session
        for camera in mock_cameras:
            session_manager.add_camera(session.id, camera.id)

        # Create routes
        for i, camera in enumerate(mock_cameras):
            route = Route(
                id=f"route-{i}",
                camera_id=camera.id,
                scene_id=f"scene-{i}"
            )
            stream_router.add_route(route)

        # Verify everything is connected
        updated_session = session_manager.get_session(session.id)
        assert len(updated_session.camera_ids) == len(mock_cameras)

        for camera in mock_cameras:
            routes = stream_router.get_routes_for_camera(camera.id)
            assert len(routes) > 0
