"""
Miktos Hub Models

Data structures for cameras, sessions, scenes, destinations, and processing.
"""

from models.camera import (
    CameraDevice,
    CameraHealth,
    CameraCapability,
    CameraMetadata,
    TransportType,
)

from models.session import (
    Session,
    SessionState,
    SessionConfig,
)

from models.scene import (
    Scene,
    SceneLayout,
    TransitionType,
    SourceConfig,
)

from models.destination import (
    StreamDestination,
    DestinationType,
    DestinationStatus,
    DestinationHealth,
    Platform,  # Alias for DestinationType
)

from models.processing import (
    MediaProcessor,
    AudioProcessor,
    VideoProcessor,
    ProcessorType,
)

__all__ = [
    # Camera
    "CameraDevice",
    "CameraHealth",
    "CameraCapability",
    "CameraMetadata",
    "TransportType",
    # Session
    "Session",
    "SessionState",
    "SessionConfig",
    # Scene
    "Scene",
    "SceneLayout",
    "TransitionType",
    "SourceConfig",
    # Destination
    "StreamDestination",
    "DestinationType",
    "DestinationStatus",
    "DestinationHealth",
    "Platform",
    # Processing
    "MediaProcessor",
    "AudioProcessor",
    "VideoProcessor",
    "ProcessorType",
]
