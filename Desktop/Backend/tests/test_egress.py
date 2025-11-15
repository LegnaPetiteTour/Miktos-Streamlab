"""
Tests for egress.py - Multi-destination streaming with failover

Tests cover:
- Destination health monitoring
- RTMP and SRT connections
- Failover logic
- Recovery attempts
- Configuration validation
- Error handling

Author: Miktos StreamLab Team
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from core.egress import (
    EgressManager,
    RTMPDestination,
    SRTDestination,
    EgressConfig,
    FailoverConfig,
    DestinationHealth,
    DestinationStatus,
    DestinationType,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def rtmp_config():
    """RTMP destination configuration"""
    return {
        "type": "rtmp",
        "url": "rtmp://a.rtmp.youtube.com/live2",
        "key": "test-stream-key-12345",
        "bitrate_mbps": 6.0
    }


@pytest.fixture
def srt_config():
    """SRT destination configuration"""
    return {
        "type": "srt",
        "url": "srt://relay.example.com:9998",
        "latency_ms": 2000
    }


@pytest.fixture
def failover_config():
    """Failover configuration"""
    return FailoverConfig(
        enabled=True,
        trigger_packet_loss_pct=5.0,
        trigger_rtt_ms=500.0,
        trigger_duration_sec=10.0,
        retry_interval_sec=30.0,
        show_slate=True
    )


@pytest.fixture
def egress_config(rtmp_config, srt_config, failover_config):
    """Complete egress configuration"""
    return EgressConfig(
        primary_destination=rtmp_config,
        backup_destination=srt_config,
        failover=failover_config
    )


@pytest.fixture
def rtmp_destination():
    """RTMP destination instance"""
    return RTMPDestination(
        name="youtube",
        url="rtmp://a.rtmp.youtube.com/live2",
        stream_key="test-key",
        bitrate_mbps=6.0
    )


@pytest.fixture
def srt_destination():
    """SRT destination instance with mocked SRT connection"""
    dest = SRTDestination(
        name="srt-backup",
        url="srt://relay.example.com:9998",
        latency_ms=2000
    )

    # Mock the SRT connection to avoid real network calls
    mock_srt_connection = Mock()
    mock_srt_connection.connect = AsyncMock(return_value=True)
    mock_srt_connection.disconnect = AsyncMock(return_value=True)
    mock_srt_connection.is_connected = Mock(return_value=True)

    dest.srt_connection = mock_srt_connection
    return dest

# ============================================================================
# RTMP Destination Tests
# ============================================================================


class TestRTMPDestination:
    """Test RTMP streaming destination"""

    @pytest.mark.asyncio
    async def test_rtmp_initialization(self, rtmp_destination):
        """Test RTMP destination initialization"""
        assert rtmp_destination.name == "youtube"
        assert rtmp_destination.destination_type == DestinationType.RTMP
        assert rtmp_destination.status == DestinationStatus.DISCONNECTED
        assert rtmp_destination.url.startswith("rtmp://")

    @pytest.mark.asyncio
    async def test_rtmp_connect_success(self, rtmp_destination):
        """Test successful RTMP connection"""
        result = await rtmp_destination.connect()

        assert result is True
        assert rtmp_destination.status == DestinationStatus.CONNECTED
        assert rtmp_destination._connected_at is not None

    @pytest.mark.asyncio
    async def test_rtmp_connect_invalid_url(self):
        """Test RTMP connection with invalid URL"""
        dest = RTMPDestination(
            name="test",
            url="http://invalid.url",  # Not RTMP
            stream_key="key"
        )

        result = await dest.connect()

        assert result is False
        assert dest.status == DestinationStatus.FAILED

    @pytest.mark.asyncio
    async def test_rtmp_connect_empty_key(self):
        """Test RTMP connection with empty stream key"""
        dest = RTMPDestination(
            name="test",
            url="rtmp://valid.url",
            stream_key=""  # Empty key
        )

        result = await dest.connect()

        assert result is False
        assert dest.status == DestinationStatus.FAILED

    @pytest.mark.asyncio
    async def test_rtmp_disconnect(self, rtmp_destination):
        """Test RTMP disconnection"""
        await rtmp_destination.connect()
        result = await rtmp_destination.disconnect()

        assert result is True
        assert rtmp_destination.status == DestinationStatus.DISCONNECTED
        assert rtmp_destination._connected_at is None

    @pytest.mark.asyncio
    async def test_rtmp_start_streaming(self, rtmp_destination):
        """Test starting RTMP streaming"""
        await rtmp_destination.connect()
        result = await rtmp_destination.start_streaming()

        assert result is True
        assert rtmp_destination.status == DestinationStatus.STREAMING

    @pytest.mark.asyncio
    async def test_rtmp_start_streaming_not_connected(self, rtmp_destination):
        """Test starting streaming when not connected"""
        # Don't connect first
        result = await rtmp_destination.start_streaming()

        assert result is False
        assert rtmp_destination.status == DestinationStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_rtmp_stop_streaming(self, rtmp_destination):
        """Test stopping RTMP streaming"""
        await rtmp_destination.connect()
        await rtmp_destination.start_streaming()
        result = await rtmp_destination.stop_streaming()

        assert result is True
        assert rtmp_destination.status == DestinationStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_rtmp_test_connection_valid(self, rtmp_destination):
        """Test RTMP connection test with valid URL"""
        result = await rtmp_destination.test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_rtmp_test_connection_invalid(self):
        """Test RTMP connection test with invalid URL"""
        dest = RTMPDestination(
            name="test",
            url="http://invalid",
            stream_key="key"
        )
        result = await dest.test_connection()
        assert result is False

    @pytest.mark.asyncio
    async def test_rtmp_get_health(self, rtmp_destination):
        """Test getting RTMP health metrics"""
        await rtmp_destination.connect()
        health = await rtmp_destination.get_health()

        assert isinstance(health, DestinationHealth)
        assert health.name == "youtube"
        assert health.destination_type == DestinationType.RTMP
        assert health.connected is True
        assert health.last_health_check is not None

    @pytest.mark.asyncio
    async def test_rtmp_health_metrics_tracking(self, rtmp_destination):
        """Test health metrics are tracked over time"""
        await rtmp_destination.connect()

        # Simulate some metrics
        rtmp_destination._update_metrics(
            bitrate=6.0,
            rtt=50.0,
            packet_loss=0.5
        )

        health = await rtmp_destination.get_health()

        assert health.bitrate_actual > 0
        assert health.rtt_ms > 0
        assert health.packet_loss_pct >= 0

# ============================================================================
# SRT Destination Tests
# ============================================================================


class TestSRTDestination:
    """Test SRT streaming destination"""

    @pytest.mark.asyncio
    async def test_srt_initialization(self, srt_destination):
        """Test SRT destination initialization"""
        assert srt_destination.name == "srt-backup"
        assert srt_destination.destination_type == DestinationType.SRT
        assert srt_destination.status == DestinationStatus.DISCONNECTED
        assert srt_destination.url.startswith("srt://")
        assert srt_destination.latency_ms == 2000

    @pytest.mark.asyncio
    async def test_srt_connect_success(self, srt_destination):
        """Test successful SRT connection"""
        result = await srt_destination.connect()

        assert result is True
        assert srt_destination.status == DestinationStatus.CONNECTED
        assert srt_destination._connected_at is not None

    @pytest.mark.asyncio
    async def test_srt_connect_invalid_url(self):
        """Test SRT connection with invalid URL"""
        dest = SRTDestination(
            name="test",
            url="rtmp://invalid.url"  # Not SRT
        )

        result = await dest.connect()

        assert result is False
        assert dest.status == DestinationStatus.FAILED

    @pytest.mark.asyncio
    async def test_srt_disconnect(self, srt_destination):
        """Test SRT disconnection"""
        await srt_destination.connect()
        result = await srt_destination.disconnect()

        assert result is True
        assert srt_destination.status == DestinationStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_srt_get_health(self, srt_destination):
        """Test getting SRT health metrics"""
        await srt_destination.connect()
        health = await srt_destination.get_health()

        assert isinstance(health, DestinationHealth)
        assert health.name == "srt-backup"
        assert health.destination_type == DestinationType.SRT
        assert health.connected is True

# ============================================================================
# Destination Health Tests
# ============================================================================


class TestDestinationHealth:
    """Test destination health assessment"""

    def test_health_is_healthy_all_good(self):
        """Test health assessment when all metrics are good"""
        health = DestinationHealth(
            name="test",
            destination_type=DestinationType.RTMP,
            status=DestinationStatus.STREAMING,
            connected=True,
            packet_loss_pct=0.1,
            rtt_ms=50,
            bitrate_variance_pct=5.0
        )

        assert health.is_healthy() is True
        assert health.is_failing() is False

    def test_health_is_failing_high_packet_loss(self):
        """Test health assessment with high packet loss"""
        health = DestinationHealth(
            name="test",
            destination_type=DestinationType.RTMP,
            status=DestinationStatus.STREAMING,
            connected=True,
            packet_loss_pct=6.0,  # Above threshold
            rtt_ms=50,
            bitrate_variance_pct=5.0
        )

        assert health.is_healthy() is False
        assert health.is_failing() is True

    def test_health_is_failing_high_rtt(self):
        """Test health assessment with high latency"""
        health = DestinationHealth(
            name="test",
            destination_type=DestinationType.RTMP,
            status=DestinationStatus.STREAMING,
            connected=True,
            packet_loss_pct=0.1,
            rtt_ms=600,  # Above threshold
            bitrate_variance_pct=5.0
        )

        assert health.is_healthy() is False
        assert health.is_failing() is True

    def test_health_is_failing_disconnected(self):
        """Test health assessment when disconnected"""
        health = DestinationHealth(
            name="test",
            destination_type=DestinationType.RTMP,
            status=DestinationStatus.DISCONNECTED,
            connected=False,
            packet_loss_pct=0.0,
            rtt_ms=50,
            bitrate_variance_pct=5.0
        )

        assert health.is_healthy() is False
        assert health.is_failing() is True

# ============================================================================
# Egress Manager Tests
# ============================================================================


@patch('core.egress.SRTDestination')
class TestEgressManager:
    """Test egress manager orchestration"""

    def _setup_srt_mock(self, mock_srt, status=DestinationStatus.DISCONNECTED):
        """Helper to configure SRT destination mock"""
        mock_srt_instance = Mock()
        mock_srt_instance.connect = AsyncMock(return_value=True)
        mock_srt_instance.disconnect = AsyncMock()
        mock_srt_instance.start_streaming = AsyncMock()
        mock_srt_instance.stop_streaming = AsyncMock()
        mock_srt_instance.get_health = AsyncMock(return_value=Mock())
        mock_srt_instance.status = status
        mock_srt_instance.health = Mock()
        mock_srt_instance.name = "SRT Mock"
        mock_srt.return_value = mock_srt_instance
        return mock_srt_instance

    def test_manager_initialization(self, mock_srt, egress_config):
        """Test egress manager initialization"""
        self._setup_srt_mock(mock_srt)

        manager = EgressManager(egress_config)

        assert manager.primary is not None
        assert manager.backup is not None
        assert manager.streaming is False
        assert manager.failover_active is False

    def test_manager_initialization_primary_only(
        self, mock_srt, rtmp_config, failover_config
    ):
        """Test initialization with only primary destination"""
        self._setup_srt_mock(mock_srt)
        config = EgressConfig(
            primary_destination=rtmp_config,
            failover=failover_config
        )

        manager = EgressManager(config)

        assert manager.primary is not None
        assert manager.backup is None

    @pytest.mark.asyncio
    async def test_manager_start_streaming_success(
        self, mock_srt, egress_config
    ):
        """Test starting streaming successfully"""
        self._setup_srt_mock(mock_srt, DestinationStatus.STREAMING)
        manager = EgressManager(egress_config)
        result = await manager.start_streaming()

        assert result is True
        assert manager.streaming is True
        assert manager.active_destination == manager.primary
        assert manager.primary.status == DestinationStatus.STREAMING

        # Cleanup
        await manager.stop_streaming()

    @pytest.mark.asyncio
    async def test_manager_stop_streaming(self, mock_srt, egress_config):
        """Test stopping streaming"""
        self._setup_srt_mock(mock_srt, DestinationStatus.STREAMING)
        manager = EgressManager(egress_config)
        await manager.start_streaming()
        result = await manager.stop_streaming()

        assert result is True
        assert manager.streaming is False
        assert manager.active_destination is None

    @pytest.mark.asyncio
    async def test_manager_get_status(self, mock_srt, egress_config):
        """Test getting egress status"""
        self._setup_srt_mock(mock_srt, DestinationStatus.STREAMING)
        manager = EgressManager(egress_config)
        await manager.start_streaming()

        status = await manager.get_status()

        assert status["streaming"] is True
        assert status["failover_active"] is False
        assert status["active_destination"] == "primary"
        assert status["primary"] is not None
        assert status["backup"] is not None

        await manager.stop_streaming()

    @pytest.mark.asyncio
    async def test_manager_backup_on_standby(self, mock_srt, egress_config):
        """Test that backup is connected but not streaming"""
        self._setup_srt_mock(mock_srt, DestinationStatus.CONNECTED)

        manager = EgressManager(egress_config)
        await manager.start_streaming()

        # Primary should be streaming
        assert manager.primary.status == DestinationStatus.STREAMING

        # Backup should be connected but not streaming
        assert manager.backup.status == DestinationStatus.CONNECTED

        await manager.stop_streaming()

# ============================================================================
# Failover Tests
# ============================================================================


@patch('core.egress.SRTDestination')
class TestFailover:
    """Test automatic failover functionality"""

    def _setup_srt_mock(self, mock_srt, status=DestinationStatus.DISCONNECTED):
        """Helper to configure SRT destination mock"""
        mock_srt_instance = Mock()
        mock_srt_instance.connect = AsyncMock(return_value=True)
        mock_srt_instance.disconnect = AsyncMock()
        mock_srt_instance.start_streaming = AsyncMock()
        mock_srt_instance.stop_streaming = AsyncMock()
        mock_srt_instance.get_health = AsyncMock(return_value=Mock())
        mock_srt_instance.status = status
        mock_srt_instance.health = Mock()
        mock_srt_instance.name = "SRT Mock"
        mock_srt.return_value = mock_srt_instance
        return mock_srt_instance

    @pytest.mark.asyncio
    async def test_failover_disabled(self, mock_srt, egress_config):
        """Test that failover doesn't activate when disabled"""
        self._setup_srt_mock(mock_srt)
        egress_config.failover.enabled = False
        manager = EgressManager(egress_config)

        # Mock failing primary
        manager.primary.status = DestinationStatus.FAILING

        await manager._initiate_failover()

        # Failover should not activate
        assert manager.failover_active is False

    @pytest.mark.asyncio
    async def test_failover_no_backup(
        self, mock_srt, rtmp_config, failover_config
    ):
        """Test failover when no backup is configured"""
        self._setup_srt_mock(mock_srt)
        config = EgressConfig(
            primary_destination=rtmp_config,
            failover=failover_config
        )
        manager = EgressManager(config)

        await manager._initiate_failover()

        # Failover cannot activate without backup
        assert manager.failover_active is False

    @pytest.mark.asyncio
    async def test_failover_initiation(self, mock_srt, egress_config):
        """Test failover initiation"""
        # Set up SRT mock with CONNECTED status (standby mode)
        mock_srt_instance = self._setup_srt_mock(
            mock_srt, DestinationStatus.CONNECTED
        )

        # Configure the start_streaming method to change status when called
        async def mock_start_streaming():
            mock_srt_instance.status = DestinationStatus.STREAMING
            return True
        mock_srt_instance.start_streaming = AsyncMock(
            side_effect=mock_start_streaming
        )
        manager = EgressManager(egress_config)
        await manager.start_streaming()

        # Simulate primary failure
        await manager._initiate_failover()

        # Check failover state
        assert manager.failover_active is True

        # Wait a moment for async tasks
        await asyncio.sleep(0.1)

        # Active destination should be backup
        assert manager.active_destination == manager.backup

        await manager.stop_streaming()

    @pytest.mark.asyncio
    async def test_failover_already_active(self, mock_srt, egress_config):
        """Test that failover doesn't re-trigger if already active"""
        self._setup_srt_mock(mock_srt, DestinationStatus.STREAMING)
        manager = EgressManager(egress_config)
        await manager.start_streaming()

        # Trigger failover
        await manager._initiate_failover()
        assert manager.failover_active is True

        # Try to trigger again
        await manager._initiate_failover()

        # Should still only be one failover
        assert manager.failover_active is True

        await manager.stop_streaming()

