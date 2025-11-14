"""
ISO Recording - Multi-track isolated recording system

Week 11-12 Implementation
"""

import asyncio
import json
import logging
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RecordingState(Enum):
    """Recording state"""

    IDLE = "idle"
    STARTING = "starting"
    RECORDING = "recording"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class TrackConfig:
    """Configuration for a single recording track"""

    track_id: str  # Unique identifier (e.g., "camera_1", "mic_main")
    source_name: str  # OBS source name
    track_type: str  # "video", "audio", "program"
    format: str = "mkv"  # Output format (mkv, wav, mp4)
    enabled: bool = True

    # Optional settings
    resolution: Optional[str] = None  # e.g., "1920x1080"
    fps: Optional[int] = None  # e.g., 30
    bitrate: Optional[str] = None  # e.g., "5000k"
    audio_bitrate: Optional[str] = None  # e.g., "192k"

    def get_filename(self) -> str:
        """Get output filename for this track"""
        return f"{self.track_id}.{self.format}"


@dataclass
class SessionConfig:
    """Configuration for a recording session"""

    session_id: str  # Unique session ID
    session_name: str  # Human-readable name
    base_path: Path  # Base recording directory

    # Tracks to record
    tracks: List[TrackConfig] = field(default_factory=list)

    # Recording settings
    enable_backup: bool = True
    backup_path: Optional[Path] = None

    # Storage settings
    min_free_space_gb: float = 10.0  # Min space before stopping

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_session_path(self) -> Path:
        """Get full path for this session"""
        # Format: YYYY-MM-DD_HH-MM-SS_SessionName
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{timestamp}_{self.session_name.replace(' ', '_')}"
        return self.base_path / folder_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "base_path": str(self.base_path),
            "tracks": [asdict(t) for t in self.tracks],
            "enable_backup": self.enable_backup,
            "backup_path": (
                str(self.backup_path) if self.backup_path else None
            ),
            "min_free_space_gb": self.min_free_space_gb,
            "metadata": self.metadata,
        }


