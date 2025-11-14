"""
Storage Manager for ISO Recording System

Manages disk space, cleanup policies, archival, and integrity verification
for recording sessions.
"""

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class StorageStats:
    """
    Storage statistics.

    Attributes:
        total_gb: Total storage capacity
        used_gb: Used storage space
        free_gb: Free storage space
        recordings_gb: Space used by recordings
        session_count: Number of sessions
        oldest_session: Oldest session date
        newest_session: Newest session date
    """

    total_gb: float
    used_gb: float
    free_gb: float
    recordings_gb: float
    session_count: int
    oldest_session: Optional[datetime] = None
    newest_session: Optional[datetime] = None

    @property
    def used_percent(self) -> float:
        """Calculate used percentage"""
        if self.total_gb == 0:
            return 0.0
        return (self.used_gb / self.total_gb) * 100

    @property
    def free_percent(self) -> float:
        """Calculate free percentage"""
        if self.total_gb == 0:
            return 0.0
        return (self.free_gb / self.total_gb) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_gb": self.total_gb,
            "used_gb": self.used_gb,
            "free_gb": self.free_gb,
            "recordings_gb": self.recordings_gb,
            "session_count": self.session_count,
            "used_percent": self.used_percent,
            "free_percent": self.free_percent,
            "oldest_session": (
                self.oldest_session.isoformat()
                if self.oldest_session
                else None
            ),
            "newest_session": (
                self.newest_session.isoformat()
                if self.newest_session
                else None
            ),
        }


@dataclass
class SessionInfo:
    """
    Recording session information.

    Attributes:
        session_id: Unique session ID
        session_name: Session name
        path: Session directory path
        created_at: Creation timestamp
        size_mb: Total session size
        program_size_mb: Program output size
        track_count: Number of ISO tracks
        has_backup: Whether backup exists
        is_complete: Whether session is complete
        metadata: Session metadata
    """

    session_id: str
    session_name: str
    path: Path
    created_at: datetime
    size_mb: float = 0.0
    program_size_mb: float = 0.0
    track_count: int = 0
    has_backup: bool = False
    is_complete: bool = False
    metadata: Dict = field(default_factory=dict)

    @property
    def age_days(self) -> float:
        """Calculate session age in days"""
        delta = datetime.now() - self.created_at
        return delta.total_seconds() / 86400

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "path": str(self.path),
            "created_at": self.created_at.isoformat(),
            "size_mb": self.size_mb,
            "program_size_mb": self.program_size_mb,
            "track_count": self.track_count,
            "has_backup": self.has_backup,
            "is_complete": self.is_complete,
            "age_days": self.age_days,
            "metadata": self.metadata,
        }


