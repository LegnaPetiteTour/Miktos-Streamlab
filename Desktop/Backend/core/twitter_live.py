"""
Twitter/X Live Integration - Stream to Twitter/X (formerly Periscope)

Provides Twitter/X Live streaming with API integration.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, UTC
import httpx

from core.streaming_platform import (
    StreamingPlatform,
    PlatformConfig,
    StreamInfo,
    StreamStatus,
    StreamHealth,
    StreamMetrics
)

logger = logging.getLogger(__name__)


class TwitterLive(StreamingPlatform):
    """
    Twitter/X Live streaming platform integration.

    Features:
    - Twitter API v2 integration
    - Live stream creation and management
    - Real-time viewer metrics
    - Stream health monitoring
    - Tweet integration ready

    Note: Twitter/X uses Media Publisher API for live streaming
    """

    API_BASE_URL = "https://api.twitter.com/2"
    MEDIA_API_URL = "https://upload.twitter.com/1.1"
    RTMP_BASE_URL = "rtmp://va.pscp.tv:80/x/"

    def __init__(self, config: PlatformConfig):
        """
        Initialize Twitter/X Live platform.

        Args:
            config: Platform configuration with API credentials
        """
        super().__init__(config)

        self.api_key: Optional[str] = None
        self.api_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.access_secret: Optional[str] = None
        self.broadcast_id: Optional[str] = None

        # Extract API credentials
        if config.api_credentials:
            self.api_key = config.api_credentials.get('api_key')
            self.api_secret = config.api_credentials.get('api_secret')
            self.access_token = config.api_credentials.get('access_token')
            self.access_secret = config.api_credentials.get('access_secret')

        self.http_client = httpx.AsyncClient(
            timeout=30.0
        )

        logger.info("Twitter/X Live platform initialized")

    async def authenticate(self) -> bool:
        """
        Authenticate with Twitter API.

        Uses OAuth 1.0a for authentication.

        Returns:
            True if authentication successful
        """
        try:
            if not all([
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_secret
            ]):
                logger.error("Missing OAuth credentials")
                return False

            # Test authentication with user info request
            response = await self.http_client.get(
                f"{self.API_BASE_URL}/users/me",
                headers=self._get_auth_headers()
            )

            if response.status_code == 200:
                data = response.json()
                username = data.get('data', {}).get('username')
                logger.info(
                    f"Authenticated as Twitter/X user: @{username}"
                )
                self._is_authenticated = True
                return True
            else:
                logger.error(
                    f"Authentication failed: {response.status_code} - "
                    f"{response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def start_stream(
        self,
        title: str,
        description: str = "",
        category: str = "",
        **kwargs: Any
    ) -> bool:
        """
        Start Twitter/X Live stream.

        Creates a broadcast and gets stream credentials.

        Args:
            title: Stream title
            description: Stream description
            category: Stream category (not used by Twitter)
            **kwargs: Additional Twitter-specific parameters

        Returns:
            True if stream started successfully
        """
        try:
            if not self._is_authenticated:
                logger.error("Not authenticated")
                return False

            # Create broadcast
            broadcast_id, stream_key = await self._create_broadcast(
                title,
                description,
                kwargs.get('is_space', False)
            )

            if not broadcast_id or not stream_key:
                return False

            # Update config with stream info
            self.config.stream_key = stream_key
            self.config.rtmp_url = f"{self.RTMP_BASE_URL}"
            self.broadcast_id = broadcast_id

            # Create stream info
            self.stream_info = StreamInfo(
                stream_id=broadcast_id,
                platform="Twitter",
                status=StreamStatus.LIVE,
                health=StreamHealth.UNKNOWN,
                started_at=datetime.now(UTC)
            )

            logger.info(
                f"Twitter/X Live stream started: {broadcast_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to start stream: {e}")
            if self.stream_info:
                self.stream_info.status = StreamStatus.ERROR
                if self.stream_info.errors is None:
                    self.stream_info.errors = []
                self.stream_info.errors.append(str(e))
            return False

    async def stop_stream(self) -> bool:
        """
        Stop Twitter/X Live stream.

        Returns:
            True if stream stopped successfully
        """
        try:
            if not self.broadcast_id:
                logger.warning("No active broadcast")
                return False

            # End broadcast
            response = await self.http_client.post(
                f"{self.MEDIA_API_URL}/broadcasts/end.json",
                headers=self._get_auth_headers(),
                json={
                    "broadcast_id": self.broadcast_id
                }
            )

            if response.status_code == 200:
                if self.stream_info:
                    self.stream_info.status = StreamStatus.OFFLINE
                    self.stream_info.ended_at = datetime.now(UTC)

                logger.info(
                    f"Twitter/X Live stream stopped: {self.broadcast_id}"
                )

                self.broadcast_id = None

                return True
            else:
                logger.error(
                    f"Failed to stop stream: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return False

    async def get_stream_health(self) -> StreamHealth:
        """
        Get Twitter/X stream health.

        Returns:
            Stream health status
        """
        try:
            if not self.broadcast_id:
                return StreamHealth.UNKNOWN

            response = await self.http_client.get(
                f"{self.MEDIA_API_URL}/broadcasts/show.json",
                headers=self._get_auth_headers(),
                params={
                    "broadcast_id": self.broadcast_id
                }
            )

            if response.status_code == 200:
                data = response.json()
                state = data.get('broadcast', {}).get('state', 'unknown')

                # Map Twitter state to our health enum
                health_map = {
                    'RUNNING': StreamHealth.GOOD,
                    'ENDED': StreamHealth.UNKNOWN,
                    'TIMED_OUT': StreamHealth.POOR,
                    'NOT_STARTED': StreamHealth.UNKNOWN
                }

                return health_map.get(state, StreamHealth.UNKNOWN)

            return StreamHealth.UNKNOWN

        except Exception as e:
            logger.error(f"Error getting stream health: {e}")
            return StreamHealth.UNKNOWN

    async def get_metrics(self) -> StreamMetrics:
        """
        Get Twitter/X stream metrics.

        Returns:
            Stream performance metrics
        """
        try:
            if not self.broadcast_id:
                return StreamMetrics()

            response = await self.http_client.get(
                f"{self.MEDIA_API_URL}/broadcasts/show.json",
                headers=self._get_auth_headers(),
                params={
                    "broadcast_id": self.broadcast_id
                }
            )

            if response.status_code == 200:
                data = response.json()
                broadcast = data.get('broadcast', {})

                # Calculate uptime
                uptime = 0
                if self.stream_info and self.stream_info.started_at:
                    uptime = int(
                        (
                            datetime.now(UTC) -
                            self.stream_info.started_at
                        ).total_seconds()
                    )

                metrics = StreamMetrics(
                    viewer_count=int(
                        broadcast.get('n_web_watching', 0)
                    ),
                    peak_viewers=int(
                        broadcast.get('n_total_watching', 0)
                    ),
                    uptime_seconds=uptime
                )

                return metrics

            return StreamMetrics()

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return StreamMetrics()

    async def update_stream_info(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        """
        Update Twitter/X stream information.

        Args:
            title: New stream title
            description: New stream description
            **kwargs: Additional parameters

        Returns:
            True if update successful
        """
        try:
            if not self.broadcast_id:
                logger.warning("No active broadcast")
                return False

            # Build update payload
            update_data: Dict[str, Any] = {
                "broadcast_id": self.broadcast_id
            }

            if title:
                update_data["title"] = title

            if description:
                update_data["description"] = description

            response = await self.http_client.post(
                f"{self.MEDIA_API_URL}/broadcasts/update.json",
                headers=self._get_auth_headers(),
                json=update_data
            )

            if response.status_code == 200:
                logger.info("Twitter/X stream info updated")
                return True
            else:
                logger.error(
                    f"Failed to update stream info: "
                    f"{response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"Error updating stream info: {e}")
            return False

    async def _create_broadcast(
        self,
        title: str,
        description: str,
        is_space: bool = False
    ) -> tuple[Optional[str], Optional[str]]:
        """Create Twitter/X broadcast"""
        try:
            broadcast_data: Dict[str, Any] = {
                "title": title,
                "description": description,
                "region": "us",
                "locale": "en",
                "source": "TWITTER_API"
            }

            if is_space:
                broadcast_data["is_space_available"] = True

            response = await self.http_client.post(
                f"{self.MEDIA_API_URL}/broadcasts/create.json",
                headers=self._get_auth_headers(),
                json=broadcast_data
            )

            if response.status_code == 200:
                data = response.json()
                broadcast = data.get('broadcast', {})
                broadcast_id = str(broadcast.get('id'))
                stream_key = str(broadcast.get('stream_name'))

                logger.info(f"Created broadcast: {broadcast_id}")
                return broadcast_id, stream_key
            else:
                logger.error(
                    f"Failed to create broadcast: "
                    f"{response.status_code} - {response.text}"
                )
                return None, None

        except Exception as e:
            logger.error(f"Error creating broadcast: {e}")
            return None, None

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get OAuth 1.0a authentication headers.

        Note: In production, use proper OAuth 1.0a signing
        with requests-oauthlib or similar library.
        """
        # Simplified for demonstration
        # In production, implement proper OAuth 1.0a signing
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def post_tweet_with_stream(
        self,
        tweet_text: str
    ) -> Optional[str]:
        """
        Post a tweet with the live stream link.

        Args:
            tweet_text: Tweet text to post

        Returns:
            Tweet ID if successful, None otherwise
        """
        try:
            if not self.broadcast_id:
                logger.warning("No active broadcast")
                return None

            # Create tweet with broadcast
            response = await self.http_client.post(
                f"{self.API_BASE_URL}/tweets",
                headers=self._get_auth_headers(),
                json={
                    "text": tweet_text,
                    "media": {
                        "media_ids": [self.broadcast_id]
                    }
                }
            )

            if response.status_code == 201:
                data = response.json()
                tweet_id = data.get('data', {}).get('id')
                logger.info(f"Posted tweet with stream: {tweet_id}")
                return str(tweet_id)
            else:
                logger.error(
                    f"Failed to post tweet: {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            return None

    async def close(self) -> None:
        """Close HTTP client"""
        await self.http_client.aclose()
