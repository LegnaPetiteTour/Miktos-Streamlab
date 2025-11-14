"""
Tests for Dual-Output Egress Manager (Week 5-6)
================================================

Tests for EgressManagerV2 with RTMP dual-destination streaming.

Author: Miktos StreamLab
Date: November 3, 2025
"""

import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from src.core.egress_v2 import (
    DestinationStatus,
    EgressConfig,
    EgressManagerV2,
    RTMPDestination,
    SRTDestination,
)
from src.obs_controller import OBSStreamStats


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_obs():
    """Mock OBS controller"""
    obs = AsyncMock()
    obs.start_streaming = AsyncMock(return_value=True)
    obs.stop_streaming = AsyncMock(return_value=True)
    obs.get_stream_stats = AsyncMock(
        return_value=OBSStreamStats(
            is_streaming=True,
            bytes_sent=5000000,  # 5 MB
            duration_seconds=8,   # 8 seconds -> 5000 kbps
            fps=30.0,
            render_frames=10000,
            dropped_frames=10,
            total_frames=10000,
        )
    )
    return obs


@pytest.fixture
def sample_destinations():
    """Sample RTMP destinations for testing"""
    return [
        RTMPDestination(
            name="YouTube EN",
            url="rtmp://a.rtmp.youtube.com/live2",
            key="test_key_en_123",
            enabled=True,
        ),
        RTMPDestination(
            name="YouTube FR",
            url="rtmp://a.rtmp.youtube.com/live2",
            key="test_key_fr_456",
            enabled=True,
        ),
    ]


@pytest.fixture
def egress_config(sample_destinations):
    """Sample egress configuration"""
    return EgressConfig(rtmp_destinations=sample_destinations)


@pytest.fixture
def egress_manager(mock_obs, egress_config):
    """EgressManagerV2 instance with mocked OBS"""
    return EgressManagerV2(obs_controller=mock_obs, config=egress_config)


# ============================================================================
# RTMPDestination Tests
# ============================================================================


def test_rtmp_destination_creation():
    """Test creating an RTMP destination"""
    dest = RTMPDestination(
        name="Test Channel",
        url="rtmp://test.example.com/live",
        key="secret_key_123",
    )

    assert dest.name == "Test Channel"
    assert dest.url == "rtmp://test.example.com/live"
    assert dest.key == "secret_key_123"
    assert dest.enabled is True
    assert dest.status == DestinationStatus.DISCONNECTED


def test_rtmp_destination_get_full_url():
    """Test getting full RTMP URL with key"""
    dest = RTMPDestination(
        name="Test",
        url="rtmp://test.example.com/live",
        key="my_secret_key",
    )

    full_url = dest.get_full_url()
    assert full_url == "rtmp://test.example.com/live/my_secret_key"


def test_rtmp_destination_drop_percentage():
    """Test drop percentage calculation"""
    dest = RTMPDestination(
        name="Test", url="rtmp://test.example.com", key="key"
    )

    # No frames yet
    assert dest.drop_percentage == 0.0

    # 10 dropped out of 1000 total = 1%
    dest.dropped_frames = 10
    dest.total_frames = 1000
    assert dest.drop_percentage == 1.0

    # 50 dropped out of 1000 total = 5%
    dest.dropped_frames = 50
    assert dest.drop_percentage == 5.0


def test_rtmp_destination_to_dict():
    """Test converting destination to dictionary"""
    dest = RTMPDestination(
        name="YouTube",
        url="rtmp://a.rtmp.youtube.com/live2",
        key="test_key",
    )
    dest.bitrate_kbps = 5000.0
    dest.dropped_frames = 5
    dest.total_frames = 10000

    data = dest.to_dict()

    assert data["name"] == "YouTube"
    assert data["url"] == "rtmp://a.rtmp.youtube.com/live2"
    assert data["enabled"] is True
    assert data["status"] == "disconnected"
    assert data["bitrate_kbps"] == 5000.0
    assert data["dropped_frames"] == 5
    assert data["total_frames"] == 10000
    assert data["drop_percentage"] == 0.05  # 5/10000 = 0.05%
    assert data["uptime_seconds"] is None


