#!/usr/bin/env python3
"""
Miktos StreamLab - Remote Control WebSocket Server
Handles bidirectional communication between desktop and camera phones
"""

import asyncio
import websockets
from websockets.legacy.server import WebSocketServerProtocol
import json
import logging
from typing import Dict, Set
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to see status messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CameraControlServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000):
        self.host = host
        self.port = port
        self.cameras: Dict[str, WebSocketServerProtocol] = {}
        self.controllers: Set[WebSocketServerProtocol] = set()

    async def register_camera(self, websocket, camera_id: str):
        """Register a camera connection"""
        self.cameras[camera_id] = websocket
        logger.info(f"📱 Camera registered: {camera_id}")

        # Notify all controllers
        await self.broadcast_to_controllers({
            "type": "camera_online",
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat()
        })

    async def unregister_camera(self, camera_id: str):
        """Unregister a camera connection"""
        if camera_id in self.cameras:
            del self.cameras[camera_id]
            logger.info(f"📱 Camera unregistered: {camera_id}")

            # Notify all controllers
            await self.broadcast_to_controllers({
                "type": "camera_offline",
                "camera_id": camera_id,
                "timestamp": datetime.now().isoformat()
            })

    async def register_controller(self, websocket):
        """Register a controller (desktop UI) connection"""
        self.controllers.add(websocket)
        total_controllers = len(self.controllers)
        logger.info(
            f"🖥️  Controller registered (total: {total_controllers})"
        )

        # Send current camera list
        await websocket.send(json.dumps({
            "type": "camera_list",
            "cameras": list(self.cameras.keys()),
            "timestamp": datetime.now().isoformat()
        }))

    async def unregister_controller(self, websocket):
        """Unregister a controller connection"""
        self.controllers.discard(websocket)
        remaining = len(self.controllers)
        logger.info(
            f"🖥️  Controller unregistered (remaining: {remaining})"
        )

    async def broadcast_to_controllers(self, message: dict):
        """Send message to all connected controllers"""
        if self.controllers:
            message_str = json.dumps(message)
            sends = [
                controller.send(message_str)
                for controller in self.controllers
            ]
            await asyncio.gather(*sends, return_exceptions=True)

    async def send_command_to_camera(self, camera_id: str, command: dict):
        """Send command to specific camera"""
        if camera_id in self.cameras:
            camera_ws = self.cameras[camera_id]
            try:
                await camera_ws.send(json.dumps(command))
                cmd = command['command']
                logger.info(f"📤 Command sent to {camera_id}: {cmd}")
                return {"status": "success"}
            except Exception as e:
                logger.error(f"❌ Failed to send command to {camera_id}: {e}")
                return {"status": "error", "message": str(e)}
        else:
            logger.warning(f"⚠️  Camera {camera_id} not connected")
            return {"status": "error", "message": "Camera not connected"}

    async def handle_camera(self, websocket, path):
        """Handle camera connections (port 9000)"""
        camera_id = None
        try:
            # First message should be registration
            registration = json.loads(await websocket.recv())

            if registration.get("type") == "register":
                camera_id = registration.get("camera_id")
                await self.register_camera(websocket, camera_id)

                # Send acknowledgment
                await websocket.send(json.dumps({
                    "type": "registered",
                    "camera_id": camera_id,
                    "timestamp": datetime.now().isoformat()
                }))

                # Handle incoming messages
                async for message_str in websocket:
                    message = json.loads(message_str)

                    if message.get("type") == "status":
                        # Forward status to all controllers
                        message["camera_id"] = camera_id
                        data = message.get('data', {})
                        ssid = data.get('wifi_ssid', 'N/A')
                        net_type = data.get('network_type', 'N/A')
                        logger.info(
                            f"📊 Status from {camera_id}: "
                            f"wifi_ssid={ssid}, network_type={net_type}"
                        )
                        await self.broadcast_to_controllers(message)

                    msg_type = message.get('type')
                    logger.debug(
                        f"📱 Message from {camera_id}: {msg_type}"
                    )

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"📱 Camera {camera_id} disconnected")
        except Exception as e:
            logger.error(f"❌ Error handling camera {camera_id}: {e}")
        finally:
            if camera_id:
                await self.unregister_camera(camera_id)

    async def handle_controller(self, websocket, path):
        """Handle controller (desktop UI) connections (port 9001)"""
        try:
            await self.register_controller(websocket)

            # Handle incoming commands
            async for message_str in websocket:
                message = json.loads(message_str)
                logger.info(f"🔍 Controller message: {message}")

                if message.get("type") == "command":
                    camera_id = message.get("camera_id")
                    command = message.get("command")
                    params = message.get("params", {})

                    logger.info(
                        f"🔍 Parsed command - camera_id: '{camera_id}', "
                        f"command: '{command}'"
                    )
                    cameras_list = list(self.cameras.keys())
                    logger.info(f"🔍 Registered cameras: {cameras_list}")

                    result = await self.send_command_to_camera(
                        camera_id,
                        {
                            "type": "command",
                            "command": command,
                            "params": params,
                            "timestamp": datetime.now().isoformat()
                        }
                    )

                    # Send result back to controller
                    await websocket.send(json.dumps({
                        "type": "command_result",
                        "camera_id": camera_id,
                        "command": command,
                        "result": result
                    }))

        except websockets.exceptions.ConnectionClosed:
            logger.info("🖥️  Controller disconnected")
        except Exception as e:
            logger.error(f"❌ Error handling controller: {e}")
        finally:
            await self.unregister_controller(websocket)

    async def handle_camera_wrapper(self, websocket):
        """Wrapper for camera handler (websockets v12+ compatibility)"""
        path = (
            websocket.request.path
            if hasattr(websocket, 'request')
            else '/'
        )
        await self.handle_camera(websocket, path)

    async def handle_controller_wrapper(self, websocket):
        """Wrapper for controller handler (websockets v12+ compatibility)"""
        path = (
            websocket.request.path
            if hasattr(websocket, 'request')
            else '/'
        )
        await self.handle_controller(websocket, path)

    async def start_camera_server(self):
        """Start server for camera connections"""
        handler = self.handle_camera_wrapper
        async with websockets.serve(handler, self.host, self.port):
            logger.info(
                f"🎥 Camera server started on "
                f"ws://{self.host}:{self.port}"
            )
            await asyncio.Future()  # run forever

    async def start_controller_server(self):
        """Start server for controller connections"""
        handler = self.handle_controller_wrapper
        controller_port = self.port + 1
        async with websockets.serve(handler, self.host, controller_port):
            logger.info(
                f"🖥️  Controller server started on "
                f"ws://{self.host}:{controller_port}"
            )
            await asyncio.Future()  # run forever

    async def start(self):
        """Start both servers"""
        logger.info("="*60)
        logger.info("🚀 Miktos StreamLab Remote Control Server")
        logger.info("="*60)
        await asyncio.gather(
            self.start_camera_server(),
            self.start_controller_server()
        )


if __name__ == "__main__":
    server = CameraControlServer(host="0.0.0.0", port=9000)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("\n👋 Server shutting down...")
