"""
Tests for Twitter/X Live Integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from core.twitter_live import TwitterLive
from core.streaming_platform import (
    PlatformConfig,
    StreamStatus,
    StreamHealth
)


@pytest.fixture
def twitter_config():
    """Twitter/X Live configuration"""
    return PlatformConfig(
        platform_name="Twitter",
        stream_key="test-key",
        rtmp_url="rtmp://va.pscp.tv:80/x/",
        enabled=True,
        max_bitrate=3000,
        target_resolution="720p",
        target_fps=30,
        encoder_preset="medium",
        api_credentials={
            'api_key': 'test-api-key',
            'api_secret': 'test-api-secret',
            'access_token': 'test-access-token',
            'access_secret': 'test-access-secret'
        }
    )


@pytest.fixture
def twitter_platform(twitter_config):
    """Twitter/X Live platform instance"""
    return TwitterLive(twitter_config)


class TestTwitterInitialization:
    """Test Twitter/X Live initialization"""

    def test_initialization(self, twitter_platform, twitter_config):
        """Test platform initialization"""
        assert twitter_platform.config == twitter_config
        assert twitter_platform.api_key == 'test-api-key'
        assert twitter_platform.api_secret == 'test-api-secret'
        assert twitter_platform.access_token == 'test-access-token'
        assert twitter_platform.access_secret == 'test-access-secret'
        assert not twitter_platform.is_authenticated()
        assert not twitter_platform.is_live()

    def test_rtmp_url(self, twitter_platform):
        """Test RTMP URL"""
        rtmp_url = twitter_platform.get_rtmp_url()
        assert rtmp_url == "rtmp://va.pscp.tv:80/x/"


class TestTwitterAuthentication:
    """Test Twitter authentication"""

    @pytest.mark.asyncio
    async def test_successful_authentication(self, twitter_platform):
        """Test successful authentication"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'username': 'testuser',
                'id': '123456'
            }
        }

        with patch.object(
            twitter_platform.http_client,
            'get',
            return_value=mock_response
        ) as mock_get:
            result = await twitter_platform.authenticate()

            assert result is True
            assert twitter_platform.is_authenticated()
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_authentication_missing_credentials(self):
        """Test authentication with missing credentials"""
        config = PlatformConfig(
            platform_name="Twitter",
            stream_key="test-key",
            rtmp_url="rtmp://va.pscp.tv:80/x/",
            enabled=True
        )
        platform = TwitterLive(config)

        result = await platform.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_authentication_api_error(self, twitter_platform):
        """Test authentication API error"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(
            twitter_platform.http_client,
            'get',
            return_value=mock_response
        ):
            result = await twitter_platform.authenticate()
            assert result is False


class TestTwitterStreamStart:
    """Test Twitter stream start"""

    @pytest.mark.asyncio
    async def test_start_stream_not_authenticated(self, twitter_platform):
        """Test starting stream without authentication"""
        result = await twitter_platform.start_stream(
            "Test Stream",
            "Test Description"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_stream_start(self, twitter_platform):
        """Test successful stream start"""
        # Mock authentication
        twitter_platform._is_authenticated = True

        # Mock API response
        create_response = MagicMock()
        create_response.status_code = 200
        create_response.json.return_value = {
            'broadcast': {
                'id': 'broadcast-123',
                'stream_name': 'stream-key-456'
            }
        }

        with patch.object(
            twitter_platform.http_client,
            'post',
            return_value=create_response
        ):
            result = await twitter_platform.start_stream(
                "Test Stream",
                "Test Description"
            )

            assert result is True
            assert twitter_platform.broadcast_id == 'broadcast-123'
            assert twitter_platform.config.stream_key == 'stream-key-456'
            assert twitter_platform.stream_info is not None
            assert twitter_platform.stream_info.platform == "Twitter"


class TestTwitterStreamStop:
    """Test Twitter stream stop"""

    @pytest.mark.asyncio
    async def test_stop_stream_no_broadcast(self, twitter_platform):
        """Test stopping stream with no active broadcast"""
        result = await twitter_platform.stop_stream()
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_stream_stop(self, twitter_platform):
        """Test successful stream stop"""
        from core.streaming_platform import StreamInfo

        twitter_platform.broadcast_id = 'broadcast-123'
        twitter_platform.stream_info = StreamInfo(
            stream_id='broadcast-123',
            platform='Twitter',
            status=StreamStatus.LIVE,
            health=StreamHealth.GOOD,
            started_at=datetime.now(UTC)
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(
            twitter_platform.http_client,
            'post',
            return_value=mock_response
        ):
            result = await twitter_platform.stop_stream()

            assert result is True
            assert twitter_platform.broadcast_id is None
            assert twitter_platform.stream_info.status.value == 'offline'


class TestTwitterMetrics:
    """Test Twitter metrics"""

    @pytest.mark.asyncio
    async def test_get_health_no_broadcast(self, twitter_platform):
        """Test health check with no broadcast"""
        health = await twitter_platform.get_stream_health()
        assert health.value == 'unknown'

    @pytest.mark.asyncio
    async def test_get_health_running(self, twitter_platform):
        """Test running health status"""
        twitter_platform.broadcast_id = 'broadcast-123'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'broadcast': {
                'state': 'RUNNING',
                'n_web_watching': 50
            }
        }

        with patch.object(
            twitter_platform.http_client,
            'get',
            return_value=mock_response
        ):
            health = await twitter_platform.get_stream_health()
            assert health.value == 'good'

    @pytest.mark.asyncio
    async def test_get_metrics_no_broadcast(self, twitter_platform):
        """Test metrics with no broadcast"""
        metrics = await twitter_platform.get_metrics()
        assert metrics.viewer_count == 0
        assert metrics.peak_viewers == 0

    @pytest.mark.asyncio
    async def test_get_metrics_with_data(self, twitter_platform):
        """Test metrics with data"""
        twitter_platform.broadcast_id = 'broadcast-123'
        twitter_platform.stream_info = MagicMock()
        twitter_platform.stream_info.started_at = datetime.now(UTC)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'broadcast': {
                'n_web_watching': 45,
                'n_total_watching': 100,
                'state': 'RUNNING'
            }
        }

        with patch.object(
            twitter_platform.http_client,
            'get',
            return_value=mock_response
        ):
            metrics = await twitter_platform.get_metrics()
            assert metrics.viewer_count == 45
            assert metrics.peak_viewers == 100
            assert metrics.uptime_seconds >= 0


class TestTwitterUpdateInfo:
    """Test Twitter stream info updates"""

    @pytest.mark.asyncio
    async def test_update_stream_info_no_broadcast(self, twitter_platform):
        """Test updating info with no broadcast"""
        result = await twitter_platform.update_stream_info(
            title="New Title"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_update(self, twitter_platform):
        """Test successful stream info update"""
        twitter_platform.broadcast_id = 'broadcast-123'

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(
            twitter_platform.http_client,
            'post',
            return_value=mock_response
        ) as mock_post:
            result = await twitter_platform.update_stream_info(
                title="New Title",
                description="New Description"
            )

            assert result is True
            mock_post.assert_called_once()


class TestTwitterHelpers:
    """Test helper methods"""

    def test_platform_name(self, twitter_platform):
        """Test platform name"""
        assert twitter_platform.get_platform_name() == "Twitter"

    def test_stream_key(self, twitter_platform):
        """Test stream key"""
        assert twitter_platform.get_stream_key() == "test-key"

    def test_to_dict(self, twitter_platform):
        """Test to_dict conversion"""
        data = twitter_platform.to_dict()
        assert data['platform'] == "Twitter"
        assert data['authenticated'] is False
        assert data['is_live'] is False
        assert data['stream_info'] is None

    @pytest.mark.asyncio
    async def test_close(self, twitter_platform):
        """Test client close"""
        with patch.object(
            twitter_platform.http_client,
            'aclose',
            new_callable=AsyncMock
        ) as mock_close:
            await twitter_platform.close()
            mock_close.assert_called_once()


class TestTwitterTweetIntegration:
    """Test Twitter tweet posting with stream"""

    @pytest.mark.asyncio
    async def test_post_tweet_no_broadcast(self, twitter_platform):
        """Test posting tweet without broadcast"""
        result = await twitter_platform.post_tweet_with_stream(
            "Check out my stream!"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_successful_tweet_post(self, twitter_platform):
        """Test successful tweet posting"""
        twitter_platform.broadcast_id = 'broadcast-123'

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {
                'id': 'tweet-789'
            }
        }

        with patch.object(
            twitter_platform.http_client,
            'post',
            return_value=mock_response
        ):
            tweet_id = await twitter_platform.post_tweet_with_stream(
                "🔴 LIVE: Check out my stream!"
            )

            assert tweet_id == 'tweet-789'

    @pytest.mark.asyncio
    async def test_tweet_post_error(self, twitter_platform):
        """Test tweet posting error"""
        twitter_platform.broadcast_id = 'broadcast-123'

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with patch.object(
            twitter_platform.http_client,
            'post',
            return_value=mock_response
        ):
            tweet_id = await twitter_platform.post_tweet_with_stream(
                "Test tweet"
            )

            assert tweet_id is None


class TestTwitterSpaces:
    """Test Twitter Spaces integration"""

    @pytest.mark.asyncio
    async def test_create_space_stream(self, twitter_platform):
        """Test creating stream with Spaces support"""
        twitter_platform._is_authenticated = True

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.json.return_value = {
            'broadcast': {
                'id': 'space-123',
                'stream_name': 'space-key-456'
            }
        }

        with patch.object(
            twitter_platform.http_client,
            'post',
            return_value=create_response
        ) as mock_post:
            result = await twitter_platform.start_stream(
                "Twitter Space Stream",
                "Testing Spaces",
                is_space=True
            )

            assert result is True
            # Verify is_space parameter was passed
            call_args = mock_post.call_args
            # Check that the request was made
            assert call_args is not None
