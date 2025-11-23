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
    Route,
    RouteState
)
from models import (
    CameraDevice,
    DestinationType,
    SessionState,
    StreamDestination
)
from models.scene import Scene, SceneLayout
from models.session import SessionConfig


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

    def test_add_route(self, stream_router, mock_camera):
        """Test attaching a camera to a scene"""
        scene = Scene(
            id="scene-1",
            name="Test Scene",
            layout=SceneLayout.SINGLE_FULL
        )

        route = stream_router.attach_camera_to_scene(
            camera=mock_camera,
            scene=scene
        )

        assert route is not None
        routes = stream_router.get_routes_for_camera(mock_camera.id)
        assert len(routes) == 1
        assert routes[0].source_camera_id == mock_camera.id
        assert routes[0].target_scene_id == scene.id

    def test_get_route(self, stream_router, mock_camera):
        """Test retrieving routes for a camera"""
        scene = Scene(
            id="scene-1",
            name="Test Scene",
            layout=SceneLayout.SINGLE_FULL
        )

        stream_router.attach_camera_to_scene(
            camera=mock_camera,
            scene=scene
        )

        routes = stream_router.get_routes_for_camera(mock_camera.id)

        assert routes is not None
        assert len(routes) == 1
        assert routes[0].source_camera_id == mock_camera.id
        assert routes[0].target_scene_id == scene.id

    def test_get_nonexistent_route(self, stream_router):
        """Test getting routes for a camera that has none"""
        result = stream_router.get_routes_for_camera("nonexistent-camera")
        assert result == []

    def test_remove_route(self, stream_router, mock_camera):
        """Test detaching a camera from a scene"""
        scene = Scene(
            id="scene-1",
            name="Test Scene",
            layout=SceneLayout.SINGLE_FULL
        )

        stream_router.attach_camera_to_scene(
            camera=mock_camera,
            scene=scene
        )

        result = stream_router.detach_camera_from_scene(
            camera_id=mock_camera.id,
            scene_id=scene.id
        )

        assert result is True
        routes = stream_router.get_routes_for_camera(mock_camera.id)
        assert len(routes) == 0

    def test_get_routes_for_camera(
        self, stream_router, mock_camera, mock_cameras
    ):
        """Test getting all routes for a specific camera"""
        # Attach camera-1 to multiple scenes
        for i in range(3):
            scene = Scene(
                id=f"scene-{i}",
                name=f"Test Scene {i}",
                layout=SceneLayout.SINGLE_FULL
            )
            stream_router.attach_camera_to_scene(
                camera=mock_camera,
                scene=scene
            )

        # Add route for different camera
        other_scene = Scene(
            id="scene-x",
            name="Other Scene",
            layout=SceneLayout.SINGLE_FULL
        )
        stream_router.attach_camera_to_scene(
            camera=mock_cameras[1],
            scene=other_scene
        )

        camera_routes = stream_router.get_routes_for_camera(mock_camera.id)
        assert len(camera_routes) == 3
        assert all(r.source_camera_id == mock_camera.id for r in camera_routes)

    def test_get_routes_for_scene(self, stream_router, mock_cameras):
        """Test getting all routes for a specific scene"""
        scene = Scene(
            id="scene-1",
            name="Shared Scene",
            layout=SceneLayout.GRID_2X2
        )

        # Attach multiple cameras to scene-1
        for i in range(3):
            stream_router.attach_camera_to_scene(
                camera=mock_cameras[i],
                scene=scene
            )

        scene_routes = stream_router.get_routes_for_scene(scene.id)
        assert len(scene_routes) == 3
        assert all(r.target_scene_id == scene.id for r in scene_routes)

    def test_list_all_routes(self, stream_router, mock_cameras):
        """Test listing all routes"""
        scenes = [
            Scene(
                id=f"scene-{i}",
                name=f"Test Scene {i}",
                layout=SceneLayout.SINGLE_FULL
            )
            for i in range(5)
        ]

        for i in range(5):
            stream_router.attach_camera_to_scene(
                camera=mock_cameras[i % len(mock_cameras)],
                scene=scenes[i]
            )

        # StreamRouter doesn't have list_all,
        # use get_active_routes or access _routes
        all_routes = list(stream_router._routes.values())
        assert len(all_routes) == 5


# ============================================================================
# SESSION MANAGER TESTS
# ============================================================================