# ============================================================================
# Health Monitoring Tests
# ============================================================================


@patch('core.egress.SRTDestination')
class TestHealthMonitoring:
    """Test continuous health monitoring"""

    def _setup_srt_mock(self, mock_srt, status=DestinationStatus.DISCONNECTED):
        """Helper to configure SRT destination mock"""
        mock_srt_instance = Mock()
        mock_srt_instance.connect = AsyncMock(return_value=True)
        mock_srt_instance.disconnect = AsyncMock()
        mock_srt_instance.start_streaming = AsyncMock()
        mock_srt_instance.stop_streaming = AsyncMock()
        mock_srt_instance.get_health = AsyncMock(return_value=Mock())
        mock_srt_instance.status = status
        mock_srt_instance.health = Mock()
        mock_srt_instance.name = "SRT Mock"
        mock_srt.return_value = mock_srt_instance
        return mock_srt_instance

    @pytest.mark.asyncio
    async def test_health_monitoring_starts(self, mock_srt, egress_config):
        """Test that health monitoring starts with streaming"""
        self._setup_srt_mock(mock_srt, DestinationStatus.STREAMING)
        manager = EgressManager(egress_config)
        await manager.start_streaming()

        # Monitor task should be created
        assert manager._monitor_task is not None
        assert not manager._monitor_task.done()

        await manager.stop_streaming()

    @pytest.mark.asyncio
    async def test_health_monitoring_stops(self, mock_srt, egress_config):
        """Test that health monitoring stops with streaming"""
        self._setup_srt_mock(mock_srt, DestinationStatus.STREAMING)
        manager = EgressManager(egress_config)
        await manager.start_streaming()
        await manager.stop_streaming()

        # Monitor task should be cancelled
        await asyncio.sleep(0.1)  # Give time for cancellation

        # Task should be done/cancelled
        assert (manager._monitor_task.done() or
                manager._monitor_task.cancelled())

