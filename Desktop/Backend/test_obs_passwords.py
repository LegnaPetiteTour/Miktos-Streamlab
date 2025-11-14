#!/usr/bin/env python3
"""Test OBS connection with and without password"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from obs_controller import OBSController  # noqa: E402  # type: ignore


async def test_connection_with_password(password: str) -> bool:
    """Test connection with given password"""
    print(f"\n🧪 Testing with password: {password[:4] if password else '(none)'}...")

    obs = OBSController(host="localhost", port=4455, password=password)
    try:
        success = await obs.connect()
        if success:
            print("✅ Connection successful!")
            await obs.disconnect()
            return True
        else:
            print("❌ Connection failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main() -> None:
    """Test different password scenarios"""
    # Load from .env
    load_dotenv()
    env_password = os.getenv("OBS_PASSWORD", "")

    print("=" * 60)
    print("Testing OBS WebSocket Connection")
    print("=" * 60)

    # Test 1: With .env password
    print("\n📋 Test 1: Password from .env file")
    print(f"   Password: {env_password}")
    result1 = await test_connection_with_password(env_password)

    # Test 2: No password
    print("\n📋 Test 2: No password (empty string)")
    result2 = await test_connection_with_password("")

    print("\n" + "=" * 60)
    print("Results:")
    print(f"  With .env password: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"  Without password:   {'✅ PASS' if result2 else '❌ FAIL'}")
    print("=" * 60)

    if result2 and not result1:
        print("\n⚠️  OBS WebSocket authentication appears to be DISABLED")
        print("   Consider enabling it in OBS: Tools → WebSocket Server Settings")


if __name__ == "__main__":
    asyncio.run(main())
