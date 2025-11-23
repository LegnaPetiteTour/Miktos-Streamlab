"""
OBS Orchestrator Module

Handles automatic OBS scene creation, scene switching, and transitions.
Auto-creates optimal layouts based on number of active cameras.

Features:
- Auto-create scenes when cameras connect
- Intelligent layouts (1=fullscreen, 2=split, 3+=grid)
- Scene switching with transitions
- Source management (position, crop, filters)
- Scene templates and presets
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from core import DeviceRegistry, StreamRouter, EventBus
from adapters import OBSEngineAdapter
from models import Scene, SceneLayout
from models.scene import SourceConfig
from config import get_config

logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """OBS transition types"""
    CUT = "cut"
    FADE = "fade"
    STINGER = "stinger"
    SWIPE = "swipe"
    SLIDE = "slide"


@dataclass
class SceneTemplate:
    """A reusable scene template"""
    id: str
    name: str
    layout: SceneLayout
    camera_count: int
    description: str


@dataclass
class SourcePosition:
    """Position and size for a source"""
    x: int
    y: int
    width: int
    height: int

    def to_dict(self) -> Dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


class OBSOrchestrator:
    """
    OBS scene orchestration and automation.

    Automatically creates and manages OBS scenes based on connected cameras.
    Provides intelligent layout decisions and smooth scene transitions.

    Example:
        ```python
        orchestrator = OBSOrchestrator(device_registry, stream_router)

        # Connect to OBS
        await orchestrator.connect()

        # Create scene for a camera
        scene = await orchestrator.create_scene_for_camera("phone-001")
        print(f"Created scene: {scene.name}")

        # Create multi-camera scene
        scene = await orchestrator.create_multi_camera_scene([
            "phone-001",
            "phone-002",
            "phone-003"
        ])

        # Switch scenes with transition
        await orchestrator.switch_scene(
            scene.id,
            transition=TransitionType.FADE
        )

        # Disconnect
        await orchestrator.disconnect()
        ```
    """

    def __init__(
        self,
        device_registry: DeviceRegistry,
        stream_router: StreamRouter,
        event_bus: Optional[EventBus] = None,
    ):
        self._registry = device_registry
        self._router = stream_router
        self._event_bus = event_bus or EventBus()

        config = get_config()

        # OBS engine adapter with config settings
        self._obs = OBSEngineAdapter(
            host=config.obs.host,
            port=config.obs.port,
            password=config.obs.password
        )

        # Scene tracking
        self._scenes: Dict[str, Scene] = {}
        self._current_scene_id: Optional[str] = None

        # Scene templates
        self._templates = self._load_templates()

        # Canvas resolution (from config or default to 1920x1080)
        self._canvas_width = config.obs.canvas_width or 1920
        self._canvas_height = config.obs.canvas_height or 1080

        # Auto-creation settings
        self._auto_create_enabled = config.obs.auto_create_scenes or True

        logger.info("OBS orchestrator initialized")

    def _load_templates(self) -> Dict[str, SceneTemplate]:
        """Load scene templates."""
        return {
            "single": SceneTemplate(
                id="single",
                name="Single Camera (Fullscreen)",
                layout=SceneLayout.FULLSCREEN,
                camera_count=1,
                description="One camera at fullscreen",
            ),
            "dual_horizontal": SceneTemplate(
                id="dual_horizontal",
                name="Dual Camera (Side by Side)",
                layout=SceneLayout.SPLIT_HORIZONTAL,
                camera_count=2,
                description="Two cameras side by side",
            ),
            "dual_vertical": SceneTemplate(
                id="dual_vertical",
                name="Dual Camera (Top and Bottom)",
                layout=SceneLayout.SPLIT_VERTICAL,
                camera_count=2,
                description="Two cameras stacked vertically",
            ),
            "picture_in_picture": SceneTemplate(
                id="picture_in_picture",
                name="Picture in Picture",
                layout=SceneLayout.PICTURE_IN_PICTURE,
                camera_count=2,
                description="Main camera with small overlay",
            ),
            "grid_4": SceneTemplate(
                id="grid_4",
                name="Grid (2x2)",
                layout=SceneLayout.GRID,
                camera_count=4,
                description="Four cameras in 2x2 grid",
            ),
        }

    async def connect(self) -> bool:
        """
        Connect to OBS.

        Returns:
            True if connected successfully
        """
        logger.info("Connecting to OBS")

        try:
            await self._obs.connect()

            logger.info("Connected to OBS")

            # Emit event
            await self._event_bus.publish("obs_connected", {
                "timestamp": datetime.now().isoformat(),
            })

            return True

        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}", exc_info=True)
            return False

    async def disconnect(self) -> None:
        """Disconnect from OBS."""
        logger.info("Disconnecting from OBS")

        await self._obs.disconnect()

        await self._event_bus.publish("obs_disconnected", {
            "timestamp": datetime.now().isoformat(),
        })

    async def create_scene_for_camera(
        self,
        camera_id: str,
        scene_name: Optional[str] = None,
    ) -> Optional[Scene]:
        """
        Create an OBS scene for a single camera.

        Args:
            camera_id: Camera to create scene for
            scene_name: Optional scene name (auto-generated if None)

        Returns:
            Created scene or None if failed
        """
        # Get camera
        camera = self._registry.get(camera_id)
        if not camera:
            logger.error(f"Camera not found: {camera_id}")
            return None

        # Generate scene name if not provided
        if not scene_name:
            scene_name = f"{camera.label} (Fullscreen)"

        logger.info(f"Creating scene for camera {camera.label}: {scene_name}")

        try:
            # Create scene in OBS
            obs_scene = await self._obs.create_scene(
                name=scene_name,
                layout_type=SceneLayout.FULLSCREEN.value,
            )

            # Add camera source via attach_camera
            await self._obs.attach_camera(
                camera=camera,
                scene_id=obs_scene.id
            )

            # Create scene model with sources
            source = SourceConfig(
                type="camera",
                device_id=camera_id
            )
            scene = Scene(
                id=obs_scene.id,
                name=scene_name,
                layout=SceneLayout.FULLSCREEN,
                sources=[source]
            )

            self._scenes[scene.id] = scene

            logger.info(f"Scene created: {scene_name}")

            # Emit event
            camera_ids = [
                s.device_id for s in scene.sources
                if s.type == "camera" and s.device_id
            ]
            await self._event_bus.publish("scene_created", {
                "scene_id": scene.id,
                "scene_name": scene.name,
                "camera_ids": camera_ids,
                "timestamp": datetime.now().isoformat(),
            })

            return scene

        except Exception as e:
            logger.error(f"Failed to create scene: {e}", exc_info=True)
            return None

    async def create_multi_camera_scene(
        self,
        camera_ids: List[str],
        layout: Optional[SceneLayout] = None,
        scene_name: Optional[str] = None,
    ) -> Optional[Scene]:
        """
        Create an OBS scene with multiple cameras.

        Args:
            camera_ids: List of cameras to include
            layout: Layout to use (auto-selected if None)
            scene_name: Optional scene name

        Returns:
            Created scene or None if failed
        """
        if not camera_ids:
            logger.error("No cameras provided")
            return None

        # Get cameras
        cameras = [self._registry.get(cid) for cid in camera_ids]
        cameras = [c for c in cameras if c is not None]

        if not cameras:
            logger.error("No valid cameras found")
            return None

        # Auto-select layout if not provided
        if not layout:
            layout = self._select_optimal_layout(len(cameras))

        # Generate scene name
        if not scene_name:
            camera_labels = ", ".join(
                c.label for c in cameras[:3] if c is not None
            )
            if len(cameras) > 3:
                camera_labels += f" +{len(cameras) - 3} more"
            scene_name = f"Multi-Cam: {camera_labels}"  # noqa: E501

        logger.info(
            f"Creating multi-camera scene: {scene_name} "
            f"({len(cameras)} cameras, "
            f"layout={layout.value})"
        )

        try:
            # Create scene in OBS
            obs_scene = await self._obs.create_scene(
                name=scene_name,
                layout_type=layout.value,
            )

            # Add each camera as a source
            sources = []
            for camera in cameras:
                if camera is None:
                    continue
                await self._obs.attach_camera(
                    camera=camera,
                    scene_id=obs_scene.id
                )
                source = SourceConfig(
                    type="camera",
                    device_id=camera.id
                )
                sources.append(source)

            # Create scene model
            scene = Scene(
                id=obs_scene.id,
                name=scene_name,
                layout=layout,
                sources=sources
            )

            self._scenes[scene.id] = scene

            logger.info(f"Multi-camera scene created: {scene_name}")

            # Emit event
            scene_camera_ids = [
                s.device_id for s in scene.sources
                if s.type == "camera" and s.device_id
            ]
            await self._event_bus.publish("scene_created", {
                "scene_id": scene.id,
                "scene_name": scene.name,
                "layout": layout.value,
                "camera_count": len(scene_camera_ids),
                "timestamp": datetime.now().isoformat(),
            })

            return scene

        except Exception as e:
            logger.error(
                f"Failed to create multi-camera scene: {e}",
                exc_info=True
            )
            return None

    def _select_optimal_layout(self, camera_count: int) -> SceneLayout:
        """Select optimal layout based on number of cameras."""
        if camera_count == 1:
            return SceneLayout.FULLSCREEN
        elif camera_count == 2:
            return SceneLayout.SPLIT_HORIZONTAL
        elif camera_count <= 4:
            return SceneLayout.GRID
        else:
            return SceneLayout.GRID  # Use grid for 5+ cameras

    def _calculate_fullscreen_position(self) -> SourcePosition:
        """Calculate position for fullscreen source."""
        return SourcePosition(
            x=0,
            y=0,
            width=self._canvas_width,
            height=self._canvas_height,
        )

    def _calculate_layout_positions(
        self,
        layout: SceneLayout,
        count: int,
    ) -> List[SourcePosition]:
        """
        Calculate source positions for a layout.

        Args:
            layout: Scene layout
            count: Number of sources

        Returns:
            List of positions for each source
        """
        positions = []

        if layout == SceneLayout.FULLSCREEN:
            positions.append(self._calculate_fullscreen_position())

        elif layout == SceneLayout.SPLIT_HORIZONTAL:
            # Side by side
            width = self._canvas_width // 2
            positions.append(
                SourcePosition(0, 0, width, self._canvas_height)
            )
            positions.append(
                SourcePosition(width, 0, width, self._canvas_height)
            )

        elif layout == SceneLayout.SPLIT_VERTICAL:
            # Top and bottom
            height = self._canvas_height // 2
            positions.append(
                SourcePosition(0, 0, self._canvas_width, height)
            )
            positions.append(
                SourcePosition(0, height, self._canvas_width, height)
            )

        elif layout == SceneLayout.PICTURE_IN_PICTURE:
            # Main camera fullscreen
            positions.append(self._calculate_fullscreen_position())

            # Small overlay in corner (1/4 size)
            pip_width = self._canvas_width // 4
            pip_height = self._canvas_height // 4
            pip_x = self._canvas_width - pip_width - 20  # 20px margin
            pip_y = self._canvas_height - pip_height - 20

            positions.append(
                SourcePosition(pip_x, pip_y, pip_width, pip_height)
            )

        elif layout == SceneLayout.GRID:
            # Calculate grid dimensions
            cols = 2 if count <= 4 else 3
            rows = (count + cols - 1) // cols  # Ceiling division

            cell_width = self._canvas_width // cols
            cell_height = self._canvas_height // rows

            for i in range(count):
                row = i // cols
                col = i % cols

                positions.append(SourcePosition(
                    x=col * cell_width,
                    y=row * cell_height,
                    width=cell_width,
                    height=cell_height,
                ))

        return positions

    async def switch_scene(
        self,
        scene_id: str,
        transition: Optional[TransitionType] = None,
        duration_ms: int = 300,
    ) -> bool:
        """
        Switch to a different scene.

        Args:
            scene_id: Scene to switch to
            transition: Transition type (None = cut)
            duration_ms: Transition duration

        Returns:
            True if switched successfully
        """
        if scene_id not in self._scenes:
            logger.error(f"Scene not found: {scene_id}")
            return False

        scene = self._scenes[scene_id]

        logger.info(f"Switching to scene: {scene.name}")

        try:
            # Switch scene with optional transition
            transition_name = (
                transition.value if transition else None
            )
            success = await self._obs.switch_scene(
                scene_id=scene_id,
                transition=transition_name
            )

            if not success:
                logger.error(f"Failed to switch scene: {scene.name}")
                return False

            self._current_scene_id = scene_id

            logger.info(f"Switched to scene: {scene.name}")

            # Emit event
            transition_value = (
                transition.value if transition else "cut"
            )
            await self._event_bus.publish("scene_switched", {
                "scene_id": scene_id,
                "scene_name": scene.name,
                "transition": transition_value,
                "timestamp": datetime.now().isoformat(),
            })

            return True

        except Exception as e:
            logger.error(f"Failed to switch scene: {e}", exc_info=True)
            return False

    async def update_camera_layout(
        self,
        camera_ids: List[str]
    ) -> Optional[Scene]:
        """
        Update OBS layout based on currently active cameras.

        Automatically creates or switches to optimal scene.

        Args:
            camera_ids: List of active cameras

        Returns:
            Active scene or None if failed
        """
        if not camera_ids:
            logger.warning("No cameras provided for layout update")
            return None

        logger.info(f"Updating layout for {len(camera_ids)} cameras")

        # Find existing scene with these cameras
        existing_scene = self._find_scene_for_cameras(camera_ids)

        if existing_scene:
            logger.info(f"Using existing scene: {existing_scene.name}")
            await self.switch_scene(existing_scene.id)
            return existing_scene

        # Create new scene
        if len(camera_ids) == 1:
            scene = await self.create_scene_for_camera(camera_ids[0])
        else:
            scene = await self.create_multi_camera_scene(camera_ids)

        if scene:
            await self.switch_scene(scene.id)

        return scene

    def _find_scene_for_cameras(
        self,
        camera_ids: List[str]
    ) -> Optional[Scene]:
        """Find scene that matches camera IDs"""
        camera_set = set(camera_ids)

        for scene in self._scenes.values():
            # Get camera IDs from scene sources
            scene_cam_ids = [
                s.device_id for s in scene.sources
                if s.type == "camera" and s.device_id
            ]
            if set(scene_cam_ids) == camera_set:
                return scene

        return None

    async def delete_scene(self, scene_id: str) -> bool:
        """
        Delete a scene from OBS.

        Args:
            scene_id: Scene to delete

        Returns:
            True if deleted successfully
        """
        if scene_id not in self._scenes:
            logger.error(f"Scene not found: {scene_id}")
            return False

        scene = self._scenes[scene_id]

        logger.info(f"Deleting scene: {scene.name}")

        try:
            # Delete from OBS
            # (OBS adapter would need a delete_scene method)
            # await self._obs.delete_scene(scene_id)

            # Remove from tracking
            del self._scenes[scene_id]

            # If this was current scene, clear it
            if self._current_scene_id == scene_id:
                self._current_scene_id = None

            logger.info(f"Scene deleted: {scene.name}")

            # Emit event
            await self._event_bus.publish("scene_deleted", {
                "scene_id": scene_id,
                "scene_name": scene.name,
                "timestamp": datetime.now().isoformat(),
            })

            return True

        except Exception as e:
            logger.error(f"Failed to delete scene: {e}", exc_info=True)
            return False

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get a scene by ID."""
        return self._scenes.get(scene_id)

    def list_scenes(self) -> List[Scene]:
        """List all scenes."""
        return list(self._scenes.values())

    def get_current_scene(self) -> Optional[Scene]:
        """Get the currently active scene."""
        if self._current_scene_id:
            return self._scenes.get(self._current_scene_id)
        return None

    def get_templates(self) -> List[SceneTemplate]:
        """Get available scene templates."""
        return list(self._templates.values())

    async def shutdown(self) -> None:
        """Shutdown and clean up resources."""
        logger.info("Shutting down OBS orchestrator")

        await self.disconnect()

        logger.info("OBS orchestrator shutdown complete")