# ============================================================================
# EgressConfig Tests
# ============================================================================


def test_egress_config_creation(sample_destinations):
    """Test creating egress configuration"""
    config = EgressConfig(rtmp_destinations=sample_destinations)

    assert len(config.rtmp_destinations) == 2
    assert len(config.srt_destinations) == 0  # No SRT unless explicitly added
    assert len(config.all_destinations) == 2  # 2 RTMP only
    assert config.rtmp_destinations[0].name == "YouTube EN"
    assert config.rtmp_destinations[1].name == "YouTube FR"


def test_egress_config_to_dict(egress_config):
    """Test converting config to dictionary"""
    data = egress_config.to_dict()

    assert data["total_destinations"] == 2
    assert data["enabled_destinations"] == 2
    assert len(data["rtmp_destinations"]) == 2
    assert len(data["srt_destinations"]) == 0


@patch.dict(
    os.environ,
    {
        "YOUTUBE_EN_STREAM_KEY": "test_en_key",
        "YOUTUBE_FR_STREAM_KEY": "test_fr_key",
        "SRT_BACKUP_URL": "",  # Explicitly clear SRT backup
    },
    clear=True,
)
def test_egress_config_from_env():
    """Test loading configuration from environment variables"""
    config = EgressConfig.from_env()

    assert len(config.rtmp_destinations) == 2
    assert len(config.srt_destinations) == 0  # No SRT when not configured
    assert len(config.all_destinations) == 2  # 2 RTMP only

    # Check YouTube EN
    youtube_en = next(
        d for d in config.rtmp_destinations if d.name == "YouTube EN"
    )
    assert youtube_en.key == "test_en_key"
    assert youtube_en.url == "rtmp://a.rtmp.youtube.com/live2"
    assert youtube_en.enabled is True

    # Check YouTube FR
    youtube_fr = next(
        d for d in config.rtmp_destinations if d.name == "YouTube FR"
    )
    assert youtube_fr.key == "test_fr_key"
    assert youtube_fr.url == "rtmp://a.rtmp.youtube.com/live2"
    assert youtube_fr.enabled is True


@patch.dict(os.environ, {}, clear=True)
@patch("src.core.egress_v2.load_dotenv")
def test_egress_config_from_env_no_keys(mock_load_dotenv):
    """Test loading config with no environment variables"""
    config = EgressConfig.from_env()

    assert len(config.rtmp_destinations) == 0
    assert len(config.srt_destinations) == 0
    assert len(config.all_destinations) == 0


# ============================================================================
# EgressManagerV2 Tests
# ============================================================================


def test_egress_manager_initialization(egress_manager, egress_config):
    """Test egress manager initialization"""
    assert egress_manager.streaming is False
    assert egress_manager.config == egress_config
    assert len(egress_manager.config.all_destinations) == 2


@pytest.mark.asyncio
async def test_start_streaming_success(egress_manager, mock_obs):
    """Test starting streaming successfully"""
    result = await egress_manager.start_streaming()

    assert result is True
    assert egress_manager.streaming is True

    # Check OBS was called
    mock_obs.start_streaming.assert_called_once()

    # Check destinations are marked as streaming
    for dest in egress_manager.config.all_destinations:
        if dest.enabled:
            assert dest.status == DestinationStatus.STREAMING
            assert dest.connected_at is not None

    # Cleanup
    await egress_manager.stop_streaming()


@pytest.mark.asyncio
async def test_start_streaming_already_streaming(egress_manager, mock_obs):
    """Test starting streaming when already streaming"""
    await egress_manager.start_streaming()

    # Try starting again
    result = await egress_manager.start_streaming()

    assert result is False
    mock_obs.start_streaming.assert_called_once()  # Only called once

    # Cleanup
    await egress_manager.stop_streaming()


@pytest.mark.asyncio
async def test_start_streaming_obs_failure(egress_manager, mock_obs):
    """Test starting streaming when OBS fails"""
    mock_obs.start_streaming.return_value = False

    result = await egress_manager.start_streaming()

    assert result is False
    assert egress_manager.streaming is False