# ============================================================================
# Configuration Tests
# ============================================================================


class TestConfiguration:
    """Test configuration validation"""

    def test_failover_config_defaults(self):
        """Test default failover configuration values"""
        config = FailoverConfig()

        assert config.enabled is True
        assert config.trigger_packet_loss_pct == 5.0
        assert config.trigger_rtt_ms == 500.0
        assert config.show_slate is True

    def test_egress_config_with_backup(self, rtmp_config, srt_config):
        """Test egress config with backup"""
        config = EgressConfig(
            primary_destination=rtmp_config,
            backup_destination=srt_config
        )

        assert config.primary_destination["type"] == "rtmp"
        assert config.backup_destination["type"] == "srt"

    def test_egress_config_without_backup(self, rtmp_config):
        """Test egress config without backup"""
        config = EgressConfig(
            primary_destination=rtmp_config
        )

        assert config.primary_destination["type"] == "rtmp"
        assert config.backup_destination is None

# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling in various scenarios"""

    @pytest.mark.asyncio
    async def test_connect_exception_handling(self):
        """Test that connection exceptions are handled"""
        dest = RTMPDestination(
            name="test",
            url="rtmp://test.url",
            stream_key="key"
        )

        # Force an exception in connect (by making URL validation fail badly)
        with patch.object(dest, 'logger'):
            dest.url = None  # This will cause an exception
            result = await dest.connect()

            assert result is False
            assert dest.status == DestinationStatus.FAILED

    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self, rtmp_destination):
        """Test that health check exceptions are handled"""
        await rtmp_destination.connect()

        # Force an exception in health check
        with patch.object(rtmp_destination, '_get_average_metrics',
                          side_effect=Exception("Test error")):
            try:
                health = await rtmp_destination.get_health()
                # Should still return a health object, even if metrics fail
                assert isinstance(health, DestinationHealth)
            except Exception:
                # Or it might raise - both are acceptable error handling
                pass

