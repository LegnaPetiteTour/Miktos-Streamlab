#!/usr/bin/env python3
"""Quick test script for remote control commands"""

import asyncio
import websockets
import json
import sys


async def send_command(command: str, camera_id: str = None):
    """Send a command to a camera via WebSocket"""
    uri = "ws://localhost:9001"  # Controller port
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to WebSocket server")
            
            # Wait for camera list
            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            camera_list = json.loads(response)
            print(f"📱 Available cameras: {camera_list}")
            
            # Get first camera if not specified
            if camera_id is None:
                cameras = camera_list.get("cameras", [])
                if not cameras:
                    print("❌ No cameras connected!")
                    return
                camera_id = cameras[0]
                print(f"📍 Using camera: {camera_id}")
            
            # Send command
            message = {
                "type": "command",
                "camera_id": camera_id,
                "command": command,
                "params": {}
            }
            
            await websocket.send(json.dumps(message))
            print(f"✅ Sent {command} command to {camera_id}")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            result = json.loads(response)
            print(f"📥 Response: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "PAUSE"
    camera_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🎮 Sending {command}...")
    asyncio.run(send_command(command, camera_id))
