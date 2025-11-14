"""
Facebook Live Integration - Stream to Facebook Live

Provides Facebook Live streaming with Graph API integration.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
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


class FacebookLive(StreamingPlatform):
    """
    Facebook Live streaming platform integration.

    Features:
    - Facebook Graph API integration
    - Live video creation and management
    - Real-time viewer metrics
    - Stream health monitoring
    - Comment integration ready
    - Privacy controls
    """

    API_BASE_URL = "https://graph.facebook.com/v18.0"
    RTMP_BASE_URL = "rtmps://live-api-s.facebook.com:443/rtmp/"

    def __init__(self, config: PlatformConfig):
        """
        Initialize Facebook Live platform.

        Args:
            config: Platform configuration with API credentials
        """
        super().__init__(config)

        self.access_token: Optional[str] = None
        self.page_id: Optional[str] = None
        self.video_id: Optional[str] = None

        # Extract API credentials
        if config.api_credentials:
            self.access_token = config.api_credentials.get('access_token')
            self.page_id = config.api_credentials.get('page_id')

        self.http_client = httpx.AsyncClient(
            base_url=self.API_BASE_URL,
            timeout=30.0
        )

        logger.info("Facebook Live platform initialized")

    async def authenticate(self) -> bool:
        """
        Authenticate with Facebook Graph API.

        Uses access token for authentication.

        Returns:
            True if authentication successful
        """
        try:
            if not self.access_token:
                logger.error("No access token provided")
                return False

            if not self.page_id:
                logger.error("No page ID provided")
                return False

            # Test authentication with page info request
            response = await self.http_client.get(
                f"/{self.page_id}",
                params={
                    "fields": "name,id",
                    "access_token": self.access_token
                }
            )

            if response.status_code == 200:
                data = response.json()
                page_name = data.get('name')
                logger.info(
                    f"Authenticated as Facebook page: {page_name}"
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
        Start Facebook Live stream.

        Creates a live video and gets stream URL/key.

        Args:
            title: Stream title
            description: Stream description
            category: Stream category (not used by Facebook)
            **kwargs: Additional Facebook-specific parameters

        Returns:
            True if stream started successfully
        """
        try:
            if not self._is_authenticated:
                logger.error("Not authenticated")
                return False

            # Create live video
            video_id = await self._create_live_video(
                title,
                description,
                kwargs.get('privacy', 'PUBLIC'),
                kwargs.get('status', 'LIVE_NOW')
            )

            if not video_id:
                return False

            # Get stream URL and key
            stream_url, stream_key = await self._get_stream_url(video_id)

            if not stream_url or not stream_key:
                return False

            # Update config with stream info
            self.config.rtmp_url = stream_url
            self.config.stream_key = stream_key
            self.video_id = video_id

            # Create stream info
            self.stream_info = StreamInfo(
                stream_id=video_id,
                platform="Facebook",
                status=StreamStatus.LIVE,
                health=StreamHealth.UNKNOWN,
                started_at=datetime.utcnow()
            )

            logger.info(
                f"Facebook Live stream started: {video_id}"
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
        Stop Facebook Live stream.

        Returns:
            True if stream stopped successfully
        """
        try:
            if not self.video_id:
                logger.warning("No active video")
                return False

            # End live video
            response = await self.http_client.post(
                f"/{self.video_id}",
                params={
                    "end_live_video": "true",
                    "access_token": self.access_token
                }
            )

            if response.status_code == 200:
                if self.stream_info:
                    self.stream_info.status = StreamStatus.OFFLINE
                    self.stream_info.ended_at = datetime.utcnow()

                logger.info(
                    f"Facebook Live stream stopped: {self.video_id}"
                )

                self.video_id = None

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
        Get Facebook Live stream health.

        Returns:
            Stream health status
        """
        try:
            if not self.video_id:
                return StreamHealth.UNKNOWN

            response = await self.http_client.get(
                f"/{self.video_id}",
                params={
                    "fields": "status,live_views",
                    "access_token": self.access_token
                }
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', {})
                video_status = status.get('video_status', 'unknown')

                # Map Facebook status to our health enum
                # Facebook doesn't provide detailed health,
                # so we infer from status
                health_map = {
                    'LIVE': StreamHealth.GOOD,
                    'PROCESSING': StreamHealth.FAIR,
                    'VOD': StreamHealth.UNKNOWN,
                    'SCHEDULED_UNPUBLISHED': StreamHealth.UNKNOWN,
                    'SCHEDULED_LIVE': StreamHealth.UNKNOWN,
                    'SCHEDULED_CANCELED': StreamHealth.UNKNOWN
                }

                return health_map.get(
                    video_status,
                    StreamHealth.UNKNOWN
                )

            return StreamHealth.UNKNOWN

        except Exception as e:
            logger.error(f"Error getting stream health: {e}")
            return StreamHealth.UNKNOWN

    async def get_metrics(self) -> StreamMetrics:
        """
        Get Facebook Live stream metrics.

        Returns:
            Stream performance metrics
        """
        try:
            if not self.video_id:
                return StreamMetrics()

            response = await self.http_client.get(
                f"/{self.video_id}",
                params={
                    "fields": "live_views,status",
                    "access_token": self.access_token
                }
            )

            if response.status_code == 200:
                data = response.json()

                # Calculate uptime
                uptime = 0
                if self.stream_info and self.stream_info.started_at:
                    uptime = int(
                        (
                            datetime.utcnow() -
                            self.stream_info.started_at
                        ).total_seconds()
                    )

                metrics = StreamMetrics(
                    viewer_count=int(data.get('live_views', 0)),
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
        Update Facebook Live stream information.

        Args:
            title: New stream title
            description: New stream description
            **kwargs: Additional parameters

        Returns:
            True if update successful
        """
        try:
            if not self.video_id:
                logger.warning("No active video")
                return False

            # Build update payload
            update_params: Dict[str, Any] = {
                "access_token": self.access_token
            }

            if title:
                update_params["title"] = title

            if description:
                update_params["description"] = description

            response = await self.http_client.post(
                f"/{self.video_id}",
                params=update_params
            )

            if response.status_code == 200:
                logger.info("Facebook Live stream info updated")
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

    async def _create_live_video(
        self,
        title: str,
        description: str,
        privacy: str = "PUBLIC",
        status: str = "LIVE_NOW"
    ) -> Optional[str]:
        """Create Facebook live video"""
        try:
            video_data = {
                "title": title,
                "description": description,
                "status": status,
                "access_token": self.access_token
            }

            # Add privacy settings
            if privacy:
                video_data["privacy"] = f'{{"value":"{privacy}"}}'

            response = await self.http_client.post(
                f"/{self.page_id}/live_videos",
                params=video_data
            )

            if response.status_code == 200:
                data = response.json()
                video_id = str(data['id'])
                logger.info(f"Created live video: {video_id}")
                return video_id
            else:
                logger.error(
                    f"Failed to create live video: "
                    f"{response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error creating live video: {e}")
            return None

    async def _get_stream_url(
        self,
        video_id: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Get stream URL and key from video"""
        try:
            response = await self.http_client.get(
                f"/{video_id}",
                params={
                    "fields": "stream_url,secure_stream_url",
                    "access_token": self.access_token
                }
            )

            if response.status_code == 200:
                data = response.json()

                # Prefer secure stream URL
                stream_url = data.get('secure_stream_url')
                if not stream_url:
                    stream_url = data.get('stream_url')

                if stream_url:
                    # Extract stream key from URL
                    # Format: rtmps://live-api-s.facebook.com:443/rtmp/STREAM_KEY
                    parts = stream_url.split('/')
                    stream_key = parts[-1] if parts else None

                    return stream_url, stream_key

            return None, None

        except Exception as e:
            logger.error(f"Error getting stream URL: {e}")
            return None, None

    async def close(self) -> None:
        """Close HTTP client"""
        await self.http_client.aclose()
