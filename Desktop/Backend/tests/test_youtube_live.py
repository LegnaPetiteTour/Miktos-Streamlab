"""
Tests for YouTube Live Integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from core.youtube_live import YouTubeLive
from core.streaming_platform import (
    PlatformConfig,
    StreamStatus,
    StreamHealth
)


@pytest.fixture
def youtube_config():
    """YouTube Live configuration"""
    return PlatformConfig(
        platform_name="YouTube",
        stream_key="test-key",
        rtmp_url="rtmp://a.rtmp.youtube.com/live2",
        enabled=True,
        max_bitrate=9000,
        target_resolution="1080p",
        target_fps=60,
        encoder_preset="medium",
        api_credentials={
            'api_key': 'test-api-key',
            'access_token': 'test-access-token'
        }
    )


@pytest.fixture
def youtube_platform(youtube_config):
    """YouTube Live platform instance"""
    return YouTubeLive(youtube_config)


class TestYouTubeInitialization:
    """Test YouTube Live initialization"""

    def test_initialization(self, youtube_platform, youtube_config):
        """Test platform initialization"""
        assert youtube_platform.config == youtube_config
        assert youtube_platform.api_key == 'test-api-key'
        assert youtube_platform.access_token == 'test-access-token'
        assert not youtube_platform.is_authenticated()
        assert not youtube_platform.is_live()

    def test_rtmp_url(self, youtube_platform):
        """Test RTMP URL generation"""
        rtmp_url = youtube_platform.get_rtmp_url()
        assert rtmp_url == "rtmp://a.rtmp.youtube.com/live2"


class TestYouTubeAuthentication:
    """Test YouTube authentication"""

    @pytest.mark.asyncio
    async def test_successful_authentication(self, youtube_platform):
        """Test successful authentication"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [{
                'snippet': {'title': 'Test Channel'},
                'contentDetails': {}
            }]
        }

        with patch.object(
            youtube_platform.http_client,
            'get',
            return_value=mock_response
        ) as mock_get:
            result = await youtube_platform.authenticate()

            assert result is True
            assert youtube_platform.is_authenticated()
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_authentication_no_token(self):
        """Test authentication without access token"""
        config = PlatformConfig(
            platform_name="YouTube",
            stream_key="test-key",
            rtmp_url="rtmp://a.rtmp.youtube.com/live2",
            enabled=True
        )
        platform = YouTubeLive(config)

        result = await platform.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_authentication_no_channel(self, youtube_platform):
        """Test authentication with no channel"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'items': []}

        with patch.object(
            youtube_platform.http_client,
            'get',
            return_value=mock_response
        ):
            result = await youtube_platform.authenticate()
            assert result is False

    @pytest.mark.asyncio
    async def test_authentication_api_error(self, youtube_platform):
        """Test authentication API error"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(
            youtube_platform.http_client,
            'get',
            return_value=mock_response
        ):
            result = await youtube_platform.authenticate()
            assert result is False


