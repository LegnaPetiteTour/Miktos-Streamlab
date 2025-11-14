"""
Timecode Synchronization for ISO Recording System

Manages timecode synchronization between multiple recording tracks
to ensure proper alignment during post-production.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TimecodeReference:
    """
    Timecode reference point.

    Attributes:
        track_id: Track identifier
        timestamp: Wall clock timestamp
        frame_number: Frame number at timestamp
        timecode: SMPTE timecode string (HH:MM:SS:FF)
        drift_ms: Detected drift in milliseconds
    """

    track_id: str
    timestamp: datetime
    frame_number: int
    timecode: str
    drift_ms: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "track_id": self.track_id,
            "timestamp": self.timestamp.isoformat(),
            "frame_number": self.frame_number,
            "timecode": self.timecode,
            "drift_ms": self.drift_ms,
        }


@dataclass
class SyncMetadata:
    """
    Synchronization metadata for session.

    Attributes:
        session_id: Session identifier
        reference_track: Primary reference track
        fps: Frames per second
        start_timecode: Session start timecode
        references: List of timecode reference points
        max_drift_ms: Maximum detected drift
        sync_warnings: List of sync warnings
    """

    session_id: str
    reference_track: str
    fps: float
    start_timecode: str
    references: List[TimecodeReference]
    max_drift_ms: float = 0.0
    sync_warnings: List[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Initialize mutable defaults"""
        if self.sync_warnings is None:
            self.sync_warnings = []

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "reference_track": self.reference_track,
            "fps": self.fps,
            "start_timecode": self.start_timecode,
            "references": [r.to_dict() for r in self.references],
            "max_drift_ms": self.max_drift_ms,
            "sync_warnings": self.sync_warnings,
        }


class TimecodeSync:
    """
    Manages timecode synchronization for ISO recordings.

    Features:
    - Track timecode references
    - Detect clock drift
    - Generate sync metadata
    - Validate track alignment
    """

    def __init__(
        self,
        session_id: str,
        reference_track: str,
        fps: float = 30.0,
    ) -> None:
        """
        Initialize timecode sync.

        Args:
            session_id: Session identifier
            reference_track: Primary reference track
            fps: Frames per second
        """
        self.session_id = session_id
        self.reference_track = reference_track
        self.fps = fps
        self.logger = logging.getLogger(__name__)

        # Sync state
        self.start_time: Optional[datetime] = None
        self.start_timecode: Optional[str] = None
        self.references: List[TimecodeReference] = []
        self.sync_warnings: List[str] = []

        # Monitoring
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_monitoring = False

    def start_sync(self, start_timecode: str = "00:00:00:00") -> None:
        """
        Start timecode synchronization.

        Args:
            start_timecode: Starting timecode (HH:MM:SS:FF)
        """
        self.start_time = datetime.now()
        self.start_timecode = start_timecode

        self.logger.info(
            f"Timecode sync started for session {self.session_id} "
            f"at {start_timecode}"
        )

    def stop_sync(self) -> None:
        """Stop timecode synchronization"""
        self.is_monitoring = False

        if self.monitor_task:
            self.monitor_task.cancel()

        self.logger.info("Timecode sync stopped")

    def add_reference(
        self, track_id: str, frame_number: int
    ) -> None:
        """
        Add timecode reference point.

        Args:
            track_id: Track identifier
            frame_number: Current frame number
        """
        if not self.start_time or not self.start_timecode:
            self.logger.warning("Sync not started")
            return

        # Calculate timecode from frame number
        timecode = self._frame_to_timecode(frame_number)

        # Create reference
        ref = TimecodeReference(
            track_id=track_id,
            timestamp=datetime.now(),
            frame_number=frame_number,
            timecode=timecode,
        )

        # Calculate drift if not reference track
        if track_id != self.reference_track:
            ref.drift_ms = self._calculate_drift(ref)

            # Check for significant drift
            if abs(ref.drift_ms) > 100:  # 100ms threshold
                warning = (
                    f"Track {track_id} has {ref.drift_ms:.1f}ms drift"
                )

                self.logger.warning(warning)
                self.sync_warnings.append(warning)

        self.references.append(ref)

    def get_sync_metadata(self) -> Optional[SyncMetadata]:
        """Get synchronization metadata"""
        if not self.start_timecode:
            return None

        # Calculate maximum drift
        max_drift = (
            max((abs(r.drift_ms) for r in self.references), default=0.0)
        )

        return SyncMetadata(
            session_id=self.session_id,
            reference_track=self.reference_track,
            fps=self.fps,
            start_timecode=self.start_timecode,
            references=self.references,
            max_drift_ms=max_drift,
            sync_warnings=self.sync_warnings,
        )

    def save_sync_metadata(self, output_path: Path) -> bool:
        """
        Save sync metadata to JSON file.

        Args:
            output_path: Output file path

        Returns:
            True if saved successfully
        """
        try:
            metadata = self.get_sync_metadata()

            if not metadata:
                return False

            with open(output_path, "w") as f:
                json.dump(metadata.to_dict(), f, indent=2)

            self.logger.info(f"Saved sync metadata to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save sync metadata: {e}")
            return False

    def _frame_to_timecode(self, frame_number: int) -> str:
        """Convert frame number to SMPTE timecode"""
        total_frames = frame_number

        # Calculate hours, minutes, seconds, frames
        fps_int = int(self.fps)

        frames = total_frames % fps_int
        total_seconds = total_frames // fps_int

        seconds = total_seconds % 60
        total_minutes = total_seconds // 60

        minutes = total_minutes % 60
        hours = total_minutes // 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

    def _timecode_to_frame(self, timecode: str) -> int:
        """Convert SMPTE timecode to frame number"""
        parts = timecode.split(":")

        if len(parts) != 4:
            return 0

        hours, minutes, seconds, frames = map(int, parts)

        fps_int = int(self.fps)

        total_frames = (
            (hours * 3600 + minutes * 60 + seconds) * fps_int
            + frames
        )

        return total_frames

    def _calculate_drift(self, ref: TimecodeReference) -> float:
        """
        Calculate drift for reference point.

        Returns:
            Drift in milliseconds
        """
        if not self.start_time:
            return 0.0

        # Find closest reference from reference track
        ref_track_refs = [
            r
            for r in self.references
            if r.track_id == self.reference_track
        ]

        if not ref_track_refs:
            return 0.0

        # Get closest reference by time
        closest_ref = min(
            ref_track_refs,
            key=lambda r: abs(
                (r.timestamp - ref.timestamp).total_seconds()
            ),
        )

        # Calculate expected time difference based on frame difference
        frame_diff = ref.frame_number - closest_ref.frame_number
        expected_time_ms = (frame_diff / self.fps) * 1000

        # Calculate actual time difference
        actual_time_ms = (
            ref.timestamp - closest_ref.timestamp
        ).total_seconds() * 1000

        # Drift is difference between actual and expected
        drift = actual_time_ms - expected_time_ms

        return drift
