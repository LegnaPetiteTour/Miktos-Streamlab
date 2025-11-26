"""
Tests for Database Persistence Layer

Tests for repositories and database operations.
"""

import pytest
import tempfile
from pathlib import Path
from typing import Generator

from db import Database
from db.repositories import (
    SessionRepository,
    CameraRepository,
    SceneRepository
)
from models import (
    CameraDevice,
    Scene,
    SceneLayout,
    SourceConfig,
    TransportType,
    CameraMetadata,
    Session,
    SessionState
)


# ============================================================================
# TEST DATABASE FIXTURE
# ============================================================================

@pytest.fixture
def test_db() -> Generator[Database, None, None]:
    """Provide a temporary test database"""
    # Create temp database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Initialize database
        db_url = f"sqlite:///{db_path}"
        db = Database(database_url=db_url)
        db.init_db()

        yield db

    finally:
        # Cleanup
        db._engine.dispose()
        Path(db_path).unlink(missing_ok=True)


# ============================================================================
# CAMERA REPOSITORY TESTS
# ============================================================================

@pytest.mark.unit
class TestCameraRepository:
    """Tests for CameraRepository"""

    def test_create_and_get_camera(self, test_db):
        """Test creating and retrieving a camera"""
        with test_db.session() as db_session:
            repo = CameraRepository(db_session)

            # Create camera device
            camera = CameraDevice(
                id="test-camera-1",
                label="Test Camera",
                transport=TransportType.SRT,
                url="srt://localhost:5000",
                metadata=CameraMetadata(
                    manufacturer="Sony",
                    model="a7 IV"
                ),
                is_registered=True
            )

            # Save to database
            saved = repo.create(camera)
            assert saved is not None

            # Retrieve camera
            retrieved = repo.get("test-camera-1")
            assert retrieved is not None
            assert str(retrieved.id) == "test-camera-1"
            assert str(retrieved.name) == "Test Camera"

    def test_list_cameras(self, test_db):
        """Test listing all cameras"""
        with test_db.session() as db_session:
            repo = CameraRepository(db_session)

            # Create multiple cameras
            for i in range(3):
                camera = CameraDevice(
                    id=f"camera-{i}",
                    label=f"Camera {i}",
                    transport=TransportType.SRT,
                    url=f"srt://localhost:{5000+i}",
                    is_registered=True
                )
                repo.create(camera)

            # List cameras
            cameras = repo.list_all()
            assert len(cameras) == 3

    def test_update_camera(self, test_db):
        """Test updating a camera"""
        with test_db.session() as db_session:
            repo = CameraRepository(db_session)

            # Create camera
            camera = CameraDevice(
                id="update-test",
                label="Original Label",
                transport=TransportType.SRT,
                url="srt://localhost:5000",
                is_registered=True
            )
            repo.create(camera)

            # Update camera
            camera.label = "Updated Label"
            camera.url = "srt://new-url:5000"
            updated = repo.update(camera)

            assert updated is not None
            # Verify by retrieving again
            retrieved = repo.get("update-test")
            assert retrieved is not None
            assert str(retrieved.name) == "Updated Label"

    def test_delete_camera(self, test_db):
        """Test deleting a camera"""
        with test_db.session() as db_session:
            repo = CameraRepository(db_session)

            # Create camera
            camera = CameraDevice(
                id="delete-test",
                label="To Delete",
                transport=TransportType.SRT,
                url="srt://localhost:5000",
                is_registered=True
            )
            repo.create(camera)

            # Delete camera
            result = repo.delete("delete-test")
            assert result is True

            # Verify deletion
            retrieved = repo.get("delete-test")
            assert retrieved is None

    def test_list_active_cameras(self, test_db):
        """Test listing only active cameras"""
        with test_db.session() as db_session:
            repo = CameraRepository(db_session)

            # Create active camera
            active_cam = CameraDevice(
                id="active-cam",
                label="Active",
                transport=TransportType.SRT,
                url="srt://localhost:5000",
                is_registered=True
            )
            repo.create(active_cam)

            # Create inactive camera
            inactive_cam = CameraDevice(
                id="inactive-cam",
                label="Inactive",
                transport=TransportType.SRT,
                url="srt://localhost:5001",
                is_registered=False
            )
            repo.create(inactive_cam)

            # List active only
            active_cameras = repo.list_active()
            assert len(active_cameras) == 1
            assert str(active_cameras[0].id) == "active-cam"


# ============================================================================
# SESSION REPOSITORY TESTS
# ============================================================================

