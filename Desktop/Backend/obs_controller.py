"""
OBS WebSocket Controller - WebSocket 5.x Protocol
=================================================

Handles communication with OBS Studio via WebSocket 5.x protocol.
Supports scene management, streaming control, and slate display.

OBS Studio Version Required: 28+ (with WebSocket 5.x plugin)
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass

try:
    from obswebsocket import obsws, requests as obs_requests  # type: ignore[import-untyped]  # noqa: E501
    from obswebsocket.exceptions import (  # type: ignore[import-untyped]
        ConnectionFailure
    )
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False
    ConnectionFailure = Exception


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
    OBS Studio controller using WebSocket 5.x protocol.

    Features:
    - Scene management (list, switch, create)
    - Streaming control (start, stop, status)
    - Source visibility control (for slate display)
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

            # Monitor health
            health = await controller.get_health()

            await controller.disconnect()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 4455,
        password: str = "",
        auto_reconnect: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize OBS controller.

        Args:
            host: OBS WebSocket server host
            port: OBS WebSocket server port
            password: OBS WebSocket password
            auto_reconnect: Enable automatic reconnection
            logger: Optional logger instance
        """
        if not OBS_AVAILABLE:
            raise ImportError(
                "obs-websocket-py is not installed. "
                "Install with: pip install obs-websocket-py"
            )

        self.host = host
        self.port = port
        self.password = password
        self.auto_reconnect = auto_reconnect

        self.logger = logger or logging.getLogger(__name__)

        self.ws: Optional[obsws] = None
        self.status = OBSStatus.DISCONNECTED
        self.streaming_status = StreamingStatus.STOPPED

        self._reconnect_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """
        Connect to OBS Studio.

        Returns:
            True if connection successful, False otherwise
        """
        if self.status == OBSStatus.CONNECTED:
            self.logger.warning("Already connected to OBS")
            return True

        try:
            self.status = OBSStatus.CONNECTING
            self.logger.info(f"Connecting to OBS at {self.host}:{self.port}")

            # Create WebSocket connection
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()

            self.status = OBSStatus.CONNECTED
            self.logger.info("Successfully connected to OBS")

            # Start health monitoring if enabled
            if self.auto_reconnect and not self._health_check_task:
                self._health_check_task = asyncio.create_task(
                    self._health_monitor()
                )

            return True

        except Exception as e:
            # Catch all connection errors
            # (ConnectionFailure, socket errors, etc.)
            self.logger.error(f"Failed to connect to OBS: {e}")
            self.status = OBSStatus.ERROR

            # Only auto-reconnect if enabled and not already reconnecting
            if self.auto_reconnect and not self._reconnect_task:
                self._reconnect_task = asyncio.create_task(
                    self._auto_reconnect()
                )

            return False

    async def disconnect(self) -> None:
        """Disconnect from OBS Studio."""
        if self._health_check_task:
            self._health_check_task.cancel()
            self._health_check_task = None

        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None

        if self.ws:
            try:
                self.ws.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting from OBS: {e}")
            finally:
                self.ws = None
                self.status = OBSStatus.DISCONNECTED
                self.logger.info("Disconnected from OBS")

    async def _auto_reconnect(self) -> None:
        """Automatic reconnection loop."""
        reconnect_delay = 5  # seconds

        while self.auto_reconnect and self.status != OBSStatus.CONNECTED:
            await asyncio.sleep(reconnect_delay)

            self.logger.info("Attempting to reconnect to OBS...")
            if await self.connect():
                self.logger.info("Successfully reconnected to OBS")
                self._reconnect_task = None
                return

            # Exponential backoff (max 60 seconds)
            reconnect_delay = min(reconnect_delay * 2, 60)

    async def _health_monitor(self) -> None:
        """Monitor OBS connection health."""
        while self.status == OBSStatus.CONNECTED:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                # Ping OBS to check connection
                if self.ws:
                    try:
                        self.ws.call(obs_requests.GetVersion())
                    except Exception:
                        self.logger.error("OBS health check failed")
                        self.status = OBSStatus.ERROR
                        if self.auto_reconnect:
                            asyncio.create_task(self._auto_reconnect())
                        break

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")

    def _ensure_connected(self) -> bool:
        """Ensure OBS is connected before operations."""
        if self.status != OBSStatus.CONNECTED or not self.ws:
            self.logger.error("Not connected to OBS")
            return False
        return True

    # ============================================================================
    # Scene Management
    # ============================================================================

    async def get_scenes(self) -> List[OBSSceneInfo]:
        """
        Get list of all scenes.

        Returns:
            List of scene information
        """
        if not self._ensure_connected():
            return []

        try:
            response = self.ws.call(  # type: ignore[union-attr]
                obs_requests.GetSceneList()
            )
            scenes = []

            current_scene = response.datain.get('currentProgramSceneName', '')

            scenes_data = response.datain.get('scenes', [])
            for idx, scene_dict in enumerate(scenes_data):
                scene_name = scene_dict.get('sceneName', '')
                scenes.append(OBSSceneInfo(
                    name=scene_name,
                    index=idx,
                    is_current=(scene_name == current_scene)
                ))

            return scenes

        except Exception as e:
            self.logger.error(f"Failed to get scenes: {e}")
            return []

    async def get_current_scene(self) -> Optional[str]:
        """
        Get current active scene.

        Returns:
            Scene name or None if error
        """
        if not self._ensure_connected():
            return None

        try:
            response = self.ws.call(  # type: ignore[union-attr]
                obs_requests.GetCurrentProgramScene()
            )
            return str(response.datain.get('currentProgramSceneName', ''))
        except Exception as e:
            self.logger.error(f"Failed to get current scene: {e}")
            return None

    async def switch_scene(self, scene_name: str) -> bool:
        """
        Switch to a different scene.

        Args:
            scene_name: Name of the scene to switch to

        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            self.logger.info(f"Switching to scene: {scene_name}")
            self.ws.call(  # type: ignore[union-attr]
                obs_requests.SetCurrentProgramScene(
                    sceneName=scene_name
                )
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to switch scene: {e}")
            return False

    async def create_scene(self, scene_name: str) -> bool:
        """
        Create a new scene.

        Args:
            scene_name: Name for the new scene

        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            self.logger.info(f"Creating scene: {scene_name}")
            self.ws.call(  # type: ignore[union-attr]
                obs_requests.CreateScene(sceneName=scene_name)
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to create scene: {e}")
            return False

    # ============================================================================
    # Source Management (for slate display)
    # ============================================================================

    async def set_source_visibility(
        self,
        scene_name: str,
        source_name: str,
        visible: bool
    ) -> bool:
        """
        Show or hide a source in a scene.

        Args:
            scene_name: Scene containing the source
            source_name: Name of the source
            visible: True to show, False to hide

        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            self.logger.info(
                f"Setting source '{source_name}' visibility to {visible} "
                f"in scene '{scene_name}'"
            )

            self.ws.call(  # type: ignore[union-attr]
                obs_requests.SetSceneItemEnabled(
                    sceneName=scene_name,
                    sceneItemId=source_name,
                    # Might need adjustment based on OBS API
                    sceneItemEnabled=visible
                )
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set source visibility: {e}")
            return False

    async def show_slate(self, scene_name: str = "Slate") -> bool:
        """
        Show the slate scene (technical difficulties screen).

        Args:
            scene_name: Name of the slate scene

        Returns:
            True if successful, False otherwise
        """
        return await self.switch_scene(scene_name)

    async def hide_slate(self, main_scene_name: str = "Main") -> bool:
        """
        Hide the slate and return to main scene.

        Args:
            main_scene_name: Name of the main scene to return to

        Returns:
            True if successful, False otherwise
        """
        return await self.switch_scene(main_scene_name)

    # ============================================================================
    # Streaming Control
    # ============================================================================

    async def start_streaming(self) -> bool:
        """
        Start streaming in OBS.

        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            # Check if already streaming
            status = await self.get_streaming_status()
            if status == StreamingStatus.ACTIVE:
                self.logger.warning("Already streaming")
                return True

            self.logger.info("Starting stream")
            self.streaming_status = StreamingStatus.STARTING

            self.ws.call(  # type: ignore[union-attr]
                obs_requests.StartStream()
            )

            self.streaming_status = StreamingStatus.ACTIVE
            self.logger.info("Stream started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
            self.streaming_status = StreamingStatus.STOPPED
            return False

    async def stop_streaming(self) -> bool:
        """
        Stop streaming in OBS.

        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            self.logger.info("Stopping stream")
            self.streaming_status = StreamingStatus.STOPPING

            self.ws.call(obs_requests.StopStream())  # type: ignore[union-attr]

            self.streaming_status = StreamingStatus.STOPPED
            self.logger.info("Stream stopped successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop streaming: {e}")
            return False

    async def get_streaming_status(self) -> StreamingStatus:
        """
        Get current streaming status.

        Returns:
            Current streaming status
        """
        if not self._ensure_connected():
            return StreamingStatus.STOPPED

        try:
            response = self.ws.call(  # type: ignore[union-attr]
                obs_requests.GetStreamStatus()
            )
            is_streaming = response.datain.get('outputActive', False)

            if is_streaming:
                self.streaming_status = StreamingStatus.ACTIVE
            else:
                self.streaming_status = StreamingStatus.STOPPED

            return self.streaming_status

        except Exception as e:
            self.logger.error(f"Failed to get streaming status: {e}")
            return StreamingStatus.STOPPED

    async def get_stream_stats(self) -> Optional[OBSStreamStats]:
        """
        Get streaming statistics.

        Returns:
            Stream statistics or None if not available
        """
        if not self._ensure_connected():
            return None

        try:
            response = self.ws.call(  # type: ignore[union-attr]
                obs_requests.GetStreamStatus()
            )
            data = response.datain

            return OBSStreamStats(
                is_streaming=data.get('outputActive', False),
                bytes_sent=data.get('outputBytes', 0),
                # Convert ms to seconds
                duration_seconds=data.get('outputDuration', 0) // 1000,
                fps=data.get('outputSkippedFrames', 0),
                render_frames=data.get('outputTotalFrames', 0),
                dropped_frames=data.get('outputSkippedFrames', 0),
                total_frames=data.get('outputTotalFrames', 0)
            )

        except Exception as e:
            self.logger.error(f"Failed to get stream stats: {e}")
            return None

    # ============================================================================
    # Health & Monitoring
    # ============================================================================

    async def get_health(self) -> Dict[str, Any]:
        """
        Get OBS health information.

        Returns:
            Dictionary with health metrics
        """
        health = {
            "connected": self.status == OBSStatus.CONNECTED,
            "status": self.status.value,
            "streaming": self.streaming_status.value,
            "version": None,
            "fps": None,
            "cpu_usage": None,
            "memory_usage": None
        }

        if not self._ensure_connected():
            return health

        try:
            # Get OBS version
            version_response = self.ws.call(  # type: ignore[union-attr]
                obs_requests.GetVersion()
            )
            health["version"] = version_response.datain.get(
                'obsVersion', 'unknown'
            )

            # Get stats
            stats_response = self.ws.call(  # type: ignore[union-attr]
                obs_requests.GetStats()
            )
            stats = stats_response.datain

            health["fps"] = stats.get('activeFps', 0)
            health["cpu_usage"] = stats.get('cpuUsage', 0)
            health["memory_usage"] = stats.get('memoryUsage', 0)

        except Exception as e:
            self.logger.error(f"Failed to get health info: {e}")

        return health

    async def get_version(self) -> Optional[str]:
        """
        Get OBS Studio version.

        Returns:
            Version string or None if error
        """
        if not self._ensure_connected():
            return None

        try:
            response = self.ws.call(  # type: ignore[union-attr]
                obs_requests.GetVersion()
            )
            return str(response.datain.get('obsVersion', ''))
        except Exception as e:
            self.logger.error(f"Failed to get OBS version: {e}")
            return None

    # ============================================================================
    # Source Management
    # ============================================================================

    async def update_text_source(
        self,
        source_name: str,
        text: str
    ) -> bool:
        """
        Update text in a text source (GDI+/FreeType).

        Args:
            source_name: Name of the text source
            text: New text content

        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            self.ws.call(  # type: ignore[union-attr]
                obs_requests.SetInputSettings(
                    inputName=source_name,
                    inputSettings={"text": text}
                )
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to update text source '{source_name}': {e}"
            )
            return False

    async def get_scene_items(self, scene_name: str) -> List[Dict[str, Any]]:
        """
        Get all items/sources in a scene.

        Args:
            scene_name: Name of the scene

        Returns:
            List of scene items with their properties
        """
        if not self._ensure_connected():
            return []

        try:
            response = self.ws.call(  # type: ignore[union-attr]
                obs_requests.GetSceneItemList(sceneName=scene_name)
            )
            return list(response.datain.get('sceneItems', []))
        except Exception as e:
            self.logger.error(
                f"Failed to get scene items for '{scene_name}': {e}"
            )
            return []