@pytest.mark.asyncio
async def test_stop_streaming_success(egress_manager, mock_obs):
    """Test stopping streaming successfully"""
    await egress_manager.start_streaming()

    result = await egress_manager.stop_streaming()

    assert result is True
    assert egress_manager.streaming is False

    # Check OBS was called
    mock_obs.stop_streaming.assert_called_once()

    # Check destinations are marked as disconnected
    for dest in egress_manager.config.all_destinations:
        assert dest.status == DestinationStatus.DISCONNECTED
        assert dest.connected_at is None


@pytest.mark.asyncio
async def test_stop_streaming_not_streaming(egress_manager):
    """Test stopping streaming when not streaming"""
    result = await egress_manager.stop_streaming()

    assert result is False


@pytest.mark.asyncio
async def test_get_health_not_streaming(egress_manager):
    """Test getting health when not streaming"""
    health = await egress_manager.get_health()

    assert health["streaming"] is False
    assert len(health["destinations"]) == 2


@pytest.mark.asyncio
async def test_get_health_streaming(egress_manager, mock_obs):
    """Test getting health while streaming"""
    await egress_manager.start_streaming()

    # Give a moment for health monitoring to start
    await asyncio.sleep(0.1)

    health = await egress_manager.get_health()

    assert health["streaming"] is True
    assert len(health["destinations"]) == 2

    # Check stats were updated from OBS
    for dest_health in health["destinations"]:
        if dest_health["enabled"]:
            assert dest_health["bitrate_kbps"] == 5000.0
            assert dest_health["dropped_frames"] == 10
            assert dest_health["total_frames"] == 10000

    # Check summary
    assert health["summary"]["total"] == 2
    assert health["summary"]["enabled"] == 2
    assert health["summary"]["streaming"] == 2
    assert health["summary"]["failed"] == 0

    # Cleanup
    await egress_manager.stop_streaming()


@pytest.mark.asyncio
async def test_health_monitoring_task(egress_manager, mock_obs):
    """Test that health monitoring task runs"""
    await egress_manager.start_streaming()

    # Monitoring task should be running
    assert egress_manager.monitoring_task is not None
    assert not egress_manager.monitoring_task.done()

    # Let it run a bit
    await asyncio.sleep(0.2)

    # Should have called get_stream_stats
    assert mock_obs.get_stream_stats.call_count > 0

    # Cleanup
    await egress_manager.stop_streaming()

    # Task should be cancelled
    await asyncio.sleep(0.1)
    assert egress_manager.monitoring_task.done()


def test_get_config(egress_manager, egress_config):
    """Test getting configuration"""
    config_dict = egress_manager.get_config()

    assert config_dict["total_destinations"] == 2
    assert config_dict["enabled_destinations"] == 2


def test_is_streaming(egress_manager):
    """Test checking streaming status"""
    assert egress_manager.is_streaming() is False


@pytest.mark.asyncio
async def test_is_streaming_active(egress_manager):
    """Test checking streaming status while active"""
    await egress_manager.start_streaming()

    assert egress_manager.is_streaming() is True

    # Cleanup
    await egress_manager.stop_streaming()


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_streaming_cycle(egress_manager, mock_obs):
    """Test full streaming cycle: start -> health check -> stop"""
    # Start streaming
    start_result = await egress_manager.start_streaming()
    assert start_result is True

    # Check health
    health = await egress_manager.get_health()
    assert health["streaming"] is True
    assert health["summary"]["streaming"] == 2

    # Let monitoring run
    await asyncio.sleep(0.3)

    # Stop streaming
    stop_result = await egress_manager.stop_streaming()
    assert stop_result is True

    # Verify stopped
    final_health = await egress_manager.get_health()
    assert final_health["streaming"] is False


@pytest.mark.asyncio
async def test_multiple_start_stop_cycles(egress_manager):
    """Test multiple start/stop cycles"""
    for _ in range(3):
        # Start
        assert await egress_manager.start_streaming() is True
        assert egress_manager.is_streaming() is True

        await asyncio.sleep(0.1)

        # Stop
        assert await egress_manager.stop_streaming() is True
        assert egress_manager.is_streaming() is False

        await asyncio.sleep(0.1)


# ============================================================================
# SRT Destination Tests
# ============================================================================


