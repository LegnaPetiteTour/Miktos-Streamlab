"""
Session Models

A session represents one live show/stream from preparation through going live
to completion.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class SessionState(Enum):
    """Lifecycle states of a streaming session"""
    PREPARING = "preparing"  # Setting up cameras, scenes, destinations
    READY = "ready"          # All setup complete, ready to go live
    LIVE = "live"            # Currently streaming
    PAUSED = "paused"        # Stream temporarily paused
    ENDING = "ending"        # Shutting down stream
    COMPLETED = "completed"  # Stream ended successfully
    FAILED = "failed"        # Stream ended with errors


@dataclass
class SessionConfig:
    """Configuration for creating a new session"""
    name: str
    description: Optional[str] = None
    
    # What cameras to use
    camera_ids: List[str] = field(default_factory=list)
    
    # Where to stream
    destination_ids: List[str] = field(default_factory=list)
    
    # Engine to use (e.g., "obs", "epiphan", "vmix")
    engine_type: str = "obs"
    
    # Processing settings
    enable_audio_enhancement: bool = True
    enable_video_enhancement: bool = True
    enable_transcription: bool = False
    transcription_languages: List[str] = field(default_factory=lambda: ["en"])
    
    # Recording settings
    enable_recording: bool = True
    enable_iso_recording: bool = False  # Record each camera separately
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Extra configuration
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """
    Represents a complete streaming session.
    
    A session encapsulates everything needed for a show:
    - Cameras (inputs)
    - Scenes (composition)
    - Destinations (outputs)
    - Processing (enhancement, transcription)
    - State management (lifecycle)
    
    Example:
        ```python
        session = Session(
            name="City Council Meeting - Nov 20",
            config=SessionConfig(
                camera_ids=["phone-001", "phone-002", "phone-003"],
                destination_ids=["youtube-en", "youtube-fr", "facebook"],
                enable_transcription=True,
                transcription_languages=["en", "fr"],
            )
        )
        ```
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    
    # Configuration
    config: SessionConfig = field(default_factory=SessionConfig)
    
    # State
    state: SessionState = SessionState.PREPARING
    
    # Registered components
    camera_ids: List[str] = field(default_factory=list)
    scene_ids: List[str] = field(default_factory=list)
    destination_ids: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Runtime data
    active_scene_id: Optional[str] = None
    recording_path: Optional[str] = None
    transcript_path: Optional[str] = None
    
    # Health metrics (updated during stream)
    total_frames_sent: int = 0
    total_frames_dropped: int = 0
    average_bitrate_kbps: float = 0.0
    
    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    def is_live(self) -> bool:
        """Check if session is currently streaming"""
        return self.state == SessionState.LIVE
    
    def can_start(self) -> bool:
        """Check if session is ready to go live"""
        return (
            self.state in [SessionState.PREPARING, SessionState.READY]
            and len(self.camera_ids) > 0
            and len(self.destination_ids) > 0
        )
    
    def duration_seconds(self) -> Optional[float]:
        """Get session duration in seconds"""
        if self.started_at is None:
            return None
        end_time = self.ended_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    def add_error(self, error_type: str, message: str, details: Optional[Dict] = None):
        """Add an error to the session log"""
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": message,
            "details": details or {},
        })
    
    def add_warning(self, warning_type: str, message: str, details: Optional[Dict] = None):
        """Add a warning to the session log"""
        self.warnings.append({
            "timestamp": datetime.now().isoformat(),
            "type": warning_type,
            "message": message,
            "details": details or {},
        })