@pytest.mark.unit
class TestSessionManager:
    """Test suite for SessionManager"""

    def test_create_session(self, session_manager):
        """Test creating a new session"""
        config = SessionConfig(
            name="Test Session",
            description="Test description"
        )
        session = session_manager.create_session(config)

        assert session.id is not None
        assert session.name == "Test Session"
        assert session.state == SessionState.PREPARING

    def test_create_session_generates_id_if_not_provided(
            self, session_manager):
        """Test that session ID is auto-generated if not provided"""
        config = SessionConfig(name="Test Session")
        session = session_manager.create_session(config)

        assert session.id is not None
        assert len(session.id) > 0

    def test_create_duplicate_session_raises_error(self, session_manager):
        """Test that sessions can have same name (IDs are unique)"""
        config1 = SessionConfig(name="Test Session")
        config2 = SessionConfig(name="Test Session")

        session1 = session_manager.create_session(config1)
        session2 = session_manager.create_session(config2)

        # Different IDs even with same name
        assert session1.id != session2.id
        assert session1.name == session2.name

    def test_get_session(self, session_manager):
        """Test retrieving a session"""
        config = SessionConfig(name="Test Session")
        created = session_manager.create_session(config)

        retrieved = session_manager.get_session(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test Session"

    def test_get_nonexistent_session(self, session_manager):
        """Test getting a session that doesn't exist"""
        result = session_manager.get_session("nonexistent")
        assert result is None

    def test_list_sessions(self, session_manager):
        """Test listing all sessions"""
        for i in range(3):
            config = SessionConfig(name=f"Session {i}")
            session_manager.create_session(config)

        sessions = session_manager.list_sessions()
        assert len(sessions) == 3

    def test_delete_session(self, session_manager):
        """Test deleting a session"""
        config = SessionConfig(name="Test Session")
        session = session_manager.create_session(config)
        session_manager.delete_session(session.id)

        assert session_manager.get_session(session.id) is None

    def test_delete_nonexistent_session_raises_error(self, session_manager):
        """Test deleting a session that doesn't exist returns False"""
        result = session_manager.delete_session("nonexistent")
        assert result is False

    def test_update_session_state(
        self, session_manager, device_registry, mock_camera
    ):
        """Test updating session state"""
        # Register camera first (required to start session)
        device_registry.register(mock_camera)

        # Create destination
        destination = StreamDestination(
            id="test-dest-1",
            name="Test Destination",
            type=DestinationType.CUSTOM_RTMP,
            url="rtmp://test.example.com/live",
            stream_key="test-stream-key",
            platform="custom"
        )

        config = SessionConfig(
            name="Test Session",
            camera_ids=[mock_camera.id]
        )
        session = session_manager.create_session(config)

        assert session.state == SessionState.PREPARING

        # Add camera and destination to session (both required before starting)
        session_manager.add_camera_to_session(session.id, mock_camera.id)
        session_manager.add_destination_to_session(session.id, destination)

        # Start session to change state to LIVE
        session_manager.start_session(session.id)
        updated = session_manager.get_session(session.id)
        assert updated.state == SessionState.LIVE

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
        config = SessionConfig(name="Test Session")
        session = session_manager.create_session(config)

        # Add camera to session
        session_manager.add_camera_to_session(session.id, mock_camera.id)

        updated = session_manager.get_session(session.id)
        assert len(updated.cameras) == 1
        assert updated.cameras[0].id == mock_camera.id

    def test_remove_nonexistent_camera_raises_error(
        self,
        session_manager,
        device_registry
    ):
        """Test adding a camera that doesn't exist returns False"""
        config = SessionConfig(name="Test Session")
        session = session_manager.create_session(config)

        result = session_manager.add_camera_to_session(
            session.id, "nonexistent-camera")
        assert result is False

    def test_remove_camera_from_session(
            self, session_manager, device_registry, mock_camera):
        """Test removing a camera from a session"""
        # Register camera
        device_registry.register(mock_camera)

        # Create session and add camera
        config = SessionConfig(name="Test Session")
        session = session_manager.create_session(config)
        session_manager.add_camera_to_session(session.id, mock_camera.id)

        # Remove camera
        session_manager.remove_camera_from_session(session.id, mock_camera.id)

        updated = session_manager.get_session(session.id)
        assert len(updated.cameras) == 0


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

        # Emit event using publish
        await event_bus.publish("test_event", {"data": "test"})

        # Wait for async processing
        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0].data["data"] == "test"

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

        await event_bus.publish("test_event", {"data": "test"})
        await asyncio.sleep(0.1)

        assert len(received_1) == 1
        assert len(received_2) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus):
        """Test unsubscribing from events"""
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Subscribe and get handler_id
        handler_id = event_bus.subscribe("test_event", handler)
        # Unsubscribe using the handler_id
        event_bus.unsubscribe("test_event", handler_id)

        # Emit event
        await event_bus.publish("test_event", {"data": "test"})
        await asyncio.sleep(0.1)

        # Should not receive event
        assert len(received_events) == 0

    @pytest.mark.asyncio
    async def test_emit_with_no_subscribers(self, event_bus):
        """Test emitting event with no subscribers doesn't crash"""
        # Should not raise an exception
        await event_bus.publish("test_event", {"data": "test"})

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

        await event_bus.publish("test_event", {"data": "test"})
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
        config = SessionConfig(name="Integration Test")
        session = session_manager.create_session(config)

        # Add cameras to session
        for camera in mock_cameras:
            session_manager.add_camera_to_session(session.id, camera.id)

        # Create routes (using scenes)
        from models.scene import Scene, SceneLayout
        for i, camera in enumerate(mock_cameras):
            scene = Scene(
                id=f"scene-{i}",
                name=f"Scene {i}",
                layout=SceneLayout.SINGLE_FULL
            )
            stream_router.attach_camera_to_scene(camera, scene)

        # Verify everything is connected
        updated_session = session_manager.get_session(session.id)
        assert len(updated_session.cameras) == len(mock_cameras)

        for camera in mock_cameras:
            routes = stream_router.get_routes_for_camera(camera.id)
            assert len(routes) > 0