class StorageManager:
    """
    Manages storage for ISO recordings.

    Features:
    - Disk space monitoring
    - Automatic cleanup policies
    - Session archival
    - Integrity verification
    """

    def __init__(
        self,
        base_path: Path,
        min_free_gb: float = 50.0,
        max_age_days: int = 90,
        max_sessions: int = 100,
    ) -> None:
        """
        Initialize storage manager.

        Args:
            base_path: Base recordings directory
            min_free_gb: Minimum free space to maintain
            max_age_days: Maximum session age before cleanup
            max_sessions: Maximum number of sessions to keep
        """
        self.base_path = Path(base_path)
        self.min_free_gb = min_free_gb
        self.max_age_days = max_age_days
        self.max_sessions = max_sessions
        self.logger = logging.getLogger(__name__)

        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_storage_stats(self) -> StorageStats:
        """Get current storage statistics"""
        try:
            # Get disk usage
            usage = shutil.disk_usage(self.base_path)
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)

            # Get recordings info
            sessions = self.list_sessions()
            recordings_gb = sum(s.size_mb for s in sessions) / 1024

            oldest = min(
                (s.created_at for s in sessions), default=None
            )
            newest = max(
                (s.created_at for s in sessions), default=None
            )

            return StorageStats(
                total_gb=total_gb,
                used_gb=used_gb,
                free_gb=free_gb,
                recordings_gb=recordings_gb,
                session_count=len(sessions),
                oldest_session=oldest,
                newest_session=newest,
            )

        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return StorageStats(
                total_gb=0.0,
                used_gb=0.0,
                free_gb=0.0,
                recordings_gb=0.0,
                session_count=0,
            )

    def list_sessions(self) -> List[SessionInfo]:
        """List all recording sessions"""
        sessions = []

        try:
            # Scan base path for session directories
            for session_dir in self.base_path.iterdir():
                if not session_dir.is_dir():
                    continue

                # Try to load session info
                session_info = self._load_session_info(session_dir)
                if session_info:
                    sessions.append(session_info)

        except Exception as e:
            self.logger.error(f"Failed to list sessions: {e}")

        # Sort by creation date (newest first)
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """Get information for specific session"""
        sessions = self.list_sessions()

        for session in sessions:
            if session.session_id == session_id:
                return session

        return None

    def cleanup_old_sessions(self) -> List[str]:
        """
        Clean up old sessions based on policies.

        Returns:
            List of deleted session IDs
        """
        deleted = []

        try:
            sessions = self.list_sessions()

            # Check if we need to clean up
            stats = self.get_storage_stats()

            # Delete by age
            cutoff_date = datetime.now() - timedelta(
                days=self.max_age_days
            )

            for session in sessions:
                should_delete = False

                # Check age policy
                if session.created_at < cutoff_date:
                    self.logger.info(
                        f"Session {session.session_id} "
                        f"exceeds max age ({session.age_days:.1f} days)"
                    )
                    should_delete = True

                # Check session count policy
                elif len(sessions) > self.max_sessions:
                    # Delete oldest sessions first
                    oldest_sessions = sorted(
                        sessions, key=lambda s: s.created_at
                    )

                    if session in oldest_sessions[
                        : len(sessions) - self.max_sessions
                    ]:
                        self.logger.info(
                            f"Session {session.session_id} "
                            "exceeds max session count"
                        )
                        should_delete = True

                # Check free space policy
                elif stats.free_gb < self.min_free_gb:
                    # Delete oldest sessions until we have enough space
                    self.logger.info(
                        f"Low disk space ({stats.free_gb:.1f}GB), "
                        f"deleting session {session.session_id}"
                    )
                    should_delete = True

                if should_delete:
                    if self.delete_session(session.session_id):
                        deleted.append(session.session_id)

                    # Refresh stats after deletion
                    stats = self.get_storage_stats()

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

        return deleted

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a recording session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            session = self.get_session_info(session_id)

            if not session:
                self.logger.warning(
                    f"Session {session_id} not found"
                )
                return False

            # Delete session directory
            shutil.rmtree(session.path)

            self.logger.info(
                f"Deleted session {session_id} "
                f"({session.size_mb:.1f}MB)"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to delete session {session_id}: {e}"
            )
            return False

    def verify_session_integrity(
        self, session_id: str
    ) -> Dict[str, bool]:
        """
        Verify session file integrity.

        Args:
            session_id: Session ID to verify

        Returns:
            Dictionary of verification results
        """
        results = {
            "metadata_exists": False,
            "program_exists": False,
            "iso_tracks_exist": False,
            "backup_exists": False,
            "logs_exist": False,
        }

        try:
            session = self.get_session_info(session_id)

            if not session:
                return results

            # Check metadata
            metadata_file = session.path / "metadata.json"
            results["metadata_exists"] = metadata_file.exists()

            # Check program output
            program_files = list(session.path.glob("program.*"))
            results["program_exists"] = len(program_files) > 0

            # Check ISO tracks
            iso_dir = session.path / "iso"
            if iso_dir.exists():
                iso_files = list(iso_dir.glob("*.*"))
                results["iso_tracks_exist"] = len(iso_files) > 0

            # Check backup
            backup_dir = session.path / "backup"
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.*"))
                results["backup_exists"] = len(backup_files) > 0

            # Check logs
            logs_dir = session.path / "logs"
            if logs_dir.exists():
                log_files = list(logs_dir.glob("*.log"))
                results["logs_exist"] = len(log_files) > 0

        except Exception as e:
            self.logger.error(
                f"Integrity verification failed for {session_id}: {e}"
            )

        return results

    def archive_session(
        self, session_id: str, archive_path: Path
    ) -> bool:
        """
        Archive a session to another location.

        Args:
            session_id: Session ID to archive
            archive_path: Destination archive directory

        Returns:
            True if archived successfully
        """
        try:
            session = self.get_session_info(session_id)

            if not session:
                self.logger.warning(
                    f"Session {session_id} not found"
                )
                return False

            # Create archive directory
            archive_path = Path(archive_path)
            archive_path.mkdir(parents=True, exist_ok=True)

            # Copy session to archive
            dest = archive_path / session.path.name
            shutil.copytree(session.path, dest)

            self.logger.info(
                f"Archived session {session_id} to {dest}"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to archive session {session_id}: {e}"
            )
            return False

    def _load_session_info(
        self, session_dir: Path
    ) -> Optional[SessionInfo]:
        """Load session information from directory"""
        try:
            # Load metadata
            metadata_file = session_dir / "metadata.json"

            if not metadata_file.exists():
                return None

            with open(metadata_file) as f:
                metadata = json.load(f)

            # Calculate session size
            size_mb = sum(
                f.stat().st_size
                for f in session_dir.rglob("*")
                if f.is_file()
            ) / (1024**2)

            # Get program size
            program_files = list(session_dir.glob("program.*"))
            program_size_mb = (
                sum(f.stat().st_size for f in program_files)
                / (1024**2)
                if program_files
                else 0.0
            )

            # Count ISO tracks
            iso_dir = session_dir / "iso"
            track_count = (
                len(list(iso_dir.glob("*.*"))) if iso_dir.exists() else 0
            )

            # Check backup
            backup_dir = session_dir / "backup"
            has_backup = backup_dir.exists() and len(
                list(backup_dir.glob("*.*"))
            ) > 0

            # Parse creation time from directory name
            # Format: YYYY-MM-DD_HH-MM-SS_SessionName
            dir_name = session_dir.name
            date_str = "_".join(dir_name.split("_")[:2])

            created_at = datetime.strptime(
                date_str, "%Y-%m-%d_%H-%M-%S"
            )

            return SessionInfo(
                session_id=metadata.get("session_id", ""),
                session_name=metadata.get("session_name", ""),
                path=session_dir,
                created_at=created_at,
                size_mb=size_mb,
                program_size_mb=program_size_mb,
                track_count=track_count,
                has_backup=has_backup,
                is_complete=True,
                metadata=metadata,
            )

        except Exception as e:
            self.logger.warning(
                f"Failed to load session info from {session_dir}: {e}"
            )
            return None
