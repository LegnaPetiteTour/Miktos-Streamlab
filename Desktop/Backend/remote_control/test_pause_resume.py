#!/usr/bin/env python3
"""
Test PAUSE and RESUME commands for multi-camera switching

This demonstrates the instant camera switching workflow:
1. START all 3 cameras
2. PAUSE Camera 2 and 3 (freeze frames)
3. Switch active camera by PAUSE/RESUME
4. Zero startup latency - sessions stay alive
"""

import asyncio
import websockets
import json
from typing import Optional


async def send_command(
    camera_id: str, command: str, params: Optional[dict] = None
):
    """Send a command to a specific camera via WebSocket controller port"""
    uri = "ws://192.168.2.36:9001"  # Controller port

    message = {
        "type": "command",
        "camera_id": camera_id,
        "command": command,
        "params": params or {}
    }

    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(message))
            print(f"✅ Sent {command} to {camera_id}")

            # Wait for acknowledgment
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            # Decode bytes to string if needed
            if isinstance(response, bytes):
                response = response.decode('utf-8')
            print(f"   Response: {response}")

    except asyncio.TimeoutError:
        print("⚠️  No response (command sent)")
    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_multi_camera_switching():
    """
    Demonstrate multi-camera switching workflow

    Simulates 3-camera setup where you switch between cameras instantly
    """

    print("\n" + "="*60)
    print("MULTI-CAMERA SWITCHING DEMO")
    print("="*60)

    # Camera IDs (replace with your actual camera IDs)
    camera1 = "bcfe653d16549338"  # Samsung S23 FE
    # camera2 = "camera_2_id"  # Replace with actual ID (multi-camera)
    # camera3 = "camera_3_id"  # Replace with actual ID (multi-camera)

    # For this demo, we'll just use camera1
    print("\n📱 Step 1: Start all cameras")
    await send_command(camera1, "START", {
        "server_ip": "192.168.2.36",
        "server_port": 8554
    })
    await asyncio.sleep(2)

    print("\n⏸️  Step 2: Pause Camera 1 (freeze frame mode)")
    await send_command(camera1, "PAUSE")
    await asyncio.sleep(2)

    print("\n▶️  Step 3: Resume Camera 1 (back to full speed)")
    await send_command(camera1, "RESUME")
    await asyncio.sleep(2)

    print("\n⏸️  Step 4: Pause again")
    await send_command(camera1, "PAUSE")
    await asyncio.sleep(2)

    print("\n⏹️  Step 5: Stop streaming")
    await send_command(camera1, "STOP")

    print("\n✅ Demo complete!")
    print("\nKey benefits:")
    print("  • Zero startup latency when switching cameras")
    print("  • Session stays alive during pause")
    print("  • 1 fps freeze frame = minimal bandwidth")
    print("  • Instant resume (no encoder restart)")


async def interactive_mode():
    """Interactive command-line interface"""
    print("\n" + "="*60)
    print("PAUSE/RESUME + STUDIO MODE INTERACTIVE TEST")
    print("="*60)
    print("\nCommands:")
    print("  1. START         - Start streaming")
    print("  2. PAUSE         - Pause (freeze frame mode)")
    print("  3. RESUME        - Resume (full speed)")
    print("  4. ENTER_STUDIO  - Enter Studio Mode")
    print("  5. EXIT_STUDIO   - Exit Studio Mode")
    print("  6. STATUS        - Get status")
    print("  7. STOP          - Stop streaming")
    print("  q. Quit")

    camera_id = "bcfe653d16549338"  # Samsung S23 FE

    while True:
        print("\n" + "-"*60)
        choice = input("Enter command (1-7, q): ").strip()

        if choice == "q":
            break
        elif choice == "1":
            await send_command(camera_id, "START", {
                "server_ip": "192.168.2.36",
                "server_port": 8554
            })
        elif choice == "2":
            await send_command(camera_id, "PAUSE")
        elif choice == "3":
            await send_command(camera_id, "RESUME")
        elif choice == "4":
            await send_command(camera_id, "ENTER_STUDIO_MODE")
        elif choice == "5":
            await send_command(camera_id, "EXIT_STUDIO_MODE")
        elif choice == "6":
            await send_command(camera_id, "STATUS")
        elif choice == "7":
            await send_command(camera_id, "STOP")
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo_multi_camera_switching())
    else:
        asyncio.run(interactive_mode())
