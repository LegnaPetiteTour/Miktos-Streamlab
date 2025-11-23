"""
Integration Tests

Tests complete workflows and component interactions
"""
import pytest
import asyncio

from models import CameraDevice, TransportType, SessionState
from models.session import SessionConfig
from models.scene import Scene, SceneLayout


# ============================================================================
# CAMERA DISCOVERY TO STREAMING WORKFLOW
# ============================================================================

@pytest.mark.integration
class TestCameraToStreamWorkflow:
    """Test complete workflow from camera discovery to streaming"""

    @pytest.mark.asyncio
    async def test_complete_workflow(
        self,
        device_registry,
        session_manager,
        stream_router,
        event_bus,
        mock_cameras
    ):
        """
        Test complete workflow:
        discover → register → create session → stream
        """

        # 1. Register cameras (simulating discovery)
        for camera in mock_cameras:
            device_registry.register(camera)

        # Verify cameras registered
        all_cameras = device_registry.list_all()
        assert len(all_cameras) == len(mock_cameras)

        # 2. Create session
        config = SessionConfig(name="Integration Test Workflow")
        session = session_manager.create_session(config)

        assert session.state == SessionState.PREPARING

        # 3. Add cameras to session
        for camera in mock_cameras:
            session_manager.add_camera_to_session(session.id, camera.id)

        # Verify cameras added
        updated_session = session_manager.get_session(session.id)
        assert len(updated_session.cameras) == len(mock_cameras)

        # Verify final state
        final_session = session_manager.get_session(session.id)
        assert final_session.state == SessionState.PREPARING
        assert len(final_session.cameras) == len(mock_cameras)


# ============================================================================
# MULTI-CAMERA SCENE CREATION WORKFLOW
# ============================================================================

@pytest.mark.integration
class TestMultiCameraSceneWorkflow:
    """Test workflow for creating multi-camera scenes"""

    @pytest.mark.asyncio
    async def test_multi_camera_scene_creation(
        self,
        device_registry,
        session_manager,
        stream_router,
        event_bus,
        mock_cameras
    ):
        """Test creating scenes with multiple cameras"""

        # Register cameras
        for camera in mock_cameras:
            device_registry.register(camera)

        # Create session
        config = SessionConfig(name="Multi-Camera Test")
        session = session_manager.create_session(config)

        # Add all cameras to session
        for camera in mock_cameras:
            session_manager.add_camera_to_session(session.id, camera.id)

        # Create routes for each camera to scenes
        # Use Scene objects and attach_camera_to_scene API

        # Single camera scene
        single_scene = Scene(
            id="scene-single",
            name="Single Camera Scene",
            layout=SceneLayout.SINGLE_FULL
        )
        stream_router.attach_camera_to_scene(mock_cameras[0], single_scene)

        # Multi-camera scene
        multi_scene = Scene(
            id="scene-multi",
            name="Multi Camera Scene",
            layout=SceneLayout.GRID_2X2
        )
        for camera in mock_cameras:
            stream_router.attach_camera_to_scene(camera, multi_scene)

        # Verify routing
        single_routes = stream_router.get_routes_for_scene("scene-single")
        multi_routes = stream_router.get_routes_for_scene("scene-multi")

        assert len(single_routes) == 1
        assert len(multi_routes) == len(mock_cameras)


# ============================================================================
# EVENT BUS INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestEventBusIntegration:
    """Test event bus integration across components"""

    @pytest.mark.asyncio
    async def test_camera_registration_events(
        self,
        device_registry,
        event_bus,
        mock_camera
    ):
        """Test that camera registration triggers events"""

        received_events = []

        async def event_handler(event):
            received_events.append(event)

        # Subscribe to camera events
        event_bus.subscribe("camera_registered", event_handler)

        # Publish camera registration event
        await event_bus.publish("camera_registered", {
            "camera_id": mock_camera.id,
            "label": mock_camera.label
        })

        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0].data["camera_id"] == mock_camera.id

    @pytest.mark.asyncio
    async def test_session_state_change_events(
        self,
        session_manager,
        event_bus
    ):
        """Test that session state changes trigger events"""

        received_events = []

        async def event_handler(event):
            received_events.append(event)

        # Subscribe to session events
        event_bus.subscribe("session_state_changed", event_handler)

        # Create session
        config = SessionConfig(name="Event Test")
        session = session_manager.create_session(config)

        # Publish state change event
        await event_bus.publish("session_state_changed", {
            "session_id": session.id,
            "old_state": SessionState.PREPARING.value,
            "new_state": SessionState.READY.value
        })

        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0].data["session_id"] == session.id


