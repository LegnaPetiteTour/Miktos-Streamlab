#!/usr/bin/env python3
"""
Camera Discovery Test Script
Tests mDNS discovery and camera registration
"""

import requests
import time
from datetime import datetime


BASE_URL = "http://127.0.0.1:8000"


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_server_health():
    """Check if Miktos Hub server is running"""
    print_header("📡 SERVER HEALTH CHECK")

    try:
        response = requests.get(f"{BASE_URL}/api/health/metrics", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is running")
            print(f"   Active sessions: {data.get('active_sessions', 0)}")
            print(f"   Total cameras: {data.get('total_cameras', 0)}")
            print(f"   CPU usage: {data.get('cpu_usage_percent', 0):.1f}%")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("\n🔧 Make sure Miktos Hub is running:")
        print("   cd '/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub'")
        print("   source ../.venv/bin/activate")
        print(
            "   uvicorn api.server:create_app --factory "
            "--host 127.0.0.1 --port 8000")
        return False


def start_discovery():
    """Start camera discovery"""
    print_header("🔍 STARTING CAMERA DISCOVERY")

    try:
        response = requests.post(f"{BASE_URL}/api/discovery/start", timeout=5)
        if response.status_code == 200:
            print("✅ Discovery started")
            return True
        else:
            print(f"⚠️  Response: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_discovery_status():
    """Check discovery status"""
    try:
        response = requests.get(f"{BASE_URL}/api/discovery/status", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data
        return None
    except Exception:
        return None


def list_cameras():
    """List all discovered cameras"""
    try:
        response = requests.get(f"{BASE_URL}/api/cameras", timeout=2)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def wait_for_cameras(timeout=30):
    """Wait for cameras to be discovered"""
    print_header(f"⏱️  WAITING FOR CAMERAS ({timeout}s timeout)")

    print("\n📱 Instructions for phone setup:")
    print("   1. Ensure phone is on the same WiFi network")
    print("   2. Open Miktos StreamLab app")
    print("   3. Tap 'Connect to Hub'")
    print("   4. App should auto-discover the Hub via mDNS")
    print("   5. Camera should start streaming\n")

    start_time = time.time()
    last_count = 0

    while (time.time() - start_time) < timeout:
        status = check_discovery_status()
        if status:
            discovered = status.get('cameras_discovered', 0)
            registered = status.get('cameras_registered', 0)

            if discovered != last_count or registered != last_count:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Discovered: {discovered}, Registered: {registered}")
                last_count = max(discovered, registered)

            if registered > 0:
                print(f"\n✅ Found {registered} camera(s)!")
                return True

        time.sleep(2)

    print("\n⏰ Timeout reached - no cameras found")
    return False


def display_camera_details():
    """Display detailed camera information"""
    print_header("📱 CAMERA DETAILS")

    cameras = list_cameras()

    if not cameras:
        print("❌ No cameras registered")
        print("\n🔧 Troubleshooting:")
        print("   • Check phone and Mac are on same WiFi")
        print("   • Verify app has network permissions")
        print("   • Check firewall isn't blocking connections")
        print("   • Try restarting the app")
        return False

    for i, camera in enumerate(cameras, 1):
        print(f"\n📷 Camera {i}:")
        print(f"   ID: {camera.get('id', 'N/A')}")
        print(f"   Name: {camera.get('name', 'N/A')}")
        print(f"   Type: {camera.get('type', 'N/A')}")
        print(f"   Status: {camera.get('status', 'N/A')}")

        if 'ip_address' in camera:
            print(f"   IP: {camera['ip_address']}")
        if 'stream_url' in camera:
            print(f"   Stream: {camera['stream_url']}")
        if 'resolution' in camera:
            res = camera['resolution']
            width = res.get('width', '?')
            height = res.get('height', '?')
            print(f"   Resolution: {width}x{height}")
        if 'battery_level' in camera:
            print(f"   Battery: {camera['battery_level']}%")

    return True


def test_camera_health():
    """Test camera health endpoints"""
    print_header("💓 CAMERA HEALTH CHECK")

    cameras = list_cameras()
    if not cameras:
        print("⚠️  No cameras to check")
        return

    for camera in cameras:
        camera_id = camera.get('id')
        try:
            response = requests.get(
                f"{BASE_URL}/api/cameras/{camera_id}/health", timeout=2)
            if response.status_code == 200:
                health = response.json()
                print(f"\n📱 {camera.get('name', camera_id)}:")
                print(f"   Status: {health.get('status', 'unknown')}")
                print(f"   Uptime: {health.get('uptime_seconds', 0)}s")
                print(f"   Frame rate: {health.get('current_fps', 0)} fps")
                print(f"   Bitrate: {health.get('bitrate_kbps', 0)} kbps")
            else:
                camera_name = camera.get('name')
                status_code = response.status_code
                print(
                    f"\n⚠️  {camera_name}: Health check failed "
                    f"({status_code})")
        except Exception as e:
            print(f"\n❌ {camera.get('name')}: {e}")


def run_full_test():
    """Run complete camera discovery test"""
    print("\n" + "🚀" * 35)
    print("  MIKTOS HUB - CAMERA DISCOVERY TEST")
    print("🚀" * 35)

    # 1. Check server
    if not test_server_health():
        return False

    time.sleep(1)

    # 2. Start discovery
    if not start_discovery():
        print("\n⚠️  Could not start discovery, but continuing...")

    time.sleep(2)

    # 3. Wait for cameras
    if wait_for_cameras(timeout=60):
        time.sleep(1)

        # 4. Display camera details
        display_camera_details()

        time.sleep(1)

        # 5. Test health
        test_camera_health()

        print_header("✅ TEST COMPLETE - SUCCESS")
        print("\n🎉 Camera discovery is working!")
        print("\nNext steps:")
        print("  • Create a scene: POST /api/scenes")
        print("  • Add cameras to scene")
        print("  • Start streaming session")
        print("  • Monitor at: http://127.0.0.1:8000/docs")

        return True
    else:
        print_header("❌ TEST COMPLETE - NO CAMERAS FOUND")
        print("\n🔧 Troubleshooting steps:")
        print("\n1. Network Configuration:")
        print("   • Ensure phone and Mac on same WiFi")
        print("   • Disable VPN if active")
        print("   • Check firewall settings")

        print("\n2. App Configuration:")
        print("   • Open Miktos StreamLab app")
        print("   • Go to Settings")
        print("   • Verify Hub IP address is correct")
        print("   • Enable 'Auto-discover Hub'")

        print("\n3. Server Logs:")
        print("   • Check: tail -f /tmp/miktos_server.log")
        print("   • Look for mDNS discovery errors")

        print("\n4. Test mDNS:")
        print("   • Run: dns-sd -B _miktos-camera._tcp")
        print("   • Should see phone advertising service")

        return False


if __name__ == "__main__":
    import sys

    success = run_full_test()
    sys.exit(0 if success else 1)
