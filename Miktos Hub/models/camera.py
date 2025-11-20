"""
Camera Device Models

Defines universal camera abstraction - phones, webcams, NDI, IP cameras, etc.
all look the same to the Hub.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class TransportType(Enum):
    """Video transport protocol types"""
    SRT = "srt"
    NDI = "ndi"
    RTSP = "rtsp"
    RTMP = "rtmp"
    USB = "usb"
    HDMI = "hdmi"  # Via capture card
    SDI = "sdi"    # Via capture card


class CameraCapability(Enum):
    """Capabilities a camera device may support"""
    VIDEO = "video"
    AUDIO = "audio"
    REMOTE_CONTROL = "remote_control"  # Can be controlled remotely
    STUDIO_MODE = "studio_mode"        # Has studio mode (dim screen, red dot)
    BATTERY_MONITOR = "battery_monitor"
    THERMAL_MONITOR = "thermal_monitor"
    NETWORK_MONITOR = "network_monitor"
    ZOOM = "zoom"
    PAN_TILT = "pan_tilt"
    FOCUS_CONTROL = "focus_control"
    EXPOSURE_CONTROL = "exposure_control"


@dataclass
class CameraHealth:
    """Real-time health metrics for a camera"""
    timestamp: datetime
    is_connected: bool
    bitrate_kbps: float
    fps: float
    dropped_frames: int
    
    # Optional metrics (may not be available for all cameras)
    battery_level: Optional[float] = None  # 0.0 - 1.0
    is_charging: Optional[bool] = None
    temperature_celsius: Optional[float] = None
    network_quality: Optional[str] = None  # "excellent", "good", "fair", "poor"
    signal_strength_dbm: Optional[int] = None  # WiFi/LTE signal
    
    def is_healthy(self) -> bool:
        """Quick health check"""
        return (
            self.is_connected
            and self.fps > 15  # Minimum acceptable FPS
            and self.bitrate_kbps > 1000  # Minimum acceptable bitrate
        )


@dataclass
class CameraMetadata:
    """Additional metadata about a camera device"""
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    resolution: Optional[str] = None  # e.g., "1920x1080"
    max_fps: Optional[int] = None
    codec: Optional[str] = None  # e.g., "H.264", "HEVC"
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CameraDevice:
    """
    Universal camera device representation.
    
    Whether it's a phone, webcam, or professional camera, they all
    look the same to the Hub through this abstraction.
    
    Example:
        ```python
        phone = CameraDevice(
            id="phone-001",
            label="Wide Shot (Phone 1)",
            transport=TransportType.SRT,
            url="srt://192.168.1.100:8888",
            capabilities=[
                CameraCapability.VIDEO,
                CameraCapability.AUDIO,
                CameraCapability.REMOTE_CONTROL,
                CameraCapability.STUDIO_MODE,
                CameraCapability.BATTERY_MONITOR,
                CameraCapability.THERMAL_MONITOR,
            ]
        )
        ```
    """
    
    id: str  # Unique identifier
    label: str  # Human-readable name
    transport: TransportType  # How video is delivered
    url: str  # Connection URL/address
    capabilities: List[CameraCapability] = field(default_factory=list)
    
    # Runtime state
    is_registered: bool = False
    health: Optional[CameraHealth] = None
    metadata: CameraMetadata = field(default_factory=CameraMetadata)
    
    # Control endpoint (if camera supports remote control)
    control_url: Optional[str] = None  # WebSocket URL for remote control
    
    def has_capability(self, capability: CameraCapability) -> bool:
        """Check if camera supports a specific capability"""
        return capability in self.capabilities
    
    def is_healthy(self) -> bool:
        """Check if camera is currently healthy"""
        return self.health is not None and self.health.is_healthy()
    
    def supports_remote_control(self) -> bool:
        """Check if camera can be controlled remotely"""
        return self.has_capability(CameraCapability.REMOTE_CONTROL)
