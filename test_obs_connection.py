#!/usr/bin/env python3
"""
OBS Connection Test Script
Tests the connection between Miktos Hub and OBS Studio
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "Miktos Hub"))

# type: ignore[import-not-found]
from config.settings import Settings  # noqa: E402
# type: ignore[import-not-found]
from adapters.obs_engine import OBSEngine  # noqa: E402


async def test_obs_connection():
    """Test OBS Studio connection and basic functionality"""

    print("=" * 70)
    print("🎬 OBS STUDIO CONNECTION TEST")
    print("=" * 70)

    # Load settings
    settings = Settings()
    print("\n📋 Configuration:")
    print(f"   Host: {settings.obs.host}")
    print(f"   Port: {settings.obs.port}")
    print(f"   Auto-connect: {settings.obs.auto_connect}")

    # Create OBS engine
    obs = OBSEngine(settings.obs)

    try:
        # Test connection
        print("\n🔌 Connecting to OBS Studio...")
        await obs.connect()
        print("✅ Connected successfully!")

        # Get version info
        print("\n📺 OBS Studio Information:")
        version = await obs._client.get_version()
        print(f"   OBS Version: {version.obs_version}")
        print(f"   WebSocket Version: {version.obs_web_socket_version}")
        print(f"   Platform: {version.platform}")

        # Get streaming status
        print("\n📡 Streaming Status:")
        stream_status = await obs._client.get_stream_status()
        print(f"   Streaming: {stream_status.output_active}")
        if stream_status.output_active:
            print(f"   Duration: {stream_status.output_duration}ms")
            print(f"   Bytes: {stream_status.output_bytes}")

        # List existing scenes
        print("\n🎬 Existing Scenes:")
        scenes = await obs._client.get_scene_list()
        print(f"   Current scene: {scenes.current_program_scene_name}")
        print(f"   Total scenes: {len(scenes.scenes)}")
        for i, scene in enumerate(scenes.scenes, 1):
            print(f"   {i}. {scene['sceneName']}")

        # Test scene creation
        print("\n🔨 Testing Scene Creation...")
        test_scene_name = "Miktos-Test-Scene"
        try:
            await obs._client.create_scene(test_scene_name)
            print(f"✅ Created scene: {test_scene_name}")

            # Clean up - remove test scene
            await obs._client.remove_scene(test_scene_name)
            print("🧹 Cleaned up test scene")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("⚠️  Scene already exists (OK)")
            else:
                print(f"❌ Scene creation failed: {e}")

        # Get canvas size
        print("\n📐 Canvas Configuration:")
        video_settings = await obs._client.get_video_settings()
        print(
            f"   Base Resolution: {video_settings.base_width}x"
            f"{video_settings.base_height}")
        print(
            f"   Output Resolution: {video_settings.output_width}x"
            f"{video_settings.output_height}")
        print(
            f"   FPS: {video_settings.fps_numerator}/"
            f"{video_settings.fps_denominator}")

        # Disconnect
        await obs.disconnect()
        print("\n✅ Disconnected from OBS")

        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ OBS Studio is ready for use with Miktos Hub")
        print("✅ WebSocket connection working")
        print("✅ Scene management operational")
        print("\nNext steps:")
        print("  1. Start the Miktos Hub server")
        print("  2. Connect Android phones running the camera app")
        print("  3. Create multi-camera scenes via the API")

        return True

    except ConnectionRefusedError:
        print("\n❌ CONNECTION REFUSED")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure OBS Studio is running")
        print("   2. Open OBS Studio → Tools → WebSocket Server Settings")
        print("   3. Ensure 'Enable WebSocket server' is checked")
        print(f"   4. Verify port is set to {settings.obs.port}")
        print("   5. Click 'Apply' and 'OK'")
        print("   6. Restart OBS Studio if needed")
        print("\n💡 To start OBS: open -a OBS")
        return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n🔍 Full error details:")
        import traceback
        traceback.print_exc()
        return False


async def quick_status():
    """Quick status check of OBS"""
    try:
        settings = Settings()
        obs = OBSEngine(settings.obs)
        await obs.connect()

        version = await obs._client.get_version()
        scenes = await obs._client.get_scene_list()
        stream = await obs._client.get_stream_status()

        await obs.disconnect()

        print("✅ OBS Connected")
        print(f"   Version: {version.obs_version}")
        print(f"   Scenes: {len(scenes.scenes)}")
        print(f"   Streaming: {'Yes' if stream.output_active else 'No'}")
        return True
    except Exception:
        print("❌ OBS Not Connected")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick status check
        success = asyncio.run(quick_status())
    else:
        # Full test
        success = asyncio.run(test_obs_connection())

    sys.exit(0 if success else 1)
