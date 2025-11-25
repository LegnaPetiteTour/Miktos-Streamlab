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
    SessionState,
)
from models.session import Session as CoreSession

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


# Camera and Scene repositories will be implemented later


# Camera and Scene repositories will be implemented later
# when we add full camera and scene persistence
