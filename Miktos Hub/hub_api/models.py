"""
API Models - Request and Response schemas

These Pydantic models define the API contract between
the Hub and any clients (web UI, mobile app, CLI tools).
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class SessionStateAPI(str, Enum):
    """Session state for API"""
    IDLE = "idle"
    PREPARING = "preparing"
    LIVE = "live"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class CameraStatusAPI(str, Enum):
    """Camera status for API"""
    DISCOVERING = "discovering"
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class StreamingStatusAPI(str, Enum):
    """Streaming status for API"""
    IDLE = "idle"
    STARTING = "starting"
    LIVE = "live"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPING = "stopping"


# ============================================================================
# SESSION MODELS
# ============================================================================

class SessionCreateRequest(BaseModel):
    """Request to create a new session"""
    name: str = Field(..., description="Session name")
    description: Optional[str] = Field(
        None, description="Optional description"
    )


class SessionCreateResponse(BaseModel):
    """Response after creating session"""
    session_id: str
    name: str
    state: SessionStateAPI
    created_at: datetime


class SessionResponse(BaseModel):
    """Complete session information"""
    id: str
    name: str
    description: Optional[str]
    state: SessionStateAPI
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    camera_ids: List[str]
    scene_ids: List[str]
    destination_ids: List[str]

    class Config:
        populate_by_name = True


class SessionListResponse(BaseModel):
    """List of sessions"""
    sessions: List[SessionResponse]
    total: int


class SessionStartRequest(BaseModel):
    """Request to start a session"""
    start_streaming: bool = Field(
        True, description="Whether to start streaming"
    )
    start_recording: bool = Field(
        False, description="Whether to start recording"
    )


class SessionStartResponse(BaseModel):
    """Response after starting session"""
    session_id: str
    state: SessionStateAPI
    streaming_started: bool
    recording_started: bool
    message: str


# ============================================================================
# CAMERA MODELS
# ============================================================================

class CameraResponse(BaseModel):
    """Camera information"""
    camera_id: str
    label: str
    status: CameraStatusAPI
    transport: str
    connection_url: str
    capabilities: List[str]

    # Health information
    is_connected: bool
    battery_percent: Optional[int]
    temperature_celsius: Optional[float]
    network_quality: Optional[str]

    metadata: Dict[str, Any]


class CameraListResponse(BaseModel):
    """List of cameras"""
    cameras: List[CameraResponse]
    total: int
    discovered_count: int
    registered_count: int


class CameraHealthResponse(BaseModel):
    """Camera health details"""
    camera_id: str
    overall_status: str

    is_connected: bool
    battery_percent: int
    temperature_celsius: float
    network_quality: str

    last_seen: datetime
    uptime_seconds: float


class CameraRegisterRequest(BaseModel):
    """Request to manually register a camera"""
    camera_id: str = Field(..., description="Camera ID to register")


class CameraRegisterResponse(BaseModel):
    """Response after registering camera"""
    camera_id: str
    registered: bool
    message: str


# ============================================================================
# SCENE MODELS
# ============================================================================

class SceneResponse(BaseModel):
    """Scene information"""
    scene_id: str
    name: str
    layout: str
    camera_ids: List[str]
    is_active: bool


class SceneListResponse(BaseModel):
    """List of scenes"""
    scenes: List[SceneResponse]
    total: int
    active_scene_id: Optional[str]


class SceneCreateRequest(BaseModel):
    """Request to create a scene"""
    name: Optional[str] = Field(
        None, description="Scene name (auto-generated if None)"
    )
    camera_ids: List[str] = Field(..., description="Cameras to include")
    layout: Optional[str] = Field(
        None, description="Layout type (auto-selected if None)"
    )


class SceneCreateResponse(BaseModel):
    """Response after creating scene"""
    scene_id: str
    name: str
    layout: str
    camera_count: int


class SceneSwitchRequest(BaseModel):
    """Request to switch scenes"""
    scene_id: str = Field(..., description="Scene to switch to")
    transition: Optional[str] = Field("fade", description="Transition type")
    duration_ms: int = Field(
        300, description="Transition duration in milliseconds"
    )


class SceneSwitchResponse(BaseModel):
    """Response after switching scenes"""
    scene_id: str
    scene_name: str
    transition_applied: str
    success: bool


# ===================================================================
# STREAMING MODELS
# ===================================================================

class StreamDestinationRequest(BaseModel):
    """Streaming destination configuration"""
    platform: str = Field(
        ...,
        description="Platform: youtube, facebook, twitter, twitch, rtmp"
    )
    stream_key: str = Field(..., description="Platform stream key")
    label: Optional[str] = Field(None, description="Friendly name")
    backup_enabled: bool = Field(
        True, description="Enable SRT backup failover"
    )


class StreamConfigureRequest(BaseModel):
    """Request to configure streaming"""
    session_id: str = Field(..., description="Session to configure")
    destinations: List[StreamDestinationRequest] = Field(
        ..., description="Streaming destinations"
    )


class StreamConfigureResponse(BaseModel):
    """Response after configuring streaming"""
    session_id: str
    destinations_configured: int
    success: bool


class StreamStartRequest(BaseModel):
    """Request to start streaming"""
    session_id: str = Field(..., description="Session to start streaming")


class StreamStartResponse(BaseModel):
    """Response after starting streaming"""
    session_id: str
    status: StreamingStatusAPI
    destinations_started: int
    total_destinations: int
    message: str


class StreamHealthResponse(BaseModel):
    """Streaming health information"""
    session_id: str
    overall_status: StreamingStatusAPI

    total_destinations: int
    healthy_destinations: int
    failed_destinations: int

    avg_bitrate_kbps: float
    avg_fps: float
    total_dropped_frames: int

    using_backup: bool
    backup_destinations: List[str]

    destinations: Dict[str, Any]
    timestamp: datetime


# ===================================================================
# HEALTH MODELS
# ===================================================================

class SystemHealthResponse(BaseModel):
    """Overall system health"""
    status: str  # "healthy", "degraded", "critical"

    # Component health
    obs_connected: bool
    cameras_registered: int
    cameras_healthy: int
    active_sessions: int
    streaming_sessions: int

    # Resource usage
    cpu_percent: Optional[float]
    memory_percent: Optional[float]
    disk_usage_percent: Optional[float]

    # Network
    network_quality: str

    timestamp: datetime


class ComponentHealthResponse(BaseModel):
    """Health of a specific component"""
    component: str
    status: str
    details: Dict[str, Any]
    last_check: datetime


# ============================================================================
# DISCOVERY MODELS
# ============================================================================

class DiscoveryStartRequest(BaseModel):
    """Request to start camera discovery"""
    timeout_seconds: int = Field(30, description="How long to discover for")


class DiscoveryStartResponse(BaseModel):
    """Response after starting discovery"""
    discovery_active: bool
    message: str


class DiscoveryStatusResponse(BaseModel):
    """Discovery status"""
    active: bool
    cameras_discovered: int
    cameras_registered: int
    discovery_method: str


# ============================================================================
# RECORDING MODELS
# ============================================================================

class RecordingStartRequest(BaseModel):
    """Request to start recording"""
    session_id: str
    mode: str = Field(
        "program_and_iso",
        description="program_only, iso_only, or program_and_iso"
    )
    enable_replay_buffer: bool = Field(
        True, description="Enable instant replay"
    )


class RecordingStartResponse(BaseModel):
    """Response after starting recording"""
    session_id: str
    recording: bool
    mode: str
    message: str


class RecordingStatusResponse(BaseModel):
    """Recording status"""
    session_id: str
    is_recording: bool
    duration_seconds: float
    file_size_mb: float
    program_file: Optional[str]
    iso_files: Dict[str, str]


# ============================================================================
# EXPORT MODELS
# ============================================================================

class ExportClipRequest(BaseModel):
    """Request to cut a clip"""
    input_file: str = Field(..., description="Source video file path")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    output_file: Optional[str] = Field(
        None, description="Output path (auto-generated if None)"
    )


class ExportClipResponse(BaseModel):
    """Response after cutting clip"""
    output_file: str
    duration_seconds: float
    success: bool


class ExportResizeRequest(BaseModel):
    """Request to resize video"""
    input_file: str = Field(..., description="Source video file path")
    platform: str = Field(
        ...,
        description="Platform: tiktok, youtube, instagram, facebook"
    )
    output_file: Optional[str] = Field(
        None, description="Output path (auto-generated if None)"
    )


class ExportResizeResponse(BaseModel):
    """Response after resizing"""
    output_file: str
    aspect_ratio: str
    resolution: str
    success: bool


# ============================================================================
# WEBSOCKET MODELS
# ============================================================================

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    event: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime


class WebSocketSubscribeRequest(BaseModel):
    """Request to subscribe to events"""
    events: List[str] = Field(..., description="Event types to subscribe to")


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
