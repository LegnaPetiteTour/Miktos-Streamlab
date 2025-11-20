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
    SourceConfig,
)

from models.destination import (
    StreamDestination,
    DestinationType,
    DestinationHealth,
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
    "SourceConfig",
    # Destination
    "StreamDestination",
    "DestinationType",
    "DestinationHealth",
    # Processing
    "MediaProcessor",
    "AudioProcessor",
    "VideoProcessor",
    "ProcessorType",
]
