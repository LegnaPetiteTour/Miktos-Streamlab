"""
Core Service Interfaces

Defines Protocol interfaces that all core services must implement.
Using Protocol (structural subtyping) allows for easy testing and flexibility.
"""

from typing import Protocol, List, Optional, Dict, Any
from models.camera import CameraDevice, CameraHealth
from models.session import Session, SessionConfig, SessionState
from models.scene import Scene, SourceConfig
from models.destination import StreamDestination, DestinationHealth
from models.processing import MediaProcessor, AudioProcessor, VideoProcessor


class DeviceRegistryProtocol(Protocol):
    """
    Interface for the Device Registry service.

    The Device Registry tracks all cameras (phones, webcams, etc.)
    and provides a unified way to access them.
    """

    def register(self, device: CameraDevice) -> None:
        """Register a new camera device"""
        ...

    def unregister(self, device_id: str) -> None:
        """Unregister a camera device"""
        ...

    def get(self, device_id: str) -> Optional[CameraDevice]:
        """Get a specific camera by ID"""
        ...

    def list_all(self) -> List[CameraDevice]:
        """List all registered cameras"""
        ...

    def update_health(self, device_id: str, health: CameraHealth) -> None:
        """Update health metrics for a camera"""
        ...

    def get_by_capability(self, capability: str) -> List[CameraDevice]:
        """Get all cameras with a specific capability"""
        ...


class StreamRouterProtocol(Protocol):
    """
    Interface for the Stream Router service.

    The Stream Router manages the routing of cameras → scenes → outputs.
    It decouples inputs from composition from destinations.
    """

    def attach_camera_to_scene(self, camera_id: str, scene_id: str) -> None:
        """Attach a camera to a scene"""
        ...

    def detach_camera_from_scene(self, camera_id: str, scene_id: str) -> None:
        """Detach a camera from a scene"""
        ...

    def route_scene_to_output(self, scene_id: str, destination_id: str) -> None:
        """Route a scene's output to a destination"""
        ...

    def unroute_scene_from_output(self, scene_id: str, destination_id: str) -> None:
        """Unroute a scene from a destination"""
        ...

    def get_scene_cameras(self, scene_id: str) -> List[str]:
        """Get all cameras attached to a scene"""
        ...

    def get_active_routes(self) -> List[Dict[str, Any]]:
        """Get all active routes (camera → scene → destination)"""
        ...


class SessionManagerProtocol(Protocol):
    """
    Interface for the Session Manager service.

    The Session Manager handles the complete lifecycle of a streaming session
    from creation through going live to completion.
    """

    def create_session(self, config: SessionConfig) -> Session:
        """Create a new session"""
        ...

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session"""
        ...

    def list_sessions(self) -> List[Session]:
        """List all sessions"""
        ...

    def start_session(self, session_id: str) -> None:
        """Start streaming (go live)"""
        ...

    def pause_session(self, session_id: str) -> None:
        """Temporarily pause streaming"""
        ...

    def resume_session(self, session_id: str) -> None:
        """Resume a paused session"""
        ...

    def stop_session(self, session_id: str) -> None:
        """Stop streaming and end session"""
        ...

    def get_session_state(self, session_id: str) -> SessionState:
        """Get current state of a session"""
        ...

    def get_active_session(self) -> Optional[Session]:
        """Get the currently live session (if any)"""
        ...


class EngineAdapterProtocol(Protocol):
    """
    Interface for streaming engine adapters (OBS, Epiphan, vMix, etc.).

    This is the key abstraction that allows the Hub to work with any engine.
    Each engine (OBS, Epiphan Pearl, vMix) implements this interface.
    """

    async def connect(self) -> None:
        """Connect to the engine"""
        ...

    async def disconnect(self) -> None:
        """Disconnect from the engine"""
        ...

    async def is_connected(self) -> bool:
        """Check if connected to engine"""
        ...

    # Scene management
    async def create_scene(self, scene: Scene) -> None:
        """Create a new scene in the engine"""
        ...

    async def delete_scene(self, scene_id: str) -> None:
        """Delete a scene"""
        ...

    async def list_scenes(self) -> List[str]:
        """List all scene IDs"""
        ...

    async def set_active_scene(self, scene_id: str) -> None:
        """Switch to a specific scene"""
        ...

    async def get_active_scene(self) -> Optional[str]:
        """Get the currently active scene ID"""
        ...

    # Source management
    async def add_source(self, scene_id: str, source: SourceConfig) -> None:
        """Add a source to a scene"""
        ...

    async def remove_source(self, scene_id: str, source_id: str) -> None:
        """Remove a source from a scene"""
        ...

    async def update_source(self, scene_id: str, source: SourceConfig) -> None:
        """Update source properties"""
        ...

    # Transitions
    async def transition(self, from_scene: str, to_scene: str, transition_type: str, duration_ms: int) -> None:
        """Transition from one scene to another"""
        ...

    # Streaming
    async def start_streaming(self, destination: StreamDestination) -> None:
        """Start streaming to a destination"""
        ...

    async def stop_streaming(self, destination_id: str) -> None:
        """Stop streaming to a destination"""
        ...

    async def is_streaming(self) -> bool:
        """Check if currently streaming"""
        ...

    # Recording
    async def start_recording(self, path: str) -> None:
        """Start recording"""
        ...

    async def stop_recording(self) -> None:
        """Stop recording"""
        ...

    # Health & metrics
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current engine metrics (FPS, dropped frames, etc.)"""
        ...


class ProcessingPipelineProtocol(Protocol):
    """
    Interface for the Processing Pipeline service.

    The Processing Pipeline chains audio/video processors together.
    """

    def add_processor(self, processor: MediaProcessor) -> None:
        """Add a processor to the pipeline"""
        ...

    def remove_processor(self, processor_id: str) -> None:
        """Remove a processor from the pipeline"""
        ...

    def get_processor(self, processor_id: str) -> Optional[MediaProcessor]:
        """Get a specific processor"""
        ...

    def list_processors(self) -> List[MediaProcessor]:
        """List all processors in the pipeline"""
        ...

    def enable_processor(self, processor_id: str) -> None:
        """Enable a processor"""
        ...

    def disable_processor(self, processor_id: str) -> None:
        """Disable a processor"""
        ...

    def clear_pipeline(self) -> None:
        """Remove all processors"""
        ...


class TranscriptionServiceProtocol(Protocol):
    """
    Interface for the Transcription Service.

    Handles live and post-stream transcription in multiple languages.
    """

    async def transcribe_live(self, audio_stream, languages: List[str]) -> Any:
        """Transcribe audio in real-time"""
        ...

    async def transcribe_file(self, file_path: str, languages: List[str]) -> Any:
        """Transcribe a recorded file"""
        ...

    async def export_transcript(self, transcript_id: str, format: str) -> str:
        """Export transcript in a specific format (SRT, VTT, TXT)"""
        ...


class ExportServiceProtocol(Protocol):
    """
    Interface for the Export/Edit Service.

    Handles cutting clips, resizing, adding captions, etc.
    """

    async def cut_clip(self, recording_path: str, start_time: float, end_time: float) -> str:
        """Cut a clip from a recording"""
        ...

    async def resize_video(self, video_path: str, target_aspect: str) -> str:
        """Resize video to target aspect ratio (16:9, 9:16, 1:1, etc.)"""
        ...

    async def add_captions(self, video_path: str, transcript_path: str) -> str:
        """Burn captions into video"""
        ...

    async def render(self, config: Dict[str, Any]) -> str:
        """Render video with specified configuration"""
        ...
