"""
Session API Routes

Endpoints for creating, managing, and controlling streaming sessions.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from hub_api.models import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionResponse,
    SessionListResponse,
    SessionStartRequest,
    SessionStartResponse,
    SuccessResponse,
    SessionStateAPI,
)
from hub_api.server import hub_state

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_session_manager():
    """Get session manager from hub state"""
    if not hub_state.session_manager:
        raise HTTPException(status_code=503,
                            detail="Session manager not initialized")
    return hub_state.session_manager


def get_event_bus():
    """Get event bus from hub state"""
    if not hub_state.event_bus:
        raise HTTPException(status_code=503,
                            detail="Event bus not initialized")
    return hub_state.event_bus


def get_streaming_manager():
    """Get streaming manager from hub state"""
    if not hub_state.streaming_manager:
        raise HTTPException(status_code=503,
                            detail="Streaming manager not initialized")
    return hub_state.streaming_manager


def get_recording_service():
    """Get recording service from hub state"""
    if not hub_state.recording_service:
        raise HTTPException(status_code=503,
                            detail="Recording service not initialized")
    return hub_state.recording_service


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=SessionCreateResponse)
async def create_session(
    request: SessionCreateRequest,
    session_manager=Depends(get_session_manager),
    event_bus=Depends(get_event_bus),
):
    """
    Create a new streaming session.

    A session represents one streaming show/event. It can have multiple
    cameras, scenes, and streaming destinations.
    """
    try:
        logger.info(f"Creating session: {request.name}")

        # Create session config
        from models.session import SessionConfig

        config = SessionConfig(
            name=request.name,
            description=request.description,
        )

        # Create session
        session = session_manager.create_session(config)

        logger.info(f"Session created: {session.id}")

        # Publish event to EventBus
        await event_bus.publish(
            event_type="session.created",
            data={
                "session_id": session.id,
                "name": session.name,
                "description": session.description or "",
                "state": session.state.value,
            },
            source="api.sessions"
        )

        return SessionCreateResponse(
            session_id=session.id,
            name=session.name,
            state=SessionStateAPI(session.state.value),
            created_at=session.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    session_manager=Depends(get_session_manager),
):
    """
    List all sessions.

    Returns both active and completed sessions.
    """
    try:
        sessions = session_manager.list_sessions()

        session_responses = [
            SessionResponse(
                session_id=s.id,
                name=s.name,
                description=s.description,
                state=SessionStateAPI(s.state.value),
                created_at=s.created_at,
                started_at=s.started_at,
                ended_at=s.ended_at,
                camera_ids=[c.id for c in s.cameras],
                scene_ids=[sc.id for sc in s.scenes],
                destination_ids=[d.id for d in s.destinations],
            )
            for s in sessions
        ]

        return SessionListResponse(
            sessions=session_responses,
            total=len(session_responses),
        )

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_manager=Depends(get_session_manager),
):
    """
    Get details of a specific session.
    """
    try:
        session = session_manager.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            session_id=session.id,
            name=session.name,
            description=session.description,
            state=SessionStateAPI(session.state.value),
            created_at=session.created_at,
            started_at=session.started_at,
            ended_at=session.ended_at,
            camera_ids=[c.id for c in session.cameras],
            scene_ids=[sc.id for sc in session.scenes],
            destination_ids=[d.id for d in session.destinations],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/start", response_model=SessionStartResponse)
async def start_session(
    session_id: str,
    request: SessionStartRequest,
    session_manager=Depends(get_session_manager),
    streaming_manager=Depends(get_streaming_manager),
    recording_service=Depends(get_recording_service),
):
    """
    Start a session (begin streaming/recording).

    This will:
    1. Start the session
    2. Optionally start streaming to configured destinations
    3. Optionally start recording
    """
    try:
        logger.info(f"Starting session: {session_id}")

        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Start session
        success = await session_manager.start_session(session_id)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to start session")

        streaming_started = False
        recording_started = False
        messages = []

        # Start streaming if requested
        if request.start_streaming:
            try:
                if not session.destinations:
                    messages.append("No streaming destinations configured")
                else:
                    streaming_started = (
                        await streaming_manager.start_stream(session_id)
                    )
                    if streaming_started:
                        dest_count = len(session.destinations)
                        messages.append(
                            f"Streaming started to {dest_count} destinations"
                        )
                    else:
                        messages.append("Streaming failed to start")
            except Exception as e:
                logger.error(f"Streaming start failed: {e}")
                messages.append(f"Streaming error: {str(e)}")

        # Start recording if requested
        if request.start_recording:
            try:
                from services import RecordingConfig, RecordingMode
                from pathlib import Path

                config = RecordingConfig(
                    mode=RecordingMode.PROGRAM_AND_ISO,
                    output_directory=Path(f"/recordings/{session_id}"),
                    enable_replay_buffer=True,
                )

                await recording_service.start_recording(
                    session_id, config)
                recording_started = True
                messages.append("Recording started")
            except Exception as e:
                logger.error(f"Recording start failed: {e}")
                messages.append(f"Recording error: {str(e)}")

        logger.info(f"Session started: {session_id}")

        return SessionStartResponse(
            session_id=session_id,
            state=(
                SessionStateAPI.LIVE
                if streaming_started
                else SessionStateAPI.PREPARING
            ),
            streaming_started=streaming_started,
            recording_started=recording_started,
            message=(
                "; ".join(messages)
                if messages
                else "Session started successfully"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/stop", response_model=SuccessResponse)
async def stop_session(
    session_id: str,
    session_manager=Depends(get_session_manager),
    streaming_manager=Depends(get_streaming_manager),
    recording_service=Depends(get_recording_service),
):
    """
    Stop a session (stop streaming/recording).

    This will gracefully stop all streaming and recording,
    then end the session.
    """
    try:
        logger.info(f"Stopping session: {session_id}")

        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = []

        # Stop streaming
        if streaming_manager.is_streaming(session_id):
            try:
                await streaming_manager.stop_stream(session_id)
                messages.append("Streaming stopped")
            except Exception as e:
                logger.error(f"Failed to stop streaming: {e}")
                messages.append(f"Streaming stop error: {str(e)}")

        # Stop recording
        if recording_service.is_recording(session_id):
            try:
                await recording_service.stop_recording(session_id)
                messages.append("Recording stopped")
            except Exception as e:
                logger.error(f"Failed to stop recording: {e}")
                messages.append(f"Recording stop error: {str(e)}")

        # Stop session
        success = await session_manager.stop_session(session_id)

        logger.info(f"Session stopped: {session_id}")

        return SuccessResponse(success=success, message="; ".join(
            messages) if messages else "Session stopped successfully", )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", response_model=SuccessResponse)
async def delete_session(
    session_id: str,
    session_manager=Depends(get_session_manager),
):
    """
    Delete a session.

    The session must be stopped before it can be deleted.
    """
    try:
        logger.info(f"Deleting session: {session_id}")

        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if stopped
        if session.state.value not in ["stopped", "idle", "error"]:
            raise HTTPException(
                status_code=400,
                detail="Session must be stopped before deletion"
            )

        # Delete session
        success = session_manager.delete_session(session_id)

        logger.info(f"Session deleted: {session_id}")

        return SuccessResponse(
            success=success,
            message="Session deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