@pytest.mark.unit
class TestSessionRepository:
    """Tests for SessionRepository"""

    def test_create_and_get_session(self, test_db):
        """Test creating and retrieving a session"""
        with test_db.session() as db_session:
            repo = SessionRepository(db_session)

            # Create session
            session = Session(
                id="test-session-1",
                name="Test Session",
                description="A test session",
                state=SessionState.PREPARING
            )

            saved = repo.create(session)
            assert saved is not None

            # Retrieve session
            retrieved = repo.get("test-session-1")
            assert retrieved is not None
            assert str(retrieved.id) == "test-session-1"
            assert str(retrieved.name) == "Test Session"

    def test_list_sessions(self, test_db):
        """Test listing all sessions"""
        with test_db.session() as db_session:
            repo = SessionRepository(db_session)

            # Create multiple sessions
            for i in range(3):
                session = Session(
                    id=f"session-{i}",
                    name=f"Session {i}",
                    state=SessionState.PREPARING
                )
                repo.create(session)

            # List sessions
            sessions = repo.list_all()
            assert len(sessions) == 3

    def test_update_session(self, test_db):
        """Test updating a session"""
        with test_db.session() as db_session:
            repo = SessionRepository(db_session)

            # Create session
            session = Session(
                id="update-test",
                name="Original Name",
                state=SessionState.PREPARING
            )
            repo.create(session)

            # Update session
            session.name = "Updated Name"
            session.state = SessionState.LIVE
            updated = repo.update(session)

            assert updated is not None
            # Verify by retrieving
            retrieved = repo.get("update-test")
            assert retrieved is not None
            assert str(retrieved.name) == "Updated Name"
            assert retrieved.state.value == SessionState.LIVE.value

    def test_list_active_sessions(self, test_db):
        """Test listing only active sessions"""
        with test_db.session() as db_session:
            repo = SessionRepository(db_session)

            # Create active session
            active = Session(
                id="active-1",
                name="Active",
                state=SessionState.LIVE
            )
            repo.create(active)

            # Create completed session
            completed = Session(
                id="completed-1",
                name="Completed",
                state=SessionState.COMPLETED
            )
            repo.create(completed)

            # List active sessions
            active_sessions = repo.list_active()
            assert len(active_sessions) == 1
            assert str(active_sessions[0].id) == "active-1"


# ============================================================================
# SCENE REPOSITORY TESTS
# ============================================================================

@pytest.mark.unit
class TestSceneRepository:
    """Tests for SceneRepository"""

    def test_create_and_get_scene(self, test_db):
        """Test creating and retrieving a scene"""
        with test_db.session() as db_session:
            # Create session first
            session_repo = SessionRepository(db_session)
            session = Session(
                id="test-session",
                name="Test Session",
                state=SessionState.PREPARING
            )
            session_repo.create(session)

            # Create scene
            scene_repo = SceneRepository(db_session)
            scene = Scene(
                id="test-scene-1",
                name="Test Scene",
                layout=SceneLayout.FULLSCREEN,
                sources=[
                    SourceConfig(
                        type="camera",
                        device_id="camera-1"
                    )
                ]
            )

            saved = scene_repo.create(scene, session_id="test-session")
            assert saved is not None

            # Retrieve scene
            retrieved = scene_repo.get("test-scene-1")
            assert retrieved is not None
            assert str(retrieved.id) == "test-scene-1"
            assert str(retrieved.name) == "Test Scene"

    def test_list_scenes_by_session(self, test_db):
        """Test listing scenes for a specific session"""
        with test_db.session() as db_session:
            # Create sessions
            session_repo = SessionRepository(db_session)
            session_a = Session(
                id="session-a",
                name="Session A",
                state=SessionState.PREPARING
            )
            session_repo.create(session_a)

            session_b = Session(
                id="session-b",
                name="Session B",
                state=SessionState.PREPARING
            )
            session_repo.create(session_b)

            # Create scenes for different sessions
            scene_repo = SceneRepository(db_session)

            scene_a1 = Scene(
                id="scene-a1",
                name="Scene A1",
                layout=SceneLayout.FULLSCREEN,
                sources=[]
            )
            scene_repo.create(scene_a1, session_id="session-a")

            scene_a2 = Scene(
                id="scene-a2",
                name="Scene A2",
                layout=SceneLayout.GRID,
                sources=[]
            )
            scene_repo.create(scene_a2, session_id="session-a")

            scene_b1 = Scene(
                id="scene-b1",
                name="Scene B1",
                layout=SceneLayout.FULLSCREEN,
                sources=[]
            )
            scene_repo.create(scene_b1, session_id="session-b")

            # List scenes for session-a
            session_a_scenes = scene_repo.list_by_session("session-a")
            assert len(session_a_scenes) == 2
            assert {s.id for s in session_a_scenes} == {"scene-a1", "scene-a2"}


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestPersistenceIntegration:
    """Integration tests for persistence layer"""

    def test_session_with_cameras_and_scenes(self, test_db):
        """Test creating a complete session with cameras and scenes"""
        with test_db.session() as db_session:
            # Create session
            session_repo = SessionRepository(db_session)
            session = Session(
                id="full-session",
                name="Full Integration Test",
                state=SessionState.LIVE
            )
            session_repo.create(session)

            # Create cameras
            camera_repo = CameraRepository(db_session)
            cam1 = CameraDevice(
                id="cam-1",
                label="Camera 1",
                transport=TransportType.SRT,
                url="srt://localhost:5000",
                is_registered=True
            )
            cam2 = CameraDevice(
                id="cam-2",
                label="Camera 2",
                transport=TransportType.RTMP,
                url="rtmp://localhost:1935/live",
                is_registered=True
            )
            camera_repo.create(cam1)
            camera_repo.create(cam2)

            # Create scenes
            scene_repo = SceneRepository(db_session)
            scene1 = Scene(
                id="scene-1",
                name="Single Camera",
                layout=SceneLayout.FULLSCREEN,
                sources=[SourceConfig(type="camera", device_id="cam-1")]
            )
            scene2 = Scene(
                id="scene-2",
                name="Multi Camera",
                layout=SceneLayout.SPLIT_HORIZONTAL,
                sources=[
                    SourceConfig(type="camera", device_id="cam-1"),
                    SourceConfig(type="camera", device_id="cam-2")
                ]
            )
            scene_repo.create(scene1, session_id="full-session")
            scene_repo.create(scene2, session_id="full-session")

            # Verify everything was created
            retrieved_session = session_repo.get("full-session")
            cameras = camera_repo.list_all()
            scenes = scene_repo.list_by_session("full-session")

            assert retrieved_session is not None
            assert len(cameras) == 2
            assert len(scenes) == 2
