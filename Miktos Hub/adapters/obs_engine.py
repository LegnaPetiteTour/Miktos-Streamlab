"""
OBS Engine Adapter - Wraps existing obs_controller.py

This adapter implements the IEngineAdapter interface using your existing
OBS controller. It translates between the Hub's generic engine interface
and the specific OBS WebSocket implementation.
"""

from typing import List, Dict, Any, Optional
import logging
import sys
import os

# Add existing backend to path
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

try:
    from obs_controller import OBSController, OBSStatus, StreamingStatus
    OBS_AVAILABLE = True
except ImportError:
    OBSController = None
    OBSStatus = None
    StreamingStatus = None
    OBS_AVAILABLE = False

from core.interfaces import EngineAdapterProtocol
from models.camera import CameraDevice, TransportType
from models.scene import Scene
from models.destination import StreamDestination
from dataclasses import dataclass
from typing import Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class EngineHealth:
    """Engine health metrics"""
    is_healthy: bool
    fps: float
    dropped_frames: int
    cpu_usage: float
    gpu_usage: float
    memory_usage: float
    details: Dict[str, Any]


class OBSEngineAdapter:
    """
    Adapter for OBS Studio engine
    
    This wraps your existing OBS controller and exposes it through
    the standard engine interface. It handles:
    - Connection management
    - Scene creation and switching
    - Camera source attachment
    - Stream start/stop
    - Health monitoring
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 4455,
        password: str = ""
    ):
        if not OBS_AVAILABLE:
            raise RuntimeError("OBS WebSocket library not available")
        
        self._controller = OBSController(
            host=host,
            port=port,
            password=password
        )
        
        self._connected = False
        self._host = host
        self._port = port
        
        logger.info(f"OBS Engine Adapter initialized (host={host}, port={port})")
    
    async def connect(self) -> bool:
        """
        Connect to OBS Studio
        
        Returns:
            True if connected successfully
        """
        try:
            success = await self._controller.connect()
            self._connected = success
            
            if success:
                logger.info("Connected to OBS Studio")
            else:
                logger.error("Failed to connect to OBS Studio")
            
            return success
            
        except Exception as e:
            logger.error(f"Error connecting to OBS: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from OBS Studio
        
        Returns:
            True if disconnected successfully
        """
        try:
            await self._controller.disconnect()
            self._connected = False
            logger.info("Disconnected from OBS Studio")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from OBS: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to OBS"""
        return self._connected and self._controller.status == OBSStatus.CONNECTED
    
    async def list_scenes(self) -> List[Scene]:
        """
        List all scenes in OBS
        
        Returns:
            List of Scene objects
        """
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return []
        
        try:
            obs_scenes = await self._controller.list_scenes()
            
            # Convert OBS scenes to Hub Scene objects
            scenes = []
            for obs_scene in obs_scenes:
                scene = Scene(
                    id=f"obs_scene_{obs_scene.name}",
                    name=obs_scene.name,
                    layout_type="custom",  # OBS uses custom layouts
                    sources=[],  # Would need additional OBS API call to get sources
                    metadata={
                        "index": obs_scene.index,
                        "is_current": obs_scene.is_current
                    }
                )
                scenes.append(scene)
            
            logger.debug(f"Listed {len(scenes)} scenes from OBS")
            return scenes
            
        except Exception as e:
            logger.error(f"Error listing OBS scenes: {e}")
            return []
    
    async def create_scene(self, name: str, layout_type: str, config: Optional[Dict] = None) -> Scene:
        """
        Create a new scene in OBS
        
        Args:
            name: Scene name
            layout_type: Layout type (not used in OBS)
            config: Additional configuration
            
        Returns:
            Created scene
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to OBS")
        
        try:
            # Create scene in OBS
            success = await self._controller.create_scene(name)
            
            if not success:
                raise RuntimeError(f"Failed to create scene: {name}")
            
            scene = Scene(
                id=f"obs_scene_{name}",
                name=name,
                layout_type=layout_type,
                sources=[],
                metadata=config or {}
            )
            
            logger.info(f"Created OBS scene: {name}")
            return scene
            
        except Exception as e:
            logger.error(f"Error creating OBS scene: {e}")
            raise
    
    async def switch_scene(self, scene_id: str, transition: Optional[str] = None) -> bool:
        """
        Switch to a different scene
        
        Args:
            scene_id: Scene ID (format: "obs_scene_{name}")
            transition: Optional transition name
            
        Returns:
            True if switched successfully
        """
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
        
        try:
            # Extract scene name from ID
            scene_name = scene_id.replace("obs_scene_", "")
            
            success = await self._controller.switch_scene(scene_name)
            
            if success:
                logger.info(f"Switched to OBS scene: {scene_name}")
            else:
                logger.error(f"Failed to switch to scene: {scene_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error switching OBS scene: {e}")
            return False
    
    async def attach_camera(self, camera: CameraDevice, scene_id: str, config: Optional[Dict] = None) -> bool:
        """
        Attach a camera to a scene
        
        For OBS, this means creating a media source (for SRT/RTSP/etc.)
        
        Args:
            camera: Camera to attach
            scene_id: Target scene
            config: Source configuration (position, size, etc.)
            
        Returns:
            True if attached successfully
        """
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
        
        try:
            scene_name = scene_id.replace("obs_scene_", "")
            
            # Determine source type based on transport
            if camera.transport == TransportType.SRT:
                # Create Media Source for SRT stream
                source_name = f"camera_{camera.id}"
                
                # For SRT, the URL format is typically: srt://host:port?streamid=...
                source_settings = {
                    "input": camera.metadata.get("srt_url", camera.id),
                    "is_local_file": False,
                    "hw_decode": True  # Use hardware decoding if available
                }
                
                # Note: This requires extending your OBS controller to support
                # creating sources. For now, log what would be created.
                logger.info(
                    f"Would create SRT source '{source_name}' in scene '{scene_name}' "
                    f"with URL: {source_settings['input']}"
                )
                
                # TODO: Implement actual source creation in obs_controller.py
                # success = await self._controller.create_media_source(
                #     scene_name, source_name, source_settings
                # )
                
                return True
                
            else:
                logger.warning(f"Unsupported transport type: {camera.transport}")
                return False
                
        except Exception as e:
            logger.error(f"Error attaching camera to OBS: {e}")
            return False
    
    async def detach_camera(self, camera_id: str, scene_id: str) -> bool:
        """
        Detach a camera from a scene
        
        Args:
            camera_id: Camera to detach
            scene_id: Scene to detach from
            
        Returns:
            True if detached successfully
        """
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
        
        try:
            scene_name = scene_id.replace("obs_scene_", "")
            source_name = f"camera_{camera_id}"
            
            logger.info(f"Would remove source '{source_name}' from scene '{scene_name}'")
            
            # TODO: Implement source removal in obs_controller.py
            # success = await self._controller.remove_source(scene_name, source_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Error detaching camera from OBS: {e}")
            return False
    
    async def start_streaming(self, destinations: List[StreamDestination]) -> bool:
        """
        Start streaming to destinations
        
        Note: OBS has a single stream output. Multi-destination streaming
        is handled by your egress_v2.py module, not OBS directly.
        
        Args:
            destinations: List of streaming destinations
            
        Returns:
            True if started successfully
        """
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
        
        try:
            success = await self._controller.start_streaming()
            
            if success:
                logger.info("Started OBS streaming")
            else:
                logger.error("Failed to start OBS streaming")
            
            return success
            
        except Exception as e:
            logger.error(f"Error starting OBS streaming: {e}")
            return False
    
    async def stop_streaming(self) -> bool:
        """
        Stop streaming
        
        Returns:
            True if stopped successfully
        """
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
        
        try:
            success = await self._controller.stop_streaming()
            
            if success:
                logger.info("Stopped OBS streaming")
            else:
                logger.error("Failed to stop OBS streaming")
            
            return success
            
        except Exception as e:
            logger.error(f"Error stopping OBS streaming: {e}")
            return False
    
    async def start_recording(self, path: Optional[str] = None) -> bool:
        """
        Start recording
        
        Args:
            path: Optional recording path
            
        Returns:
            True if started successfully
        """
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
        
        try:
            success = await self._controller.start_recording()
            
            if success:
                logger.info("Started OBS recording")
            else:
                logger.error("Failed to start OBS recording")
            
            return success
            
        except Exception as e:
            logger.error(f"Error starting OBS recording: {e}")
            return False
    
    async def stop_recording(self) -> bool:
        """
        Stop recording
        
        Returns:
            True if stopped successfully
        """
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
        
        try:
            success = await self._controller.stop_recording()
            
            if success:
                logger.info("Stopped OBS recording")
            else:
                logger.error("Failed to stop OBS recording")
            
            return success
            
        except Exception as e:
            logger.error(f"Error stopping OBS recording: {e}")
            return False
    
    async def get_health(self) -> EngineHealth:
        """
        Get engine health metrics
        
        Returns:
            Health information
        """
        if not self.is_connected():
            return EngineHealth(
                is_healthy=False,
                fps=0.0,
                dropped_frames=0,
                cpu_usage=0.0,
                gpu_usage=0.0,
                memory_usage=0.0,
                details={"error": "Not connected to OBS"}
            )
        
        try:
            # Get streaming stats from OBS
            stats = await self._controller.get_stream_stats()
            health = await self._controller.get_health()
            
            is_healthy = (
                self._connected and
                stats.drop_percentage < 5.0 and  # Less than 5% dropped frames
                health["status"] == "healthy"
            )
            
            return EngineHealth(
                is_healthy=is_healthy,
                fps=stats.fps,
                dropped_frames=stats.dropped_frames,
                cpu_usage=health.get("cpu_usage", 0.0),
                gpu_usage=health.get("gpu_usage", 0.0),
                memory_usage=health.get("memory_mb", 0.0),
                details={
                    "streaming": stats.is_streaming,
                    "total_frames": stats.total_frames,
                    "drop_percentage": stats.drop_percentage,
                    "render_frames": stats.render_frames,
                    "bytes_sent": stats.bytes_sent
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting OBS health: {e}")
            return EngineHealth(
                is_healthy=False,
                fps=0.0,
                dropped_frames=0,
                cpu_usage=0.0,
                gpu_usage=0.0,
                memory_usage=0.0,
                details={"error": str(e)}
            )
