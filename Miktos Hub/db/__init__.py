"""
Database Persistence Layer

Provides database models, connection management, and repositories.
"""

from db.database import Database, get_database, init_database, close_database
from db.models import (
    Base,
    SessionModel,
    CameraModel,
    SessionCameraModel,
    SceneModel,
    StreamDestinationModel,
    SystemStateModel,
    SessionState,
)
from db.repositories import (
    SessionRepository,
)

__all__ = [
    "Database",
    "get_database",
    "init_database",
    "close_database",
    "Base",
    "SessionModel",
    "CameraModel",
    "SessionCameraModel",
    "SceneModel",
    "StreamDestinationModel",
    "SystemStateModel",
    "SessionState",
    "SessionRepository",
]
