"""
Streaming API Routes
Handles multi-platform streaming control, monitoring, and failover.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from models.destination import StreamDestination, Platform
from models.session import SessionState
from hub_api.models import SuccessResponse

router = APIRouter(tags=["streaming"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class DestinationConfig(BaseModel):
    """Streaming destination configuration"""
    platform: Platform = Field(..., description="Streaming platform")
    stream_key: str = Field(..., description="Platform stream key")
    stream_url: Optional[str] = Field(None, description="Custom RTMP URL")
    label: Optional[str] = Field(None, description="Destination label")
    enabled: bool = Field(True, description="Enable this destination")


class ConfigureDestinationsRequest(BaseModel):
    """Request to configure streaming destinations"""
    session_id: str = Field(..., description="Session ID")
    destinations: List[DestinationConfig] = Field(
        ...,
        description="List of streaming destinations"
    )


class StartStreamRequest(BaseModel):
    """Request to start streaming"""
    session_id: str = Field(..., description="Session ID")
    start_recording: bool = Field(
        False,
        description="Also start ISO recording"
    )


class StopStreamRequest(BaseModel):
    """Request to stop streaming"""
    session_id: str = Field(..., description="Session ID")
    stop_recording: bool = Field(
        True,
        description="Also stop recording if active"
    )


class DestinationStatus(BaseModel):
    """Status of a streaming destination"""
    destination_id: str
    platform: Platform
    label: Optional[str]
    status: str  # "healthy", "degraded", "failed", "inactive"
    bitrate_kbps: float
    fps: float
    dropped_frames: int
    total_frames: int
    uptime_seconds: float
    last_error: Optional[str] = None
    using_backup: bool = False


class StreamingHealthResponse(BaseModel):
    """Complete streaming health status"""
    session_id: str
    overall_status: str  # "healthy", "degraded", "failed", "stopped"
    is_streaming: bool
    destinations: List[DestinationStatus]
    total_destinations: int
    healthy_destinations: int
    degraded_destinations: int
    failed_destinations: int
    avg_bitrate_kbps: float
    avg_fps: float
    total_dropped_frames: int
    uptime_seconds: float


class DestinationResponse(BaseModel):
    """Destination configuration response"""
    id: str
    platform: Platform
    label: Optional[str]
    enabled: bool
    status: str


class DestinationsListResponse(BaseModel):
    """List of configured destinations"""
    session_id: str
    destinations: List[DestinationResponse]
    total: int

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_streaming_module():
    """Get multi-platform streaming module instance"""
    from hub_api.server import app_state
    if not app_state.streaming_module:
        raise HTTPException(
            status_code=503,
            detail="Streaming module not initialized"
        )
    return app_state.streaming_module


def get_session_manager():
    """Get session manager instance"""
    from hub_api.server import app_state
    if not app_state.session_manager:
        raise HTTPException(
            status_code=503,
            detail="Session manager not initialized"
        )
    return app_state.session_manager

# ============================================================================
# DESTINATION CONFIGURATION
# ============================================================================


@router.get(
    "/destinations",
    response_model=DestinationsListResponse,
    summary="List streaming destinations",
    description="Get all configured streaming destinations for a session"
)
async def list_destinations(
    session_id: str,
    streaming: object = Depends(get_streaming_module)
):
    """List configured streaming destinations"""
    try:
        destinations = await streaming.get_destinations(session_id)

        dest_responses = [
            DestinationResponse(
                id=dest.id,
                platform=dest.platform,
                label=dest.label,
                enabled=dest.enabled,
                status=(
                    dest.status.value
                    if hasattr(dest, 'status')
                    else 'inactive'
                )
            )
            for dest in destinations
        ]

        return DestinationsListResponse(
            session_id=session_id,
            destinations=dest_responses,
            total=len(destinations)
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list destinations: {str(e)}"
        )


@router.post(
    "/destinations",
    response_model=SuccessResponse,
    summary="Configure streaming destinations",
    description="Set up streaming destinations for a session",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "sess_012345",
                        "destinations": [
                            {
                                "platform": "youtube",
                                "stream_key": "abcd-efgh-ijkl",
                                "label": "YouTube - Test",
                                "stream_url": None,
                                "enabled": True,
                            }
                        ],
                    }
                }
            }
        }
    },
)
async def configure_destinations(
    request: ConfigureDestinationsRequest = Body(
        ...,
        example={
            "session_id": "sess_012345",
            "destinations": [
                {
                    "platform": "youtube",
                    "stream_key": "abcd-efgh-ijkl",
                    "label": "YouTube - Test",
                    "stream_url": None,
                    "enabled": True,
                }
            ],
        },
    ),
    streaming: object = Depends(get_streaming_module),
    session_mgr: object = Depends(get_session_manager)
):
    """Configure streaming destinations"""
    try:
        # Validate session exists
        session = session_mgr.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found"
            )

        # Convert to StreamDestination objects
        destinations = []
        for dest_config in request.destinations:
            dest_id = (
                f"{request.session_id}_"
                f"{dest_config.platform.value}_"
                f"{len(destinations)}"
            )
            dest = StreamDestination(
                id=dest_id,
                platform=dest_config.platform,
                stream_key=dest_config.stream_key,
                stream_url=dest_config.stream_url,
                label=dest_config.label,
                enabled=dest_config.enabled
            )
            destinations.append(dest)

        # Configure destinations
        await streaming.configure_destinations(
            session_id=request.session_id,
            destinations=[dest.__dict__ for dest in destinations]
        )

        return SuccessResponse(
            success=True,
            message=f"Configured {len(destinations)} streaming destinations",
            data={
                "session_id": request.session_id,
                "destination_count": len(destinations)
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure destinations: {str(e)}"
        )

# ============================================================================
# STREAMING CONTROL
# ============================================================================


@router.post(
    "/start",
    response_model=SuccessResponse,
    summary="Start streaming",
    description="Start streaming to all configured destinations",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "sess_012345",
                        "start_recording": False,
                    }
                }
            }
        }
    },
)
async def start_streaming(
    request: StartStreamRequest = Body(
        ...,
        example={"session_id": "sess_012345", "start_recording": False},
    ),
    streaming: object = Depends(get_streaming_module),
    session_mgr: object = Depends(get_session_manager)
):
    """Start streaming"""
    try:
        # Validate session exists
        session = session_mgr.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found"
            )

        # Check if already streaming
        if session.state == SessionState.STREAMING:
            raise HTTPException(
                status_code=400,
                detail="Session is already streaming"
            )

        # Start streaming
        await streaming.start_stream(
            session_id=request.session_id,
            start_recording=request.start_recording
        )

        # Update session state
        session_mgr.update_session_state(
            request.session_id,
            SessionState.STREAMING
        )

        return SuccessResponse(
            success=True,
            message=f"Streaming started for session {request.session_id}",
            data={
                "session_id": request.session_id,
                "recording": request.start_recording
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start streaming: {str(e)}"
        )


@router.post(
    "/stop",
    response_model=SuccessResponse,
    summary="Stop streaming",
    description="Stop streaming to all destinations"
)
async def stop_streaming(
    request: StopStreamRequest,
    streaming: object = Depends(get_streaming_module),
    session_mgr: object = Depends(get_session_manager)
):
    """Stop streaming"""
    try:
        # Validate session exists
        session = session_mgr.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found"
            )

        # Stop streaming
        await streaming.stop_stream(
            session_id=request.session_id,
            stop_recording=request.stop_recording
        )

        # Update session state
        session_mgr.update_session_state(
            request.session_id,
            SessionState.READY
        )

        return SuccessResponse(
            success=True,
            message=f"Streaming stopped for session {request.session_id}",
            data={
                "session_id": request.session_id
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop streaming: {str(e)}"
        )

# ============================================================================
# HEALTH & MONITORING
# ============================================================================


@router.get(
    "/health",
    response_model=StreamingHealthResponse,
    summary="Get streaming health",
    description="Get real-time streaming health metrics"
)
async def get_streaming_health(
    session_id: str,
    streaming: object = Depends(get_streaming_module)
):
    """Get streaming health status"""
    try:
        health = await streaming.get_health(session_id)

        # Convert to response model
        dest_statuses = [
            DestinationStatus(
                destination_id=dest.destination_id,
                platform=(
                    Platform[dest.platform.upper()]
                    if isinstance(dest.platform, str)
                    else dest.platform
                ),
                label=dest.label,
                status=dest.status,
                bitrate_kbps=dest.bitrate_kbps,
                fps=dest.fps,
                dropped_frames=dest.dropped_frames,
                total_frames=dest.total_frames,
                uptime_seconds=dest.uptime_seconds,
                last_error=dest.last_error,
                using_backup=dest.using_backup
            )
            for dest in health.destinations
        ]

        return StreamingHealthResponse(
            session_id=session_id,
            overall_status=health.overall_status.value,
            is_streaming=health.is_streaming,
            destinations=dest_statuses,
            total_destinations=health.total_destinations,
            healthy_destinations=health.healthy_destinations,
            degraded_destinations=health.degraded_destinations,
            failed_destinations=health.failed_destinations,
            avg_bitrate_kbps=health.avg_bitrate_kbps,
            avg_fps=health.avg_fps,
            total_dropped_frames=health.total_dropped_frames,
            uptime_seconds=health.uptime_seconds
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get streaming health: {str(e)}"
        )


@router.get(
    "/destinations/{destination_id}/health",
    response_model=DestinationStatus,
    summary="Get destination health",
    description="Get health metrics for a specific destination"
)
async def get_destination_health(
    destination_id: str,
    session_id: str,
    streaming: object = Depends(get_streaming_module)
):
    """Get health status for specific destination"""
    try:
        dest_health = await streaming.get_destination_health(
            session_id,
            destination_id
        )

        if not dest_health:
            raise HTTPException(
                status_code=404,
                detail=f"Destination {destination_id} not found"
            )

        return DestinationStatus(
            destination_id=dest_health.destination_id,
            platform=(
                Platform[dest_health.platform.upper()]
                if isinstance(dest_health.platform, str)
                else dest_health.platform
            ),
            label=dest_health.label,
            status=dest_health.status,
            bitrate_kbps=dest_health.bitrate_kbps,
            fps=dest_health.fps,
            dropped_frames=dest_health.dropped_frames,
            total_frames=dest_health.total_frames,
            uptime_seconds=dest_health.uptime_seconds,
            last_error=dest_health.last_error,
            using_backup=dest_health.using_backup
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get destination health: {str(e)}"
        )

# ============================================================================
# FAILOVER CONTROL
# ============================================================================


@router.post(
    "/destinations/{destination_id}/force-failover",
    response_model=SuccessResponse,
    summary="Force failover",
    description="Manually trigger failover to backup for a destination"
)
async def force_failover(
    destination_id: str,
    session_id: str,
    streaming: object = Depends(get_streaming_module)
):
    """Force failover to backup stream"""
    try:
        await streaming.force_failover(session_id, destination_id)

        return SuccessResponse(
            success=True,
            message=f"Forced failover for destination {destination_id}",
            data={
                "destination_id": destination_id,
                "using_backup": True
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to force failover: {str(e)}"
        )


@router.post(
    "/destinations/{destination_id}/recover",
    response_model=SuccessResponse,
    summary="Recover from failover",
    description="Attempt to recover from backup to primary stream"
)
async def recover_from_failover(
    destination_id: str,
    session_id: str,
    streaming: object = Depends(get_streaming_module)
):
    """Recover from backup to primary"""
    try:
        await streaming.recover_from_failover(session_id, destination_id)

        return SuccessResponse(
            success=True,
            message=(
                f"Recovered destination {destination_id} "
                f"to primary stream"
            ),
            data={
                "destination_id": destination_id,
                "using_backup": False
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to recover from failover: {str(e)}"
        )
