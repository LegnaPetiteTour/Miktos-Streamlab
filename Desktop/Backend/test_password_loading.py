#!/usr/bin/env python3
"""Test script to verify password loading from .env file"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Now test OBS connection
from obs_controller import OBSController  # type: ignore  # noqa: E402

# Load environment variables from .env file in project root
project_root = Path(__file__).parent
dotenv_path = project_root / ".env"
print(f"Loading .env from: {dotenv_path}")
print(f".env exists: {dotenv_path.exists()}")

load_dotenv(dotenv_path)

# Check if password is loaded
obs_password = os.getenv("OBS_PASSWORD", "")
print(f"\n✅ OBS_PASSWORD loaded: {'Yes' if obs_password else 'No'}")
if obs_password:
    print(f"   Length: {len(obs_password)} characters")
    print(f"   Value: {obs_password[:4]}...{obs_password[-4:]}")


async def test_connection() -> bool:
    """Test connecting to OBS"""
    print("\n🎬 Testing OBS connection at localhost:4455...")
    print(f"   Using password: {obs_password[:4]}...{obs_password[-4:]}")

    obs = OBSController(host="localhost", port=4455, password=obs_password)

    try:
        success = await obs.connect()
        if success:
            print("✅ Successfully connected to OBS!")
            await obs.disconnect()
            return True
        else:
            print("❌ Failed to connect to OBS")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
