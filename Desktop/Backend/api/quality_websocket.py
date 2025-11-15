"""
Quality WebSocket - Real-time quality monitoring

Provides WebSocket for live quality updates.
"""

import asyncio
import logging
from typing import Optional, Any, Set
from datetime import datetime, UTC

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class QualityWebSocket:
    """
    WebSocket for real-time quality monitoring.

    Sends periodic quality updates to connected clients.
    """

    def __init__(
        self,
        quality_analyzer: Any,
        update_interval: float = 2.0
    ) -> None:
        """
        Initialize quality WebSocket.

        Args:
            quality_analyzer: QualityAnalyzer instance
            update_interval: Seconds between updates
        """
        self.analyzer = quality_analyzer
        self.update_interval = update_interval

        # Connected clients
        self.active_connections: Set[WebSocket] = set()

        # Monitoring task
        self.monitoring_task: Optional[asyncio.Task[None]] = None

        logger.info("QualityWebSocket initialized")

    async def connect(self, websocket: WebSocket) -> None:
        """
        Connect new client.

        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections.add(websocket)

        logger.info(
            f"Client connected. Total: {len(self.active_connections)}"
        )

        # Start monitoring if first client
        if len(self.active_connections) == 1:
            await self._start_monitoring()

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect client.

        Args:
            websocket: WebSocket connection
        """
        self.active_connections.discard(websocket)

        logger.info(
            f"Client disconnected. Total: {len(self.active_connections)}"
        )

        # Stop monitoring if no clients
        if len(self.active_connections) == 0:
            self._stop_monitoring()

    async def _start_monitoring(self) -> None:
        """Start quality monitoring task"""
        if not self.monitoring_task or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(
                self._monitor_quality()
            )
            logger.info("Started quality monitoring")

    def _stop_monitoring(self) -> None:
        """Stop quality monitoring task"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            logger.info("Stopped quality monitoring")

    async def _monitor_quality(self) -> None:
        """Monitor quality and broadcast updates"""
        try:
            while True:
                if not self.active_connections:
                    break

                # Analyze quality
                # In production, would capture frame from OBS
                import numpy as np

                # Simulate frame
                test_frame = np.random.randint(
                    100,
                    150,
                    (480, 640, 3),
                    dtype=np.uint8
                )

                quality = self.analyzer.analyze_frame(test_frame)

                # Prepare update
                update = {
                    'type': 'quality_update',
                    'timestamp': datetime.now(UTC).isoformat(),
                    'quality': quality.to_dict()
                }

                # Broadcast to all clients
                await self._broadcast(update)

                # Wait for next update
                await asyncio.sleep(self.update_interval)

        except asyncio.CancelledError:
            logger.info("Quality monitoring cancelled")
        except Exception as e:
            logger.error(f"Quality monitoring error: {e}")

    async def _broadcast(self, message: dict) -> None:
        """
        Broadcast message to all clients.

        Args:
            message: Message to send
        """
        disconnected = set()

        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Send failed: {e}")
                disconnected.add(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

    async def handle_client(self, websocket: WebSocket) -> None:
        """
        Handle client connection.

        Args:
            websocket: WebSocket connection
        """
        await self.connect(websocket)

        try:
            # Keep connection alive
            while True:
                # Receive messages (ping/pong)
                message = await websocket.receive_text()

                # Echo back (can add command handling here)
                await websocket.send_json({
                    'type': 'pong',
                    'received': message,
                    'timestamp': datetime.now(UTC).isoformat()
                })

        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.disconnect(websocket)