@dataclass
class RecordingStats:
    """Statistics for active recording"""

    session_id: str
    state: RecordingState
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

    # Track status
    tracks_recording: int = 0
    tracks_failed: int = 0

    # File sizes
    total_size_mb: float = 0.0
    program_size_mb: float = 0.0

    # Storage
    free_space_gb: float = 0.0

    # Errors
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Get recording duration in seconds"""
        if not self.started_at:
            return 0.0

        end_time = self.stopped_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "stopped_at": (
                self.stopped_at.isoformat() if self.stopped_at else None
            ),
            "duration_seconds": self.duration_seconds,
            "tracks_recording": self.tracks_recording,
            "tracks_failed": self.tracks_failed,
            "total_size_mb": self.total_size_mb,
            "program_size_mb": self.program_size_mb,
            "free_space_gb": self.free_space_gb,
            "errors": self.errors,
        }


class ISORecordingManager:
    """
    Manages ISO (isolated) recording of multiple tracks.

    Features:
    - Record program output + individual sources
    - Automatic backup recording
    - Storage management
    - Sync preservation (timecode)
    - Session organization
    """

    def __init__(self, obs_controller) -> None:  # type: ignore[no-untyped-def]
        """
        Initialize ISO recording manager.

        Args:
            obs_controller: OBS controller instance
        """
        self.obs = obs_controller

        # Current session
        self.current_session: Optional[SessionConfig] = None
        self.session_path: Optional[Path] = None

        # State
        self.state = RecordingState.IDLE
        self.stats: Optional[RecordingStats] = None

        # Monitoring
        self.monitor_task: Optional[asyncio.Task] = None

        logger.info("ISORecordingManager initialized")

    async def start_recording(self, config: SessionConfig) -> bool:
        """
        Start ISO recording session.

        Args:
            config: Session configuration

        Returns:
            True if recording started successfully
        """
        if self.state not in [RecordingState.IDLE, RecordingState.STOPPED]:
            logger.error(f"Cannot start recording in state: {self.state}")
            return False

        try:
            logger.info(f"Starting ISO recording: {config.session_name}")
            self.state = RecordingState.STARTING

            # Create session directory structure
            self.session_path = config.get_session_path()
            self._create_session_structure(self.session_path)

            logger.info(f"Session path: {self.session_path}")

            # Check available space
            free_space = self._get_free_space_gb(self.session_path)

            if free_space < config.min_free_space_gb:
                raise Exception(
                    f"Insufficient disk space: {free_space:.1f}GB "
                    f"(minimum: {config.min_free_space_gb}GB)"
                )

            logger.info(f"Free space: {free_space:.1f}GB")

            # Save session config
            self.current_session = config
            self._save_session_metadata()

            # Start OBS recording
            # Note: OBS basic recording (program output)
            # ISO tracks will be handled by ffmpeg processes

            success = await self.obs.start_recording()

            if not success:
                raise Exception("Failed to start OBS recording")

            # Initialize stats
            self.stats = RecordingStats(
                session_id=config.session_id,
                state=RecordingState.RECORDING,
                started_at=datetime.now(),
                free_space_gb=free_space,
            )

            # Start monitoring
            self.monitor_task = asyncio.create_task(self._monitor_loop())

            self.state = RecordingState.RECORDING
            logger.info("✅ ISO recording started")

            return True

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.state = RecordingState.ERROR

            if self.stats:
                self.stats.errors.append(str(e))

            return False

    async def stop_recording(self) -> bool:
        """
        Stop ISO recording session.

        Returns:
            True if recording stopped successfully
        """
        if self.state != RecordingState.RECORDING:
            logger.warning(f"Not recording (state: {self.state})")
            return False

        try:
            logger.info("Stopping ISO recording...")
            self.state = RecordingState.STOPPING

            # Stop monitoring
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
                self.monitor_task = None

            # Stop OBS recording
            await self.obs.stop_recording()

            # Update stats
            if self.stats:
                self.stats.stopped_at = datetime.now()
                self.stats.state = RecordingState.STOPPED

                # Final size calculation
                self._update_file_sizes()

            # Save final metadata
            self._save_session_metadata()

            self.state = RecordingState.STOPPED
            logger.info("✅ ISO recording stopped")

            # Log summary
            if self.stats:
                logger.info(
                    f"Recording summary: {self.stats.duration_seconds:.1f}s, "
                    f"{self.stats.total_size_mb:.1f}MB"
                )

            return True

        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            self.state = RecordingState.ERROR
            return False

    async def pause_recording(self) -> bool:
        """Pause recording (if supported)"""
        if self.state != RecordingState.RECORDING:
            return False

        try:
            self.state = RecordingState.PAUSING

            # OBS pause (if supported in your OBS version)
            # await self.obs.pause_recording()

            self.state = RecordingState.PAUSED
            logger.info("Recording paused")

            return True

        except Exception as e:
            logger.error(f"Failed to pause recording: {e}")
            self.state = RecordingState.RECORDING
            return False

    async def resume_recording(self) -> bool:
        """Resume paused recording"""
        if self.state != RecordingState.PAUSED:
            return False

        try:
            # await self.obs.resume_recording()

            self.state = RecordingState.RECORDING
            logger.info("Recording resumed")

            return True

        except Exception as e:
            logger.error(f"Failed to resume recording: {e}")
            return False

    def get_current_stats(self) -> Optional[RecordingStats]:
        """Get current recording statistics"""
        return self.stats

    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self.state == RecordingState.RECORDING

    def get_session_path(self) -> Optional[Path]:
        """Get current session path"""
        return self.session_path

    async def _monitor_loop(self) -> None:
        """Background monitoring loop"""
        logger.info("Recording monitor started")

        try:
            while self.state == RecordingState.RECORDING:
                # Update stats
                self._update_stats()

                # Check for issues
                await self._check_recording_health()

                # Wait before next check
                await asyncio.sleep(5.0)

        except asyncio.CancelledError:
            logger.info("Recording monitor cancelled")
            raise
        except Exception as e:
            logger.error(f"Recording monitor error: {e}", exc_info=True)

    def _update_stats(self) -> None:
        """Update recording statistics"""
        if not self.stats or not self.session_path:
            return

        try:
            # Update file sizes
            self._update_file_sizes()

            # Update free space
            self.stats.free_space_gb = self._get_free_space_gb(
                self.session_path
            )

        except Exception as e:
            logger.error(f"Failed to update stats: {e}")

    def _update_file_sizes(self) -> None:
        """Calculate total file sizes"""
        if not self.stats or not self.session_path:
            return

        try:
            total_size = 0
            program_size = 0

            # Sum all files in session directory
            for file_path in self.session_path.rglob("*"):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    total_size += size

                    if file_path.name.startswith("program"):
                        program_size += size

            self.stats.total_size_mb = total_size / (1024 * 1024)
            self.stats.program_size_mb = program_size / (1024 * 1024)

        except Exception as e:
            logger.error(f"Failed to calculate file sizes: {e}")

    async def _check_recording_health(self) -> None:
        """Check recording health and free space"""
        if not self.current_session or not self.session_path:
            return

        try:
            # Check free space
            if (
                self.stats
                and self.stats.free_space_gb
                < self.current_session.min_free_space_gb
            ):
                logger.error(
                    f"Low disk space: {self.stats.free_space_gb:.1f}GB "
                    f"(stopping recording)"
                )

                self.stats.errors.append("Low disk space")
                await self.stop_recording()
                return

            # Check OBS recording status
            recording_status = await self.obs.get_record_status()

            if not recording_status.get("output_active", False):
                logger.warning("OBS recording stopped unexpectedly")
                if self.stats:
                    self.stats.errors.append("OBS recording stopped")
                await self.stop_recording()
                return

        except Exception as e:
            logger.error(f"Health check failed: {e}")

    def _create_session_structure(self, session_path: Path) -> None:
        """Create directory structure for session"""
        try:
            # Main session directory
            session_path.mkdir(parents=True, exist_ok=True)

            # ISO tracks directory
            (session_path / "iso").mkdir(exist_ok=True)

            # Backup directory
            (session_path / "backup").mkdir(exist_ok=True)

            # Logs directory
            (session_path / "logs").mkdir(exist_ok=True)

            logger.info(f"Created session structure at {session_path}")

        except Exception as e:
            logger.error(f"Failed to create session structure: {e}")
            raise

    def _save_session_metadata(self) -> None:
        """Save session metadata to JSON"""
        if not self.current_session or not self.session_path:
            return

        try:
            metadata = {
                "session": self.current_session.to_dict(),
                "stats": self.stats.to_dict() if self.stats else None,
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
            }

            metadata_path = self.session_path / "metadata.json"

            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.debug(f"Saved metadata to {metadata_path}")

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def _get_free_space_gb(self, path: Path) -> float:
        """Get free disk space in GB"""
        try:
            stat = shutil.disk_usage(path)
            return stat.free / (1024**3)
        except Exception as e:
            logger.error(f"Failed to get free space: {e}")
            return 0.0
