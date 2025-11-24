"""
Database Models for Miktos Hub Persistence

SQLAlchemy models for persisting sessions, cameras, scenes,
and streaming state.
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
import enum

Base = declarative_base()


class TimestampMixin:
    """Mixin for created/updated timestamps"""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )


class SessionState(str, enum.Enum):
    """Session states matching models.session.SessionState"""
    PREPARING = "preparing"
    READY = "ready"
    LIVE = "live"
    PAUSED = "paused"
    ENDING = "ending"
    COMPLETED = "completed"


class SessionModel(Base, TimestampMixin):
    """
    Persistent session model.

    Stores session metadata, state, and relationships to cameras/scenes.
    """
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    state = Column(
        Enum(SessionState), default=SessionState.PREPARING, nullable=False
    )

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Extra data (renamed from metadata to avoid SQLAlchemy reserved word)
    extra_data = Column(JSON, default=dict, nullable=False)

    # Relationships
    cameras = relationship(
        "SessionCameraModel",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    scenes = relationship(
        "SceneModel",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    destinations = relationship(
        "StreamDestinationModel",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "session_id": self.id,
            "name": self.name,
            "description": self.description,
            "state": (
                self.state.value
                if isinstance(self.state, SessionState)
                else self.state
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "ended_at": (
                self.ended_at.isoformat() if self.ended_at else None
            ),
            "camera_ids": [c.camera_id for c in self.cameras],
            "scene_ids": [s.id for s in self.scenes],
            "destination_ids": [d.id for d in self.destinations],
            "metadata": self.extra_data or {}
        }


class CameraModel(Base, TimestampMixin):
    """
    Persistent camera registration.

    Stores discovered/registered cameras with their capabilities.
    """
    __tablename__ = "cameras"

    id = Column(String(36), primary_key=True)  # Camera ID
    name = Column(String(255), nullable=False)
    stream_url = Column(String(512), nullable=True)

    # Discovery info
    discovery_method = Column(String(50), nullable=True)  # mdns, manual, etc.
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)

    # Capabilities
    capabilities = Column(JSON, default=dict, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session_cameras = relationship(
        "SessionCameraModel",
        back_populates="camera",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "camera_id": self.id,
            "name": self.name,
            "stream_url": self.stream_url,
            "discovery_method": self.discovery_method,
            "host": self.host,
            "port": self.port,
            "capabilities": self.capabilities or {},
            "is_active": self.is_active,
            "last_seen": (
                self.last_seen.isoformat() if self.last_seen else None
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            )
        }


class SessionCameraModel(Base):
    """
    Association between sessions and cameras.

    Tracks which cameras are used in which sessions.
    """
    __tablename__ = "session_cameras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    camera_id = Column(String(36), ForeignKey("cameras.id"), nullable=False)

    # Camera configuration for this session
    position = Column(Integer, nullable=True)  # Camera order/position
    config = Column(JSON, default=dict, nullable=False)

    # Relationships
    session = relationship("SessionModel", back_populates="cameras")
    camera = relationship("CameraModel", back_populates="session_cameras")


class SceneModel(Base, TimestampMixin):
    """
    Persistent OBS scene configuration.

    Stores scene layouts, sources, and settings.
    """
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True)  # Scene ID
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)

    name = Column(String(255), nullable=False)
    layout = Column(
        String(50), nullable=False
    )  # fullscreen, split_horizontal, etc.

    # Scene configuration
    obs_scene_name = Column(String(255), nullable=True)
    sources = Column(
        JSON, default=list, nullable=False
    )  # List of source configs

    # Settings
    is_active = Column(Boolean, default=False, nullable=False)
    transition = Column(String(50), default="fade", nullable=False)

    # Extra data
    extra_data = Column(JSON, default=dict, nullable=False)

    # Relationships
    session = relationship("SessionModel", back_populates="scenes")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "scene_id": self.id,
            "session_id": self.session_id,
            "name": self.name,
            "layout": self.layout,
            "obs_scene_name": self.obs_scene_name,
            "sources": self.sources or [],
            "is_active": self.is_active,
            "transition": self.transition,
            "metadata": self.extra_data or {},
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            )
        }


class StreamDestinationModel(Base, TimestampMixin):
    """
    Persistent streaming destination.

    Stores RTMP/SRT destinations for multi-platform streaming.
    """
    __tablename__ = "stream_destinations"

    id = Column(String(36), primary_key=True)  # Destination ID
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)

    name = Column(String(255), nullable=False)
    platform = Column(
        String(50), nullable=False
    )  # youtube, twitch, facebook, custom

    # Connection details
    url = Column(String(512), nullable=False)
    stream_key = Column(
        String(255), nullable=True
    )  # Encrypted in production

    # Settings
    is_active = Column(Boolean, default=False, nullable=False)
    quality_preset = Column(String(50), default="hd", nullable=False)

    # Status
    last_connected = Column(DateTime, nullable=True)

    # Extra data
    extra_data = Column(JSON, default=dict, nullable=False)

    # Relationships
    session = relationship("SessionModel", back_populates="destinations")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "destination_id": self.id,
            "session_id": self.session_id,
            "name": self.name,
            "platform": self.platform,
            "url": self.url,
            "is_active": self.is_active,
            "quality_preset": self.quality_preset,
            "last_connected": (
                self.last_connected.isoformat()
                if self.last_connected
                else None
            ),
            "metadata": self.extra_data or {},
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            )
        }


class SystemStateModel(Base, TimestampMixin):
    """
    System-wide state and configuration.

    Stores app-level settings and state.
    """
    __tablename__ = "system_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(JSON, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            )
        }
