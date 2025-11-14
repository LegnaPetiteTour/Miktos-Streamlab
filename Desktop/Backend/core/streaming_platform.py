"""
Streaming Platform Interface - Base classes for multi-platform streaming

Defines common interface for all streaming platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StreamStatus(Enum):
    """Stream status states"""
    IDLE = "idle"
    STARTING = "starting"
    LIVE = "live"
    STOPPING = "stopping"
    ERROR = "error"
    OFFLINE = "offline"


class StreamHealth(Enum):
    """Stream health states"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class StreamMetrics:
    """Stream performance metrics"""
    viewer_count: int = 0
    peak_viewers: int = 0
    average_bitrate: float = 0.0
    dropped_frames: int = 0
    current_fps: float = 0.0
    uptime_seconds: int = 0
    bandwidth_mbps: float = 0.0
    latency_ms: float = 0.0


@dataclass
class PlatformConfig:
    """Platform-specific configuration"""
    platform_name: str
    stream_key: str
    rtmp_url: str
    enabled: bool = True
    max_bitrate: int = 6000  # kbps
    target_resolution: str = "1920x1080"
    target_fps: int = 30
    encoder_preset: str = "veryfast"
    api_credentials: Optional[Dict[str, str]] = None
    custom_settings: Optional[Dict[str, Any]] = None


@dataclass
class StreamInfo:
    """Current stream information"""
    stream_id: str
    platform: str
    status: StreamStatus
    health: StreamHealth
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metrics: Optional[StreamMetrics] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class StreamingPlatform(ABC):
    """
    Abstract base class for streaming platforms.

    All platform integrations must implement this interface.
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize streaming platform.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.stream_info: Optional[StreamInfo] = None
        self._is_authenticated = False

        logger.info(f"Initialized {config.platform_name} platform")

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with platform API.

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    async def start_stream(
        self,
        title: str,
        description: str = "",
        category: str = "",
        **kwargs: Any
    ) -> bool:
        """
        Start streaming to platform.

        Args:
            title: Stream title
            description: Stream description
            category: Stream category/game
            **kwargs: Platform-specific parameters

        Returns:
            True if stream started successfully
        """
        pass

    @abstractmethod
    async def stop_stream(self) -> bool:
        """
        Stop streaming to platform.

        Returns:
            True if stream stopped successfully
        """
        pass

    @abstractmethod
    async def get_stream_health(self) -> StreamHealth:
        """
        Get current stream health status.

        Returns:
            Stream health status
        """
        pass

    @abstractmethod
    async def get_metrics(self) -> StreamMetrics:
        """
        Get current stream metrics.

        Returns:
            Stream performance metrics
        """
        pass

    @abstractmethod
    async def update_stream_info(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        """
        Update stream information while live.

        Args:
            title: New stream title
            description: New stream description
            **kwargs: Platform-specific parameters

        Returns:
            True if update successful
        """
        pass

    def is_authenticated(self) -> bool:
        """Check if authenticated with platform"""
        return self._is_authenticated

    def is_live(self) -> bool:
        """Check if currently streaming"""
        return (
            self.stream_info is not None and
            self.stream_info.status == StreamStatus.LIVE
        )

    def get_rtmp_url(self) -> str:
        """Get RTMP URL for streaming"""
        return self.config.rtmp_url

    def get_stream_key(self) -> str:
        """Get stream key"""
        return self.config.stream_key

    def get_platform_name(self) -> str:
        """Get platform name"""
        return self.config.platform_name

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert platform state to dictionary.

        Returns:
            Platform state dictionary
        """
        return {
            'platform': self.config.platform_name,
            'enabled': self.config.enabled,
            'authenticated': self._is_authenticated,
            'is_live': self.is_live(),
            'stream_info': (
                {
                    'stream_id': self.stream_info.stream_id,
                    'status': self.stream_info.status.value,
                    'health': self.stream_info.health.value,
                    'started_at': (
                        self.stream_info.started_at.isoformat()
                        if self.stream_info.started_at
                        else None
                    ),
                    'metrics': (
                        {
                            'viewer_count':
                                self.stream_info.metrics.viewer_count,
                            'peak_viewers':
                                self.stream_info.metrics.peak_viewers,
                            'average_bitrate':
                                self.stream_info.metrics.average_bitrate,
                            'uptime_seconds':
                                self.stream_info.metrics.uptime_seconds
                        }
                        if self.stream_info.metrics
                        else None
                    )
                }
                if self.stream_info
                else None
            )
        }
