"""
Tests for Facebook Live Integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from core.facebook_live import FacebookLive
from core.streaming_platform import (
    PlatformConfig,
    StreamStatus,
    StreamHealth
)


@pytest.fixture
def facebook_config():
    """Facebook Live configuration"""
    return PlatformConfig(
        platform_name="Facebook",
        stream_key="test-key",
        rtmp_url="rtmps://live-api-s.facebook.com:443/rtmp/",
        enabled=True,
        max_bitrate=4000,
        target_resolution="720p",
        target_fps=30,
        encoder_preset="medium",
        api_credentials={
            'access_token': 'test-access-token',
            'page_id': '123456789'
        }
    )


@pytest.fixture
def facebook_platform(facebook_config):
    """Facebook Live platform instance"""
    return FacebookLive(facebook_config)


class TestFacebookInitialization:
    """Test Facebook Live initialization"""

    def test_initialization(self, facebook_platform, facebook_config):
        """Test platform initialization"""
        assert facebook_platform.config == facebook_config
        assert facebook_platform.access_token == 'test-access-token'
        assert facebook_platform.page_id == '123456789'
        assert not facebook_platform.is_authenticated()
        assert not facebook_platform.is_live()

    def test_rtmp_url(self, facebook_platform):
        """Test RTMP URL"""
        rtmp_url = facebook_platform.get_rtmp_url()
        assert rtmp_url == "rtmps://live-api-s.facebook.com:443/rtmp/"


class TestFacebookAuthentication:
    """Test Facebook authentication"""

    @pytest.mark.asyncio
    async def test_successful_authentication(self, facebook_platform):
        """Test successful authentication"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'Test Page',
            'id': '123456789'
        }

        with patch.object(
            facebook_platform.http_client,
            'get',
            return_value=mock_response
        ) as mock_get:
            result = await facebook_platform.authenticate()

            assert result is True
            assert facebook_platform.is_authenticated()
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_authentication_no_token(self):
        """Test authentication without access token"""
        config = PlatformConfig(
            platform_name="Facebook",
            stream_key="test-key",
            rtmp_url="rtmps://live-api-s.facebook.com:443/rtmp/",
            enabled=True
        )
        platform = FacebookLive(config)

        result = await platform.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_authentication_no_page_id(self):
        """Test authentication without page ID"""
        config = PlatformConfig(
            platform_name="Facebook",
            stream_key="test-key",
            rtmp_url="rtmps://live-api-s.facebook.com:443/rtmp/",
            enabled=True,
            api_credentials={'access_token': 'test-token'}
        )
        platform = FacebookLive(config)

        result = await platform.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_authentication_api_error(self, facebook_platform):
        """Test authentication API error"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(
            facebook_platform.http_client,
            'get',
            return_value=mock_response
        ):
            result = await facebook_platform.authenticate()
            assert result is False


class TestFacebookStreamStart:
    """Test Facebook stream start"""

    @pytest.mark.asyncio
    async def test_start_stream_not_authenticated(self, facebook_platform):
        """Test starting stream without authentication"""
        result = await facebook_platform.start_stream(
            "Test Stream",
            "Test Description"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_stream_start(self, facebook_platform):
        """Test successful stream start"""
        # Mock authentication
        facebook_platform._is_authenticated = True

        # Mock API responses
        create_response = MagicMock()
        create_response.status_code = 200
        create_response.json.return_value = {'id': 'video-123'}

        url_response = MagicMock()
        url_response.status_code = 200
        url_response.json.return_value = {
            'secure_stream_url': (
                'rtmps://live-api-s.facebook.com:443/rtmp/stream-key-456'
            )
        }

        async def mock_post(*args, **kwargs):
            return create_response

        async def mock_get(*args, **kwargs):
            return url_response

        with patch.object(
            facebook_platform.http_client,
            'post',
            side_effect=mock_post
        ), patch.object(
            facebook_platform.http_client,
            'get',
            side_effect=mock_get
        ):
            result = await facebook_platform.start_stream(
                "Test Stream",
                "Test Description"
            )

            assert result is True
            assert facebook_platform.video_id == 'video-123'
            assert (
                facebook_platform.config.rtmp_url ==
                'rtmps://live-api-s.facebook.com:443/rtmp/stream-key-456'
            )
            assert facebook_platform.config.stream_key == 'stream-key-456'
            assert facebook_platform.stream_info is not None
            assert facebook_platform.stream_info.platform == "Facebook"


class TestFacebookStreamStop:
    """Test Facebook stream stop"""

    @pytest.mark.asyncio
    async def test_stop_stream_no_video(self, facebook_platform):
        """Test stopping stream with no active video"""
        result = await facebook_platform.stop_stream()
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_stream_stop(self, facebook_platform):
        """Test successful stream stop"""
        from core.streaming_platform import StreamInfo

        facebook_platform.video_id = 'video-123'
        facebook_platform.stream_info = StreamInfo(
            stream_id='video-123',
            platform='Facebook',
            status=StreamStatus.LIVE,
            health=StreamHealth.GOOD,
            started_at=datetime.now(UTC)
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(
            facebook_platform.http_client,
            'post',
            return_value=mock_response
        ):
            result = await facebook_platform.stop_stream()

            assert result is True
            assert facebook_platform.video_id is None
            assert facebook_platform.stream_info.status.value == 'offline'


class TestFacebookMetrics:
    """Test Facebook metrics"""

    @pytest.mark.asyncio
    async def test_get_health_no_video(self, facebook_platform):
        """Test health check with no video"""
        health = await facebook_platform.get_stream_health()
        assert health.value == 'unknown'

    @pytest.mark.asyncio
    async def test_get_health_live(self, facebook_platform):
        """Test live health status"""
        facebook_platform.video_id = 'video-123'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': {
                'video_status': 'LIVE'
            },
            'live_views': 100
        }

        with patch.object(
            facebook_platform.http_client,
            'get',
            return_value=mock_response
        ):
            health = await facebook_platform.get_stream_health()
            assert health.value == 'good'

    @pytest.mark.asyncio
    async def test_get_metrics_no_video(self, facebook_platform):
        """Test metrics with no video"""
        metrics = await facebook_platform.get_metrics()
        assert metrics.viewer_count == 0
        assert metrics.peak_viewers == 0

    @pytest.mark.asyncio
    async def test_get_metrics_with_data(self, facebook_platform):
        """Test metrics with data"""
        facebook_platform.video_id = 'video-123'
        facebook_platform.stream_info = MagicMock()
        facebook_platform.stream_info.started_at = datetime.now(UTC)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'live_views': 75,
            'status': {'video_status': 'LIVE'}
        }

        with patch.object(
            facebook_platform.http_client,
            'get',
            return_value=mock_response
        ):
            metrics = await facebook_platform.get_metrics()
            assert metrics.viewer_count == 75
            assert metrics.uptime_seconds >= 0


class TestFacebookUpdateInfo:
    """Test Facebook stream info updates"""

    @pytest.mark.asyncio
    async def test_update_stream_info_no_video(self, facebook_platform):
        """Test updating info with no video"""
        result = await facebook_platform.update_stream_info(
            title="New Title"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_update(self, facebook_platform):
        """Test successful stream info update"""
        facebook_platform.video_id = 'video-123'

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(
            facebook_platform.http_client,
            'post',
            return_value=mock_response
        ) as mock_post:
            result = await facebook_platform.update_stream_info(
                title="New Title",
                description="New Description"
            )

            assert result is True
            mock_post.assert_called_once()


class TestFacebookHelpers:
    """Test helper methods"""

    def test_platform_name(self, facebook_platform):
        """Test platform name"""
        assert facebook_platform.get_platform_name() == "Facebook"

    def test_stream_key(self, facebook_platform):
        """Test stream key"""
        assert facebook_platform.get_stream_key() == "test-key"

    def test_to_dict(self, facebook_platform):
        """Test to_dict conversion"""
        data = facebook_platform.to_dict()
        assert data['platform'] == "Facebook"
        assert data['authenticated'] is False
        assert data['is_live'] is False
        assert data['stream_info'] is None

    @pytest.mark.asyncio
    async def test_close(self, facebook_platform):
        """Test client close"""
        with patch.object(
            facebook_platform.http_client,
            'aclose',
            new_callable=AsyncMock
        ) as mock_close:
            await facebook_platform.close()
            mock_close.assert_called_once()


class TestFacebookPrivacySettings:
    """Test Facebook privacy controls"""

    @pytest.mark.asyncio
    async def test_create_public_stream(self, facebook_platform):
        """Test creating public stream"""
        facebook_platform._is_authenticated = True

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.json.return_value = {'id': 'video-123'}

        url_response = MagicMock()
        url_response.status_code = 200
        url_response.json.return_value = {
            'secure_stream_url': (
                'rtmps://live-api-s.facebook.com:443/rtmp/key-123'
            )
        }

        with patch.object(
            facebook_platform.http_client,
            'post',
            return_value=create_response
        ) as mock_post, patch.object(
            facebook_platform.http_client,
            'get',
            return_value=url_response
        ):
            result = await facebook_platform.start_stream(
                "Test Stream",
                "Description",
                privacy="PUBLIC"
            )

            assert result is True
            # Verify privacy parameter was passed
            call_args = mock_post.call_args
            assert 'privacy' in call_args.kwargs['params']

    @pytest.mark.asyncio
    async def test_create_friends_only_stream(self, facebook_platform):
        """Test creating friends-only stream"""
        facebook_platform._is_authenticated = True

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.json.return_value = {'id': 'video-456'}

        url_response = MagicMock()
        url_response.status_code = 200
        url_response.json.return_value = {
            'secure_stream_url': (
                'rtmps://live-api-s.facebook.com:443/rtmp/key-456'
            )
        }

        with patch.object(
            facebook_platform.http_client,
            'post',
            return_value=create_response
        ), patch.object(
            facebook_platform.http_client,
            'get',
            return_value=url_response
        ):
            result = await facebook_platform.start_stream(
                "Private Stream",
                "Friends only",
                privacy="FRIENDS"
            )

            assert result is True
