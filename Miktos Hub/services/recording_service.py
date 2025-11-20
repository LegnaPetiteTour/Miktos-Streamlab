"""
Recording Service - Wraps existing ISO recording system

This service provides multi-track recording and replay buffer capabilities
by wrapping your existing iso_recording.py module.
"""

import sys
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from enum import Enum

# Add existing backend to path
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

try:
    from core.iso_recording import ISORecorder, ReplayBuffer
    RECORDING_AVAILABLE = True
except ImportError as e:
    ISORecorder = None
    ReplayBuffer = None
    RECORDING_AVAILABLE = False
    logging.warning(f"ISO recording module not available: {e}")

from config import get_config

logger = logging.getLogger(__name__)


class RecordingMode(Enum):
    """Recording modes"""
    PROGRAM_ONLY = "program_only"      # Only record final output
    ISO_ONLY = "iso_only"              # Only record individual camera ISOs
    PROGRAM_AND_ISO = "program_and_iso"  # Record both


class RecordingState(Enum):
    """Recording states"""
    IDLE = "idle"
    PREPARING = "preparing"
    RECORDING = "recording"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class RecordingConfig:
    """Recording configuration"""
    mode: RecordingMode
    output_directory: Path
    
    # Format settings
    video_codec: str = "h264_nvenc"  # or "libx264"
    audio_codec: str = "aac"
    video_bitrate: int = 8000  # kbps
    audio_bitrate: int = 192  # kbps
    
    # ISO settings
    record_cameras: List[str] = None  # Which cameras to record (None = all)
    
    # Replay buffer
    enable_replay_buffer: bool = True
    replay_buffer_duration: int = 300  # seconds (5 minutes)
    
    def __post_init__(self):
        if self.record_cameras is None:
            self.record_cameras = []


@dataclass
class RecordingInfo:
    """Information about an active recording"""
    session_id: str
    mode: RecordingMode
    state: RecordingState
    
    start_time: datetime
    duration_seconds: float
    
    # Files
    program_file: Optional[Path] = None
    iso_files: Dict[str, Path] = None
    
    # Stats
    file_size_mb: float = 0.0
    dropped_frames: int = 0
    
    def __post_init__(self):
        if self.iso_files is None:
            self.iso_files = {}


@dataclass
class ReplayClip:
    """A saved replay buffer clip"""
    id: str
    timestamp: datetime
    duration: float
    file_path: Path
    file_size_mb: float


