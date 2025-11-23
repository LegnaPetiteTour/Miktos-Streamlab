"""
OBS WebSocket Controller - WebSocket 5.x Protocol (obsws-python)
================================================================

Modern OBS Studio controller using obsws-python library for WebSocket 5.x.
Handles scene management, streaming control, and health monitoring.

OBS Studio Version Required: 28+ (with WebSocket 5.x)
Library: obsws-python >= 1.8.0
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass

try:
    import obsws_python as obs
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False

logger = logging.getLogger(__name__)


class OBSStatus(Enum):
    """OBS connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class StreamingStatus(Enum):
    """OBS streaming status"""
    STOPPED = "stopped"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"


@dataclass
class OBSSceneInfo:
    """Scene information"""
    name: str
    index: int
    is_current: bool = False


@dataclass
class OBSStreamStats:
    """Streaming statistics"""
    is_streaming: bool
    bytes_sent: int
    duration_seconds: int
    fps: float
    render_frames: int
    dropped_frames: int
    total_frames: int

    @property
    def drop_percentage(self) -> float:
        """Calculate drop percentage"""
        if self.total_frames == 0:
            return 0.0
        return (self.dropped_frames / self.total_frames) * 100


class OBSController:
    """
    OBS Studio controller using obsws-python (WebSocket 5.x).

    Features:
    - Scene management (list, switch, create)
    - Streaming control (start, stop, status)
    - Source visibility control
    - Health monitoring
    - Automatic reconnection

    Usage:
        controller = OBSController(
            host='localhost',
            port=4455,
            password='your_password'
        )

        if await controller.connect():
            # Get current scene
            scene = await controller.get_current_scene()

            # Switch scene
            await controller.switch_scene("Main Scene")

            # Start streaming
            await controller.start_streaming()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 4455,
        password: str = "",
        auto_reconnect: bool = True,
        reconnect_interval: int = 10
    ):
        """
        Initialize OBS controller

        Args:
            host: OBS WebSocket host
            port: OBS WebSocket port
            password: OBS WebSocket password
            auto_reconnect: Enable automatic reconnection
            reconnect_interval: Seconds between reconnection attempts
        """
        if not OBS_AVAILABLE:
            raise RuntimeError(
                "obsws-python not installed. "
                "Install with: pip install obsws-python"
            )

        self._host = host
        self._port = port
        self._password = password
        self._auto_reconnect = auto_reconnect
        self._reconnect_interval = reconnect_interval

        self._client: Optional[obs.ReqClient] = None
        self._status = OBSStatus.DISCONNECTED
        self._reconnect_task: Optional[asyncio.Task] = None

        logger.info(
            f"OBSController initialized (host={host}, port={port})"
        )

    async def connect(self) -> bool:
        """
        Connect to OBS Studio

        Returns:
            True if connected successfully
        """
        try:
            self._status = OBSStatus.CONNECTING
            logger.info(f"Connecting to OBS at {self._host}:{self._port}")

            # Create synchronous client
            self._client = obs.ReqClient(
                host=self._host,
                port=self._port,
                password=self._password,
                timeout=5
            )

            # Test connection by getting version
            version_info = self._client.get_version()
            logger.info(
                f"Connected to OBS {version_info.obs_version} "
                f"(WebSocket {version_info.obs_web_socket_version})"
            )

            self._status = OBSStatus.CONNECTED

            # Start auto-reconnect monitor if enabled
            if self._auto_reconnect and not self._reconnect_task:
                self._reconnect_task = asyncio.create_task(
                    self._auto_reconnect_loop()
                )

            return True

        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            self._status = OBSStatus.ERROR
            self._client = None
            return False

    async def disconnect(self) -> None:
        """Disconnect from OBS Studio"""
        try:
            # Cancel reconnect task
            if self._reconnect_task:
                self._reconnect_task.cancel()
                self._reconnect_task = None

            # Close client
            if self._client:
                self._client = None

            self._status = OBSStatus.DISCONNECTED
            logger.info("Disconnected from OBS")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def _auto_reconnect_loop(self) -> None:
        """Monitor connection and auto-reconnect if needed"""
        while self._auto_reconnect:
            try:
                await asyncio.sleep(self._reconnect_interval)

                # Check if still connected
                if not self.is_connected():
                    logger.info("Attempting to reconnect to OBS...")
                    await self.connect()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reconnect loop: {e}")

    def is_connected(self) -> bool:
        """Check if connected to OBS"""
        if not self._client:
            return False

        try:
            # Try to get version as connection check
            self._client.get_version()
            return True
        except Exception:
            self._status = OBSStatus.DISCONNECTED
            return False

    def _ensure_connected(self) -> bool:
        """
        Ensure OBS is connected

        Raises:
            ConnectionError if not connected
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to OBS")
        return True

    async def get_scenes(self) -> List[OBSSceneInfo]:
        """
        Get list of all scenes

        Returns:
            List of scene information
        """
        self._ensure_connected()

        try:
            # Get scene list
            response = self._client.get_scene_list()

            # Get current scene name
            current_scene = response.current_program_scene_name

            scenes = []
            for idx, scene in enumerate(response.scenes):
                scenes.append(OBSSceneInfo(
                    name=scene['sceneName'],
                    index=idx,
                    is_current=(scene['sceneName'] == current_scene)
                ))

            return scenes

        except Exception as e:
            logger.error(f"Failed to get scenes: {e}")
            return []

    async def get_current_scene(self) -> Optional[str]:
        """
        Get current active scene name

        Returns:
            Scene name or None
        """
        self._ensure_connected()

        try:
            response = self._client.get_current_program_scene()
            return response.current_program_scene_name

        except Exception as e:
            logger.error(f"Failed to get current scene: {e}")
            return None

    async def switch_scene(self, scene_name: str) -> bool:
        """
        Switch to specified scene

        Args:
            scene_name: Name of scene to switch to

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            self._client.set_current_program_scene(scene_name)
            logger.info(f"Switched to scene: {scene_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to switch scene: {e}")
            return False

    async def create_scene(self, scene_name: str) -> bool:
        """
        Create a new scene

        Args:
            scene_name: Name for new scene

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            self._client.create_scene(scene_name)
            logger.info(f"Created scene: {scene_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create scene: {e}")
            return False

    async def set_source_visibility(
        self,
        scene_name: str,
        source_name: str,
        visible: bool
    ) -> bool:
        """
        Set visibility of a source in a scene

        Args:
            scene_name: Scene containing the source
            source_name: Source to modify
            visible: True to show, False to hide

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            # Get scene item ID
            response = self._client.get_scene_item_id(
                scene_name,
                source_name
            )
            item_id = response.scene_item_id

            # Set visibility
            self._client.set_scene_item_enabled(
                scene_name,
                item_id,
                visible
            )

            logger.info(
                f"Set {source_name} visibility to {visible} "
                f"in {scene_name}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to set source visibility: {e}")
            return False

    async def start_streaming(self) -> bool:
        """
        Start streaming

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            # Check if already streaming
            status = self._client.get_stream_status()
            if status.output_active:
                logger.warning("Already streaming")
                return True

            # Start streaming
            self._client.start_stream()
            logger.info("Started streaming")
            return True

        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            return False

    async def stop_streaming(self) -> bool:
        """
        Stop streaming

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            # Check if streaming
            status = self._client.get_stream_status()
            if not status.output_active:
                logger.warning("Not currently streaming")
                return True

            # Stop streaming
            self._client.stop_stream()
            logger.info("Stopped streaming")
            return True

        except Exception as e:
            logger.error(f"Failed to stop streaming: {e}")
            return False

    async def get_streaming_status(self) -> StreamingStatus:
        """
        Get current streaming status

        Returns:
            StreamingStatus enum value
        """
        self._ensure_connected()

        try:
            status = self._client.get_stream_status()
            return (
                StreamingStatus.ACTIVE if status.output_active
                else StreamingStatus.STOPPED
            )

        except Exception as e:
            logger.error(f"Failed to get streaming status: {e}")
            return StreamingStatus.STOPPED

    async def get_stream_stats(self) -> Optional[OBSStreamStats]:
        """
        Get streaming statistics

        Returns:
            Stream statistics or None
        """
        self._ensure_connected()

        try:
            status = self._client.get_stream_status()
            stats = self._client.get_stats()

            return OBSStreamStats(
                is_streaming=status.output_active,
                bytes_sent=status.output_bytes,
                duration_seconds=int(status.output_duration / 1000),
                fps=stats.active_fps,
                render_frames=stats.render_total_frames,
                dropped_frames=stats.render_skipped_frames,
                total_frames=stats.output_total_frames
            )

        except Exception as e:
            logger.error(f"Failed to get stream stats: {e}")
            return None

    async def get_health(self) -> Dict[str, Any]:
        """
        Get OBS health metrics

        Returns:
            Health metrics dictionary
        """
        self._ensure_connected()

        try:
            stats = self._client.get_stats()

            return {
                "connected": True,
                "fps": stats.active_fps,
                "cpu_usage": stats.cpu_usage,
                "memory_usage": stats.memory_usage,
                "render_frames": stats.render_total_frames,
                "skipped_frames": stats.render_skipped_frames,
                "output_frames": stats.output_total_frames,
                "average_frame_time": stats.average_frame_render_time
            }

        except Exception as e:
            logger.error(f"Failed to get health: {e}")
            return {
                "connected": False,
                "error": str(e)
            }

    async def get_version(self) -> Optional[str]:
        """
        Get OBS version

        Returns:
            Version string or None
        """
        self._ensure_connected()

        try:
            version_info = self._client.get_version()
            return version_info.obs_version

        except Exception as e:
            logger.error(f"Failed to get version: {e}")
            return None

    async def update_text_source(
        self,
        source_name: str,
        text: str
    ) -> bool:
        """
        Update text in a text source

        Args:
            source_name: Name of text source
            text: New text content

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            self._client.set_input_settings(
                source_name,
                {"text": text},
                True  # overlay (don't replace all settings)
            )
            logger.info(f"Updated text source '{source_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to update text source: {e}")
            return False

    async def get_scene_items(
        self,
        scene_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get all items in a scene

        Args:
            scene_name: Scene to query

        Returns:
            List of scene item dictionaries
        """
        self._ensure_connected()

        try:
            response = self._client.get_scene_item_list(scene_name)
            return response.scene_items

        except Exception as e:
            logger.error(f"Failed to get scene items: {e}")
            return []

    async def start_recording(self) -> bool:
        """
        Start recording

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            # Check if already recording
            status = self._client.get_record_status()
            if status.output_active:
                logger.warning("Already recording")
                return True

            # Start recording
            self._client.start_record()
            logger.info("Started recording")
            return True

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False

    async def stop_recording(self) -> bool:
        """
        Stop recording

        Returns:
            True if successful
        """
        self._ensure_connected()

        try:
            # Check if recording
            status = self._client.get_record_status()
            if not status.output_active:
                logger.warning("Not currently recording")
                return True

            # Stop recording
            self._client.stop_record()
            logger.info("Stopped recording")
            return True

        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False
