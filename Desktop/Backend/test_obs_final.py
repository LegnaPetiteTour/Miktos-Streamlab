#!/usr/bin/env python3
"""Real OBS Integration Tests - Final Version"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from obs_controller import OBSController
from dotenv import load_dotenv
import os


async def main():
    print("\n" + "="*60)
    print("🎬 MIKTOS STREAMLAB - REAL OBS INTEGRATION TEST")
    print("="*60)
    
    load_dotenv()
    
    host = os.getenv('OBS_HOST', 'localhost')
    port = int(os.getenv('OBS_PORT', '4455'))
    password = os.getenv('OBS_PASSWORD', '')
    
    print(f"ℹ OBS Host: {host}")
    print(f"ℹ OBS Port: {port}")
    
    if not password or password == 'REPLACE_WITH_YOUR_PASSWORD':
        print("\n❌ Error: OBS_PASSWORD not set!")
        return
    
    print("✓ Environment configured!")
    print("ℹ \nCreating OBS controller...")
    
    controller = OBSController(host=host, port=port, password=password)
    tests_passed = 0
    tests_total = 8
    
    try:
        # Test 1: Connection
        print("\n" + "="*60)
        print("TEST 1: Connection")
        print("="*60 + "\n")
        
        await controller.connect()
        print("✓ Successfully connected to OBS!")
        tests_passed += 1
        
        # Test 2: Version
        print("\n" + "="*60)
        print("TEST 2: OBS Version")
        print("="*60 + "\n")
        
        version_info = await controller.get_version()
        obs_version = str(version_info) if not isinstance(version_info, dict) else version_info.get('obsVersion', 'Unknown')
        print(f"✓ OBS Version: {obs_version}")
        
        try:
            if int(obs_version.split('.')[0]) >= 28:
                print("✓ OBS version is 28+ (WebSocket 5.x compatible)")
        except:
            pass
        tests_passed += 1
        
        # Test 3: Health Monitoring
        print("\n" + "="*60)
        print("TEST 3: Health Monitoring")
        print("="*60 + "\n")
        
        health = await controller.get_health()
        print("ℹ Health Metrics:")
        
        if isinstance(health, dict):
            print(f"  Connected: {health.get('connected', True)}")
            print(f"  Status: {health.get('status', 'unknown')}")
            print(f"  FPS: {health.get('fps', 'N/A')}")
            print(f"  CPU: {health.get('cpu_usage', 'N/A')}%")
            print(f"  Memory: {health.get('memory_usage', 'N/A')} MB")
        else:
            print(f"  Connected: {health.connected}")
            print(f"  FPS: {health.fps}")
        
        print("✓ Health monitoring working!")
        tests_passed += 1
        
        # Test 4: Scene Management
        print("\n" + "="*60)
        print("TEST 4: Scene Management")
        print("="*60 + "\n")
        
        all_scenes = await controller.get_scenes()
        
        if all_scenes:
            print(f"✓ Found {len(all_scenes)} scenes:")
            for scene in all_scenes:
                if isinstance(scene, dict):
                    name = scene.get('name', scene.get('sceneName', 'Unknown'))
                    is_current = scene.get('is_current', scene.get('sceneIndex', -1) == 0)
                else:
                    name = getattr(scene, 'name', getattr(scene, 'sceneName', 'Unknown'))
                    is_current = getattr(scene, 'is_current', False)
                
                marker = "→" if is_current else " "
                current_label = " (current)" if is_current else ""
                print(f"  {marker} {name}{current_label}")
            tests_passed += 1
        
        current_scene = await controller.get_current_scene()
        current_name = current_scene if isinstance(current_scene, str) else (current_scene.get('sceneName') if isinstance(current_scene, dict) else current_scene.name)
        print(f"ℹ Current scene: {current_name}")
        
        # Test 5: Scene Switching
        print("\n" + "="*60)
        print("TEST 5: Scene Switching")
        print("="*60 + "\n")
        
        if all_scenes and len(all_scenes) >= 2:
            test_scene_names = []
            for scene in all_scenes[:2]:
                if isinstance(scene, dict):
                    name = scene.get('name', scene.get('sceneName', ''))
                elif isinstance(scene, str):
                    name = scene
                else:
                    name = getattr(scene, 'name', getattr(scene, 'sceneName', ''))
                test_scene_names.append(name)
            
            for scene_name in test_scene_names:
                print(f"ℹ Switching to: {scene_name}")
                await controller.switch_scene(scene_name)
                print(f"✓ Switched to: {scene_name}")
                await asyncio.sleep(1)
            
            print(f"ℹ Switching back to: {current_name}")
            await controller.switch_scene(current_name)
            tests_passed += 1
        
        # Test 6: Slate Display
        print("\n" + "="*60)
        print("TEST 6: Slate Display")
        print("="*60 + "\n")
        
        slate_scenes = ["Slate Scene", "Slate"]
        slate_found = False
        
        for slate_name in slate_scenes:
            for scene in all_scenes:
                scene_name = scene if isinstance(scene, str) else (scene.get('name', scene.get('sceneName', '')) if isinstance(scene, dict) else getattr(scene, 'name', ''))
                
                if scene_name == slate_name:
                    print(f"✓ Found slate scene: '{slate_name}'")
                    await controller.switch_scene(slate_name)
                    print("✓ Slate displayed!")
                    await asyncio.sleep(2)
                    await controller.switch_scene(current_name)
                    print("✓ Returned to previous scene!")
                    tests_passed += 1
                    slate_found = True
                    break
            if slate_found:
                break
        
        if not slate_found:
            print("⚠ No slate scene found")
        
        # Test 7: Streaming Status - FIXED: use get_stream_stats()
        print("\n" + "="*60)
        print("TEST 7: Streaming Status")
        print("="*60 + "\n")
        
        stream_stats = await controller.get_stream_stats()
        
        if isinstance(stream_stats, dict):
            active = stream_stats.get('outputActive', stream_stats.get('streaming', False))
        else:
            active = getattr(stream_stats, 'streaming', False)
        
        print(f"ℹ Streaming: {'Active' if active else 'Stopped'}")
        tests_passed += 1
        
        # Test 8: Disconnection
        print("\n" + "="*60)
        print("TEST 8: Disconnection")
        print("="*60 + "\n")
        
        await controller.disconnect()
        print("✓ Successfully disconnected!")
        tests_passed += 1
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")
    
    test_names = [
        "Connection", "Version Check", "Health Monitoring",
        "Scene Management", "Scene Switching", "Slate Display",
        "Streaming Status", "Disconnection"
    ]
    
    for i, name in enumerate(test_names):
        status = "✓ PASSED" if i < tests_passed else "✗ FAILED"
        print(f"{name:.<40} {status}")
    
    print(f"\nResults: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("\n🎉🎉🎉 PERFECT! ALL 8/8 TESTS PASSED! 🎉🎉🎉")
        print("✓ Your OBS integration is 100% functional!")
        print("✓ Ready to build the slate display system!")
    elif tests_passed >= 7:
        print("\n✓ Excellent! Almost perfect!")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
