"""
Tests for OBS WebSocket Controller
==================================

Comprehensive test suite for OBS controller functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import Optional

# Mock the OBS library if not installed
try:
    from obswebsocket import obsws, requests as obs_requests
    from obswebsocket.exceptions import ConnectionFailure
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False
    
    # Create mock classes for testing
    class obsws:
        def __init__(self, *args, **kwargs):
            pass
        
        def connect(self):
            pass
        
        def disconnect(self):
            pass
        
        def call(self, request):
            return MagicMock()
    
    class obs_requests:
        @staticmethod
        def GetVersion():
            return MagicMock()
        
        @staticmethod
        def GetSceneList():
            return MagicMock()
        
        @staticmethod
        def GetCurrentProgramScene():
            return MagicMock()
        
        @staticmethod
        def SetCurrentProgramScene(sceneName):
            return MagicMock()
        
        @staticmethod
        def CreateScene(sceneName):
            return MagicMock()
        
        @staticmethod
        def StartStream():
            return MagicMock()
        
        @staticmethod
        def StopStream():
            return MagicMock()
        
        @staticmethod
        def GetStreamStatus():
            return MagicMock()
        
        @staticmethod
        def GetStats():
            return MagicMock()
        
        @staticmethod
        def SetSceneItemEnabled(sceneName, sceneItemId, sceneItemEnabled):
            return MagicMock()
    
    class ConnectionFailure(Exception):
        pass

# Import after mocking
import sys
sys.modules['obswebsocket'] = MagicMock()
sys.modules['obswebsocket.requests'] = MagicMock()
sys.modules['obswebsocket.exceptions'] = MagicMock()

from obs_controller import (
    OBSController,
    OBSStatus,
    StreamingStatus,
    OBSSceneInfo,
    OBSStreamStats
)


@pytest.fixture
def mock_obs_response():
    """Create a mock OBS response"""
    response = MagicMock()
    response.datain = {}
    return response


@pytest.fixture
def controller():
    """Create OBS controller instance with cleanup"""
    with patch('obs_controller.obsws'):
        ctrl = OBSController(
            host='localhost',
            port=4455,
            password='test_password',
            auto_reconnect=False
        )
        yield ctrl
        
        # Cleanup after test - cancel any background tasks
        if hasattr(ctrl, '_health_check_task') and ctrl._health_check_task:
            ctrl._health_check_task.cancel()
            ctrl._health_check_task = None
        if hasattr(ctrl, '_reconnect_task') and ctrl._reconnect_task:
            ctrl._reconnect_task.cancel()
            ctrl._reconnect_task = None
        # Reset status
        ctrl.status = OBSStatus.DISCONNECTED
        ctrl.ws = None


@pytest.fixture
def connected_controller():
    """Create a connected OBS controller with cleanup"""
    with patch('obs_controller.obsws') as mock_ws:
        # Mock successful connection
        mock_instance = MagicMock()
        mock_ws.return_value = mock_instance
        
        ctrl = OBSController(
            host='localhost',
            port=4455,
            password='test_password',
            auto_reconnect=False
        )
        
        # Manually set connected state
        ctrl.ws = mock_instance
        ctrl.status = OBSStatus.CONNECTED
        
        yield ctrl
        
        # Cleanup after test - cancel any background tasks
        if hasattr(ctrl, '_health_check_task') and ctrl._health_check_task:
            ctrl._health_check_task.cancel()
            ctrl._health_check_task = None
        if hasattr(ctrl, '_reconnect_task') and ctrl._reconnect_task:
            ctrl._reconnect_task.cancel()
            ctrl._reconnect_task = None
        # Reset status
        ctrl.status = OBSStatus.DISCONNECTED
        ctrl.ws = None


# ============================================================================
# Connection Tests
# ============================================================================

class TestConnection:
    """Test OBS connection functionality"""
    
    @pytest.mark.asyncio
    async def test_successful_connection(self, controller):
        """Test successful connection to OBS"""
        with patch('obs_controller.obsws') as mock_ws:
            # Mock successful WebSocket connection
            mock_instance = MagicMock()
            mock_ws.return_value = mock_instance
            
            result = await controller.connect()
            
            assert result is True
            assert controller.status == OBSStatus.CONNECTED
    
    @pytest.mark.asyncio
    async def test_connection_failure(self, controller):
        """Test connection failure handling"""
        with patch('obs_controller.obsws') as mock_ws:
            mock_ws.side_effect = ConnectionFailure("Connection refused")
            
            controller.auto_reconnect = False
            result = await controller.connect()
            
            assert result is False
            assert controller.status == OBSStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_already_connected(self, connected_controller):
        """Test connecting when already connected"""
        result = await connected_controller.connect()
        
        assert result is True
        assert connected_controller.status == OBSStatus.CONNECTED
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connected_controller):
        """Test disconnection"""
        await connected_controller.disconnect()
        
        assert connected_controller.status == OBSStatus.DISCONNECTED
        assert connected_controller.ws is None
    
    @pytest.mark.asyncio
    async def test_auto_reconnect_disabled(self, controller):
        """Test that auto reconnect doesn't start when disabled"""
        controller.auto_reconnect = False
        
        with patch('obs_controller.obsws') as mock_ws:
            mock_ws.side_effect = ConnectionFailure("Connection refused")
            
            await controller.connect()
            
            assert controller._reconnect_task is None
    
    @pytest.mark.asyncio
    async def test_health_check_starts_on_connect(self, controller):
        """Test that health monitoring starts on successful connection"""
        controller.auto_reconnect = True
        
        with patch('obs_controller.obsws') as mock_ws:
            # Mock successful WebSocket connection
            mock_instance = MagicMock()
            mock_ws.return_value = mock_instance
            
            with patch.object(controller, '_health_monitor',
                              new_callable=AsyncMock):
                result = await controller.connect()
                
                # Should connect successfully
                assert result is True
                assert controller.status == OBSStatus.CONNECTED
                # Health check task should be created
                assert controller._health_check_task is not None


