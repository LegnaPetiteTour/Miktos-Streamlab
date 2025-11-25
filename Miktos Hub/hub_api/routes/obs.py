"""
OBS Studio API Routes

Direct endpoints for controlling OBS Studio - scene management,
sources, filters, and streaming controls.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["obs"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class OBSSceneResponse(BaseModel):
    """OBS Scene information"""
    name: str = Field(..., description="Scene name")
    is_active: bool = Field(
        ..., description="Whether this is the active scene"
    )
    index: int = Field(..., description="Scene index in OBS")


class OBSSceneListResponse(BaseModel):
    """List of OBS scenes"""
    scenes: List[OBSSceneResponse]
    total: int
    current_scene: str


class OBSSceneSwitchRequest(BaseModel):
    """Request to switch OBS scene"""
    scene_name: str = Field(..., description="Name of the scene to switch to")


class OBSStatusResponse(BaseModel):
    """OBS connection status"""
    connected: bool
    version: Optional[str] = None
    websocket_version: Optional[str] = None
    recording: bool = False
    streaming: bool = False
    current_scene: Optional[str] = None


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_obs_orchestrator():
    """Get OBS orchestrator instance"""
    from hub_api.server import hub_state
    if not hub_state.obs_orchestrator:
        raise HTTPException(
            status_code=503,
            detail="OBS orchestrator not initialized"
        )
    return hub_state.obs_orchestrator


# ============================================================================
# OBS ENDPOINTS
# ============================================================================

@router.get(
    "/status",
    response_model=OBSStatusResponse,
    summary="Get OBS connection status",
    description="Check if OBS is connected and get current status"
)
async def get_obs_status(
    obs_orchestrator=Depends(get_obs_orchestrator)
):
    """Get OBS connection status and current state"""
    try:
        # Check if connected
        if not obs_orchestrator.is_connected:
            return OBSStatusResponse(connected=False)

        # Get OBS engine adapter
        obs_engine = obs_orchestrator._obs
        controller = obs_engine._controller

        # Get version info
        version = await controller.get_version()

        # Get streaming status
        streaming_status = await controller.get_streaming_status()
        is_streaming = streaming_status.value == "active"

        # Get current scene from orchestrator
        current_scene_obj = obs_orchestrator.get_current_scene()
        scene_name = (
            current_scene_obj.name if current_scene_obj else None
        )

        return OBSStatusResponse(
            connected=True,
            version=version or "Unknown",
            websocket_version="5.x",  # WebSocket v5
            recording=False,  # TODO: Add recording status check
            streaming=is_streaming,
            current_scene=scene_name
        )

    except Exception as e:
        logger.error(f"Failed to get OBS status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get OBS status: {str(e)}"
        )


@router.get(
    "/scenes",
    response_model=OBSSceneListResponse,
    summary="List all OBS scenes",
    description="Get all scenes configured in OBS Studio"
)
async def list_obs_scenes(
    obs_orchestrator=Depends(get_obs_orchestrator)
):
    """List all OBS scenes"""
    try:
        if not obs_orchestrator.is_connected:
            raise HTTPException(
                status_code=503,
                detail="OBS Studio not connected"
            )

        # Get scenes from orchestrator
        scene_list = obs_orchestrator.list_scenes()
        current_scene = obs_orchestrator.get_current_scene()
        current_scene_name = current_scene.name if current_scene else ""

        scenes = []
        for idx, scene in enumerate(scene_list):
            scenes.append(OBSSceneResponse(
                name=scene.name,
                is_active=(scene.name == current_scene_name),
                index=idx
            ))

        return OBSSceneListResponse(
            scenes=scenes,
            total=len(scenes),
            current_scene=current_scene_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list OBS scenes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list OBS scenes: {str(e)}"
        )


@router.post(
    "/scenes/{scene_name}/activate",
    summary="Switch to an OBS scene",
    description="Change the active scene in OBS Studio"
)
async def switch_obs_scene(
    scene_name: str,
    obs_orchestrator=Depends(get_obs_orchestrator)
):
    """Switch to a specific OBS scene"""
    try:
        if not obs_orchestrator.is_connected:
            raise HTTPException(
                status_code=503,
                detail="OBS Studio not connected"
            )

        # Find the scene by name
        scene = None
        for s in obs_orchestrator.list_scenes():
            if s.name == scene_name:
                scene = s
                break

        if not scene:
            raise HTTPException(
                status_code=404,
                detail=f"Scene not found: {scene_name}"
            )

        # Switch the scene
        success = await obs_orchestrator.switch_scene(
            scene.id, transition="fade"
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to switch scene"
            )

        return {
            "success": True,
            "message": f"Switched to scene: {scene_name}",
            "scene_name": scene_name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to switch OBS scene: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to switch scene: {str(e)}"
        )


@router.post(
    "/scenes/switch",
    summary="Switch OBS scene (alternative endpoint)",
    description="Change the active scene in OBS Studio using request body"
)
async def switch_obs_scene_by_body(
    request: OBSSceneSwitchRequest,
    obs_orchestrator=Depends(get_obs_orchestrator)
):
    """Switch to a specific OBS scene using request body"""
    return await switch_obs_scene(request.scene_name, obs_orchestrator)
