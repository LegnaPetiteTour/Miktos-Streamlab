"""
Scenes API Routes
Handles OBS scene management, switching, and composition.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from models.scene import (  # type: ignore[import-not-found]
    SceneLayout, TransitionType)
from hub_api.models import SuccessResponse  # type: ignore[import-not-found]

router = APIRouter(tags=["scenes"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class CreateSceneRequest(BaseModel):
    """Request to create a new scene"""
    session_id: str = Field(..., description="Session ID")
    name: str = Field(..., description="Scene name")
    layout: SceneLayout = Field(..., description="Scene layout type")
    camera_ids: List[str] = Field(
        default=[], description="Camera IDs to include")
    description: Optional[str] = Field(None, description="Scene description")


class SceneSwitchRequest(BaseModel):
    """Request to switch active scene"""
    session_id: str = Field(..., description="Session ID")
    scene_id: str = Field(..., description="Target scene ID")
    transition: Optional[TransitionType] = Field(
        TransitionType.CUT,
        description="Transition type"
    )
    transition_duration_ms: Optional[int] = Field(
        300,
        description="Transition duration in milliseconds",
        ge=0,
        le=5000
    )


class SceneResponse(BaseModel):
    """Scene information response"""
    id: str
    session_id: str
    name: str
    layout: SceneLayout
    camera_ids: List[str]
    is_active: bool
    description: Optional[str] = None


class ScenesListResponse(BaseModel):
    """List of scenes response"""
    scenes: List[SceneResponse]
    total: int
    active_scene_id: Optional[str] = None

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_obs_orchestrator():
    """Get OBS orchestrator instance"""
    from hub_api.server import app_state  # type: ignore[import-not-found]
    if not app_state.obs_orchestrator:
        raise HTTPException(
            status_code=503,
            detail="OBS orchestrator not initialized"
        )
    return app_state.obs_orchestrator


def get_session_manager():
    """Get session manager instance"""
    from hub_api.server import app_state
    if not app_state.session_manager:
        raise HTTPException(
            status_code=503,
            detail="Session manager not initialized"
        )
    return app_state.session_manager


def get_device_registry():
    """Get device registry instance"""
    from hub_api.server import app_state
    if not app_state.device_registry:
        raise HTTPException(
            status_code=503,
            detail="Device registry not initialized"
        )
    return app_state.device_registry

# ============================================================================
# SCENE ROUTES
# ============================================================================


@router.get(
    "",
    response_model=ScenesListResponse,
    summary="List all scenes",
    description="Get all scenes for a session"
)
async def list_scenes(
    session_id: str,
    obs: object = Depends(get_obs_orchestrator),
    session_mgr: object = Depends(get_session_manager)
):
    """List all scenes in a session"""
    try:
        # Validate session exists
        session = session_mgr.get_session(session_id)  # type: ignore[attr-defined]
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        scenes = await obs.list_scenes(  # type: ignore[attr-defined]
            session_id)
        active_scene_id = await obs.get_active_scene(session_id)  # type: ignore[attr-defined]  # noqa: E501

        scene_responses = [
            SceneResponse(
                id=scene.id,
                session_id=scene.session_id,
                name=scene.name,
                layout=scene.layout,
                camera_ids=scene.camera_ids,
                is_active=(scene.id == active_scene_id),
                description=scene.description
            )
            for scene in scenes
        ]

        return ScenesListResponse(
            scenes=scene_responses,
            total=len(scenes),
            active_scene_id=active_scene_id
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list scenes: {str(e)}"
        )


@router.get(
    "/{scene_id}",
    response_model=SceneResponse,
    summary="Get scene details",
    description="Get detailed information about a specific scene"
)
async def get_scene(
    scene_id: str,
    obs: object = Depends(get_obs_orchestrator)
):
    """Get scene by ID"""
    try:
        scene = await obs.get_scene(scene_id)  # type: ignore[attr-defined]

        if not scene:
            raise HTTPException(
                status_code=404,
                detail=f"Scene {scene_id} not found"
            )

        active_scene_id = await obs.get_active_scene(scene.session_id)  # type: ignore[attr-defined]  # noqa: E501

        return SceneResponse(
            id=scene.id,
            session_id=scene.session_id,
            name=scene.name,
            layout=scene.layout,
            camera_ids=scene.camera_ids,
            is_active=(scene.id == active_scene_id),
            description=scene.description
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scene: {str(e)}"
        )


@router.post(
    "",
    response_model=SceneResponse,
    status_code=201,
    summary="Create new scene",
    description="Create a new scene with specified layout and cameras"
)
async def create_scene(
    request: CreateSceneRequest,
    obs: object = Depends(get_obs_orchestrator),
    session_mgr: object = Depends(get_session_manager),
    registry: object = Depends(get_device_registry)
):
    """Create a new scene"""
    try:
        # Validate session exists
        session = session_mgr.get_session(  # type: ignore[attr-defined]
            request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found"
            )

        # Validate cameras exist
        for camera_id in request.camera_ids:
            camera = registry.get(camera_id)  # type: ignore[attr-defined]
            if not camera:
                raise HTTPException(
                    status_code=404,
                    detail=f"Camera {camera_id} not found"
                )

        # Create scene
        if len(request.camera_ids) == 1:
            scene = await obs.create_scene_for_camera(  # type: ignore[attr-defined]  # noqa: E501
                request.camera_ids[0],
                scene_name=request.name,
                session_id=request.session_id
            )
        else:
            scene = await obs.create_multi_camera_scene(  # type: ignore[attr-defined]  # noqa: E501
                camera_ids=request.camera_ids,
                layout=request.layout,
                scene_name=request.name,
                session_id=request.session_id
            )

        return SceneResponse(
            id=scene.id,
            session_id=scene.session_id,
            name=scene.name,
            layout=scene.layout,
            camera_ids=scene.camera_ids,
            is_active=False,
            description=request.description
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create scene: {str(e)}"
        )


@router.post(
    "/switch",
    response_model=SuccessResponse,
    summary="Switch active scene",
    description="Switch to a different scene with optional transition"
)
async def switch_scene(
    request: SceneSwitchRequest,
    obs: object = Depends(get_obs_orchestrator)
):
    """Switch to a different scene"""
    try:
        await obs.switch_scene(  # type: ignore[attr-defined]
            scene_id=request.scene_id,
            transition=request.transition,
            duration_ms=request.transition_duration_ms
        )

        return SuccessResponse(
            success=True,
            message=f"Switched to scene {request.scene_id}",
            data={"scene_id": request.scene_id}
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to switch scene: {str(e)}"
        )


@router.delete(
    "/{scene_id}",
    response_model=SuccessResponse,
    summary="Delete scene",
    description="Delete a scene (cannot delete active scene)"
)
async def delete_scene(
    scene_id: str,
    obs: object = Depends(get_obs_orchestrator)
):
    """Delete a scene"""
    try:
        scene = await obs.get_scene(scene_id)  # type: ignore[attr-defined]
        if not scene:
            raise HTTPException(
                status_code=404,
                detail=f"Scene {scene_id} not found"
            )

        # Check if scene is active
        active_scene_id = await obs.get_active_scene(scene.session_id)  # type: ignore[attr-defined]  # noqa: E501
        if scene_id == active_scene_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot delete active scene. "
                    "Switch to another scene first."
                )
            )

        await obs.delete_scene(scene_id)  # type: ignore[attr-defined]

        return SuccessResponse(
            success=True,
            message=f"Scene {scene_id} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete scene: {str(e)}"
        )

# ============================================================================
# SCENE TEMPLATES
# ============================================================================


@router.get(
    "/templates",
    response_model=List[dict],
    summary="List scene templates",
    description="Get available scene templates for quick setup"
)
async def list_templates(
    obs: object = Depends(get_obs_orchestrator)
):
    """List available scene templates"""
    try:
        templates = await obs.list_scene_templates()  # type: ignore[attr-defined]  # noqa: E501
        return templates

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.post(
    "/from-template",
    response_model=SceneResponse,
    status_code=201,
    summary="Create scene from template",
    description="Create a scene using a predefined template"
)
async def create_from_template(
    session_id: str,
    template_name: str,
    camera_ids: List[str],
    scene_name: Optional[str] = None,
    obs: object = Depends(get_obs_orchestrator)
):
    """Create scene from template"""
    try:
        scene = await obs.create_scene_from_template(  # type: ignore[attr-defined]  # noqa: E501
            session_id=session_id,
            template_name=template_name,
            camera_ids=camera_ids,
            name=scene_name
        )

        return SceneResponse(
            id=scene.id,
            session_id=scene.session_id,
            name=scene.name,
            layout=scene.layout,
            camera_ids=scene.camera_ids,
            is_active=False
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create scene from template: {str(e)}"
        )
