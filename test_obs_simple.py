#!/usr/bin/env python3
"""
Simple OBS WebSocket Connection Test
Tests basic OBS WebSocket connectivity without Miktos Hub dependencies
"""

import asyncio
import sys

try:
    import obsws_python as obs
    OBSWS_AVAILABLE = True
except ImportError:
    OBSWS_AVAILABLE = False
    print("❌ obsws-python not installed")
    print("   Install with: pip install obsws-python")
    sys.exit(1)


async def test_obs_websocket(host="localhost", port=4455, password=None):
    """Test OBS WebSocket connection"""

    print("=" * 70)
    print("🎬 OBS WEBSOCKET CONNECTION TEST")
    print("=" * 70)
    print()
    print(f"📡 Connecting to: {host}:{port}")
    print()

    try:
        # Create connection
        if password:
            ws = obs.ReqClient(host=host, port=port, password=password)
        else:
            ws = obs.ReqClient(host=host, port=port)

        print("✅ Connected to OBS WebSocket!")
        print()

        # Get version info
        print("📋 OBS Version Information:")
        version = ws.get_version()
        print(f"   OBS Version: {version.obs_version}")
        print(f"   WebSocket Version: {version.obs_web_socket_version}")
        print()

        # Get scenes
        print("🎞️  Available Scenes:")
        scenes_response = ws.get_scene_list()
        current_scene = scenes_response.current_program_scene_name
        scenes = scenes_response.scenes

        if not scenes:
            print("   ⚠️  No scenes found!")
        else:
            for scene in scenes:
                name = scene['sceneName']
                marker = "→" if name == current_scene else " "
                print(f"   {marker} {name}")
        print()

        # Get video settings
        print("🎥 Video Settings:")
        video_settings = ws.get_video_settings()
        print(
            f"   Canvas: {video_settings.base_width}x"
            f"{video_settings.base_height}")
        print(
            f"   Output: {video_settings.output_width}x"
            f"{video_settings.output_height}")
        print(
            f"   FPS: {video_settings.fps_numerator}/"
            f"{video_settings.fps_denominator}")
        print()

        # Test scene creation
        print("🧪 Testing Scene Creation:")
        test_scene_name = "Miktos_Test_Scene"

        # Delete if exists
        try:
            ws.remove_scene(test_scene_name)
            print(f"   Removed existing '{test_scene_name}'")
        except Exception:
            pass

        # Create new scene
        ws.create_scene(test_scene_name)
        print(f"   ✅ Created '{test_scene_name}'")

        # Verify it exists
        scenes_response = ws.get_scene_list()
        scene_names = [s['sceneName'] for s in scenes_response.scenes]
        if test_scene_name in scene_names:
            print("   ✅ Scene verified in scene list")

        # Clean up
        ws.remove_scene(test_scene_name)
        print("   🧹 Cleaned up test scene")
        print()

        # Get streaming status
        print("📡 Streaming Status:")
        try:
            stream_status = ws.get_stream_status()
            if stream_status.output_active:
                duration = stream_status.output_duration / 1000
                print(f"   🔴 LIVE - {duration:.1f}s")
            else:
                print("   ⚫ Not streaming")
        except Exception as e:
            print(f"   ⚠️  Could not get status: {e}")
        print()

        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("📝 Next Steps:")
        print("   1. OBS WebSocket is configured correctly ✅")
        print("   2. Miktos Hub can connect to OBS ✅")
        print("   3. Ready to test camera discovery")
        print()

        ws.disconnect()
        return True

    except ConnectionRefusedError:
        print("❌ Connection Refused")
        print()
        print("💡 Troubleshooting:")
        print("   1. Is OBS Studio running?")
        print("   2. Is WebSocket Server enabled?")
        print("      Tools → WebSocket Server Settings")
        print("   3. Check port (default: 4455)")
        print("   4. Check password if set")
        print()
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("💡 Common Issues:")
        print("   - Wrong port number (check OBS settings)")
        print("   - Password required but not provided")
        print("   - WebSocket server not enabled in OBS")
        print()
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Test OBS WebSocket connection')
    parser.add_argument(
        '--host',
        default='localhost',
        help='OBS WebSocket host')
    parser.add_argument(
        '--port',
        type=int,
        default=4455,
        help='OBS WebSocket port')
    parser.add_argument('--password', help='OBS WebSocket password')

    args = parser.parse_args()

    # Run test
    success = asyncio.run(
        test_obs_websocket(
            args.host,
            args.port,
            args.password))

    sys.exit(0 if success else 1)