# ============================================================================
# Scene Management Tests
# ============================================================================

class TestSceneManagement:
    """Test scene management functionality"""
    
    @pytest.mark.asyncio
    async def test_get_scenes(self, connected_controller, mock_obs_response):
        """Test getting list of scenes"""
        mock_obs_response.datain = {
            'currentProgramSceneName': 'Scene 2',
            'scenes': [
                {'sceneName': 'Scene 1'},
                {'sceneName': 'Scene 2'},
                {'sceneName': 'Scene 3'}
            ]
        }
        
        connected_controller.ws.call.return_value = mock_obs_response
        
        scenes = await connected_controller.get_scenes()
        
        assert len(scenes) == 3
        assert scenes[0].name == 'Scene 1'
        assert scenes[0].is_current is False
        assert scenes[1].name == 'Scene 2'
        assert scenes[1].is_current is True
    
    @pytest.mark.asyncio
    async def test_get_scenes_not_connected(self, controller):
        """Test getting scenes when not connected"""
        scenes = await controller.get_scenes()
        
        assert scenes == []
    
    @pytest.mark.asyncio
    async def test_get_current_scene(self, connected_controller, mock_obs_response):
        """Test getting current scene"""
        mock_obs_response.datain = {
            'currentProgramSceneName': 'Main Scene'
        }
        
        connected_controller.ws.call.return_value = mock_obs_response
        
        current = await connected_controller.get_current_scene()
        
        assert current == 'Main Scene'
    
    @pytest.mark.asyncio
    async def test_switch_scene(self, connected_controller):
        """Test switching scenes"""
        result = await connected_controller.switch_scene('New Scene')
        
        assert result is True
        connected_controller.ws.call.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_switch_scene_not_connected(self, controller):
        """Test switching scene when not connected"""
        result = await controller.switch_scene('New Scene')
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_create_scene(self, connected_controller):
        """Test creating a new scene"""
        result = await connected_controller.create_scene('Test Scene')
        
        assert result is True
        connected_controller.ws.call.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_scene_error(self, connected_controller):
        """Test error handling when creating scene"""
        connected_controller.ws.call.side_effect = Exception("Creation failed")
        
        result = await connected_controller.create_scene('Test Scene')
        
        assert result is False


# ============================================================================
# Source Management Tests
# ============================================================================

class TestSourceManagement:
    """Test source visibility and slate management"""
    
    @pytest.mark.asyncio
    async def test_set_source_visibility(self, connected_controller):
        """Test setting source visibility"""
        result = await connected_controller.set_source_visibility(
            scene_name='Main',
            source_name='Slate',
            visible=True
        )
        
        assert result is True
        connected_controller.ws.call.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_slate(self, connected_controller):
        """Test showing slate scene"""
        with patch.object(connected_controller, 'switch_scene', return_value=True) as mock_switch:
            result = await connected_controller.show_slate('Technical Difficulties')
            
            assert result is True
            mock_switch.assert_called_once_with('Technical Difficulties')
    
    @pytest.mark.asyncio
    async def test_hide_slate(self, connected_controller):
        """Test hiding slate and returning to main scene"""
        with patch.object(connected_controller, 'switch_scene', return_value=True) as mock_switch:
            result = await connected_controller.hide_slate('Main Scene')
            
            assert result is True
            mock_switch.assert_called_once_with('Main Scene')


