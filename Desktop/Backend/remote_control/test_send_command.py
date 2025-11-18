#!/usr/bin/env python3
"""
Quick test to send a command directly to a camera
"""
import asyncio
import websockets
import json


async def send_test_command():
    # Connect as a controller
    async with websockets.connect('ws://localhost:9001') as websocket:
        print("✅ Connected as controller")

        # Wait a moment
        await asyncio.sleep(1)

        # Send a START command
        command = {
            "type": "command",
            "camera_id": "bcfe653d16549338",
            "command": "START",
            "params": {},
            "timestamp": "2025-11-17T00:00:00"
        }

        print(f"📤 Sending command: {command}")
        await websocket.send(json.dumps(command))

        # Wait for response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"📬 Response: {response}")
        except asyncio.TimeoutError:
            print("⏱️  No response received (timeout)")

        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(send_test_command())
