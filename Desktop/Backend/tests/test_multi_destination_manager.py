"""
Tests for Multi-Destination Broadcast Manager
"""

import pytest
from typing import Optional

from core.multi_destination_manager import MultiDestinationManager
from core.streaming_platform import (
    StreamingPlatform,
    PlatformConfig,
    StreamHealth,
    StreamMetrics
)


class MockPlatform(StreamingPlatform):
    """Mock streaming platform for testing"""

    def __init__(self, name: str, config: PlatformConfig):
        super().__init__(config)
        self.name = name
        self._authenticated = False
        self._streaming = False

    async def authenticate(self) -> bool:
        self._authenticated = True
        self._is_authenticated = True
        return True

    async def start_stream(
        self,
        title: str,
        description: str = "",
        category: str = "",
        **kwargs
    ) -> bool:
        if not self._authenticated:
            return False
        self._streaming = True
        return True

    async def stop_stream(self) -> bool:
        self._streaming = False
        return True

    async def get_stream_health(self) -> StreamHealth:
        return StreamHealth.GOOD if self._streaming else StreamHealth.UNKNOWN

    async def get_metrics(self) -> StreamMetrics:
        return StreamMetrics(
            viewer_count=100,
            uptime_seconds=300
        )

    async def update_stream_info(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> bool:
        return True

    async def close(self) -> None:
        pass


@pytest.fixture
def manager():
    """Multi-destination manager instance"""
    return MultiDestinationManager()


@pytest.fixture
def mock_platforms():
    """Create mock platforms"""
    youtube_config = PlatformConfig(
        platform_name="YouTube",
        stream_key="yt-key",
        rtmp_url="rtmp://youtube.com",
        enabled=True
    )

    facebook_config = PlatformConfig(
        platform_name="Facebook",
        stream_key="fb-key",
        rtmp_url="rtmps://facebook.com",
        enabled=True
    )

    twitter_config = PlatformConfig(
        platform_name="Twitter",
        stream_key="tw-key",
        rtmp_url="rtmp://twitter.com",
        enabled=True
    )

    return {
        'youtube': MockPlatform('YouTube', youtube_config),
        'facebook': MockPlatform('Facebook', facebook_config),
        'twitter': MockPlatform('Twitter', twitter_config)
    }


class TestManagerInitialization:
    """Test multi-destination manager initialization"""

    def test_initialization(self, manager):
        """Test manager initialization"""
        assert len(manager.platforms) == 0
        assert len(manager.platform_status) == 0
        assert not manager.is_streaming()

    def test_add_platform(self, manager, mock_platforms):
        """Test adding platforms"""
        manager.add_platform('youtube', mock_platforms['youtube'])

        assert 'youtube' in manager.platforms
        assert 'youtube' in manager.platform_status
        assert len(manager.get_platforms()) == 1

    def test_add_multiple_platforms(self, manager, mock_platforms):
        """Test adding multiple platforms"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        assert len(manager.platforms) == 3
        assert set(manager.get_platforms()) == {'youtube', 'facebook', 'twitter'}

    def test_remove_platform(self, manager, mock_platforms):
        """Test removing a platform"""
        manager.add_platform('youtube', mock_platforms['youtube'])

        result = manager.remove_platform('youtube')

        assert result is True
        assert 'youtube' not in manager.platforms
        assert len(manager.platforms) == 0

    def test_remove_nonexistent_platform(self, manager):
        """Test removing platform that doesn't exist"""
        result = manager.remove_platform('nonexistent')
        assert result is False


class TestAuthentication:
    """Test platform authentication"""

    @pytest.mark.asyncio
    async def test_authenticate_all_success(self, manager, mock_platforms):
        """Test successful authentication of all platforms"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        results = await manager.authenticate_all()

        assert len(results) == 3
        assert all(results.values())
        assert all(p.is_authenticated() for p in mock_platforms.values())

    @pytest.mark.asyncio
    async def test_authenticate_all_partial_failure(self, manager):
        """Test authentication with some failures"""
        # Create platforms with different auth behaviors
        good_config = PlatformConfig(
            platform_name="Good",
            stream_key="key",
            rtmp_url="rtmp://good.com",
            enabled=True
        )

        good_platform = MockPlatform('Good', good_config)
        bad_platform = MockPlatform('Bad', good_config)

        # Make bad platform fail auth
        async def fail_auth():
            return False
        bad_platform.authenticate = fail_auth

        manager.add_platform('good', good_platform)
        manager.add_platform('bad', bad_platform)

        results = await manager.authenticate_all()

        assert results['good'] is True
        assert results['bad'] is False


class TestStreamControl:
    """Test stream start/stop operations"""

    @pytest.mark.asyncio
    async def test_start_all_not_authenticated(self, manager, mock_platforms):
        """Test starting streams without authentication"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        results = await manager.start_all("Test Stream")

        # Should fail because not authenticated
        assert all(not v for v in results.values())
        assert not manager.is_streaming()

    @pytest.mark.asyncio
    async def test_start_all_success(self, manager, mock_platforms):
        """Test successful stream start on all platforms"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        results = await manager.start_all(
            "Test Stream",
            "Test Description"
        )

        assert len(results) == 3
        assert all(results.values())
        assert manager.is_streaming()
        assert len(manager.get_active_platforms()) == 3

    @pytest.mark.asyncio
    async def test_stop_all_success(self, manager, mock_platforms):
        """Test successful stream stop on all platforms"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        results = await manager.stop_all()

        assert len(results) == 3
        assert all(results.values())
        assert not manager.is_streaming()
        assert len(manager.get_active_platforms()) == 0

    @pytest.mark.asyncio
    async def test_stop_specific_platform(self, manager, mock_platforms):
        """Test stopping a specific platform"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        result = await manager.stop_platform('youtube')

        assert result is True
        assert 'youtube' not in manager.get_active_platforms()
        assert 'facebook' in manager.get_active_platforms()
        assert 'twitter' in manager.get_active_platforms()
        assert manager.is_streaming()  # Still streaming on other platforms

    @pytest.mark.asyncio
    async def test_stop_last_platform(self, manager, mock_platforms):
        """Test stopping the last active platform"""
        manager.add_platform('youtube', mock_platforms['youtube'])

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        result = await manager.stop_platform('youtube')

        assert result is True
        assert not manager.is_streaming()


class TestStatusMonitoring:
    """Test platform status monitoring"""

    @pytest.mark.asyncio
    async def test_get_platform_status(self, manager, mock_platforms):
        """Test getting status for a specific platform"""
        manager.add_platform('youtube', mock_platforms['youtube'])

        status = manager.get_platform_status('youtube')

        assert status is not None
        assert status.platform_name == 'youtube'
        assert not status.is_active
        assert status.status.value == 'idle'

    @pytest.mark.asyncio
    async def test_get_all_status(self, manager, mock_platforms):
        """Test getting status for all platforms"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        all_status = manager.get_all_status()

        assert len(all_status) == 3
        assert 'youtube' in all_status
        assert 'facebook' in all_status
        assert 'twitter' in all_status

    @pytest.mark.asyncio
    async def test_status_updates_after_start(self, manager, mock_platforms):
        """Test status updates after starting streams"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        status = manager.get_platform_status('youtube')

        assert status.is_active
        assert status.status.value == 'live'


class TestAggregatedMetrics:
    """Test aggregated metrics"""

    @pytest.mark.asyncio
    async def test_aggregated_metrics_no_streams(self, manager, mock_platforms):
        """Test metrics when no streams are active"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        metrics = manager.get_aggregated_metrics()

        assert metrics.total_viewers == 0
        assert metrics.active_platforms == 0
        assert metrics.overall_health.value == 'unknown'

    @pytest.mark.asyncio
    async def test_aggregated_metrics_with_streams(
        self,
        manager,
        mock_platforms
    ):
        """Test metrics with active streams"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        # Update metrics manually for testing
        for name in manager.platform_status:
            manager.platform_status[name].metrics = StreamMetrics(
                viewer_count=100,
                uptime_seconds=300
            )
            manager.platform_status[name].health = StreamHealth.GOOD

        metrics = manager.get_aggregated_metrics()

        assert metrics.total_viewers == 300  # 100 per platform
        assert metrics.active_platforms == 3
        assert metrics.overall_health.value == 'good'
        assert len(metrics.viewers_by_platform) == 3

    @pytest.mark.asyncio
    async def test_aggregated_metrics_viewers_by_platform(
        self,
        manager,
        mock_platforms
    ):
        """Test viewer breakdown by platform"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        # Set different viewer counts
        manager.platform_status['youtube'].metrics = StreamMetrics(
            viewer_count=150
        )
        manager.platform_status['facebook'].metrics = StreamMetrics(
            viewer_count=75
        )
        manager.platform_status['twitter'].metrics = StreamMetrics(
            viewer_count=25
        )

        metrics = manager.get_aggregated_metrics()

        assert metrics.total_viewers == 250
        assert metrics.viewers_by_platform['youtube'] == 150
        assert metrics.viewers_by_platform['facebook'] == 75
        assert metrics.viewers_by_platform['twitter'] == 25


class TestCleanup:
    """Test cleanup operations"""

    @pytest.mark.asyncio
    async def test_close_all(self, manager, mock_platforms):
        """Test closing all platform connections"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        await manager.close_all()

        # Verify monitoring stopped
        assert not manager.is_streaming()


class TestHealthAggregation:
    """Test overall health calculation"""

    @pytest.mark.asyncio
    async def test_excellent_health(self, manager, mock_platforms):
        """Test excellent overall health"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        # Set all platforms to excellent
        for name in manager.platform_status:
            manager.platform_status[name].health = StreamHealth.EXCELLENT

        metrics = manager.get_aggregated_metrics()
        assert metrics.overall_health.value == 'excellent'

    @pytest.mark.asyncio
    async def test_mixed_health(self, manager, mock_platforms):
        """Test mixed health levels"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        # Set mixed health levels
        manager.platform_status['youtube'].health = StreamHealth.EXCELLENT
        manager.platform_status['facebook'].health = StreamHealth.GOOD
        manager.platform_status['twitter'].health = StreamHealth.FAIR

        metrics = manager.get_aggregated_metrics()
        assert metrics.overall_health.value == 'good'

    @pytest.mark.asyncio
    async def test_poor_health(self, manager, mock_platforms):
        """Test poor overall health"""
        for name, platform in mock_platforms.items():
            manager.add_platform(name, platform)

        await manager.authenticate_all()
        await manager.start_all("Test Stream")

        # Set all platforms to poor
        for name in manager.platform_status:
            manager.platform_status[name].health = StreamHealth.POOR

        metrics = manager.get_aggregated_metrics()
        assert metrics.overall_health.value == 'poor'
        assert metrics.failed_platforms == 3