# ============================================================================
# Streaming Control Tests
# ============================================================================

class TestStreamingControl:
    """Test streaming start/stop functionality"""
    
    @pytest.mark.asyncio
    async def test_start_streaming(self, connected_controller, mock_obs_response):
        """Test starting stream"""
        mock_obs_response.datain = {'outputActive': False}
        connected_controller.ws.call.return_value = mock_obs_response
        
        result = await connected_controller.start_streaming()
        
        assert result is True
        assert connected_controller.streaming_status == StreamingStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_start_streaming_already_active(self, connected_controller, mock_obs_response):
        """Test starting stream when already streaming"""
        mock_obs_response.datain = {'outputActive': True}
        connected_controller.ws.call.return_value = mock_obs_response
        
        result = await connected_controller.start_streaming()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_start_streaming_not_connected(self, controller):
        """Test starting stream when not connected"""
        result = await controller.start_streaming()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_stop_streaming(self, connected_controller):
        """Test stopping stream"""
        connected_controller.streaming_status = StreamingStatus.ACTIVE
        
        result = await connected_controller.stop_streaming()
        
        assert result is True
        assert connected_controller.streaming_status == StreamingStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_stop_streaming_error(self, connected_controller):
        """Test error handling when stopping stream"""
        connected_controller.ws.call.side_effect = Exception("Stop failed")
        
        result = await connected_controller.stop_streaming()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_streaming_status(self, connected_controller, mock_obs_response):
        """Test getting streaming status"""
        mock_obs_response.datain = {'outputActive': True}
        connected_controller.ws.call.return_value = mock_obs_response
        
        status = await connected_controller.get_streaming_status()
        
        assert status == StreamingStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_get_stream_stats(self, connected_controller, mock_obs_response):
        """Test getting stream statistics"""
        mock_obs_response.datain = {
            'outputActive': True,
            'outputBytes': 1024000,
            'outputDuration': 30000,  # 30 seconds in ms
            'outputTotalFrames': 900,
            'outputSkippedFrames': 10
        }
        connected_controller.ws.call.return_value = mock_obs_response
        
        stats = await connected_controller.get_stream_stats()
        
        assert stats is not None
        assert stats.is_streaming is True
        assert stats.bytes_sent == 1024000
        assert stats.duration_seconds == 30
        assert stats.total_frames == 900
        assert stats.dropped_frames == 10
        assert stats.drop_percentage > 0
    
    @pytest.mark.asyncio
    async def test_stream_stats_drop_percentage(self):
        """Test drop percentage calculation"""
        stats = OBSStreamStats(
            is_streaming=True,
            bytes_sent=1000,
            duration_seconds=30,
            fps=30.0,
            render_frames=900,
            dropped_frames=9,
            total_frames=900
        )
        
        assert abs(stats.drop_percentage - 1.0) < 0.01  # ~1%


# ============================================================================
# Health & Monitoring Tests
# ============================================================================

class TestHealthMonitoring:
    """Test health monitoring and diagnostics"""
    
    @pytest.mark.asyncio
    async def test_get_health_connected(self, connected_controller, mock_obs_response):
        """Test getting health info when connected"""
        version_response = MagicMock()
        version_response.datain = {'obsVersion': '29.0.0'}
        
        stats_response = MagicMock()
        stats_response.datain = {
            'activeFps': 60.0,
            'cpuUsage': 15.5,
            'memoryUsage': 512.0
        }
        
        connected_controller.ws.call.side_effect = [version_response, stats_response]
        
        health = await connected_controller.get_health()
        
        assert health['connected'] is True
        assert health['status'] == 'connected'
        assert health['version'] == '29.0.0'
        assert health['fps'] == 60.0
        assert health['cpu_usage'] == 15.5
    
    @pytest.mark.asyncio
    async def test_get_health_not_connected(self, controller):
        """Test getting health info when not connected"""
        health = await controller.get_health()
        
        assert health['connected'] is False
        assert health['status'] == 'disconnected'
        assert health['version'] is None
    
    @pytest.mark.asyncio
    async def test_get_version(self, connected_controller, mock_obs_response):
        """Test getting OBS version"""
        mock_obs_response.datain = {'obsVersion': '29.0.2'}
        connected_controller.ws.call.return_value = mock_obs_response
        
        version = await connected_controller.get_version()
        
        assert version == '29.0.2'
    
    @pytest.mark.asyncio
    async def test_get_version_not_connected(self, controller):
        """Test getting version when not connected"""
        version = await controller.get_version()
        
        assert version is None