class RecordingService:
    """
    Multi-track recording and replay buffer service.
    
    Manages ISO recording of individual cameras plus program output,
    with support for replay buffers and instant replay.
    
    Example:
        ```python
        service = RecordingService()
        
        # Configure recording
        config = RecordingConfig(
            mode=RecordingMode.PROGRAM_AND_ISO,
            output_directory=Path("/recordings"),
            enable_replay_buffer=True,
        )
        
        # Start recording
        await service.start_recording(
            session_id="show-001",
            config=config,
        )
        
        # Check status
        info = service.get_recording_info("show-001")
        print(f"Recording: {info.duration_seconds}s")
        print(f"Size: {info.file_size_mb:.1f} MB")
        
        # Save instant replay
        clip = await service.save_replay(
            session_id="show-001",
            duration=30.0  # Last 30 seconds
        )
        print(f"Saved replay: {clip.file_path}")
        
        # Stop recording
        await service.stop_recording("show-001")
        ```
    """
    
    def __init__(self):
        if not RECORDING_AVAILABLE:
            raise RuntimeError("ISO recording module not available - check backend installation")
        
        config = get_config()
        
        # Default recording directory
        self._recordings_dir = Path(config.paths.recordings_directory)
        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        
        # ISO recorder
        self._iso_recorder = ISORecorder(
            output_directory=str(self._recordings_dir),
        )
        
        # Replay buffer manager
        self._replay_buffer = ReplayBuffer(
            buffer_duration=300,  # 5 minutes default
        )
        
        # Active recordings
        self._active_recordings: Dict[str, RecordingInfo] = {}
        
        logger.info(f"Recording service initialized (directory: {self._recordings_dir})")
    
    async def start_recording(
        self,
        session_id: str,
        config: RecordingConfig,
    ) -> RecordingInfo:
        """
        Start recording a session.
        
        Args:
            session_id: Session to record
            config: Recording configuration
            
        Returns:
            Recording information
        """
        logger.info(f"Starting recording for session {session_id}, mode={config.mode.value}")
        
        if session_id in self._active_recordings:
            logger.warning(f"Recording already active for session {session_id}")
            return self._active_recordings[session_id]
        
        try:
            # Create session directory
            session_dir = config.output_directory / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Start program recording if needed
            program_file = None
            if config.mode in [RecordingMode.PROGRAM_ONLY, RecordingMode.PROGRAM_AND_ISO]:
                program_file = session_dir / f"program_{session_id}.mp4"
                
                await self._iso_recorder.start_program_recording(
                    output_path=str(program_file),
                    video_codec=config.video_codec,
                    audio_codec=config.audio_codec,
                    video_bitrate=config.video_bitrate,
                    audio_bitrate=config.audio_bitrate,
                )
                
                logger.info(f"Program recording started: {program_file}")
            
            # Start ISO recording if needed
            iso_files = {}
            if config.mode in [RecordingMode.ISO_ONLY, RecordingMode.PROGRAM_AND_ISO]:
                cameras = config.record_cameras if config.record_cameras else []
                
                for camera_id in cameras:
                    iso_file = session_dir / f"iso_{camera_id}_{session_id}.mp4"
                    
                    await self._iso_recorder.start_iso_recording(
                        camera_id=camera_id,
                        output_path=str(iso_file),
                        video_codec=config.video_codec,
                        audio_codec=config.audio_codec,
                        video_bitrate=config.video_bitrate,
                        audio_bitrate=config.audio_bitrate,
                    )
                    
                    iso_files[camera_id] = iso_file
                    logger.info(f"ISO recording started for {camera_id}: {iso_file}")
            
            # Start replay buffer if enabled
            if config.enable_replay_buffer:
                await self._replay_buffer.start(
                    session_id=session_id,
                    duration=config.replay_buffer_duration,
                )
                logger.info(f"Replay buffer enabled ({config.replay_buffer_duration}s)")
            
            # Create recording info
            info = RecordingInfo(
                session_id=session_id,
                mode=config.mode,
                state=RecordingState.RECORDING,
                start_time=datetime.now(),
                duration_seconds=0.0,
                program_file=program_file,
                iso_files=iso_files,
            )
            
            self._active_recordings[session_id] = info
            
            logger.info(f"Recording started successfully")
            return info
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}", exc_info=True)
            raise
    
    async def stop_recording(self, session_id: str) -> RecordingInfo:
        """
        Stop recording a session.
        
        Args:
            session_id: Session to stop recording
            
        Returns:
            Final recording information
        """
        logger.info(f"Stopping recording for session {session_id}")
        
        if session_id not in self._active_recordings:
            raise RuntimeError(f"No active recording for session {session_id}")
        
        info = self._active_recordings[session_id]
        
        try:
            # Stop program recording
            if info.program_file:
                await self._iso_recorder.stop_program_recording()
                logger.info("Program recording stopped")
            
            # Stop ISO recordings
            for camera_id in info.iso_files.keys():
                await self._iso_recorder.stop_iso_recording(camera_id)
                logger.info(f"ISO recording stopped for {camera_id}")
            
            # Stop replay buffer
            await self._replay_buffer.stop(session_id)
            logger.info("Replay buffer stopped")
            
            # Update info
            info.state = RecordingState.STOPPED
            info.duration_seconds = (datetime.now() - info.start_time).total_seconds()
            
            # Calculate total file size
            total_size = 0.0
            if info.program_file and info.program_file.exists():
                total_size += info.program_file.stat().st_size / (1024 * 1024)
            
            for iso_file in info.iso_files.values():
                if iso_file.exists():
                    total_size += iso_file.stat().st_size / (1024 * 1024)
            
            info.file_size_mb = total_size
            
            # Remove from active recordings
            del self._active_recordings[session_id]
            
            logger.info(
                f"Recording stopped - Duration: {info.duration_seconds:.1f}s, "
                f"Size: {info.file_size_mb:.1f} MB"
            )
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}", exc_info=True)
            info.state = RecordingState.ERROR
            raise
    
    async def pause_recording(self, session_id: str) -> bool:
        """
        Pause an active recording.
        
        Args:
            session_id: Session to pause
            
        Returns:
            True if paused successfully
        """
        logger.info(f"Pausing recording for session {session_id}")
        
        if session_id not in self._active_recordings:
            raise RuntimeError(f"No active recording for session {session_id}")
        
        info = self._active_recordings[session_id]
        
        try:
            await self._iso_recorder.pause()
            info.state = RecordingState.PAUSED
            logger.info("Recording paused")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause recording: {e}", exc_info=True)
            return False
    
    async def resume_recording(self, session_id: str) -> bool:
        """
        Resume a paused recording.
        
        Args:
            session_id: Session to resume
            
        Returns:
            True if resumed successfully
        """
        logger.info(f"Resuming recording for session {session_id}")
        
        if session_id not in self._active_recordings:
            raise RuntimeError(f"No active recording for session {session_id}")
        
        info = self._active_recordings[session_id]
        
        try:
            await self._iso_recorder.resume()
            info.state = RecordingState.RECORDING
            logger.info("Recording resumed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume recording: {e}", exc_info=True)
            return False
    
    def get_recording_info(self, session_id: str) -> Optional[RecordingInfo]:
        """
        Get information about an active recording.
        
        Args:
            session_id: Session to get info for
            
        Returns:
            Recording info or None if not recording
        """
        info = self._active_recordings.get(session_id)
        
        if info:
            # Update duration
            info.duration_seconds = (datetime.now() - info.start_time).total_seconds()
        
        return info
    
    def is_recording(self, session_id: str) -> bool:
        """Check if session is recording"""
        return session_id in self._active_recordings
    
    def list_active_recordings(self) -> List[str]:
        """Get list of sessions currently recording"""
        return list(self._active_recordings.keys())
    
    async def save_replay(
        self,
        session_id: str,
        duration: float = 30.0,
        name: Optional[str] = None,
    ) -> ReplayClip:
        """
        Save the last N seconds from replay buffer.
        
        Args:
            session_id: Session to save replay from
            duration: How many seconds to save
            name: Optional name for the clip
            
        Returns:
            Saved replay clip
        """
        logger.info(f"Saving replay for session {session_id} (duration={duration}s)")
        
        if not await self._replay_buffer.is_active(session_id):
            raise RuntimeError(f"Replay buffer not active for session {session_id}")
        
        try:
            import uuid
            
            # Generate clip ID
            clip_id = f"replay_{uuid.uuid4().hex[:8]}"
            
            # Generate filename
            if name:
                filename = f"replay_{name}_{session_id}.mp4"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"replay_{timestamp}_{session_id}.mp4"
            
            output_path = self._recordings_dir / session_id / filename
            
            # Save from replay buffer
            await self._replay_buffer.save(
                session_id=session_id,
                duration=duration,
                output_path=str(output_path),
            )
            
            # Get file size
            file_size = output_path.stat().st_size / (1024 * 1024)
            
            clip = ReplayClip(
                id=clip_id,
                timestamp=datetime.now(),
                duration=duration,
                file_path=output_path,
                file_size_mb=file_size,
            )
            
            logger.info(f"Replay saved: {output_path} ({file_size:.1f} MB)")
            return clip
            
        except Exception as e:
            logger.error(f"Failed to save replay: {e}", exc_info=True)
            raise
    
    async def get_replay_buffer_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get replay buffer status.
        
        Args:
            session_id: Session to check
            
        Returns:
            Buffer status information
        """
        try:
            status = await self._replay_buffer.get_status(session_id)
            return {
                "active": status.get("active", False),
                "duration": status.get("duration", 0),
                "buffer_size_mb": status.get("size_mb", 0.0),
                "available_duration": status.get("available_duration", 0.0),
            }
        except Exception as e:
            logger.error(f"Failed to get replay buffer status: {e}")
            return {
                "active": False,
                "duration": 0,
                "buffer_size_mb": 0.0,
                "available_duration": 0.0,
            }
    
    def set_recordings_directory(self, directory: Path) -> None:
        """
        Set the recordings output directory.
        
        Args:
            directory: New recordings directory
        """
        directory.mkdir(parents=True, exist_ok=True)
        self._recordings_dir = directory
        logger.info(f"Recordings directory set to: {directory}")
    
    def is_available(self) -> bool:
        """Check if recording module is available"""
        return RECORDING_AVAILABLE
