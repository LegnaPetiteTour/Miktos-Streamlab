"""
Session Manager - Manages streaming session lifecycle

A Session represents a complete streaming show:
- Configuration (cameras, scenes, destinations)
- State management (preparing → live → ended)
- Event tracking
- Recording management
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from models.session import Session, SessionState, SessionConfig
from models.destination import StreamDestination
from core.device_registry import DeviceRegistry
from core.stream_router import StreamRouter

logger = logging.getLogger(__name__)


@dataclass
class SessionEvent:
    """Event that occurred during a session"""
    timestamp: datetime
    type: str  # "camera_added", "stream_started", "error", etc.
    details: Dict
    severity: str = "info"  # "info", "warning", "error"


class SessionManager:
    """
    Manages the lifecycle of streaming sessions

    A session is the complete context for a show:
    - Which cameras are involved
    - What scenes exist
    - Where we're streaming to
    - Current state (preparing, live, ended)
    - All events that occurred
    """

    def __init__(
        self,
        device_registry: DeviceRegistry,
        stream_router: StreamRouter
    ):
        self._device_registry = device_registry
        self._stream_router = stream_router

        # Active sessions indexed by ID
        self._sessions: Dict[str, Session] = {}

        # Current active session (only one can be live at a time)
        self._active_session_id: Optional[str] = None

        logger.info("SessionManager initialized")

    def create_session(self, config: SessionConfig) -> Session:
        """
        Create a new session

        Args:
            config: Session configuration

        Returns:
            Created session
        """
        session = Session(
            name=config.name,
            description=config.description,
            config=config,
            state=SessionState.PREPARING,
        )

        self._sessions[session.id] = session
        self._log_event(session, "session_created", {"config": config.name})

        logger.info(f"Created session: {session.id} - {config.name}")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Session]:
        """List all sessions"""
        return list(self._sessions.values())

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: Session to delete

        Returns:
            True if deleted
        """
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]

        # Can't delete active session
        if session.state == SessionState.LIVE:
            logger.error(f"Cannot delete live session: {session_id}")
            return False

        # Clear routing if session was active
        if session.state in [SessionState.PAUSED, SessionState.ENDING]:
            self._clear_session_routes(session)

        # Remove session
        del self._sessions[session_id]

        if self._active_session_id == session_id:
            self._active_session_id = None

        logger.info(f"Deleted session: {session_id}")
        return True

    def start_session(self, session_id: str) -> bool:
        """
        Start a session (go live)

        Args:
            session_id: Session to start

        Returns:
            True if started successfully
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return False

        # Check if another session is active
        if self._active_session_id and self._active_session_id != session_id:
            logger.error(
                f"Another session is active: {
                    self._active_session_id}")
            return False

        # Can only start from PREPARING state
        if session.state != SessionState.PREPARING:
            logger.error(f"Cannot start session in state: {session.state}")
            return False

        # Validate session has required components
        if not session.cameras:
            logger.error("Cannot start session without cameras")
            return False

        if not session.destinations:
            logger.error("Cannot start session without destinations")
            return False

        # Activate all routes
        for camera in session.cameras:
            routes = self._stream_router.get_routes_for_camera(camera.id)
            for route in routes:
                self._stream_router.activate_route(route.id)

        # Update state
        session.state = SessionState.LIVE
        session.updated_at = datetime.now()
        self._active_session_id = session_id

        self._log_event(session, "session_started", {
            "cameras": len(session.cameras),
            "scenes": len(session.scenes),
            "destinations": len(session.destinations)
        })

        logger.info(f"Started session: {session_id}")
        return True

    def pause_session(self, session_id: str) -> bool:
        """
        Pause a session

        Args:
            session_id: Session to pause

        Returns:
            True if paused
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        if session.state != SessionState.LIVE:
            logger.error(f"Cannot pause session in state: {session.state}")
            return False

        # Deactivate all routes
        for camera in session.cameras:
            routes = self._stream_router.get_routes_for_camera(camera.id)
            for route in routes:
                self._stream_router.deactivate_route(route.id)

        session.state = SessionState.PAUSED
        session.updated_at = datetime.now()

        self._log_event(session, "session_paused", {})
        logger.info(f"Paused session: {session_id}")
        return True

    def resume_session(self, session_id: str) -> bool:
        """
        Resume a paused session

        Args:
            session_id: Session to resume

        Returns:
            True if resumed
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        if session.state != SessionState.PAUSED:
            logger.error(f"Cannot resume session in state: {session.state}")
            return False

        # Reactivate all routes
        for camera in session.cameras:
            routes = self._stream_router.get_routes_for_camera(camera.id)
            for route in routes:
                self._stream_router.activate_route(route.id)

        session.state = SessionState.LIVE
        session.updated_at = datetime.now()

        self._log_event(session, "session_resumed", {})
        logger.info(f"Resumed session: {session_id}")
        return True

    def end_session(self, session_id: str) -> bool:
        """
        End a session

        Args:
            session_id: Session to end

        Returns:
            True if ended
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        if session.state not in [SessionState.LIVE, SessionState.PAUSED]:
            logger.error(f"Cannot end session in state: {session.state}")
            return False

        # Clear all routes
        self._clear_session_routes(session)

        session.state = SessionState.ENDED
        session.updated_at = datetime.now()

        if self._active_session_id == session_id:
            self._active_session_id = None

        self._log_event(
            session, "session_ended", {
                "duration_seconds": (
                    datetime.now() - session.created_at).total_seconds()})

        logger.info(f"Ended session: {session_id}")
        return True

    def add_camera_to_session(
        self,
        session_id: str,
        camera_id: str
    ) -> bool:
        """
        Add a camera to a session

        Args:
            session_id: Target session
            camera_id: Camera to add

        Returns:
            True if added
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Get camera from registry
        camera = self._device_registry.get(camera_id)
        if not camera:
            logger.error(f"Camera not found: {camera_id}")
            return False

        # Check if already in session
        if any(c.id == camera_id for c in session.cameras):
            logger.warning(f"Camera already in session: {camera_id}")
            return False

        session.cameras.append(camera)
        session.updated_at = datetime.now()

        self._log_event(session, "camera_added", {"camera_id": camera_id})
        logger.info(f"Added camera {camera_id} to session {session_id}")
        return True

    def remove_camera_from_session(
        self,
        session_id: str,
        camera_id: str
    ) -> bool:
        """
        Remove a camera from a session

        Args:
            session_id: Target session
            camera_id: Camera to remove

        Returns:
            True if removed
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Find and remove camera
        original_count = len(session.cameras)
        session.cameras = [c for c in session.cameras if c.id != camera_id]

        if len(session.cameras) == original_count:
            logger.warning(f"Camera not in session: {camera_id}")
            return False

        # Clear routes involving this camera
        routes = self._stream_router.get_routes_for_camera(camera_id)
        for route in routes:
            self._stream_router.detach_camera_from_scene(
                camera_id, route.target_scene_id)

        session.updated_at = datetime.now()

        self._log_event(session, "camera_removed", {"camera_id": camera_id})
        logger.info(f"Removed camera {camera_id} from session {session_id}")
        return True

    def add_destination_to_session(
        self,
        session_id: str,
        destination: StreamDestination
    ) -> bool:
        """
        Add a streaming destination to a session

        Args:
            session_id: Target session
            destination: Destination to add

        Returns:
            True if added
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Check if already in session
        if any(d.id == destination.id for d in session.destinations):
            logger.warning(f"Destination already in session: {destination.id}")
            return False

        session.destinations.append(destination)
        session.updated_at = datetime.now()

        self._log_event(session, "destination_added", {
            "destination_id": destination.id,
            "platform": destination.platform
        })

        logger.info(
            f"Added destination {
                destination.id} to session {session_id}")
        return True

    def remove_destination_from_session(
        self,
        session_id: str,
        destination_id: str
    ) -> bool:
        """
        Remove a destination from a session

        Args:
            session_id: Target session
            destination_id: Destination to remove

        Returns:
            True if removed
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        original_count = len(session.destinations)
        session.destinations = [
            d for d in session.destinations if d.id != destination_id]

        if len(session.destinations) == original_count:
            logger.warning(f"Destination not in session: {destination_id}")
            return False

        session.updated_at = datetime.now()

        self._log_event(
            session, "destination_removed", {
                "destination_id": destination_id})
        logger.info(
            f"Removed destination {destination_id} from session {session_id}")
        return True

    def get_active_session(self) -> Optional[Session]:
        """Get the currently active (live) session"""
        if not self._active_session_id:
            return None
        return self._sessions.get(self._active_session_id)

    def _clear_session_routes(self, session: Session) -> None:
        """Clear all routes for a session"""
        for camera in session.cameras:
            routes = self._stream_router.get_routes_for_camera(camera.id)
            for route in routes:
                self._stream_router.detach_camera_from_scene(
                    camera.id,
                    route.target_scene_id
                )

    def _log_event(
        self,
        session: Session,
        event_type: str,
        details: Dict,
        severity: str = "info"
    ) -> None:
        """Log an event to the session"""
        event = SessionEvent(
            timestamp=datetime.now(),
            type=event_type,
            details=details,
            severity=severity
        )
        session.events.append(event)
