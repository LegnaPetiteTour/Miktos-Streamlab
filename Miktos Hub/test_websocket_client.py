#!/usr/bin/env python3
"""
Simple WebSocket client to test real-time event streaming
"""
import asyncio
import json
import websockets
import sys


async def test_websocket():
    """Connect to WebSocket and listen for events"""
    uri = "ws://localhost:8000/ws"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected!")

            # Receive welcome message
            welcome = await websocket.recv()
            print("\n📨 Welcome message:")
            print(json.dumps(json.loads(welcome), indent=2))

            # Subscribe to all events
            subscribe_msg = {
                "type": "subscribe",
                "event_types": ["*"]  # Subscribe to all events
            }
            await websocket.send(json.dumps(subscribe_msg))
            print(f"\n📤 Sent: {json.dumps(subscribe_msg, indent=2)}")

            # Receive subscription confirmation
            response = await websocket.recv()
            print("\n📨 Response:")
            print(json.dumps(json.loads(response), indent=2))

            # Listen for events
            print("\n👂 Listening for events... (Press Ctrl+C to stop)")
            print("=" * 60)

            while True:
                message = await websocket.recv()
                data = json.loads(message)

                print(f"\n🔔 Event received: {data.get('type', 'unknown')}")
                print(json.dumps(data, indent=2))
                print("-" * 60)

    except websockets.exceptions.ConnectionClosed:
        print("\n❌ Connection closed")
    except KeyboardInterrupt:
        print("\n\n👋 Disconnected")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_websocket())
    sys.exit(exit_code)
