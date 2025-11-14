"""
Quality WebSocket Client - UI integration for real-time quality updates

Connects quality panel to WebSocket for live monitoring.
"""

import logging
import json
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QThread  # type: ignore[import-not-found]
from PyQt6.QtWebSockets import QWebSocket  # type: ignore[import-not-found]
from PyQt6.QtNetwork import QAbstractSocket  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


class QualityWebSocketClient(QObject):
    """
    WebSocket client for quality monitoring.

    Connects to quality WebSocket and emits signals on updates.
    """

    # Signals
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    qualityUpdate = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        url: str = "ws://localhost:8000/ws/quality",
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)

        self.url = url
        self.websocket: Optional[QWebSocket] = None
        self.auto_reconnect = True
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

        logger.info(f"QualityWebSocketClient initialized: {url}")

    def connect_to_server(self) -> None:
        """Connect to WebSocket server"""
        if self.websocket:
            self.websocket.close()

        self.websocket = QWebSocket()
        assert self.websocket is not None  # Type narrowing for Pylance

        # Connect signals
        self.websocket.connected.connect(self._on_connected)
        self.websocket.disconnected.connect(self._on_disconnected)
        self.websocket.textMessageReceived.connect(self._on_message)
        self.websocket.errorOccurred.connect(self._on_error)

        # Open connection
        logger.info(f"Connecting to {self.url}")
        self.websocket.open(self.url)

    def disconnect_from_server(self) -> None:
        """Disconnect from WebSocket server"""
        self.auto_reconnect = False

        if self.websocket:
            self.websocket.close()
            self.websocket = None

    def send_message(self, message: str) -> None:
        """
        Send message to server.

        Args:
            message: Message to send
        """
        if (
            self.websocket and
            self.websocket.state() ==
            QAbstractSocket.SocketState.ConnectedState
        ):
            self.websocket.sendTextMessage(message)
        else:
            logger.warning("Cannot send message: not connected")

    def _on_connected(self) -> None:
        """Handle connection established"""
        logger.info("WebSocket connected")
        self.reconnect_attempts = 0
        self.connected.emit()

    def _on_disconnected(self) -> None:
        """Handle disconnection"""
        logger.info("WebSocket disconnected")
        self.disconnected.emit()

        # Auto-reconnect if enabled
        if (
            self.auto_reconnect and
            self.reconnect_attempts < self.max_reconnect_attempts
        ):
            self.reconnect_attempts += 1
            logger.info(
                f"Reconnecting... (attempt {self.reconnect_attempts}/"
                f"{self.max_reconnect_attempts})"
            )
            QThread.msleep(2000)  # Wait 2 seconds
            self.connect_to_server()

    def _on_message(self, message: str) -> None:
        """
        Handle incoming message.

        Args:
            message: JSON message from server
        """
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'quality_update':
                quality_data = data.get('quality', {})
                self.qualityUpdate.emit(quality_data)
            elif msg_type == 'pong':
                # Pong response - connection alive
                pass
            else:
                logger.warning(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _on_error(self, error_code: QAbstractSocket.SocketError) -> None:
        """
        Handle WebSocket error.

        Args:
            error_code: Error code
        """
        if self.websocket:
            error_msg = self.websocket.errorString()
            logger.error(f"WebSocket error ({error_code}): {error_msg}")
            self.error.emit(error_msg)

    def is_connected(self) -> bool:
        """Check if connected to server"""
        return (
            self.websocket is not None and
            self.websocket.state() == QAbstractSocket.SocketState.ConnectedState
        )