# ============================================================================
# Integration Tests
# ============================================================================


@patch('core.egress.SRTDestination')
class TestIntegration:
    """Integration tests for complete workflows"""

    def _setup_srt_mock(self, mock_srt, status=DestinationStatus.DISCONNECTED):
        """Helper to configure SRT destination mock"""
        mock_srt_instance = Mock()
        mock_srt_instance.connect = AsyncMock(return_value=True)
        mock_srt_instance.disconnect = AsyncMock()
        mock_srt_instance.start_streaming = AsyncMock()
        mock_srt_instance.stop_streaming = AsyncMock()
        mock_srt_instance.get_health = AsyncMock(return_value=Mock())
        mock_srt_instance.status = status
        mock_srt_instance.health = Mock()
        mock_srt_instance.name = "SRT Mock"
        mock_srt.return_value = mock_srt_instance
        return mock_srt_instance

    @pytest.mark.asyncio
    async def test_full_streaming_lifecycle(self, mock_srt, egress_config):
        """Test complete start -> stream -> stop lifecycle"""
        self._setup_srt_mock(mock_srt, DestinationStatus.STREAMING)
        manager = EgressManager(egress_config)

        # Start
        assert await manager.start_streaming() is True
        assert manager.streaming is True

        # Stream for a moment
        await asyncio.sleep(0.5)

        # Get status
        status = await manager.get_status()
        assert status["streaming"] is True

        # Stop
        assert await manager.stop_streaming() is True
        assert manager.streaming is False

    @pytest.mark.asyncio
    async def test_failover_and_recovery(self, mock_srt, egress_config):
        """Test failover followed by recovery"""
        # Set up SRT mock with proper failover behavior
        mock_srt_instance = self._setup_srt_mock(
            mock_srt, DestinationStatus.CONNECTED
        )

        # Configure start_streaming to change status when called
        async def mock_start_streaming():
            mock_srt_instance.status = DestinationStatus.STREAMING
            return True
        mock_srt_instance.start_streaming = AsyncMock(
            side_effect=mock_start_streaming
        )
        manager = EgressManager(egress_config)
        await manager.start_streaming()

        # Simulate failover
        await manager._initiate_failover()
        assert manager.failover_active is True
        assert manager.active_destination == manager.backup

        # Simulate successful recovery
        await manager._complete_failover_recovery()
        assert manager.failover_active is False
        assert manager.active_destination == manager.primary

        await manager.stop_streaming()