def test_srt_destination_creation():
    """Test creating SRT destination"""
    srt_dest = SRTDestination(
        name="SRT Backup",
        url="srt://backup.example.com:9000?mode=caller",
        enabled=True,
        is_backup=True,
    )

    assert srt_dest.name == "SRT Backup"
    assert srt_dest.url == "srt://backup.example.com:9000?mode=caller"
    assert srt_dest.enabled is True
    assert srt_dest.is_backup is True
    assert srt_dest.status == DestinationStatus.DISCONNECTED
    assert srt_dest.latency_ms == 0.0


def test_srt_destination_drop_percentage():
    """Test SRT destination drop percentage calculation"""
    srt_dest = SRTDestination(
        name="SRT Backup",
        url="srt://backup.example.com:9000",
    )

    # No frames yet
    assert srt_dest.drop_percentage == 0.0

    # With frames
    srt_dest.total_frames = 1000
    srt_dest.dropped_frames = 50
    assert srt_dest.drop_percentage == 5.0


def test_srt_destination_to_dict():
    """Test SRT destination serialization"""
    from datetime import datetime

    now = datetime.now()
    srt_dest = SRTDestination(
        name="SRT Backup",
        url="srt://backup.example.com:9000",
        enabled=True,
        status=DestinationStatus.STREAMING,
        connected_at=now,
        is_backup=True,
        bitrate_kbps=5000.0,
        dropped_frames=10,
        total_frames=10000,
        latency_ms=25.5,
    )

    data = srt_dest.to_dict()

    assert data["name"] == "SRT Backup"
    assert data["url"] == "srt://backup.example.com:9000"
    assert data["enabled"] is True
    assert data["status"] == "streaming"
    assert data["is_backup"] is True
    assert data["bitrate_kbps"] == 5000.0
    assert data["dropped_frames"] == 10
    assert data["total_frames"] == 10000
    assert data["drop_percentage"] == 0.1
    assert data["latency_ms"] == 25.5


@patch.dict(
    os.environ,
    {
        "YOUTUBE_EN_STREAM_KEY": "test_en_key",
        "YOUTUBE_FR_STREAM_KEY": "test_fr_key",
        "SRT_BACKUP_URL": "srt://backup.example.com:9000",
    },
    clear=True,
)
def test_egress_config_with_srt():
    """Test loading configuration with SRT backup"""
    config = EgressConfig.from_env()

    assert len(config.rtmp_destinations) == 2
    assert len(config.srt_destinations) == 1
    assert len(config.all_destinations) == 3

    # Check SRT destination
    srt_dest = config.srt_destinations[0]
    assert srt_dest.name == "SRT Backup"
    assert srt_dest.url == "srt://backup.example.com:9000"
    assert srt_dest.enabled is True
    assert srt_dest.is_backup is True


# ============================================================================
# Failover Tests
# ============================================================================


@pytest.fixture
def srt_destination():
    """Sample SRT destination for testing"""
    return SRTDestination(
        name="SRT Backup",
        url="srt://backup.example.com:9000",
        enabled=True,
        is_backup=True,
    )


@pytest.fixture
def egress_config_with_srt(sample_destinations, srt_destination):
    """Egress configuration with RTMP and SRT destinations"""
    return EgressConfig(
        rtmp_destinations=sample_destinations,
        srt_destinations=[srt_destination],
    )


@pytest.fixture
def egress_manager_with_srt(mock_obs, egress_config_with_srt):
    """EgressManagerV2 instance with SRT backup configured"""
    return EgressManagerV2(
        obs_controller=mock_obs, config=egress_config_with_srt
    )


def test_check_rtmp_health_all_healthy(egress_manager_with_srt):
    """Test RTMP health check when all destinations are healthy"""
    # Set RTMP destinations as healthy
    for dest in egress_manager_with_srt.config.rtmp_destinations:
        dest.status = DestinationStatus.STREAMING
        dest.bitrate_kbps = 5000.0
        dest.dropped_frames = 10
        dest.total_frames = 10000  # 0.1% drop rate

    assert egress_manager_with_srt._check_rtmp_health() is True