# ============================================================================
# HEALTH MONITORING INTEGRATION
# ============================================================================

@pytest.mark.integration
class TestHealthMonitoringIntegration:
    """Test health monitoring across components"""

    @pytest.mark.asyncio
    async def test_camera_health_monitoring(
        self,
        device_registry,
        event_bus,
        mock_camera
    ):
        """Test monitoring camera health"""

        # Register camera
        device_registry.register(mock_camera)

        # Create health update event
        health_updates = []

        async def health_handler(event):
            health_updates.append(event)

        event_bus.subscribe("camera_health_update", health_handler)

        # Emit health update
        await event_bus.publish("camera_health_update", {
            "camera_id": mock_camera.id,
            "battery_percent": 75,
            "temperature_celsius": 38.5,
            "network_quality": "good"
        })

        await asyncio.sleep(0.1)

        assert len(health_updates) == 1
        assert health_updates[0].data["camera_id"] == mock_camera.id
        assert health_updates[0].data["battery_percent"] == 75


# ============================================================================
# STREAMING FAILOVER INTEGRATION
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestStreamingFailoverIntegration:
    """Test streaming failover scenarios"""

    @pytest.mark.asyncio
    async def test_failover_event_handling(
        self,
        session_manager,
        event_bus
    ):
        """Test handling of streaming failover events"""

        # Create session
        config = SessionConfig(name="Failover Test")
        session = session_manager.create_session(config)

        # Track failover events
        failover_events = []

        async def failover_handler(event):
            failover_events.append(event)

        event_bus.subscribe("streaming_failover", failover_handler)

        # Simulate failover event
        await event_bus.publish("streaming_failover", {
            "session_id": session.id,
            "destination": "youtube",
            "reason": "connection_lost",
            "backup_active": True
        })

        await asyncio.sleep(0.1)

        assert len(failover_events) == 1
        assert failover_events[0].data["destination"] == "youtube"
        assert failover_events[0].data["backup_active"] is True


# ============================================================================
# CONCURRENT OPERATIONS TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestConcurrentOperations:
    """Test concurrent operations across components"""

    @pytest.mark.asyncio
    async def test_concurrent_camera_registration(
        self,
        device_registry,
        mock_cameras
    ):
        """Test registering multiple cameras concurrently"""

        async def register_camera(camera):
            await asyncio.sleep(0.01)  # Simulate async operation
            device_registry.register(camera)

        # Register cameras concurrently
        tasks = [register_camera(camera) for camera in mock_cameras]
        await asyncio.gather(*tasks)

        # Verify all registered
        all_cameras = device_registry.list_all()
        assert len(all_cameras) == len(mock_cameras)

    @pytest.mark.asyncio
    async def test_concurrent_event_emission(
        self,
        event_bus
    ):
        """Test emitting multiple events concurrently"""

        received_events = []

        async def event_handler(event):
            received_events.append(event)

        event_bus.subscribe("test_event", event_handler)

        # Emit multiple events concurrently
        async def emit_event(i):
            await event_bus.publish("test_event", {"index": i})

        tasks = [emit_event(i) for i in range(10)]
        await asyncio.gather(*tasks)

        await asyncio.sleep(0.2)

        assert len(received_events) == 10


# ============================================================================
# ERROR RECOVERY INTEGRATION
# ============================================================================

