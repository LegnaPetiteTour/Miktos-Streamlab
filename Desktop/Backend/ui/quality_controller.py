"""
Quality Controller - Integration layer for quality UI

Connects quality panel to API and WebSocket for complete functionality.
"""

import logging
from typing import Optional, TYPE_CHECKING
import httpx

from PyQt6.QtCore import QObject, pyqtSlot  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from ui.quality_panel import QualityPanel

logger = logging.getLogger(__name__)


class QualityController(QObject):
    """
    Controller for quality panel.

    Manages communication between UI, API, and WebSocket.
    """

    def __init__(
        self,
        quality_panel: 'QualityPanel',  # noqa: F821
        api_base_url: str = "http://localhost:8000",
        websocket_url: str = "ws://localhost:8000/ws/quality",
        source_name: str = "Camera",
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)

        self.panel = quality_panel
        self.api_base_url = api_base_url
        self.source_name = source_name

        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(base_url=api_base_url)

        # WebSocket client
        from ui.quality_websocket_client import QualityWebSocketClient
        self.websocket = QualityWebSocketClient(websocket_url, self)

        self._connect_signals()

        logger.info("QualityController initialized")

    def _connect_signals(self) -> None:
        """Connect panel signals to handlers"""
        # Panel signals
        self.panel.presetApplied.connect(self._on_preset_applied)
        self.panel.adjustmentChanged.connect(self._on_adjustment_changed)
        self.panel.nvEffectChanged.connect(self._on_nv_effect_changed)
        self.panel.autoEnhanceRequested.connect(self._on_auto_enhance)
        self.panel.resetRequested.connect(self._on_reset)

        # WebSocket signals
        self.websocket.connected.connect(self._on_ws_connected)
        self.websocket.disconnected.connect(self._on_ws_disconnected)
        self.websocket.qualityUpdate.connect(self._on_quality_update)
        self.websocket.error.connect(self._on_ws_error)

    def start(self) -> None:
        """Start quality monitoring"""
        # Check NVIDIA status
        self._check_nvidia_status()

        # Connect WebSocket
        self.websocket.connect_to_server()

        logger.info("Quality monitoring started")

    def stop(self) -> None:
        """Stop quality monitoring"""
        self.websocket.disconnect_from_server()
        logger.info("Quality monitoring stopped")

    @pyqtSlot(str)
    def _on_preset_applied(self, preset_name: str) -> None:
        """
        Handle preset applied.

        Args:
            preset_name: Name of preset to apply
        """
        try:
            import asyncio

            async def apply_preset() -> None:
                response = await self.http_client.post(
                    "/quality/apply-preset",
                    json={
                        "source_name": self.source_name,
                        "preset_name": preset_name
                    }
                )
                response.raise_for_status()
                logger.info(f"Applied preset: {preset_name}")

            # Run async in event loop
            asyncio.create_task(apply_preset())

        except Exception as e:
            logger.error(f"Failed to apply preset: {e}")

    @pyqtSlot(str, float)
    def _on_adjustment_changed(self, adjustment_type: str, value: float) -> None:
        """
        Handle manual adjustment changed.

        Args:
            adjustment_type: Type of adjustment
            value: Adjustment value
        """
        try:
            import asyncio

            async def apply_adjustment() -> None:
                response = await self.http_client.post(
                    "/quality/adjust",
                    json={
                        "source_name": self.source_name,
                        "adjustment_type": adjustment_type,
                        "value": value
                    }
                )
                response.raise_for_status()
                logger.debug(
                    f"Applied adjustment: {adjustment_type} = {value}"
                )

            asyncio.create_task(apply_adjustment())

        except Exception as e:
            logger.error(f"Failed to apply adjustment: {e}")

    @pyqtSlot(str, int)
    def _on_nv_effect_changed(self, effect: str, intensity: int) -> None:
        """
        Handle NVIDIA effect changed.

        Args:
            effect: Effect name
            intensity: Effect intensity (0-100)
        """
        try:
            import asyncio

            async def apply_effect() -> None:
                response = await self.http_client.post(
                    "/quality/nvidia",
                    json={
                        "source_name": self.source_name,
                        "effect": effect,
                        "intensity": intensity
                    }
                )
                response.raise_for_status()
                logger.info(f"Applied NVIDIA effect: {effect} = {intensity}")

            asyncio.create_task(apply_effect())

        except Exception as e:
            logger.error(f"Failed to apply NVIDIA effect: {e}")

    @pyqtSlot()
    def _on_auto_enhance(self) -> None:
        """Handle auto-enhance requested"""
        try:
            import asyncio

            async def auto_enhance() -> None:
                response = await self.http_client.post(
                    "/quality/auto-enhance",
                    json={
                        "source_name": self.source_name,
                        "preset": "professional"
                    }
                )
                response.raise_for_status()
                logger.info("Auto-enhancement applied")

            asyncio.create_task(auto_enhance())

        except Exception as e:
            logger.error(f"Failed to auto-enhance: {e}")

    @pyqtSlot()
    def _on_reset(self) -> None:
        """Handle reset requested"""
        try:
            import asyncio

            async def reset() -> None:
                response = await self.http_client.post(
                    "/quality/reset",
                    json={"source_name": self.source_name}
                )
                response.raise_for_status()
                logger.info("Quality reset")

            asyncio.create_task(reset())

        except Exception as e:
            logger.error(f"Failed to reset: {e}")

    @pyqtSlot()
    def _on_ws_connected(self) -> None:
        """Handle WebSocket connected"""
        self.panel.set_websocket_connected(True)
        logger.info("Quality WebSocket connected")

    @pyqtSlot()
    def _on_ws_disconnected(self) -> None:
        """Handle WebSocket disconnected"""
        self.panel.set_websocket_connected(False)
        logger.info("Quality WebSocket disconnected")

    @pyqtSlot(dict)
    def _on_quality_update(self, quality_data: dict) -> None:
        """
        Handle quality update from WebSocket.

        Args:
            quality_data: Quality analysis data
        """
        self.panel.update_quality(quality_data)

    @pyqtSlot(str)
    def _on_ws_error(self, error_msg: str) -> None:
        """
        Handle WebSocket error.

        Args:
            error_msg: Error message
        """
        logger.error(f"WebSocket error: {error_msg}")

    def _check_nvidia_status(self) -> None:
        """Check NVIDIA Broadcast status"""
        try:
            import asyncio

            async def check_status() -> None:
                response = await self.http_client.get(
                    "/quality/nvidia/status"
                )
                response.raise_for_status()

                status = response.json()
                available = status.get('available', False)
                gpu_name = status.get('gpu_name', '')

                self.panel.update_nvidia_status(available, gpu_name)

            asyncio.create_task(check_status())

        except Exception as e:
            logger.error(f"Failed to check NVIDIA status: {e}")
            self.panel.update_nvidia_status(False, "")
