#!/usr/bin/env python3
"""
Start streaming application without GUI for failover testing
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
load_dotenv()

from obs_controller import OBSController  # noqa: E402
from core.egress_v2 import (  # noqa: E402
    EgressManagerV2,
    EgressConfig,
)


async def main() -> int:
    """Main streaming application"""
    print("=" * 60)
    print("🎥 Miktos StreamLab - Streaming with Failover Monitoring")
    print("=" * 60)

    # Get OBS credentials from environment
    obs_host = os.getenv("OBS_HOST", "localhost")
    obs_port = int(os.getenv("OBS_PORT", "4455"))
    obs_password = os.getenv("OBS_PASSWORD", "")

    print("\n🔑 OBS Configuration:")
    print(f"   Host: {obs_host}")
    print(f"   Port: {obs_port}")
    print(f"   Password: {'Yes' if obs_password else 'No'}")
    if obs_password:
        print(f"   (Length: {len(obs_password)} characters)")

    # Connect to OBS
    obs = OBSController(host=obs_host, port=obs_port, password=obs_password)
    print("\n🎬 Connecting to OBS...")
    success = await obs.connect()

    if not success:
        print("❌ Failed to connect to OBS. Exiting.")
        return 1

    print("✅ Connected to OBS successfully")

    # Create egress manager with failover support
    print("\n🚀 Initializing egress manager...")
    config = EgressConfig.from_env()
    egress = EgressManagerV2(obs_controller=obs, config=config)

    print("\n📡 Configured destinations:")
    print(f"   RTMP: {len(config.rtmp_destinations)} destinations")
    for dest in config.rtmp_destinations:
        print(f"      - {dest.name}")
    print(f"   SRT:  {len(config.srt_destinations)} backup destinations")
    for dest in config.srt_destinations:  # type: ignore[assignment]
        print(f"      - {dest.name} (BACKUP)")

    # Start streaming
    print("\n▶️  Starting streaming...")
    await egress.start_streaming()

    print("\n✅ Streaming started with automatic failover monitoring")
    print("   • Health checks every 5 seconds")
    print("   • Failover after 3 consecutive failures (~15 sec)")
    print("   • Recovery after 5 consecutive healthy checks (~25 sec)")
    print("\n📊 Monitoring stream health...")
    print("   Press Ctrl+C to stop\n")

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping streaming...")
        await egress.stop_streaming()
        await obs.disconnect()
        print("✅ Streaming stopped")

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
