#!/usr/bin/env python3
"""
Camera State Diagnostic Tool
Monitors camera state changes and identifies patterns
"""

import asyncio
import json
import websockets
from datetime import datetime
from collections import defaultdict

# Track state transitions
state_history = []
state_durations = defaultdict(list)
last_state = None
last_state_time = None

async def monitor_camera():
    """Connect to WebSocket server and monitor camera states"""
    uri = "ws://localhost:9001"
    
    print("=" * 70)
    print("CAMERA STATE DIAGNOSTIC TEST")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    print("Connecting to WebSocket server...")
    print()
    
    global last_state, last_state_time
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to control server")
            print("📊 Monitoring camera state changes for 30 seconds...")
            print()
            print(f"{'Time':<12} {'State':<12} {'Duration':<15} {'Details'}")
            print("-" * 70)
            
            # Set timeout for 30 seconds
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < 30:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'status':
                        status = data.get('data', {})
                        state = status.get('state', 'UNKNOWN')
                        camera_id = data.get('camera_id', 'unknown')
                        now = datetime.now()
                        
                        # Calculate duration if we have a previous state
                        duration_ms = ""
                        if last_state and last_state_time:
                            duration = (now - last_state_time).total_seconds() * 1000
                            duration_ms = f"{duration:.0f}ms"
                            state_durations[last_state].append(duration)
                        
                        # Only print if state changed
                        if state != last_state:
                            # Get additional details
                            is_streaming = status.get('is_streaming', False)
                            is_paused = status.get('is_paused', False)
                            details = []
                            if is_streaming:
                                details.append("streaming")
                            if is_paused:
                                details.append("paused")
                            details_str = ", ".join(details) if details else "-"
                            
                            print(f"{now.strftime('%H:%M:%S.%f')[:-3]:<12} {state:<12} {duration_ms:<15} {details_str}")
                            
                            state_history.append({
                                'time': now,
                                'state': state,
                                'duration_ms': duration_ms,
                                'camera_id': camera_id
                            })
                            
                            last_state = state
                            last_state_time = now
                        
                except asyncio.TimeoutError:
                    continue
                except json.JSONDecodeError:
                    continue
            
            print()
            print("=" * 70)
            print("DIAGNOSTIC RESULTS")
            print("=" * 70)
            print()
            
            # Analyze state durations
            if state_durations:
                print("State Duration Analysis:")
                print("-" * 70)
                for state, durations in state_durations.items():
                    if durations:
                        avg_duration = sum(durations) / len(durations)
                        min_duration = min(durations)
                        max_duration = max(durations)
                        count = len(durations)
                        print(f"{state}:")
                        print(f"  Count: {count}")
                        print(f"  Average: {avg_duration:.0f}ms")
                        print(f"  Min: {min_duration:.0f}ms")
                        print(f"  Max: {max_duration:.0f}ms")
                        print()
            
            # Identify patterns
            print("Pattern Analysis:")
            print("-" * 70)
            if len(state_history) >= 3:
                # Check for cycling pattern
                states_only = [s['state'] for s in state_history[-10:]]
                if len(set(states_only)) == 2 and len(states_only) >= 4:
                    print("⚠️  DETECTED: Rapid state cycling between 2 states")
                    print(f"   States: {' → '.join(states_only[-6:])}")
                    print()
                    print("💡 DIAGNOSIS:")
                    print("   The phone is rapidly switching between states.")
                    print("   This suggests the app is trying to stream but failing.")
                    print("   Possible causes:")
                    print("   1. No SRT receiver is accepting the stream")
                    print("   2. Network connectivity issues")
                    print("   3. Streaming configuration mismatch")
                    print()
                    print("🔧 SOLUTION:")
                    print("   Start the SRT receiver to accept the phone's stream:")
                    print("   cd Desktop/Backend/mobile &&  \\")
                    print("   /path/to/venv/bin/python srt_receiver.py --port 8554")
                else:
                    print("✅ No obvious cycling pattern detected")
            else:
                print("⚠️  Not enough data to analyze patterns")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(monitor_camera())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
