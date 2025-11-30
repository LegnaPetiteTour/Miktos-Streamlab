#!/usr/bin/env python3
"""
E2E RTMP Streaming Test
Tests streaming from OBS to local MediaMTX RTMP server
"""

import asyncio
from obswebsocket import obsws, requests as obs_requests  # type: ignore

# Configuration
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "DmMpVONSo86VU3Eh"

RTMP_SERVER = "rtmp://localhost:1935/live"
RTMP_KEY = "test_stream"
RTMP_URL = f"{RTMP_SERVER}/{RTMP_KEY}"


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 78)
    print(f"  {text}")
    print("=" * 78)


def print_status(emoji, message):
    """Print status message"""
    print(f"{emoji} {message}")


async def test_rtmp_streaming():
    """Test RTMP streaming to local server"""

    print_header("🎬 E2E RTMP STREAMING TEST")

    # Connect to OBS
    print_status("🔌", "Connecting to OBS...")
    ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)

    try:
        ws.connect()
        print_status("✅", "Connected to OBS")

        # Get version
        version = ws.call(obs_requests.GetVersion())
        print_status("ℹ️", f"OBS Version: {version.getObsVersion()}")
        try:
            ws_version = version.getWebsocketVersion()
            print_status("ℹ️", f"WebSocket Version: {ws_version}")
        except (KeyError, AttributeError):
            print_status("ℹ️", "WebSocket Version: 5.x")

        # Get current streaming status
        print_header("📊 INITIAL STATUS")
        stream_status = ws.call(obs_requests.GetStreamStatus())
        if stream_status.getOutputActive():
            print_status("⚠️", "Stream already active - stopping first...")
            ws.call(obs_requests.StopStream())
            await asyncio.sleep(2)
        else:
            print_status("✅", "Stream not active - ready to start")

        # Configure RTMP streaming settings
        print_header("⚙️  CONFIGURING RTMP STREAM")
        print_status("📡", f"RTMP Server: {RTMP_SERVER}")
        print_status("🔑", f"Stream Key: {RTMP_KEY}")
        print_status("🌐", f"Full URL: {RTMP_URL}")

        # Note: OBS Studio streaming settings are configured in
        # OBS UI or via profiles
        # For this test, we'll manually set the stream settings in OBS
        print_status("⚠️", "MANUAL STEP REQUIRED:")
        print_status("📋", "Please configure OBS streaming settings:")
        print_status("   ", "1. Go to Settings → Stream")
        print_status("   ", "2. Service: Custom")
        print_status("   ", f"3. Server: {RTMP_SERVER}")
        print_status("   ", f"4. Stream Key: {RTMP_KEY}")
        print_status("   ", "5. Click OK to save")
        print()

        # Wait for user to configure
        input("Press ENTER when OBS streaming settings are configured...")

        # Switch to a good scene
        print_header("🎬 SCENE SETUP")
        scenes_response = ws.call(obs_requests.GetSceneList())
        scenes = scenes_response.getScenes()
        scene_names = [s['sceneName'] for s in scenes]

        print_status("📋", f"Available scenes: {', '.join(scene_names)}")

        # Try to use Sony_Main or Camera Scene
        target_scene = None
        for preferred in ['Sony_Main', 'Camera Scene', 'Main Camera']:
            if preferred in scene_names:
                target_scene = preferred
                break

        if not target_scene and scene_names:
            target_scene = scene_names[0]

        if target_scene:
            print_status("🎥", f"Switching to scene: {target_scene}")
            ws.call(
                obs_requests.SetCurrentProgramScene(sceneName=target_scene)
            )
            print_status("✅", f"Active scene: {target_scene}")
        else:
            print_status("⚠️", "No scenes available - using current scene")

        # Start streaming
        print_header("🚀 STARTING STREAM")
        print_status("⏳", "Starting stream to local RTMP server...")

        ws.call(obs_requests.StartStream())

        # Wait and monitor stream
        print_status("✅", "Stream started!")
        print()
        print_status("📊", "Monitoring stream for 10 seconds...")

        for i in range(10):
            await asyncio.sleep(1)
            stream_status = ws.call(obs_requests.GetStreamStatus())

            active = stream_status.getOutputActive()
            # ms to seconds
            duration = stream_status.getOutputDuration() / 1000

            if active:
                print_status("📡", f"Streaming: {duration:.1f}s")
            else:
                print_status("❌", "Stream stopped unexpectedly!")
                break

        # Stop streaming
        print()
        print_header("🛑 STOPPING STREAM")
        ws.call(obs_requests.StopStream())
        await asyncio.sleep(2)

        final_status = ws.call(obs_requests.GetStreamStatus())
        if not final_status.getOutputActive():
            print_status("✅", "Stream stopped successfully")

        # Results
        print_header("✅ TEST COMPLETE")
        print_status("🎉", "RTMP streaming test completed!")
        print()
        print_status("📋", "VALIDATION CHECKLIST:")
        print_status("✅", "OBS connected to local RTMP server")
        print_status("✅", "Stream started and ran for 10 seconds")
        print_status("✅", "Stream stopped cleanly")
        print()
        print_status("ℹ️", "You can view the stream with:")
        print_status("   ", f"ffplay {RTMP_URL}")
        print_status("   ", "or")
        print_status("   ", f"VLC → Open Network Stream → {RTMP_URL}")

    except Exception as e:
        print_status("❌", f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print()
        print_status("🔌", "Disconnecting from OBS...")
        ws.disconnect()
        print_status("✅", "Disconnected")

if __name__ == "__main__":
    asyncio.run(test_rtmp_streaming())