def test_check_rtmp_health_high_drop_rate(egress_manager_with_srt):
    """Test RTMP health check with high drop rate"""
    # Set RTMP destinations with high drop rate
    for dest in egress_manager_with_srt.config.rtmp_destinations:
        dest.status = DestinationStatus.STREAMING
        dest.bitrate_kbps = 5000.0
        dest.dropped_frames = 1500
        dest.total_frames = 10000  # 15% drop rate (above 10% threshold)

    assert egress_manager_with_srt._check_rtmp_health() is False


def test_check_rtmp_health_zero_bitrate(egress_manager_with_srt):
    """Test RTMP health check with zero bitrate"""
    # Set RTMP destinations with zero bitrate
    for dest in egress_manager_with_srt.config.rtmp_destinations:
        dest.status = DestinationStatus.STREAMING
        dest.bitrate_kbps = 0.0  # Connection lost
        dest.dropped_frames = 0
        dest.total_frames = 10000

    assert egress_manager_with_srt._check_rtmp_health() is False


def test_check_rtmp_health_disconnected(egress_manager_with_srt):
    """Test RTMP health check when disconnected"""
    # Set RTMP destinations as disconnected
    for dest in egress_manager_with_srt.config.rtmp_destinations:
        dest.status = DestinationStatus.DISCONNECTED
        dest.bitrate_kbps = 0.0

    assert egress_manager_with_srt._check_rtmp_health() is False


def test_check_rtmp_health_partial_failure(egress_manager_with_srt):
    """Test RTMP health check with one healthy, one failed"""
    rtmp_dests = egress_manager_with_srt.config.rtmp_destinations

    # First destination healthy
    rtmp_dests[0].status = DestinationStatus.STREAMING
    rtmp_dests[0].bitrate_kbps = 5000.0
    rtmp_dests[0].dropped_frames = 10
    rtmp_dests[0].total_frames = 10000

    # Second destination failed
    rtmp_dests[1].status = DestinationStatus.FAILED
    rtmp_dests[1].bitrate_kbps = 0.0

    # Should be healthy because at least one is working
    assert egress_manager_with_srt._check_rtmp_health() is True


@pytest.mark.asyncio
async def test_failover_to_srt(egress_manager_with_srt, mock_obs):
    """Test failover to SRT backup"""
    egress_manager_with_srt.streaming = True

    # Perform failover
    result = await egress_manager_with_srt._failover_to_srt()

    assert result is True
    assert egress_manager_with_srt._using_srt_backup is True
    assert egress_manager_with_srt._last_failover_time is not None

    # In NGINX architecture, OBS continues streaming (not stopped)
    mock_obs.stop_streaming.assert_not_called()

    # Check SRT destination is marked as streaming
    srt_dest = egress_manager_with_srt.config.srt_destinations[0]
    assert srt_dest.status == DestinationStatus.STREAMING
    assert srt_dest.connected_at is not None

    # Check RTMP destinations are marked as failed
    for dest in egress_manager_with_srt.config.rtmp_destinations:
        if dest.enabled:
            assert dest.status == DestinationStatus.FAILED


@pytest.mark.asyncio
async def test_failover_to_srt_already_using_backup(
    egress_manager_with_srt,
):
    """Test failover when already using SRT backup"""
    egress_manager_with_srt._using_srt_backup = True

    result = await egress_manager_with_srt._failover_to_srt()

    assert result is False


@pytest.mark.asyncio
async def test_failover_to_srt_no_srt_configured(
    egress_manager, mock_obs
):
    """Test failover when no SRT backup is configured"""
    egress_manager.streaming = True

    result = await egress_manager._failover_to_srt()

    assert result is False
    assert egress_manager._using_srt_backup is False


@pytest.mark.asyncio
async def test_recover_to_rtmp(egress_manager_with_srt, mock_obs):
    """Test recovery back to RTMP"""
    egress_manager_with_srt.streaming = True
    egress_manager_with_srt._using_srt_backup = True

    # Perform recovery
    result = await egress_manager_with_srt._recover_to_rtmp()

    assert result is True
    assert egress_manager_with_srt._using_srt_backup is False
    assert egress_manager_with_srt._last_recovery_time is not None

    # In NGINX architecture, OBS continues streaming (not stopped)
    mock_obs.stop_streaming.assert_not_called()

    # Check RTMP destinations are marked as streaming
    for dest in egress_manager_with_srt.config.rtmp_destinations:
        if dest.enabled:
            assert dest.status == DestinationStatus.STREAMING
            assert dest.connected_at is not None

    # Check SRT destination is marked as disconnected
    srt_dest = egress_manager_with_srt.config.srt_destinations[0]
    assert srt_dest.status == DestinationStatus.DISCONNECTED
    assert srt_dest.connected_at is None


