#!/usr/bin/env python3
"""
Quick test for Desktop Control Panel
Verifies that all components are working
"""

import sys
import time
import subprocess
from pathlib import Path


def test_imports():
    """Test that all required packages are installed"""
    print("🔍 Testing Python imports...")
    try:
        import flask  # noqa: F401
        import flask_socketio  # noqa: F401
        import flask_cors  # noqa: F401
        import websockets  # noqa: F401
        print("✅ All packages installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False


def test_files_exist():
    """Test that all required files exist"""
    print("\n🔍 Checking required files...")

    files = [
        "websocket_server.py",
        "control_panel.py",
        "templates/control_panel.html",
        "start_control_panel.sh"
    ]

    all_exist = True
    for file in files:
        path = Path(file)
        if path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - NOT FOUND")
            all_exist = False

    return all_exist


def test_websocket_server():
    """Test that WebSocket server can start"""
    print("\n🔍 Testing WebSocket server startup...")

    try:
        # Start server in background
        proc = subprocess.Popen(
            [sys.executable, "websocket_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for startup
        time.sleep(3)

        # Check if still running
        if proc.poll() is None:
            print("✅ WebSocket server started successfully")
            proc.terminate()
            proc.wait()
            return True
        else:
            stdout, stderr = proc.communicate()
            print("❌ Server failed to start")
            print(f"Error: {stderr.decode()}")
            return False

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False


def test_control_panel():
    """Test that control panel can start"""
    print("\n🔍 Testing Flask control panel...")

    # Just test import
    try:
        import control_panel  # noqa: F401
        # Verify the module has expected attributes
        assert hasattr(control_panel, 'app')
        print("✅ Control panel imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing control panel: {e}")
        return False


def main():
    print("=" * 60)
    print("  Desktop Control Panel - System Test")
    print("=" * 60)
    print()

    results = []

    # Run tests
    results.append(("Package Installation", test_imports()))
    results.append(("Required Files", test_files_exist()))
    results.append(("WebSocket Server", test_websocket_server()))
    results.append(("Control Panel", test_control_panel()))

    # Summary
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Control panel is ready to use.")
        print("\nNext steps:")
        print("1. Start the control panel:")
        print("   ./start_control_panel.sh")
        print("\n2. Open browser:")
        print("   http://localhost:5000")
        print("\n3. Enable remote control on Android app")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
