#!/usr/bin/env python3
"""
Complete API Test Suite
Tests all major endpoints of Miktos Hub
"""

import requests
import json
import time
from datetime import datetime


BASE_URL = "http://127.0.0.1:8000"


class APITester:
    def __init__(self):
        self.results = []
        self.session_id = None
        self.scene_id = None
        self.camera_ids = []
    
    def test(self, name, func):
        """Run a test and record result"""
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print('='*70)
        try:
            result = func()
            status = "✅ PASS" if result else "❌ FAIL"
            self.results.append((name, result))
            print(f"\n{status}")
            return result
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            self.results.append((name, False))
            return False
    
    def test_health_metrics(self):
        """Test health metrics endpoint"""
        response = requests.get(f"{BASE_URL}/api/health/metrics", timeout=5)
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            return False
        
        data = response.json()
        print(f"Active sessions: {data.get('active_sessions')}")
        print(f"Total cameras: {data.get('total_cameras')}")
        print(f"CPU usage: {data.get('cpu_usage_percent')}%")
        print(f"Memory usage: {data.get('memory_usage_percent')}%")
        return True
    
    def test_session_creation(self):
        """Test creating a session"""
        payload = {
            "name": "API Test Session",
            "description": "Automated testing session"
        }
        response = requests.post(f"{BASE_URL}/api/", json=payload, timeout=5)
        
        if response.status_code not in [200, 201]:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        self.session_id = data.get('session_id')
        print(f"Session ID: {self.session_id}")
        print(f"Name: {data.get('name')}")
        print(f"State: {data.get('state')}")
        return self.session_id is not None
    
    def test_list_sessions(self):
        """Test listing all sessions"""
        response = requests.get(f"{BASE_URL}/api/", timeout=5)
        
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            return False
        
        sessions = response.json()
        print(f"Total sessions: {len(sessions)}")
        for session in sessions:
            print(f"  - {session.get('name')} ({session.get('state')})")
        return True
    
    def test_scene_creation(self):
        """Test creating a scene"""
        payload = {
            "name": "Test Scene - 4-Grid",
            "layout": "grid_2x2",
            "description": "Automated test scene"
        }
        response = requests.post(f"{BASE_URL}/api/scenes", json=payload, timeout=5)
        
        if response.status_code not in [200, 201]:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        self.scene_id = data.get('scene_id') or data.get('id')
        print(f"Scene ID: {self.scene_id}")
        print(f"Name: {data.get('name')}")
        print(f"Layout: {data.get('layout')}")
        return self.scene_id is not None
    
    def test_list_scenes(self):
        """Test listing all scenes"""
        response = requests.get(f"{BASE_URL}/api/scenes", timeout=5)
        
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            return False
        
        scenes = response.json()
        print(f"Total scenes: {len(scenes)}")
        for scene in scenes:
            print(f"  - {scene.get('name')} ({scene.get('layout')})")
        return True
    
    def test_camera_discovery_status(self):
        """Test camera discovery status"""
        response = requests.get(f"{BASE_URL}/api/discovery/status", timeout=5)
        
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            return False
        
        data = response.json()
        print(f"Discovery active: {data.get('active')}")
        print(f"Method: {data.get('discovery_method')}")
        print(f"Cameras discovered: {data.get('cameras_discovered')}")
        print(f"Cameras registered: {data.get('cameras_registered')}")
        return True
    
    def test_list_cameras(self):
        """Test listing cameras"""
        response = requests.get(f"{BASE_URL}/api/cameras", timeout=5)
        
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            return False
        
        cameras = response.json()
        print(f"Total cameras: {len(cameras)}")
        
        self.camera_ids = []
        for camera in cameras:
            camera_id = camera.get('id')
            self.camera_ids.append(camera_id)
            print(f"\n  Camera: {camera.get('name')}")
            print(f"    ID: {camera_id}")
            print(f"    Type: {camera.get('type')}")
            print(f"    Status: {camera.get('status')}")
        
        return True
    
    def test_streaming_destinations(self):
        """Test streaming destinations endpoint"""
        response = requests.get(f"{BASE_URL}/api/streaming/destinations", timeout=5)
        
        # 404 is OK if endpoint doesn't exist yet
        if response.status_code == 404:
            print("Endpoint not implemented yet (OK)")
            return True
        
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            return False
        
        destinations = response.json()
        print(f"Total destinations: {len(destinations)}")
        return True
    
    def test_api_documentation(self):
        """Test that API docs are accessible"""
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            return False
        
        print("API documentation is accessible")
        print(f"URL: {BASE_URL}/docs")
        return True
    
    def test_openapi_spec(self):
        """Test OpenAPI specification"""
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            return False
        
        spec = response.json()
        paths = spec.get('paths', {})
        print(f"Total API endpoints: {len(paths)}")
        print("\nAvailable endpoints:")
        for path in sorted(paths.keys())[:10]:
            methods = ', '.join(paths[path].keys())
            print(f"  {path} [{methods.upper()}]")
        if len(paths) > 10:
            print(f"  ... and {len(paths) - 10} more")
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for _, result in self.results if result)
        total = len(self.results)
        
        print(f"\nResults: {passed}/{total} tests passed")
        print(f"Success rate: {(passed/total*100):.1f}%\n")
        
        for name, result in self.results:
            status = "✅" if result else "❌"
            print(f"{status} {name}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return False


def main():
    """Run all tests"""
    print("\n" + "🧪" * 35)
    print("  MIKTOS HUB - COMPREHENSIVE API TEST")
    print("🧪" * 35)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = APITester()
    
    # Core health tests
    tester.test("Health Metrics", tester.test_health_metrics)
    tester.test("API Documentation", tester.test_api_documentation)
    tester.test("OpenAPI Specification", tester.test_openapi_spec)
    
    time.sleep(0.5)
    
    # Session tests
    tester.test("Session Creation", tester.test_session_creation)
    tester.test("List Sessions", tester.test_list_sessions)
    
    time.sleep(0.5)
    
    # Scene tests
    tester.test("Scene Creation", tester.test_scene_creation)
    tester.test("List Scenes", tester.test_list_scenes)
    
    time.sleep(0.5)
    
    # Camera tests
    tester.test("Camera Discovery Status", tester.test_camera_discovery_status)
    tester.test("List Cameras", tester.test_list_cameras)
    
    time.sleep(0.5)
    
    # Streaming tests
    tester.test("Streaming Destinations", tester.test_streaming_destinations)
    
    # Print summary
    success = tester.print_summary()
    
    # Additional info
    if tester.session_id:
        print(f"\n📝 Created session ID: {tester.session_id}")
    if tester.scene_id:
        print(f"🎬 Created scene ID: {tester.scene_id}")
    if tester.camera_ids:
        print(f"📱 Found {len(tester.camera_ids)} camera(s)")
    
    print(f"\n🔗 Explore the API:")
    print(f"   Interactive docs: {BASE_URL}/docs")
    print(f"   Redoc: {BASE_URL}/redoc")
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
