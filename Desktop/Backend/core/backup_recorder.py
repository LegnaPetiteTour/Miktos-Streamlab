"""
Backup Recorder for ISO Recording System

Manages redundant recording to secondary storage with periodic sync
and verification.
"""

import asyncio
import hashlib
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BackupConfig:
    """
    Backup configuration.

    Attributes:
        enabled: Whether backup is enabled
        backup_path: Backup storage location
        sync_interval_sec: Sync interval in seconds
        verify_checksums: Whether to verify file checksums
        keep_incremental: Whether to keep incremental backups
        max_backup_age_days: Maximum backup age before cleanup
    """

    enabled: bool = True
    backup_path: Path = Path.home() / "Miktos_Backups"
    sync_interval_sec: int = 60
    verify_checksums: bool = True
    keep_incremental: bool = False
    max_backup_age_days: int = 30

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "enabled": self.enabled,
            "backup_path": str(self.backup_path),
            "sync_interval_sec": self.sync_interval_sec,
            "verify_checksums": self.verify_checksums,
            "keep_incremental": self.keep_incremental,
            "max_backup_age_days": self.max_backup_age_days,
        }


@dataclass
class BackupStats:
    """
    Backup statistics.

    Attributes:
        session_id: Session being backed up
        last_sync: Last sync timestamp
        files_backed_up: Number of files backed up
        total_size_mb: Total backup size
        failed_files: List of failed file paths
        checksum_mismatches: List of checksum mismatches
        is_syncing: Whether currently syncing
    """

    session_id: str
    last_sync: Optional[datetime] = None
    files_backed_up: int = 0
    total_size_mb: float = 0.0
    failed_files: List[str] = field(default_factory=list)
    checksum_mismatches: List[str] = field(default_factory=list)
    is_syncing: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "last_sync": (
                self.last_sync.isoformat() if self.last_sync else None
            ),
            "files_backed_up": self.files_backed_up,
            "total_size_mb": self.total_size_mb,
            "failed_files": self.failed_files,
            "checksum_mismatches": self.checksum_mismatches,
            "is_syncing": self.is_syncing,
        }