# ============================================================================
# Data Model Tests
# ============================================================================

class TestDataModels:
    """Test data model classes"""
    
    def test_obs_scene_info(self):
        """Test OBSSceneInfo dataclass"""
        scene = OBSSceneInfo(
            name='Test Scene',
            index=0,
            is_current=True
        )
        
        assert scene.name == 'Test Scene'
        assert scene.index == 0
        assert scene.is_current is True
    
    def test_obs_stream_stats(self):
        """Test OBSStreamStats dataclass"""
        stats = OBSStreamStats(
            is_streaming=True,
            bytes_sent=1000000,
            duration_seconds=60,
            fps=30.0,
            render_frames=1800,
            dropped_frames=0,
            total_frames=1800
        )
        
        assert stats.is_streaming is True
        assert stats.duration_seconds == 60
        assert stats.drop_percentage == 0.0
    
    def test_stream_stats_zero_frames(self):
        """Test drop percentage with zero frames"""
        stats = OBSStreamStats(
            is_streaming=False,
            bytes_sent=0,
            duration_seconds=0,
            fps=0.0,
            render_frames=0,
            dropped_frames=0,
            total_frames=0
        )
        
        assert stats.drop_percentage == 0.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_streaming_lifecycle(self, connected_controller, mock_obs_response):
        """Test complete streaming lifecycle"""
        # Setup mock responses
        mock_obs_response.datain = {
            'outputActive': False,
            'currentProgramSceneName': 'Main',
            'scenes': [{'sceneName': 'Main'}]
        }
        connected_controller.ws.call.return_value = mock_obs_response
        
        # 1. Get current scene
        scene = await connected_controller.get_current_scene()
        assert scene == 'Main'
        
        # 2. Start streaming
        result = await connected_controller.start_streaming()
        assert result is True
        
        # 3. Get streaming status
        status = await connected_controller.get_streaming_status()
        assert status in [StreamingStatus.ACTIVE, StreamingStatus.STOPPED]
        
        # 4. Stop streaming
        result = await connected_controller.stop_streaming()
        assert result is True
        
        # 5. Disconnect
        await connected_controller.disconnect()
        assert connected_controller.status == OBSStatus.DISCONNECTED
    
    @pytest.mark.asyncio
    async def test_scene_switching_workflow(self, connected_controller):
        """Test scene switching workflow"""
        # Create scene
        result = await connected_controller.create_scene('Slate')
        assert result is True
        
        # Switch to slate
        result = await connected_controller.show_slate('Slate')
        assert result is True
        
        # Switch back to main
        result = await connected_controller.hide_slate('Main')
        assert result is True
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, controller):
        """Test error recovery and resilience"""
        # Fail to connect
        with patch('obs_controller.obsws') as mock_ws:
            mock_ws.side_effect = ConnectionFailure("Connection refused")
            
            result = await controller.connect()
            assert result is False
            assert controller.status == OBSStatus.ERROR
        
        # Operations should fail gracefully
        result = await controller.start_streaming()
        assert result is False
        
        scenes = await controller.get_scenes()
        assert scenes == []


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_rapid_scene_switching(self, connected_controller):
        """Test rapid scene switching performance"""
        scenes = ['Scene1', 'Scene2', 'Scene3']
        
        for _ in range(3):  # Switch 3 times through all scenes
            for scene in scenes:
                result = await connected_controller.switch_scene(scene)
                assert result is True
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, connected_controller, mock_obs_response):
        """Test concurrent OBS operations"""
        mock_obs_response.datain = {'outputActive': False}
        connected_controller.ws.call.return_value = mock_obs_response
        
        # Run multiple operations concurrently
        tasks = [
            connected_controller.get_current_scene(),
            connected_controller.get_streaming_status(),
            connected_controller.get_health()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete without errors
        assert len(results) == 3
        assert not any(isinstance(r, Exception) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
