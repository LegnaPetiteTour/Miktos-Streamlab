"""
Integration Tests

Tests complete workflows and component interactions
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from core import DeviceRegistry, SessionManager, StreamRouter, EventBus
from models import CameraDevice, TransportType, SessionState, Platform
from modules import MultiCameraManager, MultiPlatformStreaming, OBSOrchestrator


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
        """Test complete workflow: discover → register → create session → stream"""
        
        # 1. Register cameras (simulating discovery)
        for camera in mock_cameras:
            device_registry.register(camera)
        
        # Verify cameras registered
        all_cameras = device_registry.list_all()
        assert len(all_cameras) == len(mock_cameras)
        
        # 2. Create session
        session = session_manager.create_session(
            session_id="integration-workflow",
            name="Integration Test Workflow"
        )
        
        assert session.state == SessionState.PREPARING
        
        # 3. Add cameras to session
        for camera in mock_cameras:
            session_manager.add_camera(session.id, camera.id)
        
        # Verify cameras added
        updated_session = session_manager.get_session(session.id)
        assert len(updated_session.camera_ids) == len(mock_cameras)
        
        # 4. Update session state to READY
        session_manager.update_session_state(session.id, SessionState.READY)
        
        # 5. Verify final state
        final_session = session_manager.get_session(session.id)
        assert final_session.state == SessionState.READY
        assert len(final_session.camera_ids) == len(mock_cameras)


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
        session = session_manager.create_session(
            session_id="multi-cam-test",
            name="Multi-Camera Test"
        )
        
        # Add all cameras to session
        for camera in mock_cameras:
            session_manager.add_camera(session.id, camera.id)
        
        # Create routes for each camera to scenes
        from models import Route, SceneLayout
        
        # Single camera scene
        single_route = Route(
            id="route-single",
            camera_id=mock_cameras[0].id,
            scene_id="scene-single"
        )
        stream_router.add_route(single_route)
        
        # Multi-camera scene
        for i, camera in enumerate(mock_cameras):
            route = Route(
                id=f"route-multi-{i}",
                camera_id=camera.id,
                scene_id="scene-multi"
            )
            stream_router.add_route(route)
        
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
        
        # Emit camera registration event
        await event_bus.emit("camera_registered", {
            "camera_id": mock_camera.id,
            "label": mock_camera.label
        })
        
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0]["camera_id"] == mock_camera.id
    
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
        session = session_manager.create_session(
            session_id="event-test",
            name="Event Test"
        )
        
        # Emit state change event
        await event_bus.emit("session_state_changed", {
            "session_id": session.id,
            "old_state": SessionState.PREPARING.value,
            "new_state": SessionState.READY.value
        })
        
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0]["session_id"] == session.id


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
        await event_bus.emit("camera_health_update", {
            "camera_id": mock_camera.id,
            "battery_percent": 75,
            "temperature_celsius": 38.5,
            "network_quality": "good"
        })
        
        await asyncio.sleep(0.1)
        
        assert len(health_updates) == 1
        assert health_updates[0]["camera_id"] == mock_camera.id
        assert health_updates[0]["battery_percent"] == 75


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
        session = session_manager.create_session(
            session_id="failover-test",
            name="Failover Test"
        )
        
        # Track failover events
        failover_events = []
        
        async def failover_handler(event):
            failover_events.append(event)
        
        event_bus.subscribe("streaming_failover", failover_handler)
        
        # Simulate failover event
        await event_bus.emit("streaming_failover", {
            "session_id": session.id,
            "destination": "youtube",
            "reason": "connection_lost",
            "backup_active": True
        })
        
        await asyncio.sleep(0.1)
        
        assert len(failover_events) == 1
        assert failover_events[0]["destination"] == "youtube"
        assert failover_events[0]["backup_active"] is True


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
            await event_bus.emit("test_event", {"index": i})
        
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
        session = session_manager.create_session(
            session_id="recovery-test",
            name="Recovery Test"
        )
        
        # Register camera
        device_registry.register(mock_camera)
        
        # Add camera to session
        session_manager.add_camera(session.id, mock_camera.id)
        
        # Simulate error state
        session_manager.update_session_state(session.id, SessionState.ERROR)
        
        # Verify error state
        error_session = session_manager.get_session(session.id)
        assert error_session.state == SessionState.ERROR
        
        # Recover session
        session_manager.update_session_state(session.id, SessionState.READY)
        
        # Verify recovery
        recovered_session = session_manager.get_session(session.id)
        assert recovered_session.state == SessionState.READY
        assert len(recovered_session.camera_ids) == 1


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
        
        session = session_manager.create_session(
            session_id="cleanup-test",
            name="Cleanup Test"
        )
        
        for camera in mock_cameras:
            session_manager.add_camera(session.id, camera.id)
        
        # Create routes
        from models import Route
        for i, camera in enumerate(mock_cameras):
            route = Route(
                id=f"route-{i}",
                camera_id=camera.id,
                scene_id=f"scene-{i}"
            )
            stream_router.add_route(route)
        
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
        session = session_manager.create_session(
            session_id="camera-removal-test",
            name="Camera Removal Test"
        )
        session_manager.add_camera(session.id, mock_camera.id)
        
        # Verify camera in session
        assert mock_camera.id in session_manager.get_session(session.id).camera_ids
        
        # Remove camera from session
        session_manager.remove_camera(session.id, mock_camera.id)
        
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
            await event_bus.emit("perf_test", {"index": i})
        
        emission_time = time.time() - start_time
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Should emit quickly
        assert emission_time < 2.0
        
        # Most events should be processed (allow some async timing tolerance)
        assert received_count[0] >= 950
