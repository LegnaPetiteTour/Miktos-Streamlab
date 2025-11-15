"""
Unit tests for ISO Recording System core modules
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.backup_recorder import BackupConfig, BackupRecorder
from core.ffmpeg_recorder import FFmpegRecorder
from core.iso_recording import (
    ISORecordingManager,
    RecordingState,
    SessionConfig,
)
from core.performance_optimizer import (
    PerformanceOptimizer,
    PerformanceProfile,
)
from core.recovery_manager import RecoveryManager
from core.storage_manager import StorageManager
from core.timecode_sync import TimecodeSync


class TestISORecordingManager:
    """Test ISO Recording Manager"""

    @pytest.fixture
    def mock_obs(self):
        """Create mock OBS controller"""
        obs = MagicMock()
        obs.is_recording = MagicMock(return_value=False)
        obs.start_recording = AsyncMock(return_value=True)
        obs.stop_recording = AsyncMock(return_value=True)
        obs.get_record_status = AsyncMock(
            return_value={"output_active": True}
        )
        return obs

    @pytest.fixture
    def temp_session_path(self):
        """Create temporary session directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_manager_initialization(self, mock_obs):
        """Test manager initialization"""
        manager = ISORecordingManager(mock_obs)
        assert manager.obs == mock_obs
        assert manager.current_session is None
        assert manager.session_path is None

    @pytest.mark.asyncio
    async def test_start_recording(
        self, mock_obs, temp_session_path
    ):
        """Test starting recording session"""
        manager = ISORecordingManager(mock_obs)

        config = SessionConfig(
            session_id="test_session",
            session_name="Test Session",
            base_path=temp_session_path,
            tracks=[],
            min_free_space_gb=1.0,
        )

        result = await manager.start_recording(config)
        assert result is True
        assert manager.is_recording() is True
        assert manager.session_path is not None

        # Verify session structure created
        assert (manager.session_path / "iso").exists()
        assert (manager.session_path / "backup").exists()
        assert (manager.session_path / "logs").exists()

        # Stop recording
        await manager.stop_recording()

    @pytest.mark.asyncio
    async def test_recording_stats(self, mock_obs, temp_session_path):
        """Test recording statistics"""
        manager = ISORecordingManager(mock_obs)

        config = SessionConfig(
            session_id="test_session",
            session_name="Test Session",
            base_path=temp_session_path,
            tracks=[],
        )

        await manager.start_recording(config)

        stats = manager.get_current_stats()
        assert stats is not None
        assert stats.session_id == "test_session"
        assert stats.state == RecordingState.RECORDING

        await manager.stop_recording()


class TestStorageManager:
    """Test Storage Manager"""

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_storage_initialization(self, temp_storage_path):
        """Test storage manager initialization"""
        manager = StorageManager(
            base_path=temp_storage_path,
            min_free_gb=10.0,
            max_age_days=30,
        )

        assert manager.base_path == temp_storage_path
        assert manager.min_free_gb == 10.0
        assert manager.max_age_days == 30

    def test_get_storage_stats(self, temp_storage_path):
        """Test getting storage statistics"""
        manager = StorageManager(base_path=temp_storage_path)

        stats = manager.get_storage_stats()
        assert stats.total_gb > 0
        assert stats.free_gb > 0
        assert stats.session_count == 0

    def test_list_sessions_empty(self, temp_storage_path):
        """Test listing sessions with empty directory"""
        manager = StorageManager(base_path=temp_storage_path)

        sessions = manager.list_sessions()
        assert len(sessions) == 0


class TestFFmpegRecorder:
    """Test FFmpeg Recorder"""

    @pytest.mark.asyncio
    async def test_recorder_initialization(self):
        """Test FFmpeg recorder initialization"""
        recorder = FFmpegRecorder()
        assert len(recorder.processes) == 0

    @pytest.mark.asyncio
    async def test_track_state_check(self):
        """Test checking track recording state"""
        recorder = FFmpegRecorder()

        # Non-existent track should not be recording
        assert recorder.is_recording("track1") is False

        # State should be None for non-existent track
        assert recorder.get_process_state("track1") is None