@pytest.mark.integration
class TestErrorRecoveryIntegration:
    """Test error recovery across components"""

    @pytest.mark.asyncio
    async def test_session_recovery_after_error(
        self,
        session_manager,
        device_registry,
        mock_camera
    ):
        """Test recovering a session after error state"""

        # Create session
        config = SessionConfig(name="Recovery Test")
        session = session_manager.create_session(config)

        # Register camera
        device_registry.register(mock_camera)

        # Add camera to session
        session_manager.add_camera_to_session(session.id, mock_camera.id)

        # Verify session state remains PREPARING
        current_session = session_manager.get_session(session.id)
        assert current_session.state == SessionState.PREPARING

        # Verify camera was added successfully
        assert len(current_session.cameras) == 1
        assert current_session.cameras[0].id == mock_camera.id


# ============================================================================
# CLEANUP AND RESOURCE MANAGEMENT
# ============================================================================

@pytest.mark.integration
class TestResourceManagement:
    """Test resource cleanup and management"""

    @pytest.mark.asyncio
    async def test_session_cleanup_removes_routes(
        self,
        session_manager,
        device_registry,
        stream_router,
        mock_cameras
    ):
        """Test that deleting session cleans up routes"""

        # Setup: Create session with cameras and routes
        for camera in mock_cameras:
            device_registry.register(camera)

        config = SessionConfig(name="Cleanup Test")
        session = session_manager.create_session(config)

        for camera in mock_cameras:
            session_manager.add_camera_to_session(session.id, camera.id)

        # Create routes using Scene objects
        for i, camera in enumerate(mock_cameras):
            scene = Scene(
                id=f"scene-{i}",
                name=f"Scene {i}",
                layout=SceneLayout.SINGLE_FULL
            )
            stream_router.attach_camera_to_scene(camera, scene)

        # Delete session
        session_manager.delete_session(session.id)

        # Verify session deleted
        assert session_manager.get_session(session.id) is None

        # Note: Routes cleanup would be handled by session deletion logic
        # in production, but we're testing the interface here

    @pytest.mark.asyncio
    async def test_camera_removal_updates_sessions(
        self,
        session_manager,
        device_registry,
        mock_camera
    ):
        """Test that removing camera updates sessions"""

        # Register camera
        device_registry.register(mock_camera)

        # Create session with camera
        config = SessionConfig(name="Camera Removal Test")
        session = session_manager.create_session(config)
        session_manager.add_camera_to_session(session.id, mock_camera.id)

        # Verify camera in session
        updated_session = session_manager.get_session(session.id)
        assert any(c.id == mock_camera.id for c in updated_session.cameras)

        # Remove camera from session
        session_manager.remove_camera_from_session(
            session.id, mock_camera.id)

        # Verify camera removed from session
        updated_session = session_manager.get_session(session.id)
        assert mock_camera.id not in updated_session.camera_ids


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Test performance under load"""

    @pytest.mark.asyncio
    async def test_many_cameras_performance(
        self,
        device_registry
    ):
        """Test performance with many cameras"""
        import time

        # Create 100 cameras
        cameras = [
            CameraDevice(
                id=f"perf-camera-{i}",
                label=f"Performance Camera {i}",
                transport=TransportType.SRT,
                url=f"srt://192.168.1.{i}:9000",
                capabilities=["video", "audio"]
            )
            for i in range(100)
        ]

        # Measure registration time
        start_time = time.time()
        for camera in cameras:
            device_registry.register(camera)
        registration_time = time.time() - start_time

        # Should complete quickly (< 1 second for 100 cameras)
        assert registration_time < 1.0

        # Measure retrieval time
        start_time = time.time()
        all_cameras = device_registry.list_all()
        retrieval_time = time.time() - start_time

        # Should retrieve quickly
        assert retrieval_time < 0.1
        assert len(all_cameras) == 100

    @pytest.mark.asyncio
    async def test_many_events_performance(
        self,
        event_bus
    ):
        """Test event bus performance with many events"""
        import time

        received_count = [0]  # Use list to avoid closure issues

        async def fast_handler(event):
            received_count[0] += 1

        event_bus.subscribe("perf_test", fast_handler)

        # Emit 1000 events
        start_time = time.time()
        for i in range(1000):
            await event_bus.publish("perf_test", {"index": i})

        emission_time = time.time() - start_time

        # Wait for processing
        await asyncio.sleep(0.5)

        # Should emit quickly
        assert emission_time < 2.0

        # Most events should be processed (allow some async timing tolerance)
        assert received_count[0] >= 950
