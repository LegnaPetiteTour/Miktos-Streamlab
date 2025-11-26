"""
Camera API Routes

Endpoints for camera discovery, registration, and health monitoring.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List

from hub_api.models import (
    CameraResponse,
    CameraListResponse,
    CameraHealthResponse,
    CameraRegisterRequest,
    CameraRegisterResponse,
    CameraStatusAPI,
    DiscoveryStartRequest,
    DiscoveryStartResponse,
    DiscoveryStatusResponse,
    SuccessResponse,
)
from hub_api.server import hub_state

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_camera_manager():
    """Get camera manager from hub state"""
    if not hub_state.camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not initialized")
    return hub_state.camera_manager


def get_device_registry():
    """Get device registry from hub state"""
    if not hub_state.device_registry:
        raise HTTPException(status_code=503, detail="Device registry not initialized")
    return hub_state.device_registry


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/", response_model=CameraListResponse)
async def list_cameras(
    camera_manager=Depends(get_camera_manager),
    device_registry=Depends(get_device_registry),
):
    """
    List all cameras (discovered and registered).

    Returns both discovered cameras (not yet registered) and
    registered cameras (active in the system).
    """
    try:
        # Get discovered cameras
        discovered = camera_manager.get_discovered_cameras()

        # Get registered cameras
        registered = device_registry.list_all()

        # Build response
        cameras = []

        # Add all discovered cameras
        for camera in discovered:
            is_registered = device_registry.get(camera.id) is not None

            cameras.append(CameraResponse(
                camera_id=camera.id,
                label=camera.label,
                status=CameraStatusAPI.REGISTERED if is_registered else CameraStatusAPI.DISCOVERED,
                transport=camera.transport.value,
                connection_url=camera.connection_url,
                capabilities=camera.capabilities,
                is_connected=camera.health.is_connected if hasattr(camera, 'health') else False,
                battery_percent=camera.metadata.get("battery_percent"),
                temperature_celsius=camera.metadata.get("temperature_celsius"),
                network_quality=camera.metadata.get("network_quality"),
                metadata=camera.metadata,
            ))

        return CameraListResponse(
            cameras=cameras,
            total=len(cameras),
            discovered_count=len(discovered),
            registered_count=len(registered),
        )

    except Exception as e:
        logger.error(f"Failed to list cameras: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
    device_registry=Depends(get_device_registry),
):
    """
    Get details of a specific camera.
    """
    try:
        camera = device_registry.get(camera_id)

        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")

        return CameraResponse(
            camera_id=camera.id,
            label=camera.label,
            status=CameraStatusAPI.REGISTERED,
            transport=camera.transport.value,
            connection_url=camera.connection_url,
            capabilities=camera.capabilities,
            is_connected=camera.health.is_connected if hasattr(camera, 'health') else False,
            battery_percent=camera.metadata.get("battery_percent"),
            temperature_celsius=camera.metadata.get("temperature_celsius"),
            network_quality=camera.metadata.get("network_quality"),
            metadata=camera.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get camera: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{camera_id}/health", response_model=CameraHealthResponse)
async def get_camera_health(
    camera_id: str,
    camera_manager=Depends(get_camera_manager),
):
    """
    Get detailed health information for a camera.

    Includes battery, temperature, network quality, and connection status.
    """
    try:
        health = await camera_manager.get_camera_health(camera_id)

        if not health:
            raise HTTPException(status_code=404, detail="Camera not found or not registered")

        return CameraHealthResponse(
            camera_id=camera_id,
            overall_status=health.overall_status,
            is_connected=health.is_connected,
            battery_percent=health.battery_percent,
            temperature_celsius=health.temperature_celsius,
            network_quality=health.network_quality,
            last_seen=health.last_seen,
            uptime_seconds=health.uptime_seconds,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get camera health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/register",
    response_model=CameraRegisterResponse,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {"camera_id": "cam_abcd1234"}
                }
            }
        }
    },
)
async def register_camera(
    request: CameraRegisterRequest = Body(
        ...,
        example={"camera_id": "cam_abcd1234"},
    ),
    camera_manager=Depends(get_camera_manager),
):
    """
    Register a discovered camera.

    This makes the camera available for use in sessions.
    """
    try:
        logger.info(f"Registering camera: {request.camera_id}")

        success = await camera_manager.register_camera(request.camera_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to register camera",
            )

        return CameraRegisterResponse(
            camera_id=request.camera_id,
            registered=True,
            message="Camera registered successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register camera: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{camera_id}/unregister", response_model=SuccessResponse)
async def unregister_camera(
    camera_id: str,
    camera_manager=Depends(get_camera_manager),
):
    """
    Unregister a camera.

    This removes the camera from the system.
    """
    try:
        logger.info(f"Unregistering camera: {camera_id}")

        success = await camera_manager.unregister_camera(camera_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to unregister camera",
            )

        return SuccessResponse(
            success=True,
            message="Camera unregistered successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister camera: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discovery/start", response_model=DiscoveryStartResponse)
async def start_discovery(
    request: DiscoveryStartRequest,
    camera_manager=Depends(get_camera_manager),
):
    """
    Start camera discovery.

    Begins scanning the network for cameras via mDNS/Bonjour.
    """
    try:
        logger.info("Starting camera discovery")

        await camera_manager.start_discovery()

        return DiscoveryStartResponse(
            discovery_active=True,
            message="Discovery started",
        )

    except Exception as e:
        logger.error(f"Failed to start discovery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discovery/stop", response_model=SuccessResponse)
async def stop_discovery(
    camera_manager=Depends(get_camera_manager),
):
    """
    Stop camera discovery.
    """
    try:
        logger.info("Stopping camera discovery")

        await camera_manager.stop_discovery()

        return SuccessResponse(
            success=True,
            message="Discovery stopped",
        )

    except Exception as e:
        logger.error(f"Failed to stop discovery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discovery/status", response_model=DiscoveryStatusResponse)
async def get_discovery_status(
    camera_manager=Depends(get_camera_manager),
):
    """
    Get current discovery status.
    """
    try:
        discovered = camera_manager.get_discovered_cameras()
        registered = camera_manager.get_registered_cameras()

        return DiscoveryStatusResponse(
            active=camera_manager._discovery_active,
            cameras_discovered=len(discovered),
            cameras_registered=len(registered),
            discovery_method="mdns",
        )

    except Exception as e:
        logger.error(f"Failed to get discovery status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