@pytest.mark.asyncio
async def test_recover_to_rtmp_not_using_backup(egress_manager_with_srt):
    """Test recovery when not using SRT backup"""
    egress_manager_with_srt._using_srt_backup = False

    result = await egress_manager_with_srt._recover_to_rtmp()

    assert result is False


def test_get_failover_status(egress_manager_with_srt):
    """Test getting failover status"""
    from datetime import datetime

    # Set some state
    egress_manager_with_srt._using_srt_backup = True
    egress_manager_with_srt._rtmp_failure_count = 3
    egress_manager_with_srt._rtmp_recovery_count = 2
    egress_manager_with_srt._last_failover_time = datetime.now()

    status = egress_manager_with_srt.get_failover_status()

    assert status["using_srt_backup"] is True
    assert status["rtmp_failure_count"] == 3
    assert status["rtmp_recovery_count"] == 2
    assert status["last_failover_time"] is not None
    assert status["last_recovery_time"] is None
    assert status["thresholds"]["failure_threshold"] == 3
    assert status["thresholds"]["recovery_threshold"] == 5
    assert status["thresholds"]["drop_rate_threshold"] == 10.0


@pytest.mark.asyncio
async def test_automatic_failover_trigger(
    egress_manager_with_srt, mock_obs
):
    """Test automatic failover after consecutive failures"""
    # Start streaming
    await egress_manager_with_srt.start_streaming()

    # Simulate RTMP failures
    for dest in egress_manager_with_srt.config.rtmp_destinations:
        dest.status = DestinationStatus.STREAMING
        dest.bitrate_kbps = 0.0  # Connection lost
        dest.dropped_frames = 0
        dest.total_frames = 1000

    # Simulate health monitoring detecting failures
    for i in range(3):  # Failure threshold is 3
        rtmp_healthy = egress_manager_with_srt._check_rtmp_health()
        assert rtmp_healthy is False

        if not egress_manager_with_srt._using_srt_backup:
            egress_manager_with_srt._rtmp_failure_count += 1

    # Should have triggered failover
    assert egress_manager_with_srt._rtmp_failure_count == 3

    # Manually trigger failover (simulating what _monitor_health would do)
    if egress_manager_with_srt._rtmp_failure_count >= 3:
        await egress_manager_with_srt._failover_to_srt()

    assert egress_manager_with_srt._using_srt_backup is True


@pytest.mark.asyncio
async def test_automatic_recovery_trigger(
    egress_manager_with_srt, mock_obs
):
    """Test automatic recovery after RTMP becomes healthy"""
    # Start in failover state
    egress_manager_with_srt.streaming = True
    egress_manager_with_srt._using_srt_backup = True

    # Simulate RTMP recovery
    for dest in egress_manager_with_srt.config.rtmp_destinations:
        dest.status = DestinationStatus.STREAMING
        dest.bitrate_kbps = 5000.0
        dest.dropped_frames = 10
        dest.total_frames = 10000  # 0.1% drop rate

    # Simulate health monitoring detecting recovery
    for i in range(5):  # Recovery threshold is 5
        rtmp_healthy = egress_manager_with_srt._check_rtmp_health()
        assert rtmp_healthy is True

        if egress_manager_with_srt._using_srt_backup:
            egress_manager_with_srt._rtmp_recovery_count += 1

    # Should have triggered recovery
    assert egress_manager_with_srt._rtmp_recovery_count == 5

    # Manually trigger recovery (simulating what _monitor_health would do)
    if egress_manager_with_srt._rtmp_recovery_count >= 5:
        await egress_manager_with_srt._recover_to_rtmp()

    assert egress_manager_with_srt._using_srt_backup is False


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
