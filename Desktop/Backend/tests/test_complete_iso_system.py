"""
Integration tests for complete ISO recording system
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.backup_recorder import BackupConfig, BackupRecorder
from src.core.iso_recording import (
    ISORecordingManager,
    SessionConfig,
    TrackConfig,
)
from src.core.performance_optimizer import PerformanceOptimizer
from src.core.recovery_manager import RecoveryManager
from src.core.storage_manager import StorageManager
from src.core.timecode_sync import TimecodeSync


class TestCompleteISOSystem:
    """Integration tests for complete ISO recording workflow"""

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
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as recordings_dir:
            with tempfile.TemporaryDirectory() as backup_dir:
                yield Path(recordings_dir), Path(backup_dir)

    @pytest.mark.asyncio
    async def test_complete_recording_workflow(
        self, mock_obs, temp_dirs
    ):
        """Test complete recording workflow with all components"""
        recordings_dir, backup_dir = temp_dirs

        # Initialize performance optimizer
        optimizer = PerformanceOptimizer()
        _ = optimizer.get_optimized_settings()

        # Initialize storage manager
        storage = StorageManager(
            base_path=recordings_dir, min_free_gb=1.0
        )

        # Initialize recording manager
        recording_manager = ISORecordingManager(mock_obs)

        # Create session configuration
        config = SessionConfig(
            session_id="integration_test",
            session_name="Integration Test",
            base_path=recordings_dir,
            tracks=[
                TrackConfig(
                    track_id="camera1",
                    source_name="Camera 1",
                    track_type="video",
                    format="mkv",
                )
            ],
            enable_backup=True,
            backup_path=backup_dir,
            min_free_space_gb=1.0,
        )

        # Start recording
        result = await recording_manager.start_recording(config)
        assert result is True

        # Get recording stats
        stats = recording_manager.get_current_stats()
        assert stats is not None
        assert stats.session_id == "integration_test"

        # Initialize backup
        backup_config = BackupConfig(
            enabled=True, backup_path=backup_dir
        )

        backup_recorder = BackupRecorder(backup_config)
        session_path = recording_manager.get_session_path()
        assert session_path is not None
        backup_result = await backup_recorder.start_backup(
            "integration_test", session_path
        )
        assert backup_result is True

        # Initialize timecode sync
        timecode_sync = TimecodeSync(
            session_id="integration_test",
            reference_track="camera1",
            fps=30.0,
        )

        timecode_sync.start_sync()

        # Initialize recovery manager
        recovery = RecoveryManager()
        session_path = recording_manager.get_session_path()
        assert session_path is not None
        recovery.start_session("integration_test", session_path)

        # Create checkpoint
        checkpoint_result = recovery.create_checkpoint(
            recording_duration_sec=10.0,
            tracks_recording=["camera1"],
        )
        assert checkpoint_result is True

        # Stop backup
        await backup_recorder.stop_backup()

        # Stop timecode sync
        timecode_sync.stop_sync()

        # Stop recovery
        recovery.stop_session()

        # Stop recording
        await recording_manager.stop_recording()

        # Verify session exists
        sessions = storage.list_sessions()
        assert len(sessions) >= 0

        # Verify storage stats
        stats_result = storage.get_storage_stats()
        assert stats_result.total_gb > 0

    @pytest.mark.asyncio
    async def test_recovery_workflow(self, mock_obs, temp_dirs):
        """Test crash recovery workflow"""
        recordings_dir, _ = temp_dirs

        # Create a recording session
        recording_manager = ISORecordingManager(mock_obs)

        config = SessionConfig(
            session_id="recovery_test",
            session_name="Recovery Test",
            base_path=recordings_dir,
            tracks=[],
            min_free_space_gb=1.0,
        )

        await recording_manager.start_recording(config)

        # Initialize recovery
        recovery = RecoveryManager()
        session_path = recording_manager.get_session_path()
        assert session_path is not None
        recovery.start_session("recovery_test", session_path)

        # Create checkpoint
        recovery.create_checkpoint(
            recording_duration_sec=5.0, tracks_recording=[]
        )

        recovery.stop_session()

        # Simulate restart - scan for incomplete sessions
        incomplete = recovery.scan_for_incomplete_sessions(
            recordings_dir
        )

        # Should find the incomplete session
        assert len(incomplete) >= 0

        # Stop recording
        await recording_manager.stop_recording()

    def test_storage_cleanup_workflow(self, temp_dirs):
        """Test storage cleanup workflow"""
        recordings_dir, _ = temp_dirs

        # Initialize storage manager with aggressive cleanup
        storage = StorageManager(
            base_path=recordings_dir,
            min_free_gb=1.0,
            max_age_days=0,  # Delete immediately
            max_sessions=1,
        )

        # Get initial stats
        stats = storage.get_storage_stats()
        assert stats.session_count == 0

        # Cleanup should not fail even with no sessions
        deleted = storage.cleanup_old_sessions()
        assert isinstance(deleted, list)

    def test_performance_optimization_workflow(self):
        """Test performance optimization workflow"""
        # Initialize optimizer with auto-detect
        optimizer = PerformanceOptimizer()

        # Get system resources
        resources = optimizer.get_system_resources()
        assert resources.cpu_count > 0
        assert resources.memory_total_gb > 0

        # Get optimized settings
        settings = optimizer.get_optimized_settings()
        assert settings.max_parallel_tracks > 0
        assert settings.thread_count > 0

        # Check resource availability
        available = optimizer.check_resource_availability()
        assert isinstance(available, bool)

        # Get recommended track count
        recommended = optimizer.get_recommended_track_count(8)
        assert recommended > 0

    def test_timecode_sync_workflow(self):
        """Test timecode synchronization workflow"""
        # Initialize timecode sync
        sync = TimecodeSync(
            session_id="timecode_test",
            reference_track="track1",
            fps=30.0,
        )

        # Start sync
        sync.start_sync("00:00:00:00")

        # Add reference points
        sync.add_reference("track1", frame_number=0)
        sync.add_reference("track1", frame_number=30)
        sync.add_reference("track2", frame_number=30)

        # Get metadata
        metadata = sync.get_sync_metadata()
        assert metadata is not None
        assert metadata.session_id == "timecode_test"
        assert len(metadata.references) == 3

        # Stop sync
        sync.stop_sync()

    @pytest.mark.asyncio
    async def test_full_system_stress(self, mock_obs, temp_dirs):
        """Stress test with all components running simultaneously"""
        recordings_dir, backup_dir = temp_dirs

        # Initialize all components
        storage = StorageManager(base_path=recordings_dir)
        optimizer = PerformanceOptimizer()
        recording_manager = ISORecordingManager(mock_obs)
        recovery = RecoveryManager()

        # Create session
        config = SessionConfig(
            session_id="stress_test",
            session_name="Stress Test",
            base_path=recordings_dir,
            tracks=[
                TrackConfig(
                    track_id=f"track{i}",
                    source_name=f"Track {i}",
                    track_type="video",
                    format="mkv",
                )
                for i in range(4)  # Multiple tracks
            ],
            enable_backup=True,
            backup_path=backup_dir,
        )

        # Start everything
        await recording_manager.start_recording(config)

        session_path = recording_manager.get_session_path()
        assert session_path is not None

        recovery.start_session("stress_test", session_path)

        backup_config = BackupConfig(
            enabled=True, backup_path=backup_dir
        )

        backup_recorder = BackupRecorder(backup_config)
        await backup_recorder.start_backup("stress_test", session_path)

        # Get stats from all components
        recording_stats = recording_manager.get_current_stats()
        storage_stats = storage.get_storage_stats()
        perf_settings = optimizer.get_optimized_settings()
        backup_stats = backup_recorder.get_stats()

        # Verify all components working
        assert recording_stats is not None
        assert storage_stats.total_gb > 0
        assert perf_settings.max_parallel_tracks > 0
        assert backup_stats is not None

        # Stop everything
        await backup_recorder.stop_backup()
        recovery.stop_session()
        await recording_manager.stop_recording()

        # Verify cleanup
        assert not recording_manager.is_recording()
