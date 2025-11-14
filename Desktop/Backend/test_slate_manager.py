#!/usr/bin/env python3
"""
Slate Manager Integration Tests
Tests slate display system with real OBS
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from obs_controller import OBSController  # type: ignore  # noqa: E402,E501
from slate_manager import SlateManager  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
import os  # noqa: E402


async def main() -> None:
    """Run slate manager integration tests"""

    print("\n" + "="*60)
    print("🎨 SLATE MANAGER INTEGRATION TEST")
    print("="*60)

    load_dotenv()

    host = os.getenv('OBS_HOST', 'localhost')
    port = int(os.getenv('OBS_PORT', '4455'))
    password = os.getenv('OBS_PASSWORD', '')

    print(f"ℹ OBS Host: {host}")
    print(f"ℹ OBS Port: {port}")

    if not password or password == 'REPLACE_WITH_YOUR_PASSWORD':
        print("\n❌ Error: OBS_PASSWORD not set in .env file!")
        return

    print("✓ Environment configured!")
    print("ℹ Creating OBS controller and slate manager...\n")

    obs = OBSController(host=host, port=port, password=password)
    slate = SlateManager(obs)

    tests_passed = 0
    tests_total = 7

    try:
        # Test 1: Connection
        print("="*60)
        print("TEST 1: OBS Connection")
        print("="*60 + "\n")

        await obs.connect()
        print("✓ Connected to OBS\n")
        tests_passed += 1

        # Test 2: Verify slate scene exists
        print("="*60)
        print("TEST 2: Verify Slate Scene")
        print("="*60 + "\n")

        scenes = await obs.get_scenes()
        slate_exists = False

        for s in scenes:
            if isinstance(s, str):
                scene_name = s
            elif isinstance(s, dict):
                scene_name = str(s.get('name', s.get('sceneName', '')))
            else:
                scene_name = str(getattr(s, 'name', ''))

            if scene_name == slate.slate_scene_name:
                slate_exists = True
                break

        if slate_exists:
            print(f"✓ Found slate scene: '{slate.slate_scene_name}'\n")
            tests_passed += 1
        else:
            print(f"❌ Slate scene '{slate.slate_scene_name}' not found!")
            print("Please create this scene in OBS before running tests\n")

        # Test 3: Inspect slate scene sources
        print("="*60)
        print("TEST 3: Inspect Slate Scene")
        print("="*60 + "\n")

        sources = await slate.get_slate_scene_sources()
        if sources:
            print(f"✓ Found {len(sources)} sources in slate scene:")
            for source in sources:
                print(f"  • {source}")
            print()
            tests_passed += 1
        else:
            print("⚠ No sources found in slate scene\n")

        # Test 4: Show slate with default message
        print("="*60)
        print("TEST 4: Show Slate (Default Message)")
        print("="*60 + "\n")

        print("ℹ Displaying slate... (watch OBS preview!)")
        success = await slate.show_slate()

        if success:
            print("✓ Slate displayed successfully")
            print("ℹ Waiting 3 seconds...\n")
            await asyncio.sleep(3)
            tests_passed += 1
        else:
            print("❌ Failed to display slate\n")

        # Test 5: Update slate message
        print("="*60)
        print("TEST 5: Update Slate Message")
        print("="*60 + "\n")

        new_message = "Stream reconnecting - please stand by"
        print(f"ℹ Updating message to: '{new_message}'")
        success = await slate.update_message(new_message)

        if success:
            print("✓ Message updated successfully")
            print("ℹ Waiting 2 seconds...\n")
            await asyncio.sleep(2)
            tests_passed += 1
        else:
            print("❌ Failed to update message\n")

        # Test 6: Hide slate
        print("="*60)
        print("TEST 6: Hide Slate")
        print("="*60 + "\n")

        print("ℹ Hiding slate and returning to previous scene...")
        success = await slate.hide_slate()

        if success:
            print("✓ Slate hidden successfully\n")
            tests_passed += 1
        else:
            print("❌ Failed to hide slate\n")

        await asyncio.sleep(1)

        # Test 7: Flash slate (auto-hide)
        print("="*60)
        print("TEST 7: Flash Slate (Auto-Hide)")
        print("="*60 + "\n")

        flash_message = "This slate will auto-hide in 2 seconds!"
        print(f"ℹ Flashing slate with message: '{flash_message}'")
        success = await slate.flash_slate(flash_message, duration=2.0)

        if success:
            print("✓ Flash slate successful")
            tests_passed += 1
        else:
            print("❌ Flash slate failed\n")

        # Wait for flash to complete
        await asyncio.sleep(3)

        # Cleanup
        await obs.disconnect()
        print("\n✓ Disconnected from OBS")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")

    test_names = [
        "OBS Connection",
        "Verify Slate Scene",
        "Inspect Slate Scene",
        "Show Slate",
        "Update Message",
        "Hide Slate",
        "Flash Slate"
    ]

    for i, name in enumerate(test_names):
        status = "✓ PASSED" if i < tests_passed else "✗ FAILED"
        print(f"{name:.<40} {status}")

    print(f"\nResults: {tests_passed}/{tests_total} tests passed")

    if tests_passed == tests_total:
        print("\n🎉 PERFECT! SLATE MANAGER FULLY FUNCTIONAL! 🎉")
        print("✓ Ready to integrate with failover system!")
    elif tests_passed >= tests_total - 1:
        print("\n✓ Excellent! Almost perfect!")
    else:
        print("\n⚠ Some tests need attention")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