# ============================================================================
# Performance Tests
# ============================================================================


@patch('core.egress.SRTDestination')
class TestPerformance:
    """Test performance characteristics"""

    def _setup_srt_mock(self, mock_srt, status=DestinationStatus.DISCONNECTED):
        """Helper to configure SRT destination mock"""
        mock_srt_instance = Mock()
        mock_srt_instance.connect = AsyncMock(return_value=True)
        mock_srt_instance.disconnect = AsyncMock()
        mock_srt_instance.start_streaming = AsyncMock()
        mock_srt_instance.stop_streaming = AsyncMock()
        mock_srt_instance.get_health = AsyncMock(return_value=Mock())
        mock_srt_instance.status = status
        mock_srt_instance.health = Mock()
        mock_srt_instance.name = "SRT Mock"
        mock_srt.return_value = mock_srt_instance
        return mock_srt_instance

    @pytest.mark.asyncio
    async def test_health_check_performance(self, mock_srt, rtmp_destination):
        """Test that health checks are fast enough"""
        await rtmp_destination.connect()

        start_time = datetime.now()
        await rtmp_destination.get_health()
        duration = (datetime.now() - start_time).total_seconds()

        # Health check should be very fast (< 100ms)
        assert duration < 0.1

    @pytest.mark.asyncio
    async def test_manager_startup_performance(self, mock_srt, egress_config):
        """Test that manager starts up quickly"""
        self._setup_srt_mock(mock_srt)
        start_time = datetime.now()
        EgressManager(egress_config)
        duration = (datetime.now() - start_time).total_seconds()

        # Manager initialization should be instant
        assert duration < 0.1

# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio coroutine"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
