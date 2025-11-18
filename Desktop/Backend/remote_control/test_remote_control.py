#!/usr/bin/env python3
"""
Test client for Remote Control Commands
Connects to the controller port and sends commands to cameras
"""

import asyncio
import websockets
import json
from datetime import datetime

class RemoteControlTester:
    def __init__(self, server_host="localhost", controller_port=9001):
        self.server_url = f"ws://{server_host}:{controller_port}"
        self.websocket = None
        
    async def connect(self):
        """Connect to the controller server"""
        print(f"🔌 Connecting to {self.server_url}...")
        self.websocket = await websockets.connect(self.server_url)
        print("✅ Connected to remote control server")
        
    async def receive_messages(self):
        """Listen for incoming messages"""
        try:
            async for message_str in self.websocket:
                message = json.loads(message_str)
                msg_type = message.get("type")
                
                if msg_type == "camera_list":
                    cameras = message.get("cameras", [])
                    print(f"\n📱 Available cameras: {cameras if cameras else 'None'}")
                    
                elif msg_type == "camera_online":
                    camera_id = message.get("camera_id")
                    print(f"\n✅ Camera online: {camera_id}")
                    
                elif msg_type == "camera_offline":
                    camera_id = message.get("camera_id")
                    print(f"\n❌ Camera offline: {camera_id}")
                    
                elif msg_type == "status":
                    camera_id = message.get("camera_id")
                    status = message.get("status")
                    print(f"\n📊 Status from {camera_id}: {status}")
                    
                elif msg_type == "command_result":
                    camera_id = message.get("camera_id")
                    command = message.get("command")
                    result = message.get("result")
                    print(f"\n📬 Command '{command}' result for {camera_id}: {result}")
                    
                else:
                    print(f"\n📨 Received: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("\n❌ Connection closed")
    
    async def send_command(self, camera_id: str, command: str, params: dict = None):
        """Send a command to a camera"""
        message = {
            "type": "command",
            "camera_id": camera_id,
            "command": command,
            "params": params or {},
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n📤 Sending command to {camera_id}: {command}")
        if params:
            print(f"   Parameters: {params}")
            
        await self.websocket.send(json.dumps(message))
    
    async def interactive_mode(self):
        """Interactive command mode"""
        print("\n" + "="*60)
        print("📱 REMOTE CONTROL TEST CLIENT")
        print("="*60)
        print("\nAvailable Commands:")
        print("  1. START           - Start streaming")
        print("  2. STOP            - Stop streaming")
        print("  3. ENTER_STUDIO    - Enter Studio Mode")
        print("  4. EXIT_STUDIO     - Exit Studio Mode")
        print("  5. STATUS          - Request status update")
        print("  6. QUIT            - Exit test client")
        print("="*60)
        
        # Start listening for messages in background
        asyncio.create_task(self.receive_messages())
        
        # Wait a bit for camera list
        await asyncio.sleep(1)
        
        while True:
            print("\n" + "-"*60)
            camera_id = input("Enter camera ID (or 'quit'): ").strip()
            
            if camera_id.lower() == 'quit':
                break
                
            if not camera_id:
                print("❌ Camera ID required")
                continue
            
            print("\nSelect command:")
            print("  1 - START")
            print("  2 - STOP")
            print("  3 - ENTER_STUDIO")
            print("  4 - EXIT_STUDIO")
            print("  5 - STATUS")
            
            choice = input("Choice (1-5): ").strip()
            
            command_map = {
                "1": "START",
                "2": "STOP",
                "3": "ENTER_STUDIO_MODE",
                "4": "EXIT_STUDIO_MODE",
                "5": "STATUS"
            }
            
            command = command_map.get(choice)
            if command:
                await self.send_command(camera_id, command)
                await asyncio.sleep(0.5)  # Wait for response
            else:
                print("❌ Invalid choice")
    
    async def run_automated_test(self, camera_id: str):
        """Run automated test sequence"""
        print("\n" + "="*60)
        print("🧪 AUTOMATED REMOTE CONTROL TEST")
        print("="*60)
        
        # Start listening for messages
        asyncio.create_task(self.receive_messages())
        
        # Wait for camera list
        print("\n⏳ Waiting for camera to connect...")
        await asyncio.sleep(2)
        
        tests = [
            ("STATUS", None, "Request initial status"),
            ("START", None, "Start streaming"),
            ("ENTER_STUDIO_MODE", None, "Enter Studio Mode"),
            ("STATUS", None, "Check status in Studio Mode"),
            ("EXIT_STUDIO_MODE", None, "Exit Studio Mode"),
            ("STATUS", None, "Check status after exit"),
            ("STOP", None, "Stop streaming"),
        ]
        
        for i, (command, params, description) in enumerate(tests, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}/{len(tests)}: {description}")
            print(f"{'='*60}")
            
            await self.send_command(camera_id, command, params)
            
            # Wait for response
            await asyncio.sleep(2)
            
            if i < len(tests):
                input("\nPress Enter to continue to next test...")
        
        print("\n" + "="*60)
        print("✅ AUTOMATED TEST COMPLETE")
        print("="*60)
    
    async def close(self):
        """Close connection"""
        if self.websocket:
            await self.websocket.close()
            print("\n👋 Disconnected")

async def main():
    import sys
    
    tester = RemoteControlTester()
    
    try:
        await tester.connect()
        
        if len(sys.argv) > 1 and sys.argv[1] == "auto":
            # Automated test mode
            camera_id = sys.argv[2] if len(sys.argv) > 2 else "camera_001"
            await tester.run_automated_test(camera_id)
        else:
            # Interactive mode
            await tester.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await tester.close()

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║        Miktos StreamLab - Remote Control Test Client         ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
  Interactive mode:  python3 test_remote_control.py
  Automated test:    python3 test_remote_control.py auto [camera_id]

Make sure the WebSocket server is running first!
""")
    
    asyncio.run(main())
