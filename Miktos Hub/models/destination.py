"""
Streaming Destination Models

Defines where streams are sent (YouTube, Facebook, Twitter, etc.)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime


class DestinationType(Enum):
    """Supported streaming platforms"""
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    TWITCH = "twitch"
    LINKEDIN = "linkedin"
    CUSTOM_RTMP = "custom_rtmp"
    CUSTOM_SRT = "custom_srt"


# Alias for backward compatibility
Platform = DestinationType


class DestinationStatus(Enum):
    """Status of a streaming destination"""
    IDLE = "idle"  # Configured but not streaming
    CONNECTING = "connecting"  # Attempting to connect
    LIVE = "live"  # Actively streaming
    ERROR = "error"  # Connection/stream error
    DISCONNECTED = "disconnected"  # Was connected, now disconnected


@dataclass
class DestinationHealth:
    """Real-time health metrics for a streaming destination"""
    timestamp: datetime
    is_connected: bool
    is_streaming: bool
    
    # Stream metrics
    bitrate_kbps: float = 0.0
    fps: float = 0.0
    dropped_frames: int = 0
    total_frames_sent: int = 0
    
    # Network metrics
    rtt_ms: Optional[float] = None  # Round-trip time
    packet_loss_percent: Optional[float] = None
    jitter_ms: Optional[float] = None
    
    # Platform-specific
    viewer_count: Optional[int] = None
    concurrent_viewers: Optional[int] = None
    
    # Error tracking
    last_error: Optional[str] = None
    error_count: int = 0
    
    def is_healthy(self) -> bool:
        """Quick health check"""
        return (
            self.is_connected
            and self.is_streaming
            and self.fps > 15
            and self.packet_loss_percent is not None
            and self.packet_loss_percent < 5.0  # Less than 5% loss
        )


@dataclass
class StreamDestination:
    """
    Represents a streaming destination (platform or custom server).
    
    Destinations can be platforms like YouTube/Facebook or custom RTMP/SRT servers.
    
    Example:
        ```python
        # YouTube destination
        youtube = StreamDestination(
            id="youtube-en",
            name="YouTube - English Channel",
            type=DestinationType.YOUTUBE,
            url="rtmp://a.rtmp.youtube.com/live2",
            stream_key="xxxx-xxxx-xxxx-xxxx",
            enabled=True,
        )
        
        # Custom RTMP server
        custom = StreamDestination(
            id="backup-server",
            name="Backup RTMP Server",
            type=DestinationType.CUSTOM_RTMP,
            url="rtmp://backup.example.com:1935/live",
            stream_key="my-stream-key",
            enabled=True,
        )
        ```
    """
    
    # Identity
    id: str
    name: str
    type: DestinationType
    
    # Connection details
    url: str  # RTMP or SRT URL
    stream_key: str  # Stream key/password
    
    # Configuration
    enabled: bool = True
    is_backup: bool = False  # Is this a failover backup?
    priority: int = 0  # Higher priority = preferred destination
    
    # Quality settings
    target_bitrate_kbps: int = 6000
    target_fps: int = 30
    keyframe_interval: int = 2  # seconds
    
    # Platform-specific settings
    channel_id: Optional[str] = None  # For YouTube
    page_id: Optional[str] = None  # For Facebook
    extra: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime state
    status: DestinationStatus = DestinationStatus.IDLE  # For compatibility
    health: Optional[DestinationHealth] = None
    last_connected_at: Optional[datetime] = None
    last_disconnected_at: Optional[datetime] = None
    
    # Failover state
    using_backup: bool = False  # Currently using backup path?
    failover_count: int = 0  # How many times we've failed over
    
    def is_healthy(self) -> bool:
        """Check if destination is currently healthy"""
        return self.health is not None and self.health.is_healthy()
    
    def is_connected(self) -> bool:
        """Check if destination is currently connected"""
        return self.health is not None and self.health.is_connected
    
    def should_failover(self) -> bool:
        """Check if we should failover to backup"""
        if not self.health:
            return True
        
        # Failover conditions:
        # - Not connected
        # - High packet loss
        # - Too many errors
        return (
            not self.health.is_connected
            or (self.health.packet_loss_percent is not None and self.health.packet_loss_percent > 10.0)
            or self.health.error_count > 3
        )
