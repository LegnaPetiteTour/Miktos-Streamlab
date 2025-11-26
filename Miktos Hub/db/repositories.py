"""
Repository Layer for Database Operations

Provides high-level database operations for sessions, cameras, and scenes.
"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models import (
    SessionModel,
    SessionCameraModel,
    CameraModel,
    SceneModel,
    SessionState,
)
from models.session import Session as CoreSession
from models.camera import CameraDevice
from models.scene import Scene as CoreScene

logger = logging.getLogger(__name__)


class SessionRepository:
    """
    Repository for session persistence operations.

    Handles converting between core models and database models.
    """

    def __init__(self, db_session: Session):
        """
        Initialize repository.

        Args:
            db_session: SQLAlchemy database session
        """
        self._db = db_session

    def create(self, session: CoreSession) -> SessionModel:
        """
        Persist a new session.

        Args:
            session: Core session model

        Returns:
            Database session model
        """
        try:
            db_session = SessionModel(
                id=session.id,
                name=session.name,
                description=session.description,
                state=SessionState(session.state.value),
                started_at=session.started_at,
                ended_at=session.ended_at,
                extra_data={}
            )

            self._db.add(db_session)
            self._db.commit()
            self._db.refresh(db_session)

            logger.info(f"Persisted session: {session.id}")
            return db_session

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to create session: {e}", exc_info=True)
            raise

    def get(self, session_id: str) -> Optional[SessionModel]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session model or None
        """
        return self._db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()

    def list_all(self) -> List[SessionModel]:
        """
        Get all sessions.

        Returns:
            List of session models
        """
        return self._db.query(SessionModel).all()

    def list_active(self) -> List[SessionModel]:
        """
        Get all active (non-ended) sessions.

        Returns:
            List of active session models
        """
        return self._db.query(SessionModel).filter(
            SessionModel.state.in_([
                SessionState.PREPARING,
                SessionState.READY,
                SessionState.LIVE,
                SessionState.PAUSED
            ])
        ).all()

    def update(self, session: CoreSession) -> SessionModel:
        """
        Update an existing session.

        Args:
            session: Core session model

        Returns:
            Updated database session model
        """
        try:
            db_session = self.get(session.id)
            if not db_session:
                raise ValueError(f"Session not found: {session.id}")

            # Update fields (type: ignore for SQLAlchemy ORM assignments)
            db_session.name = session.name  # type: ignore[assignment]
            db_session.description = (
                session.description  # type: ignore[assignment]
            )
            db_session.state = (
                SessionState(session.state.value)  # type: ignore[assignment]
            )
            db_session.started_at = (
                session.started_at  # type: ignore[assignment]
            )
            db_session.ended_at = (
                session.ended_at  # type: ignore[assignment]
            )
            db_session.extra_data = {}  # type: ignore[assignment]
            db_session.updated_at = datetime.utcnow()

            self._db.commit()
            self._db.refresh(db_session)

            logger.debug(f"Updated session: {session.id}")
            return db_session

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to update session: {e}", exc_info=True)
            raise

    def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted
        """
        try:
            db_session = self.get(session_id)
            if not db_session:
                return False

            self._db.delete(db_session)
            self._db.commit()

            logger.info(f"Deleted session: {session_id}")
            return True

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to delete session: {e}", exc_info=True)
            return False

    def add_camera(
        self, session_id: str, camera_id: str, position: int = 0
    ) -> bool:
        """
        Associate a camera with a session.

        Args:
            session_id: Session ID
            camera_id: Camera ID
            position: Camera position/order

        Returns:
            True if added
        """
        try:
            # Check if already associated
            existing = self._db.query(SessionCameraModel).filter(
                SessionCameraModel.session_id == session_id,
                SessionCameraModel.camera_id == camera_id
            ).first()

            if existing:
                logger.debug(
                    f"Camera {camera_id} already in session {session_id}"
                )
                return True

            association = SessionCameraModel(
                session_id=session_id,
                camera_id=camera_id,
                position=position,
                config={}
            )

            self._db.add(association)
            self._db.commit()

            logger.info(f"Added camera {camera_id} to session {session_id}")
            return True

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(
                f"Failed to add camera to session: {e}", exc_info=True
            )
            return False

    def remove_camera(self, session_id: str, camera_id: str) -> bool:
        """
        Remove a camera from a session.

        Args:
            session_id: Session ID
            camera_id: Camera ID

        Returns:
            True if removed
        """
        try:
            association = self._db.query(SessionCameraModel).filter(
                SessionCameraModel.session_id == session_id,
                SessionCameraModel.camera_id == camera_id
            ).first()

            if not association:
                return False

            self._db.delete(association)
            self._db.commit()

            logger.info(
                f"Removed camera {camera_id} from session {session_id}"
            )
            return True

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to remove camera from session: {e}")
            return False


class CameraRepository:
    """
    Repository for camera persistence operations.

    Handles saving and loading camera registrations.
    """

    def __init__(self, db_session: Session):
        """Initialize repository."""
        self._db = db_session

    def create(self, camera: CameraDevice) -> CameraModel:
        """
        Persist a camera registration.

        Args:
            camera: Core camera device model

        Returns:
            Database camera model
        """
        try:
            db_camera = CameraModel(
                id=camera.id,
                name=camera.label,
                stream_url=camera.url,
                discovery_method=camera.metadata.extra.get("discovery_method"),
                host=camera.metadata.extra.get("host"),
                port=camera.metadata.extra.get("port"),
                capabilities={
                    "transport": camera.transport.value,
                    "capabilities": [cap.value for cap in camera.capabilities],
                    "is_registered": camera.is_registered,
                },
                is_active=camera.is_registered,
                last_seen=datetime.utcnow()
            )

            self._db.add(db_camera)
            self._db.commit()
            self._db.refresh(db_camera)

            logger.info(f"Persisted camera: {camera.id} - {camera.label}")
            return db_camera

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to create camera: {e}", exc_info=True)
            raise

    def get(self, camera_id: str) -> Optional[CameraModel]:
        """
        Get a camera by ID.

        Args:
            camera_id: Camera ID

        Returns:
            Camera model or None
        """
        return self._db.query(CameraModel).filter(
            CameraModel.id == camera_id
        ).first()

    def list_all(self) -> List[CameraModel]:
        """
        Get all cameras.

        Returns:
            List of camera models
        """
        return self._db.query(CameraModel).all()

    def list_active(self) -> List[CameraModel]:
        """
        Get all active cameras.

        Returns:
            List of active camera models
        """
        return self._db.query(CameraModel).filter(
            CameraModel.is_active == True  # noqa: E712
        ).all()

    def update(self, camera: CameraDevice) -> CameraModel:
        """
        Update an existing camera.

        Args:
            camera: Core camera device model

        Returns:
            Updated database camera model
        """
        try:
            db_camera = self.get(camera.id)
            if not db_camera:
                raise ValueError(f"Camera not found: {camera.id}")

            # Update fields
            db_camera.name = camera.label  # type: ignore[assignment]
            db_camera.stream_url = camera.url  # type: ignore[assignment]
            db_camera.capabilities = {  # type: ignore[assignment]
                "transport": camera.transport.value,
                "capabilities": [cap.value for cap in camera.capabilities],
                "is_registered": camera.is_registered,
            }
            db_camera.is_active = (  # type: ignore[assignment]
                camera.is_registered  # type: ignore[assignment]
            )  # type: ignore[assignment]
            db_camera.last_seen = datetime.utcnow()  # type: ignore[assignment]
            db_camera.updated_at = datetime.utcnow()

            self._db.commit()
            self._db.refresh(db_camera)

            logger.debug(f"Updated camera: {camera.id}")
            return db_camera

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to update camera: {e}", exc_info=True)
            raise

    def delete(self, camera_id: str) -> bool:
        """
        Delete a camera.

        Args:
            camera_id: Camera ID

        Returns:
            True if deleted
        """
        try:
            db_camera = self.get(camera_id)
            if not db_camera:
                return False

            self._db.delete(db_camera)
            self._db.commit()

            logger.info(f"Deleted camera: {camera_id}")
            return True

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to delete camera: {e}", exc_info=True)
            return False

    def mark_inactive(self, camera_id: str) -> bool:
        """
        Mark a camera as inactive (soft delete).

        Args:
            camera_id: Camera ID

        Returns:
            True if marked inactive
        """
        try:
            db_camera = self.get(camera_id)
            if not db_camera:
                return False

            db_camera.is_active = False  # type: ignore[assignment]
            db_camera.updated_at = datetime.utcnow()
            self._db.commit()

            logger.info(f"Marked camera inactive: {camera_id}")
            return True

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to mark camera inactive: {e}")
            return False


class SceneRepository:
    """
    Repository for scene persistence operations.

    Handles saving and loading scene configurations.
    """

    def __init__(self, db_session: Session):
        """Initialize repository."""
        self._db = db_session

    def create(self, scene: CoreScene, session_id: str) -> SceneModel:
        """
        Persist a scene.

        Args:
            scene: Core scene model
            session_id: Associated session ID

        Returns:
            Database scene model
        """
        try:
            db_scene = SceneModel(
                id=scene.id,
                session_id=session_id,
                name=scene.name,
                layout=scene.layout.value,
                obs_scene_name=scene.extra.get("obs_scene_name"),
                sources=[
                    {
                        "id": src.id,
                        "type": src.type,
                        "device_id": src.device_id,
                        "file_path": src.file_path,
                        "x": src.x,
                        "y": src.y,
                        "width": src.width,
                        "height": src.height,
                        "z_index": src.z_index,
                        "opacity": src.opacity,
                        "visible": src.visible,
                        "rotation": src.rotation,
                        "scale": src.scale,
                        "filters": src.filters,
                        "include_audio": src.include_audio,
                        "audio_volume": src.audio_volume,
                    }
                    for src in scene.sources
                ],
                is_active=False,  # Scenes don't have is_active in core model
                transition=scene.default_transition,
                extra_data=scene.extra
            )

            self._db.add(db_scene)
            self._db.commit()
            self._db.refresh(db_scene)

            logger.info(
                f"Persisted scene: {scene.id} - {scene.name} "
                f"in session {session_id}"
            )
            return db_scene

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to create scene: {e}", exc_info=True)
            raise

    def get(self, scene_id: str) -> Optional[SceneModel]:
        """
        Get a scene by ID.

        Args:
            scene_id: Scene ID

        Returns:
            Scene model or None
        """
        return self._db.query(SceneModel).filter(
            SceneModel.id == scene_id
        ).first()

    def list_by_session(self, session_id: str) -> List[SceneModel]:
        """
        Get all scenes for a session.

        Args:
            session_id: Session ID

        Returns:
            List of scene models
        """
        return self._db.query(SceneModel).filter(
            SceneModel.session_id == session_id
        ).all()

    def update(self, scene: CoreScene) -> SceneModel:
        """
        Update an existing scene.

        Args:
            scene: Core scene model

        Returns:
            Updated database scene model
        """
        try:
            db_scene = self.get(scene.id)
            if not db_scene:
                raise ValueError(f"Scene not found: {scene.id}")

            # Update fields
            db_scene.name = scene.name  # type: ignore[assignment]
            db_scene.layout = scene.layout.value  # type: ignore[assignment]
            db_scene.obs_scene_name = (  # type: ignore[assignment]
                scene.extra.get("obs_scene_name")  # type: ignore[assignment]
            )  # type: ignore[assignment]
            db_scene.sources = [  # type: ignore[assignment]
                {
                    "id": src.id,
                    "type": src.type,
                    "device_id": src.device_id,
                    "file_path": src.file_path,
                    "x": src.x,
                    "y": src.y,
                    "width": src.width,
                    "height": src.height,
                    "z_index": src.z_index,
                    "opacity": src.opacity,
                    "visible": src.visible,
                    "rotation": src.rotation,
                    "scale": src.scale,
                    "filters": src.filters,
                    "include_audio": src.include_audio,
                    "audio_volume": src.audio_volume,
                }
                for src in scene.sources
            ]
            db_scene.is_active = False  # type: ignore[assignment]
            db_scene.transition = (  # type: ignore[assignment]
                scene.default_transition  # type: ignore[assignment]
            )  # type: ignore[assignment]
            db_scene.extra_data = scene.extra  # type: ignore[assignment]
            db_scene.updated_at = datetime.utcnow()

            self._db.commit()
            self._db.refresh(db_scene)

            logger.debug(f"Updated scene: {scene.id}")
            return db_scene

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to update scene: {e}", exc_info=True)
            raise

    def delete(self, scene_id: str) -> bool:
        """
        Delete a scene.

        Args:
            scene_id: Scene ID

        Returns:
            True if deleted
        """
        try:
            db_scene = self.get(scene_id)
            if not db_scene:
                return False

            self._db.delete(db_scene)
            self._db.commit()

            logger.info(f"Deleted scene: {scene_id}")
            return True

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to delete scene: {e}", exc_info=True)
            return False


# Export repository classes
__all__ = [
    "SessionRepository",
    "CameraRepository",
    "SceneRepository",
]
