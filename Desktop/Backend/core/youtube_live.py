"""
YouTube Live Integration - Stream to YouTube Live

Provides YouTube Live streaming with API integration.
"""

import logging
import asyncio
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


class YouTubeLive(StreamingPlatform):
    """
    YouTube Live streaming platform integration.

    Features:
    - YouTube Data API v3 integration
    - Live stream creation and management
    - Real-time viewer metrics
    - Stream health monitoring
    - Chat integration ready
    """

    API_BASE_URL = "https://www.googleapis.com/youtube/v3"
    RTMP_BASE_URL = "rtmp://a.rtmp.youtube.com/live2"

    def __init__(self, config: PlatformConfig):
        """
        Initialize YouTube Live platform.

        Args:
            config: Platform configuration with API credentials
        """
        super().__init__(config)

        self.api_key: Optional[str] = None
        self.access_token: Optional[str] = None
        self.broadcast_id: Optional[str] = None
        self.stream_id: Optional[str] = None

        # Extract API credentials
        if config.api_credentials:
            self.api_key = config.api_credentials.get('api_key')
            self.access_token = config.api_credentials.get('access_token')

        self.http_client = httpx.AsyncClient(
            base_url=self.API_BASE_URL,
            timeout=30.0
        )

        logger.info("YouTube Live platform initialized")

    async def authenticate(self) -> bool:
        """
        Authenticate with YouTube API.

        Uses OAuth2 access token for authentication.

        Returns:
            True if authentication successful
        """
        try:
            if not self.access_token:
                logger.error("No access token provided")
                return False

            # Test authentication with channel list request
            response = await self.http_client.get(
                "/channels",
                params={
                    "part": "snippet,contentDetails",
                    "mine": "true"
                },
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    channel = data['items'][0]
                    channel_title = channel['snippet']['title']
                    logger.info(
                        f"Authenticated as YouTube channel: {channel_title}"
                    )
                    self._is_authenticated = True
                    return True
                else:
                    logger.error("No YouTube channel found")
                    return False
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
        Start YouTube Live stream.

        Creates a broadcast and binds it to a stream.

        Args:
            title: Stream title
            description: Stream description
            category: Stream category ID (optional)
            **kwargs: Additional YouTube-specific parameters

        Returns:
            True if stream started successfully
        """
        try:
            if not self._is_authenticated:
                logger.error("Not authenticated")
                return False

            # Create live broadcast
            broadcast_id = await self._create_broadcast(
                title,
                description,
                kwargs.get('privacy_status', 'public'),
                kwargs.get('scheduled_start_time')
            )

            if not broadcast_id:
                return False

            # Create live stream
            stream_id = await self._create_stream(
                title,
                kwargs.get('resolution', '1080p'),
                kwargs.get('frame_rate', '30fps')
            )

            if not stream_id:
                return False

            # Bind broadcast to stream
            if not await self._bind_broadcast(broadcast_id, stream_id):
                return False

            # Get stream key from stream
            stream_key = await self._get_stream_key(stream_id)

            if not stream_key:
                return False

            # Update config with stream key
            self.config.stream_key = stream_key
            self.broadcast_id = broadcast_id
            self.stream_id = stream_id

            # Create stream info
            self.stream_info = StreamInfo(
                stream_id=broadcast_id,
                platform="YouTube",
                status=StreamStatus.STARTING,
                health=StreamHealth.UNKNOWN,
                started_at=datetime.now(UTC),
                metrics=StreamMetrics()
            )

            logger.info(
                f"YouTube stream started: {broadcast_id} "
                f"(Stream: {stream_id})"
            )

            # Transition to live
            await self._transition_to_live(broadcast_id)

            return True

        except Exception as e:
            logger.error(f"Failed to start stream: {e}")
            if self.stream_info:
                self.stream_info.status = StreamStatus.ERROR
                self.stream_info.errors.append(str(e))  # type: ignore[union-attr]
            return False

    async def stop_stream(self) -> bool:
        """
        Stop YouTube Live stream.

        Returns:
            True if stream stopped successfully
        """
        try:
            if not self.broadcast_id:
                logger.warning("No active broadcast")
                return False

            # Transition broadcast to complete
            response = await self.http_client.post(
                "/liveBroadcasts/transition",
                params={
                    "broadcastStatus": "complete",
                    "id": self.broadcast_id,
                    "part": "status"
                },
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )

            if response.status_code == 200:
                if self.stream_info:
                    self.stream_info.status = StreamStatus.OFFLINE
                    self.stream_info.ended_at = datetime.now(UTC)

                logger.info(
                    f"YouTube stream stopped: {self.broadcast_id}"
                )

                self.broadcast_id = None
                self.stream_id = None

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
        Get YouTube stream health.

        Returns:
            Stream health status
        """
        try:
            if not self.broadcast_id:
                return StreamHealth.UNKNOWN

            response = await self.http_client.get(
                "/liveBroadcasts",
                params={
                    "part": "status,contentDetails",
                    "id": self.broadcast_id
                },
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    broadcast = data['items'][0]
                    health_status = broadcast['status'].get(
                        'healthStatus', {}
                    )
                    status = health_status.get('status', 'unknown')

                    # Map YouTube health to our enum
                    health_map = {
                        'good': StreamHealth.EXCELLENT,
                        'ok': StreamHealth.GOOD,
                        'bad': StreamHealth.POOR,
                        'noData': StreamHealth.UNKNOWN
                    }

                    return health_map.get(status, StreamHealth.UNKNOWN)

            return StreamHealth.UNKNOWN

        except Exception as e:
            logger.error(f"Error getting stream health: {e}")
            return StreamHealth.UNKNOWN

    async def get_metrics(self) -> StreamMetrics:
        """
        Get YouTube stream metrics.

        Returns:
            Stream performance metrics
        """
        try:
            if not self.broadcast_id:
                return StreamMetrics()

            response = await self.http_client.get(
                "/liveBroadcasts",
                params={
                    "part": "statistics,contentDetails",
                    "id": self.broadcast_id
                },
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    broadcast = data['items'][0]
                    stats = broadcast.get('statistics', {})

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
                            stats.get('concurrentViewers', 0)
                        ),
                        peak_viewers=int(
                            stats.get('peakConcurrentViewers', 0)
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
        Update YouTube stream information.

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
                "id": self.broadcast_id,
                "snippet": {}
            }

            if title:
                update_data["snippet"]["title"] = title

            if description:
                update_data["snippet"]["description"] = description

            response = await self.http_client.put(
                "/liveBroadcasts",
                params={"part": "snippet"},
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json=update_data
            )

            if response.status_code == 200:
                logger.info("YouTube stream info updated")
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
        privacy_status: str = "public",
        scheduled_start_time: Optional[datetime] = None
    ) -> Optional[str]:
        """Create YouTube live broadcast"""
        try:
            # Default to immediate start
            if not scheduled_start_time:
                scheduled_start_time = datetime.now(UTC)

            broadcast_data = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "scheduledStartTime": (
                        scheduled_start_time.isoformat() + 'Z'
                    )
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                },
                "contentDetails": {
                    "enableAutoStart": True,
                    "enableAutoStop": True,
                    "enableDvr": True,
                    "enableContentEncryption": False,
                    "enableEmbed": True,
                    "recordFromStart": True
                }
            }

            response = await self.http_client.post(
                "/liveBroadcasts",
                params={"part": "snippet,status,contentDetails"},
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json=broadcast_data
            )

            if response.status_code == 200:
                data = response.json()
                broadcast_id = str(data['id'])
                logger.info(f"Created broadcast: {broadcast_id}")
                return broadcast_id
            else:
                logger.error(
                    f"Failed to create broadcast: {response.status_code} - "
                    f"{response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error creating broadcast: {e}")
            return None

    async def _create_stream(
        self,
        title: str,
        resolution: str = "1080p",
        frame_rate: str = "30fps"
    ) -> Optional[str]:
        """Create YouTube live stream"""
        try:
            stream_data = {
                "snippet": {
                    "title": f"{title} - Stream"
                },
                "cdn": {
                    "frameRate": frame_rate,
                    "resolution": resolution,
                    "ingestionType": "rtmp"
                }
            }

            response = await self.http_client.post(
                "/liveStreams",
                params={"part": "snippet,cdn"},
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json=stream_data
            )

            if response.status_code == 200:
                data = response.json()
                stream_id = str(data['id'])
                logger.info(f"Created stream: {stream_id}")
                return stream_id
            else:
                logger.error(
                    f"Failed to create stream: {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"Error creating stream: {e}")
            return None

    async def _bind_broadcast(
        self,
        broadcast_id: str,
        stream_id: str
    ) -> bool:
        """Bind broadcast to stream"""
        try:
            response = await self.http_client.post(
                "/liveBroadcasts/bind",
                params={
                    "id": broadcast_id,
                    "streamId": stream_id,
                    "part": "id,contentDetails"
                },
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )

            if response.status_code == 200:
                logger.info("Broadcast bound to stream")
                return True
            else:
                logger.error(
                    f"Failed to bind broadcast: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"Error binding broadcast: {e}")
            return False

    async def _get_stream_key(self, stream_id: str) -> Optional[str]:
        """Get stream key from stream"""
        try:
            response = await self.http_client.get(
                "/liveStreams",
                params={
                    "part": "cdn",
                    "id": stream_id
                },
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    stream_key = str(
                        data['items'][0]['cdn']['ingestionInfo'][
                            'streamName'
                        ]
                    )
                    return stream_key

            return None

        except Exception as e:
            logger.error(f"Error getting stream key: {e}")
            return None

    async def _transition_to_live(self, broadcast_id: str) -> bool:
        """Transition broadcast to live status"""
        try:
            # Wait a bit for encoder to connect
            await asyncio.sleep(5)

            response = await self.http_client.post(
                "/liveBroadcasts/transition",
                params={
                    "broadcastStatus": "live",
                    "id": broadcast_id,
                    "part": "status"
                },
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )

            if response.status_code == 200:
                if self.stream_info:
                    self.stream_info.status = StreamStatus.LIVE
                logger.info("Broadcast transitioned to live")
                return True
            else:
                logger.warning(
                    f"Failed to transition to live: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"Error transitioning to live: {e}")
            return False

    async def close(self) -> None:
        """Close HTTP client"""
        await self.http_client.aclose()
