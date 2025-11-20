#!/usr/bin/env python3
"""
Miktos StreamLab - Desktop Control Panel
Flask + SocketIO web interface for controlling camera phones
"""

import asyncio
import json
import logging
import threading
from datetime import datetime
from typing import Dict

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import websockets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'miktos-streamlab-secret-2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
camera_statuses: Dict[str, dict] = {}
ws_controller = None


class WebSocketController:
    """Manages WebSocket connection to the camera control server"""

    def __init__(
            self,
            server_host: str = "localhost",
            server_port: int = 9001):
        self.server_host = server_host
        self.server_port = server_port
        self.websocket = None
        self.connected = False
        self.loop = None

    async def connect_and_listen(self):
        """Connect to WebSocket server and listen for messages"""
        uri = f"ws://{self.server_host}:{self.server_port}"
        logger.info(f"🔌 Connecting to WebSocket server at {uri}...")

        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.connected = True
                logger.info("✅ Connected to WebSocket server")

                # Listen for messages from server
                async for message_str in websocket:
                    message = json.loads(message_str)
                    await self.handle_server_message(message)

        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
            self.connected = False

    async def handle_server_message(self, message: dict):
        """Handle messages from the WebSocket server"""
        msg_type = message.get("type")

        if msg_type == "camera_online":
            camera_id = message.get("camera_id")
            logger.info(f"📱 Camera online: {camera_id}")
            if camera_id:
                camera_statuses[camera_id] = {
                    "state": "IDLE",
                    "battery": 0,
                    "network_type": "UNKNOWN",
                    "thermal": "OK",
                    "online": True,
                    "last_seen": datetime.now().isoformat()
                }
            # Notify web clients
            socketio.emit('camera_online', {"camera_id": camera_id})

        elif msg_type == "camera_offline":
            camera_id = message.get("camera_id")
            logger.info(f"📱 Camera offline: {camera_id}")
            # Remove camera from status dict to prevent phantom data
            if camera_id in camera_statuses:
                del camera_statuses[camera_id]
            socketio.emit('camera_offline', {"camera_id": camera_id})

        elif msg_type == "camera_list":
            cameras = message.get("cameras", [])
            logger.info(f"📋 Camera list: {len(cameras)} cameras")
            for camera_id in cameras:
                if camera_id not in camera_statuses:
                    camera_statuses[camera_id] = {
                        "state": "IDLE",
                        "battery": 0,
                        "network_type": "UNKNOWN",
                        "thermal": "OK",
                        "online": True,
                        "last_seen": datetime.now().isoformat()
                    }
            socketio.emit(
                'camera_list', {
                    "cameras": list(
                        camera_statuses.keys())})

        elif msg_type == "status":
            # Status update from camera
            camera_id = message.get("camera_id")
            data = message.get("data", {})

            if camera_id in camera_statuses:
                # Convert state to uppercase for UI compatibility
                state = data.get("state", "UNKNOWN").upper()

                camera_statuses[camera_id].update({
                    "state": state,
                    "battery": data.get("battery_level", 0),
                    "network_type": data.get("network_type", "UNKNOWN"),
                    "wifi_ssid": data.get("wifi_ssid", ""),
                    "wifi_status": data.get("wifi_status", "Disconnected"),
                    "lte_status": data.get("lte_status", "Disconnected"),
                    "thermal": data.get("thermal_state", "OK"),
                    "uptime_seconds": data.get("uptime_seconds", 0),
                    "is_streaming": data.get("is_streaming", False),
                    "is_paused": data.get("is_paused", False),
                    "is_studio_mode": data.get("is_studio_mode", False),
                    "bitrate_mbps": round(
                        data.get("actual_bitrate_mbps", 0.0), 1
                    ),
                    "online": True,
                    "last_seen": datetime.now().isoformat()
                })

                # Notify web clients
                socketio.emit('status_update', {
                    "camera_id": camera_id,
                    "status": camera_statuses[camera_id]
                })

    async def send_command(
            self,
            camera_id: str,
            command: str,
            params: dict | None = None):
        """Send command to camera via WebSocket server"""
        if not self.connected or not self.websocket:
            return {"status": "error", "message": "Not connected to server"}

        message = {
            "type": "command",
            "camera_id": camera_id,
            "command": command,
            "params": params or {},
            "timestamp": datetime.now().isoformat()
        }

        try:
            import json
            await self.websocket.send(json.dumps(message))
            logger.info(f"📤 Command sent: {command} to {camera_id}")

            # Note: Don't wait for response here - it will be handled
            # by connect_and_listen(). Responses will come through
            # handle_server_message()
            return {"status": "sent"}

        except Exception as e:
            logger.error(f"❌ Error sending command: {e}")
            return {"status": "error", "message": str(e)}


def run_websocket_client():
    """Run WebSocket client in background thread"""
    global ws_controller
    ws_controller = WebSocketController()

    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(ws_controller.connect_and_listen())
    except Exception as e:
        logger.error(f"❌ WebSocket client error: {e}")
    finally:
        loop.close()


# Flask Routes
@app.route('/')
def index():
    """Serve the control panel UI"""
    return render_template('control_panel.html')


@app.route('/api/cameras')
def get_cameras():
    """Get list of connected cameras and their statuses"""
    return jsonify({
        "cameras": list(camera_statuses.keys()),
        "statuses": camera_statuses,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/command', methods=['POST'])
def send_command():
    """Send command to camera"""
    data = request.json
    if not data:
        return jsonify({
            "status": "error",
            "message": "No data provided"
        }), 400

    camera_id = data.get('camera_id')
    command = data.get('command')
    params = data.get('params', {})

    if not camera_id or not command:
        return jsonify({
            "status": "error",
            "message": "Missing camera_id or command"
        }), 400

    # Send command via WebSocket (synchronously)
    if ws_controller and ws_controller.connected:
        # Run async command in the event loop
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            ws_controller.send_command(camera_id, command, params)
        )
        loop.close()
        return jsonify(result)
    else:
        return jsonify({
            "status": "error",
            "message": "Not connected to WebSocket server"
        }), 503


# SocketIO Events
@socketio.on('connect')
def handle_connect():
    """Client connected to SocketIO"""
    logger.info('🌐 Web client connected')
    emit('cameras', {
        "cameras": list(camera_statuses.keys()),
        "statuses": camera_statuses
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected from SocketIO"""
    logger.info('🌐 Web client disconnected')


@socketio.on('request_status')
def handle_status_request(data):
    """Client requesting status update"""
    camera_id = data.get('camera_id')
    if camera_id and camera_id in camera_statuses:
        emit('status_update', {
            "camera_id": camera_id,
            "status": camera_statuses[camera_id]
        })


if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("🎮 Miktos StreamLab - Desktop Control Panel")
    logger.info("=" * 70)

    # Start WebSocket client in background thread
    ws_thread = threading.Thread(target=run_websocket_client, daemon=True)
    ws_thread.start()

    # Give WebSocket client time to connect
    import time
    time.sleep(2)

    # Start Flask server on port 8080 to avoid macOS Control Center conflict
    logger.info("🌐 Starting web server on http://0.0.0.0:8080")
    logger.info("📱 Open http://localhost:8080 in your browser")
    logger.info("=" * 70)

    socketio.run(app, host='0.0.0.0', port=8080, debug=False)
