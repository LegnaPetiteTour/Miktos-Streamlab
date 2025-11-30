#!/usr/bin/env python3
"""
OBS Integration Test Suite

Tests Hub → OBS communication and scene management functionality.
Run with OBS Studio running and WebSocket server enabled.
"""

import sys
from obsws_python import ReqClient  # type: ignore
from config.settings import OBSConfig


class OBSIntegrationTest:
    """Test suite for OBS integration"""

    def __init__(self):
        self.obs_config = OBSConfig()
        self.client = None
        self.test_results = []

    def connect(self):
        """Connect to OBS WebSocket"""
        try:
            self.client = ReqClient(
                host=self.obs_config.host,
                port=self.obs_config.port,
                password=self.obs_config.password,
                timeout=5
            )
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    def disconnect(self):
        """Disconnect from OBS"""
        if self.client:
            self.client.disconnect()

    def test_connection(self):
        """Test 1: Basic connection and version info"""
        print("\n🧪 Test 1: Connection & Version Info")
        try:
            version = self.client.get_version()  # type: ignore
            print(f"   ✅ OBS Version: {version.obs_version}")  # type: ignore
            ws_ver = version.obs_web_socket_version  # type: ignore
            print(f"   ✅ WebSocket Version: {ws_ver}")
            self.test_results.append(("Connection", True))
            return True
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            self.test_results.append(("Connection", False))
            return False

    def test_scene_list(self):
        """Test 2: List existing scenes"""
        print("\n🧪 Test 2: Scene Discovery")
        try:
            scenes = self.client.get_scene_list()  # type: ignore
            current = self.client.get_current_program_scene()  # type: ignore

            print(f"   ✅ Found {len(scenes.scenes)} scenes")  # type: ignore
            current_name = current.current_program_scene_name  # type: ignore
            print(f"   ✅ Current: {current_name}")

            for scene in scenes.scenes[:5]:  # type: ignore
                is_current = scene["sceneName"]
                # Check if this is the current scene
                curr_scene = current.current_program_scene_name  # type: ignore
                is_current = is_current == curr_scene
                marker = "→" if is_current else " "
                print(f"     {marker} {scene['sceneName']}")

            self.test_results.append(("Scene Discovery", True))
            return True
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            self.test_results.append(("Scene Discovery", False))
            return False

    def test_scene_creation(self):
        """Test 3: Create new test scene"""
        print("\n🧪 Test 3: Scene Creation")
        test_scene = "Hub_Test_Scene"

        try:
            # Check if scene exists, delete if it does
            scenes = self.client.get_scene_list()  # type: ignore
            existing = [s["sceneName"] for s in scenes.scenes]  # type: ignore

            if test_scene in existing:
                print("   🗑️  Removing existing test scene...")
                self.client.remove_scene(test_scene)  # type: ignore

            # Create new scene
            self.client.create_scene(test_scene)  # type: ignore
            print(f"   ✅ Created scene: {test_scene}")

            # Verify it exists
            scenes = self.client.get_scene_list()  # type: ignore
            all_scenes = scenes.scenes  # type: ignore
            scene_names = [s["sceneName"] for s in all_scenes]
            if test_scene in scene_names:
                print("   ✅ Scene verified in scene list")
                self.test_results.append(("Scene Creation", True))
                return True
            else:
                print("   ❌ Scene not found after creation")
                self.test_results.append(("Scene Creation", False))
                return False

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            self.test_results.append(("Scene Creation", False))
            return False

    def test_scene_switching(self):
        """Test 4: Switch between scenes"""
        print("\n🧪 Test 4: Scene Switching")
        test_scene = "Hub_Test_Scene"

        try:
            # Get current scene
            current = self.client.get_current_program_scene()  # type: ignore
            original_scene = current.current_program_scene_name  # type: ignore
            print(f"   📍 Original scene: {original_scene}")

            # Switch to test scene
            self.client.set_current_program_scene(test_scene)  # type: ignore
            print(f"   ✅ Switched to: {test_scene}")

            # Verify switch
            current = self.client.get_current_program_scene()  # type: ignore
            current_name = current.current_program_scene_name  # type: ignore
            if current_name == test_scene:
                print("   ✅ Scene switch verified")

                # Switch back
                self.client.set_current_program_scene(  # type: ignore
                    original_scene
                )
                print(f"   ✅ Restored original scene: {original_scene}")

                self.test_results.append(("Scene Switching", True))
                return True
            else:
                print("   ❌ Scene switch failed")
                self.test_results.append(("Scene Switching", False))
                return False

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            self.test_results.append(("Scene Switching", False))
            return False

    def test_scene_sources(self):
        """Test 5: Add sources to scene"""
        print("\n🧪 Test 5: Scene Source Management")
        test_scene = "Hub_Test_Scene"

        try:
            # Add a color source (universally supported)
            source_name = "Hub_Test_Color"

            # Check if source exists
            try:
                self.client.remove_input(source_name)  # type: ignore
            except Exception:
                pass  # Source doesn't exist, that's fine

            # Create color source
            settings = {
                "color": 0xFF0000FF,  # Red color
                "width": 1920,
                "height": 1080
            }

            self.client.create_input(  # type: ignore
                sceneName=test_scene,
                inputName=source_name,
                inputKind="color_source_v3",
                inputSettings=settings,
                sceneItemEnabled=True
            )
            print(f"   ✅ Created color source: {source_name}")

            # Verify source in scene
            items = self.client.get_scene_item_list(test_scene)  # type: ignore
            scene_items = items.scene_items  # type: ignore
            source_found = any(
                item["sourceName"] == source_name
                for item in scene_items
            )

            if source_found:
                print("   ✅ Source verified in scene")
                self.test_results.append(("Source Management", True))
                return True
            else:
                print("   ❌ Source not found in scene")
                self.test_results.append(("Source Management", False))
                return False

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            self.test_results.append(("Source Management", False))
            return False

    def test_streaming_status(self):
        """Test 6: Get streaming and recording status"""
        print("\n🧪 Test 6: Streaming Status")

        try:
            stream_status = self.client.get_stream_status()  # type: ignore
            record_status = self.client.get_record_status()  # type: ignore

            stream_active = stream_status.output_active  # type: ignore
            print(f"   ✅ Stream Active: {stream_active}")
            record_active = record_status.output_active  # type: ignore
            print(f"   ✅ Recording Active: {record_active}")

            if stream_status.output_active:  # type: ignore
                duration = stream_status.output_duration / 1000  # type: ignore
                print(f"   📊 Stream Duration: {duration:.1f}s")

            self.test_results.append(("Status Query", True))
            return True

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            self.test_results.append(("Status Query", False))
            return False

    def cleanup(self):
        """Clean up test artifacts"""
        print("\n🧹 Cleanup")
        try:
            # Remove test scene
            self.client.remove_scene("Hub_Test_Scene")  # type: ignore
            print("   ✅ Removed test scene")
        except Exception:
            print("   ℹ️  Test scene already removed")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)

        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")

        print("-" * 60)
        print(f"Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print(f"⚠️  {total - passed} test(s) failed")
            return 1


def main():
    """Run OBS integration tests"""
    print("=" * 60)
    print("🎬 OBS INTEGRATION TEST SUITE")
    print("=" * 60)

    tester = OBSIntegrationTest()

    # Connect
    print("\n🔌 Connecting to OBS...")
    if not tester.connect():
        print("\n❌ Cannot connect to OBS. Please ensure:")
        print("   1. OBS Studio is running")
        print("   2. WebSocket server is enabled (Tools → WebSocket Settings)")
        print("   3. Password in config/settings.py is correct")
        return 1

    print("✅ Connected to OBS WebSocket")

    # Run tests
    try:
        tester.test_connection()
        tester.test_scene_list()
        tester.test_scene_creation()
        tester.test_scene_switching()
        tester.test_scene_sources()
        tester.test_streaming_status()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup and disconnect
        tester.cleanup()
        tester.disconnect()

    # Print summary
    exit_code = tester.print_summary()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
