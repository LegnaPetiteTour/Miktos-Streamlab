#!/usr/bin/env python3
"""
Miktos StreamLab - Remote Control CLI
Control your camera phones from the command line
"""

import asyncio
import websockets
import json
import sys


async def send_command(command: str, camera_id: str | None = None):
    """Send a command to a camera via WebSocket"""
    uri = "ws://localhost:9001"  # Controller port
    
    try:
        async with websockets.connect(uri) as websocket:
            # Wait for camera list
            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            camera_list = json.loads(response)
            cameras = camera_list.get("cameras", [])
            
            if not cameras:
                print("❌ No cameras connected!")
                print("💡 Make sure:")
                print("   1. Camera app is running")
                print("   2. Remote control is enabled in settings")
                print("   3. WebSocket server is running")
                return False
            
            # Get first camera if not specified
            if camera_id is None:
                camera_id = cameras[0]
            
            # Send command
            message = {
                "type": "command",
                "camera_id": camera_id,
                "command": command,
                "params": {}
            }
            
            await websocket.send(json.dumps(message))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            result = json.loads(response)
            
            if result.get("result", {}).get("status") == "success":
                return True
            else:
                print(f"❌ Command failed: {result}")
                return False
            
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for server response")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_usage():
    """Print usage information"""
    print("""
🎮 Miktos StreamLab Remote Control CLI

Usage:
    ./remote_control.py <command> [camera_id]

Commands:
    START              Start streaming
    STOP               Stop streaming
    PAUSE              Pause stream (freeze frame at 1 fps)
    RESUME             Resume normal streaming
    ENTER_STUDIO_MODE  Enter low-power Studio Mode

Examples:
    ./remote_control.py PAUSE
    ./remote_control.py RESUME
    ./remote_control.py ENTER_STUDIO_MODE
    ./remote_control.py STOP bcfe653d16549338

Camera ID:
    If not specified, uses the first available camera
    """)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print_usage()
        sys.exit(0)
    
    command = sys.argv[1].upper()
    camera_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    valid_commands = ["START", "STOP", "PAUSE", "RESUME", "ENTER_STUDIO_MODE"]
    if command not in valid_commands:
        print(f"❌ Invalid command: {command}")
        print(f"✅ Valid commands: {', '.join(valid_commands)}")
        sys.exit(1)
    
    # Run command
    print(f"📡 Sending {command} command...")
    success = asyncio.run(send_command(command, camera_id))
    
    if success:
        icon = {
            "START": "🎬",
            "STOP": "⏹️",
            "PAUSE": "⏸️",
            "RESUME": "▶️",
            "ENTER_STUDIO_MODE": "🌙"
        }.get(command, "✅")
        print(f"{icon} {command} command sent successfully!")
        sys.exit(0)
    else:
        sys.exit(1)