class TestYouTubeStreamStart:
    """Test YouTube stream start"""

    @pytest.mark.asyncio
    async def test_start_stream_not_authenticated(self, youtube_platform):
        """Test starting stream without authentication"""
        result = await youtube_platform.start_stream(
            "Test Stream",
            "Test Description"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_stream_start(self, youtube_platform):
        """Test successful stream start"""
        # Mock authentication
        youtube_platform._is_authenticated = True

        # Mock API responses
        broadcast_response = MagicMock()
        broadcast_response.status_code = 200
        broadcast_response.json.return_value = {'id': 'broadcast-123'}

        stream_response = MagicMock()
        stream_response.status_code = 200
        stream_response.json.return_value = {'id': 'stream-456'}

        bind_response = MagicMock()
        bind_response.status_code = 200

        key_response = MagicMock()
        key_response.status_code = 200
        key_response.json.return_value = {
            'items': [{
                'cdn': {
                    'ingestionInfo': {'streamName': 'test-stream-key'}
                }
            }]
        }

        transition_response = MagicMock()
        transition_response.status_code = 200

        async def mock_post(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'liveBroadcasts' in url and 'transition' not in url:
                return broadcast_response
            elif 'liveStreams' in url:
                return stream_response
            elif 'bind' in url:
                return bind_response
            elif 'transition' in url:
                return transition_response
            return MagicMock(status_code=200)

        async def mock_get(*args, **kwargs):
            return key_response

        with patch.object(
            youtube_platform.http_client,
            'post',
            side_effect=mock_post
        ), patch.object(
            youtube_platform.http_client,
            'get',
            side_effect=mock_get
        ):
            result = await youtube_platform.start_stream(
                "Test Stream",
                "Test Description"
            )

            assert result is True
            assert youtube_platform.broadcast_id == 'broadcast-123'
            assert youtube_platform.stream_id == 'stream-456'
            assert youtube_platform.config.stream_key == 'test-stream-key'
            assert youtube_platform.stream_info is not None
            assert youtube_platform.stream_info.platform == "YouTube"


class TestYouTubeStreamStop:
    """Test YouTube stream stop"""

    @pytest.mark.asyncio
    async def test_stop_stream_no_broadcast(self, youtube_platform):
        """Test stopping stream with no active broadcast"""
        result = await youtube_platform.stop_stream()
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_stream_stop(self, youtube_platform):
        """Test successful stream stop"""
        from core.streaming_platform import StreamInfo

        youtube_platform.broadcast_id = 'broadcast-123'
        youtube_platform.stream_info = StreamInfo(
            stream_id='broadcast-123',
            platform='YouTube',
            status=StreamStatus.LIVE,
            health=StreamHealth.GOOD,
            started_at=datetime.now(UTC)
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(
            youtube_platform.http_client,
            'post',
            return_value=mock_response
        ):
            result = await youtube_platform.stop_stream()

            assert result is True
            assert youtube_platform.broadcast_id is None
            assert youtube_platform.stream_id is None
            assert youtube_platform.stream_info.status.value == 'offline'


class TestYouTubeMetrics:
    """Test YouTube metrics"""

    @pytest.mark.asyncio
    async def test_get_health_no_broadcast(self, youtube_platform):
        """Test health check with no broadcast"""
        health = await youtube_platform.get_stream_health()
        assert health.value == 'unknown'

    @pytest.mark.asyncio
    async def test_get_health_excellent(self, youtube_platform):
        """Test excellent health status"""
        youtube_platform.broadcast_id = 'broadcast-123'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [{
                'status': {
                    'healthStatus': {'status': 'good'}
                }
            }]
        }

        with patch.object(
            youtube_platform.http_client,
            'get',
            return_value=mock_response
        ):
            health = await youtube_platform.get_stream_health()
            assert health.value == 'excellent'

    @pytest.mark.asyncio
    async def test_get_metrics_no_broadcast(self, youtube_platform):
        """Test metrics with no broadcast"""
        metrics = await youtube_platform.get_metrics()
        assert metrics.viewer_count == 0
        assert metrics.peak_viewers == 0

    @pytest.mark.asyncio
    async def test_get_metrics_with_data(self, youtube_platform):
        """Test metrics with data"""
        youtube_platform.broadcast_id = 'broadcast-123'
        youtube_platform.stream_info = MagicMock()
        youtube_platform.stream_info.started_at = datetime.now(UTC)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [{
                'statistics': {
                    'concurrentViewers': '150',
                    'peakConcurrentViewers': '200'
                }
            }]
        }

        with patch.object(
            youtube_platform.http_client,
            'get',
            return_value=mock_response
        ):
            metrics = await youtube_platform.get_metrics()
            assert metrics.viewer_count == 150
            assert metrics.peak_viewers == 200
            assert metrics.uptime_seconds >= 0


class TestYouTubeUpdateInfo:
    """Test YouTube stream info updates"""

    @pytest.mark.asyncio
    async def test_update_stream_info_no_broadcast(self, youtube_platform):
        """Test updating info with no broadcast"""
        result = await youtube_platform.update_stream_info(
            title="New Title"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_update(self, youtube_platform):
        """Test successful stream info update"""
        youtube_platform.broadcast_id = 'broadcast-123'

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(
            youtube_platform.http_client,
            'put',
            return_value=mock_response
        ) as mock_put:
            result = await youtube_platform.update_stream_info(
                title="New Title",
                description="New Description"
            )

            assert result is True
            mock_put.assert_called_once()


class TestYouTubeHelpers:
    """Test helper methods"""

    def test_platform_name(self, youtube_platform):
        """Test platform name"""
        assert youtube_platform.get_platform_name() == "YouTube"

    def test_stream_key(self, youtube_platform):
        """Test stream key"""
        assert youtube_platform.get_stream_key() == "test-key"

    def test_to_dict(self, youtube_platform):
        """Test to_dict conversion"""
        data = youtube_platform.to_dict()
        assert data['platform'] == "YouTube"
        assert data['authenticated'] is False
        assert data['is_live'] is False
        assert data['stream_info'] is None

    @pytest.mark.asyncio
    async def test_close(self, youtube_platform):
        """Test client close"""
        with patch.object(
            youtube_platform.http_client,
            'aclose',
            new_callable=AsyncMock
        ) as mock_close:
            await youtube_platform.close()
            mock_close.assert_called_once()
