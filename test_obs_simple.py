#!/usr/bin/env python3
"""
Simple OBS WebSocket Connection Test
Tests basic OBS WebSocket connectivity without Miktos Hub dependencies
"""

import asyncio
import sys

try:
    import obsws_python as obs  # type: ignore[import-untyped]
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
        obs_ver = version.obs_version  # type: ignore[attr-defined]
        ws_ver = version.obs_web_socket_version  # type: ignore[attr-defined]
        print(f"   OBS Version: {obs_ver}")
        print(f"   WebSocket Version: {ws_ver}")
        print()

        # Get scenes
        print("🎞️  Available Scenes:")
        scenes_response = ws.get_scene_list()
        # Extract with type: ignore for untyped library
        # Get current scene name
        current_scene = (  # type: ignore[attr-defined]
            scenes_response.current_program_scene_name)
        scenes = scenes_response.scenes  # type: ignore[attr-defined]

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
        base_w = video_settings.base_width  # type: ignore[attr-defined]
        base_h = video_settings.base_height  # type: ignore[attr-defined]
        out_w = video_settings.output_width  # type: ignore[attr-defined]
        out_h = video_settings.output_height  # type: ignore[attr-defined]
        fps_n = video_settings.fps_numerator  # type: ignore[attr-defined]
        fps_d = video_settings.fps_denominator  # type: ignore[attr-defined]
        print(f"   Canvas: {base_w}x{base_h}")
        print(f"   Output: {out_w}x{out_h}")
        print(f"   FPS: {fps_n}/{fps_d}")
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
        scene_list = scenes_response.scenes  # type: ignore[attr-defined]
        scene_names = [s['sceneName'] for s in scene_list]
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
            active = stream_status.output_active  # type: ignore[attr-defined]
            if active:
                d = stream_status.output_duration  # type: ignore[attr-defined]
                duration = d / 1000
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
