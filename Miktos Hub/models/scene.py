"""
Scene Models

Scenes define how cameras and sources are composed into the final output.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
import uuid


class SceneLayout(Enum):
    """Pre-defined scene layouts"""
    SINGLE_FULL = "single_full"  # One camera, full screen
    FULLSCREEN = "single_full"  # Alias for backward compatibility
    PICTURE_IN_PICTURE = "picture_in_picture"  # Main + small overlay
    SIDE_BY_SIDE = "side_by_side"  # Two cameras side-by-side
    SPLIT_HORIZONTAL = "side_by_side"  # Alias for side-by-side
    SPLIT_VERTICAL = "split_vertical"  # Two cameras stacked vertically
    GRID = "grid_2x2"  # Alias for 2x2 grid
    GRID_2X2 = "grid_2x2"  # Four cameras in 2x2 grid
    GRID_3X3 = "grid_3x3"  # Nine cameras in 3x3 grid
    CUSTOM = "custom"  # Custom positioning


class TransitionType(Enum):
    """Scene transition types"""
    CUT = "cut"  # Instant switch
    FADE = "fade"  # Crossfade
    SLIDE = "slide"  # Slide transition
    WIPE = "wipe"  # Wipe transition


@dataclass
class SourceConfig:
    """
    Configuration for a source within a scene.

    A source can be a camera, screen share, image, video, etc.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "camera"  # "camera", "screen", "image", "video", "text"

    # Reference to device/resource
    device_id: Optional[str] = None  # For cameras
    file_path: Optional[str] = None  # For images/videos

    # Position and size (normalized 0.0 - 1.0)
    x: float = 0.0  # Left position
    y: float = 0.0  # Top position
    width: float = 1.0  # Width
    height: float = 1.0  # Height

    # Display properties
    z_index: int = 0  # Layer order (higher = on top)
    opacity: float = 1.0  # 0.0 (transparent) to 1.0 (opaque)
    visible: bool = True

    # Transform
    rotation: float = 0.0  # Degrees
    scale: float = 1.0

    # Filters/effects
    filters: List[str] = field(default_factory=list)

    # Audio
    include_audio: bool = True
    audio_volume: float = 1.0  # 0.0 (muted) to 1.0 (full volume)

    # Extra configuration
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Scene:
    """
    A scene defines how sources are composed into the final output.

    Scenes can have multiple sources (cameras, images, text, etc.) positioned
    and layered to create the final composition.

    Example:
        ```python
        # Single camera full screen
        scene = Scene(
            name="Wide Shot",
            layout=SceneLayout.SINGLE_FULL,
            sources=[
                SourceConfig(
                    type="camera",
                    device_id="phone-001",
                    x=0.0, y=0.0,
                    width=1.0, height=1.0,
                )
            ]
        )

        # Picture-in-picture
        scene = Scene(
            name="Main + Speaker",
            layout=SceneLayout.PICTURE_IN_PICTURE,
            sources=[
                # Main camera (full screen, background)
                SourceConfig(
                    type="camera",
                    device_id="phone-001",
                    x=0.0, y=0.0,
                    width=1.0, height=1.0,
                    z_index=0,
                ),
                # Speaker camera (small overlay)
                SourceConfig(
                    type="camera",
                    device_id="phone-002",
                    x=0.7, y=0.7,
                    width=0.25, height=0.25,
                    z_index=1,
                ),
            ]
        )
        ```
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None

    # Layout
    layout: SceneLayout = SceneLayout.SINGLE_FULL

    # Sources in this scene
    sources: List[SourceConfig] = field(default_factory=list)

    # Transition settings
    default_transition: str = "fade"  # "cut", "fade", "slide", etc.
    transition_duration_ms: int = 300

    # Audio mixing
    audio_sources: List[str] = field(default_factory=list)  # Source IDs to mix

    # Extra configuration
    extra: Dict[str, Any] = field(default_factory=dict)

    def add_source(self, source: SourceConfig):
        """Add a source to the scene"""
        self.sources.append(source)

    def remove_source(self, source_id: str):
        """Remove a source from the scene"""
        self.sources = [s for s in self.sources if s.id != source_id]

    def get_source(self, source_id: str) -> Optional[SourceConfig]:
        """Get a specific source by ID"""
        for source in self.sources:
            if source.id == source_id:
                return source
        return None

    def get_camera_sources(self) -> List[SourceConfig]:
        """Get all camera sources in this scene"""
        return [s for s in self.sources if s.type == "camera"]
