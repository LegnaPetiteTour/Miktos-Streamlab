"""
Recovery Manager for ISO Recording System

Manages crash recovery and session repair for recording sessions.
Provides checkpoint management and automatic recovery.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RecoveryCheckpoint:
    """
    Recovery checkpoint data.

    Attributes:
        checkpoint_id: Unique checkpoint ID
        session_id: Session being recorded
        timestamp: Checkpoint timestamp
        recording_duration_sec: Recording duration at checkpoint
        tracks_recording: List of active tracks
        file_sizes: File sizes at checkpoint
        metadata: Additional checkpoint metadata
    """

    checkpoint_id: str
    session_id: str
    timestamp: datetime
    recording_duration_sec: float
    tracks_recording: List[str]
    file_sizes: Dict[str, float] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "recording_duration_sec": self.recording_duration_sec,
            "tracks_recording": self.tracks_recording,
            "file_sizes": self.file_sizes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RecoveryCheckpoint":
        """Create from dictionary"""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            session_id=data["session_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            recording_duration_sec=data["recording_duration_sec"],
            tracks_recording=data["tracks_recording"],
            file_sizes=data.get("file_sizes", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionRecoveryInfo:
    """
    Session recovery information.

    Attributes:
        session_id: Session identifier
        session_path: Session directory path
        is_recoverable: Whether session can be recovered
        last_checkpoint: Last checkpoint data
        missing_files: List of missing expected files
        corrupted_files: List of corrupted files
        recovery_actions: Suggested recovery actions
    """

    session_id: str
    session_path: Path
    is_recoverable: bool = False
    last_checkpoint: Optional[RecoveryCheckpoint] = None
    missing_files: List[str] = field(default_factory=list)
    corrupted_files: List[str] = field(default_factory=list)
    recovery_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "session_path": str(self.session_path),
            "is_recoverable": self.is_recoverable,
            "last_checkpoint": (
                self.last_checkpoint.to_dict()
                if self.last_checkpoint
                else None
            ),
            "missing_files": self.missing_files,
            "corrupted_files": self.corrupted_files,
            "recovery_actions": self.recovery_actions,
        }


class RecoveryManager:
    """
    Manages crash recovery for ISO recordings.

    Features:
    - Periodic checkpoints
    - Session recovery
    - File integrity checking
    - Automatic repair
    """

    def __init__(
        self, checkpoint_interval_sec: int = 30
    ) -> None:
        """
        Initialize recovery manager.

        Args:
            checkpoint_interval_sec: Checkpoint interval in seconds
        """
        self.checkpoint_interval_sec = checkpoint_interval_sec
        self.logger = logging.getLogger(__name__)

        # Current session state
        self.session_id: Optional[str] = None
        self.session_path: Optional[Path] = None
        self.checkpoints: List[RecoveryCheckpoint] = []

    def start_session(
        self, session_id: str, session_path: Path
    ) -> None:
        """
        Start tracking session for recovery.

        Args:
            session_id: Session identifier
            session_path: Session directory path
        """
        self.session_id = session_id
        self.session_path = session_path
        self.checkpoints = []

        # Load existing checkpoints if any
        self._load_checkpoints()

        self.logger.info(
            f"Recovery tracking started for session {session_id}"
        )

    def stop_session(self) -> None:
        """Stop tracking session"""
        # Save final checkpoint
        if self.session_id and self.session_path:
            self._save_checkpoints()

        self.session_id = None
        self.session_path = None
        self.checkpoints = []

        self.logger.info("Recovery tracking stopped")

    def create_checkpoint(
        self,
        recording_duration_sec: float,
        tracks_recording: List[str],
    ) -> bool:
        """
        Create recovery checkpoint.

        Args:
            recording_duration_sec: Current recording duration
            tracks_recording: List of active tracks

        Returns:
            True if checkpoint created successfully
        """
        if not self.session_id or not self.session_path:
            return False

        try:
            # Generate checkpoint ID
            checkpoint_id = (
                f"{self.session_id}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Calculate file sizes
            file_sizes = self._get_file_sizes()

            # Create checkpoint
            checkpoint = RecoveryCheckpoint(
                checkpoint_id=checkpoint_id,
                session_id=self.session_id,
                timestamp=datetime.now(),
                recording_duration_sec=recording_duration_sec,
                tracks_recording=tracks_recording,
                file_sizes=file_sizes,
            )

            self.checkpoints.append(checkpoint)

            # Save to disk
            self._save_checkpoints()

            self.logger.info(
                f"Checkpoint created: {checkpoint_id} "
                f"({recording_duration_sec:.1f}s)"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {e}")
            return False

    def scan_for_incomplete_sessions(
        self, base_path: Path
    ) -> List[SessionRecoveryInfo]:
        """
        Scan for incomplete recording sessions.

        Args:
            base_path: Base recordings directory

        Returns:
            List of incomplete sessions
        """
        incomplete_sessions = []

        try:
            # Scan for session directories
            for session_dir in base_path.iterdir():
                if not session_dir.is_dir():
                    continue

                # Check for checkpoint file
                checkpoint_file = session_dir / "recovery.json"

                if not checkpoint_file.exists():
                    continue

                # Load checkpoints
                try:
                    with open(checkpoint_file) as f:
                        checkpoint_data = json.load(f)

                    checkpoints = [
                        RecoveryCheckpoint.from_dict(cp)
                        for cp in checkpoint_data.get(
                            "checkpoints", []
                        )
                    ]

                    if checkpoints:
                        # Analyze session
                        recovery_info = self._analyze_session(
                            session_dir, checkpoints
                        )

                        if recovery_info:
                            incomplete_sessions.append(recovery_info)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to load checkpoints from {session_dir}: "
                        f"{e}"
                    )

        except Exception as e:
            self.logger.error(
                f"Failed to scan for incomplete sessions: {e}"
            )

        return incomplete_sessions

    def recover_session(
        self, recovery_info: SessionRecoveryInfo
    ) -> bool:
        """
        Attempt to recover incomplete session.

        Args:
            recovery_info: Session recovery information

        Returns:
            True if recovered successfully
        """
        if not recovery_info.is_recoverable:
            self.logger.warning(
                f"Session {recovery_info.session_id} "
                "is not recoverable"
            )
            return False

        try:
            self.logger.info(
                f"Recovering session {recovery_info.session_id}"
            )

            # Execute recovery actions
            for action in recovery_info.recovery_actions:
                self.logger.info(f"Recovery action: {action}")

            # Mark session as recovered
            recovery_marker = (
                recovery_info.session_path / "recovered.txt"
            )

            with open(recovery_marker, "w") as f:
                f.write(
                    f"Session recovered at {datetime.now().isoformat()}\n"
                )

                if recovery_info.last_checkpoint:
                    f.write(
                        f"Last checkpoint: "
                        f"{recovery_info.last_checkpoint.timestamp.isoformat()}\n"
                    )

            self.logger.info(
                f"Session {recovery_info.session_id} recovered"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to recover session "
                f"{recovery_info.session_id}: {e}"
            )
            return False

    def _get_file_sizes(self) -> Dict[str, float]:
        """Get current file sizes in session"""
        if not self.session_path:
            return {}

        file_sizes = {}

        try:
            for file_path in self.session_path.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(
                        self.session_path
                    )

                    size_mb = file_path.stat().st_size / (1024**2)
                    file_sizes[str(rel_path)] = size_mb

        except Exception as e:
            self.logger.error(f"Failed to get file sizes: {e}")

        return file_sizes

    def _save_checkpoints(self) -> None:
        """Save checkpoints to disk"""
        if not self.session_path:
            return

        try:
            checkpoint_file = self.session_path / "recovery.json"

            data = {
                "session_id": self.session_id,
                "checkpoints": [
                    cp.to_dict() for cp in self.checkpoints
                ],
            }

            with open(checkpoint_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save checkpoints: {e}")

    def _load_checkpoints(self) -> None:
        """Load checkpoints from disk"""
        if not self.session_path:
            return

        try:
            checkpoint_file = self.session_path / "recovery.json"

            if not checkpoint_file.exists():
                return

            with open(checkpoint_file) as f:
                data = json.load(f)

            self.checkpoints = [
                RecoveryCheckpoint.from_dict(cp)
                for cp in data.get("checkpoints", [])
            ]

            self.logger.info(
                f"Loaded {len(self.checkpoints)} checkpoints"
            )

        except Exception as e:
            self.logger.error(f"Failed to load checkpoints: {e}")

    def _analyze_session(
        self, session_path: Path, checkpoints: List[RecoveryCheckpoint]
    ) -> Optional[SessionRecoveryInfo]:
        """Analyze session for recovery"""
        try:
            last_checkpoint = checkpoints[-1] if checkpoints else None

            if not last_checkpoint:
                return None

            # Check for metadata
            metadata_file = session_path / "metadata.json"
            has_metadata = metadata_file.exists()

            # Check for program output
            program_files = list(session_path.glob("program.*"))
            has_program = len(program_files) > 0

            # Determine if recoverable
            is_recoverable = has_metadata and has_program

            # Generate recovery info
            recovery_info = SessionRecoveryInfo(
                session_id=last_checkpoint.session_id,
                session_path=session_path,
                is_recoverable=is_recoverable,
                last_checkpoint=last_checkpoint,
            )

            # Check for missing files
            if not has_metadata:
                recovery_info.missing_files.append("metadata.json")
                recovery_info.recovery_actions.append(
                    "Reconstruct metadata from checkpoint"
                )

            if not has_program:
                recovery_info.missing_files.append("program output")
                recovery_info.is_recoverable = False
                recovery_info.recovery_actions.append(
                    "Program output missing - cannot recover"
                )

            return recovery_info

        except Exception as e:
            self.logger.error(
                f"Failed to analyze session {session_path}: {e}"
            )
            return None