class BackupRecorder:
    """
    Manages backup recording to secondary storage.

    Features:
    - Periodic sync to backup location
    - Checksum verification
    - Incremental backups
    - Automatic cleanup
    """

    def __init__(self, config: BackupConfig) -> None:
        """
        Initialize backup recorder.

        Args:
            config: Backup configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Current backup state
        self.session_path: Optional[Path] = None
        self.backup_session_path: Optional[Path] = None
        self.stats: Optional[BackupStats] = None

        # Background tasks
        self.sync_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Ensure backup directory exists
        if self.config.enabled:
            self.config.backup_path.mkdir(parents=True, exist_ok=True)

    async def start_backup(
        self, session_id: str, session_path: Path
    ) -> bool:
        """
        Start backup for recording session.

        Args:
            session_id: Session ID
            session_path: Source session directory

        Returns:
            True if backup started successfully
        """
        try:
            if not self.config.enabled:
                self.logger.info("Backup disabled")
                return False

            self.session_path = session_path
            self.backup_session_path = (
                self.config.backup_path / session_path.name
            )

            # Create backup directory
            self.backup_session_path.mkdir(parents=True, exist_ok=True)

            # Initialize stats
            self.stats = BackupStats(session_id=session_id)

            # Start sync task
            self.is_running = True
            self.sync_task = asyncio.create_task(self._sync_loop())

            self.logger.info(
                f"Backup started for session {session_id} "
                f"to {self.backup_session_path}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to start backup: {e}")
            return False

    async def stop_backup(self) -> bool:
        """
        Stop backup and perform final sync.

        Returns:
            True if stopped successfully
        """
        try:
            self.is_running = False

            # Cancel sync task
            if self.sync_task:
                self.sync_task.cancel()

                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass

            # Perform final sync
            if self.session_path and self.backup_session_path:
                await self._sync_files()

            self.logger.info("Backup stopped")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop backup: {e}")
            return False

    def get_stats(self) -> Optional[BackupStats]:
        """Get current backup statistics"""
        return self.stats

    async def verify_backup(self) -> bool:
        """
        Verify backup integrity.

        Returns:
            True if backup is valid
        """
        try:
            if not self.session_path or not self.backup_session_path:
                return False

            if not self.config.verify_checksums:
                # Just check files exist
                return self._verify_files_exist()

            # Verify checksums
            return await self._verify_checksums()

        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False

    async def _sync_loop(self) -> None:
        """Background sync loop"""
        while self.is_running:
            try:
                # Perform sync
                await self._sync_files()

                # Wait for next sync interval
                await asyncio.sleep(self.config.sync_interval_sec)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(5)

    async def _sync_files(self) -> None:
        """Sync files to backup location"""
        if not self.session_path or not self.backup_session_path:
            return

        if not self.stats:
            return

        try:
            self.stats.is_syncing = True

            # Get all files from source
            source_files = [
                f
                for f in self.session_path.rglob("*")
                if f.is_file()
            ]

            # Sync each file
            for source_file in source_files:
                try:
                    # Get relative path
                    rel_path = source_file.relative_to(
                        self.session_path
                    )

                    dest_file = self.backup_session_path / rel_path

                    # Check if file needs to be copied
                    if self._needs_sync(source_file, dest_file):
                        # Create parent directory
                        dest_file.parent.mkdir(
                            parents=True, exist_ok=True
                        )

                        # Copy file
                        await asyncio.to_thread(
                            shutil.copy2, source_file, dest_file
                        )

                        self.stats.files_backed_up += 1

                        # Verify checksum if enabled
                        if self.config.verify_checksums:
                            if not await self._verify_file_checksum(
                                source_file, dest_file
                            ):
                                self.stats.checksum_mismatches.append(
                                    str(rel_path)
                                )

                except Exception as e:
                    self.logger.error(
                        f"Failed to sync {source_file}: {e}"
                    )
                    self.stats.failed_files.append(str(source_file))

            # Update stats
            self.stats.total_size_mb = (
                sum(
                    f.stat().st_size
                    for f in self.backup_session_path.rglob("*")
                    if f.is_file()
                )
                / (1024**2)
            )

            self.stats.last_sync = datetime.now()

        except Exception as e:
            self.logger.error(f"Sync failed: {e}")

        finally:
            if self.stats:
                self.stats.is_syncing = False

    def _needs_sync(
        self, source_file: Path, dest_file: Path
    ) -> bool:
        """Check if file needs to be synced"""
        # If destination doesn't exist, sync needed
        if not dest_file.exists():
            return True

        # If incremental backups disabled, skip if exists
        if not self.config.keep_incremental:
            return False

        # Check if source is newer
        source_mtime = source_file.stat().st_mtime
        dest_mtime = dest_file.stat().st_mtime

        return source_mtime > dest_mtime

    def _verify_files_exist(self) -> bool:
        """Verify all source files exist in backup"""
        if not self.session_path or not self.backup_session_path:
            return False

        try:
            source_files = [
                f.relative_to(self.session_path)
                for f in self.session_path.rglob("*")
                if f.is_file()
            ]

            for rel_path in source_files:
                dest_file = self.backup_session_path / rel_path

                if not dest_file.exists():
                    self.logger.warning(
                        f"Missing backup file: {rel_path}"
                    )
                    return False

            return True

        except Exception as e:
            self.logger.error(f"File existence check failed: {e}")
            return False

    async def _verify_checksums(self) -> bool:
        """Verify file checksums match"""
        if not self.session_path or not self.backup_session_path:
            return False

        try:
            source_files = [
                f
                for f in self.session_path.rglob("*")
                if f.is_file()
            ]

            for source_file in source_files:
                rel_path = source_file.relative_to(self.session_path)
                dest_file = self.backup_session_path / rel_path

                if not dest_file.exists():
                    self.logger.warning(
                        f"Missing backup file: {rel_path}"
                    )
                    return False

                # Verify checksum
                if not await self._verify_file_checksum(
                    source_file, dest_file
                ):
                    self.logger.warning(
                        f"Checksum mismatch: {rel_path}"
                    )
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Checksum verification failed: {e}")
            return False

    async def _verify_file_checksum(
        self, source_file: Path, dest_file: Path
    ) -> bool:
        """Verify checksums of two files match"""
        try:
            source_hash = await asyncio.to_thread(
                self._calculate_checksum, source_file
            )

            dest_hash = await asyncio.to_thread(
                self._calculate_checksum, dest_file
            )

            return source_hash == dest_hash

        except Exception as e:
            self.logger.error(
                f"Checksum calculation failed for {source_file}: {e}"
            )
            return False

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)

        return sha256.hexdigest()