class TestBackupRecorder:
    """Test Backup Recorder"""

    @pytest.fixture
    def temp_paths(self):
        """Create temporary paths for backup testing"""
        with tempfile.TemporaryDirectory() as session_dir:
            with tempfile.TemporaryDirectory() as backup_dir:
                yield Path(session_dir), Path(backup_dir)

    @pytest.mark.asyncio
    async def test_backup_initialization(self, temp_paths):
        """Test backup recorder initialization"""
        _, backup_path = temp_paths

        config = BackupConfig(
            enabled=True,
            backup_path=backup_path,
            sync_interval_sec=10,
        )

        recorder = BackupRecorder(config)
        assert recorder.config.enabled is True
        assert recorder.session_path is None

    @pytest.mark.asyncio
    async def test_start_backup(self, temp_paths):
        """Test starting backup"""
        session_path, backup_path = temp_paths

        config = BackupConfig(
            enabled=True, backup_path=backup_path
        )

        recorder = BackupRecorder(config)
        result = await recorder.start_backup(
            "test_session", session_path
        )

        assert result is True
        assert recorder.is_running is True

        # Stop backup
        await recorder.stop_backup()


class TestTimecodeSync:
    """Test Timecode Synchronization"""

    def test_sync_initialization(self):
        """Test timecode sync initialization"""
        sync = TimecodeSync(
            session_id="test_session",
            reference_track="track1",
            fps=30.0,
        )

        assert sync.session_id == "test_session"
        assert sync.reference_track == "track1"
        assert sync.fps == 30.0

    def test_frame_to_timecode_conversion(self):
        """Test frame number to timecode conversion"""
        sync = TimecodeSync(
            session_id="test", reference_track="track1", fps=30.0
        )

        # Test various frame numbers
        assert sync._frame_to_timecode(0) == "00:00:00:00"
        assert sync._frame_to_timecode(30) == "00:00:01:00"
        assert sync._frame_to_timecode(1800) == "00:01:00:00"
        assert sync._frame_to_timecode(108000) == "01:00:00:00"

    def test_timecode_to_frame_conversion(self):
        """Test timecode to frame number conversion"""
        sync = TimecodeSync(
            session_id="test", reference_track="track1", fps=30.0
        )

        # Test various timecodes
        assert sync._timecode_to_frame("00:00:00:00") == 0
        assert sync._timecode_to_frame("00:00:01:00") == 30
        assert sync._timecode_to_frame("00:01:00:00") == 1800
        assert sync._timecode_to_frame("01:00:00:00") == 108000


class TestRecoveryManager:
    """Test Recovery Manager"""

    @pytest.fixture
    def temp_session_path(self):
        """Create temporary session directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_recovery_initialization(self):
        """Test recovery manager initialization"""
        manager = RecoveryManager(checkpoint_interval_sec=30)
        assert manager.checkpoint_interval_sec == 30
        assert manager.session_id is None

    def test_start_session(self, temp_session_path):
        """Test starting recovery tracking"""
        manager = RecoveryManager()
        manager.start_session("test_session", temp_session_path)

        assert manager.session_id == "test_session"
        assert manager.session_path == temp_session_path

        manager.stop_session()

    def test_create_checkpoint(self, temp_session_path):
        """Test creating recovery checkpoint"""
        manager = RecoveryManager()
        manager.start_session("test_session", temp_session_path)

        result = manager.create_checkpoint(
            recording_duration_sec=60.0,
            tracks_recording=["track1", "track2"],
        )

        assert result is True
        assert len(manager.checkpoints) == 1

        manager.stop_session()


class TestPerformanceOptimizer:
    """Test Performance Optimizer"""

    def test_optimizer_initialization(self):
        """Test optimizer initialization"""
        optimizer = PerformanceOptimizer(
            profile=PerformanceProfile.BALANCED
        )

        assert optimizer.profile == PerformanceProfile.BALANCED

    def test_get_system_resources(self):
        """Test getting system resources"""
        optimizer = PerformanceOptimizer()
        resources = optimizer.get_system_resources()

        assert resources.cpu_count > 0
        assert resources.memory_total_gb > 0
        assert 0 <= resources.cpu_percent <= 100
        assert 0 <= resources.memory_percent <= 100

    def test_get_optimized_settings(self):
        """Test getting optimized settings"""
        optimizer = PerformanceOptimizer(
            profile=PerformanceProfile.HIGH
        )

        settings = optimizer.get_optimized_settings()

        assert settings.profile == PerformanceProfile.HIGH
        assert settings.max_parallel_tracks > 0
        assert settings.thread_count > 0

    def test_check_resource_availability(self):
        """Test resource availability check"""
        optimizer = PerformanceOptimizer()
        result = optimizer.check_resource_availability()

        # Should return a boolean
        assert isinstance(result, bool)
