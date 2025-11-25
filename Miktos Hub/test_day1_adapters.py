#!/usr/bin/env python3
"""
Day 1 - Adapter Testing Script

Tests that model adapters correctly bridge Hub ↔ Backend models.
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Add backend to path
backend_path = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
sys.path.insert(0, backend_path)

print("=" * 60)
print("DAY 1 - MODEL ADAPTER TESTING")
print("=" * 60)
print()

# Test 1: Import adapters
print("Test 1: Importing ModelAdapter...")
try:
    from adapters.model_adapters import ModelAdapter
    print("✅ ModelAdapter imported successfully")
except Exception as e:
    print(f"❌ Failed to import ModelAdapter: {e}")
    sys.exit(1)

# Test 2: Check if backend is available
print("\nTest 2: Checking backend availability...")
if ModelAdapter.is_available():
    print("✅ Backend models are available")
else:
    print("❌ Backend models NOT available")
    print("   This is expected if Backend path is incorrect")
    sys.exit(1)

# Test 3: Import Hub models
print("\nTest 3: Importing Hub models...")
try:
    from models import (
        StreamDestination,
        DestinationType,
        DestinationStatus as HubDestStatus
    )
    print("✅ Hub models imported successfully")
except Exception as e:
    print(f"❌ Failed to import Hub models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Import Backend models
print("\nTest 4: Importing Backend models...")
try:
    from core.egress_v2 import (
        RTMPDestination,
        DestinationStatus as BackendDestStatus
    )
    print("✅ Backend models imported successfully")
except Exception as e:
    print(f"❌ Failed to import Backend models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Create Hub destination
print("\nTest 5: Creating Hub StreamDestination...")
try:
    hub_dest = StreamDestination(
        id="test-youtube",
        name="Test YouTube",
        type=DestinationType.YOUTUBE,
        url="rtmp://a.rtmp.youtube.com/live2",
        stream_key="test-key-12345",
        enabled=True,
        status=HubDestStatus.IDLE
    )
    print("✅ Hub StreamDestination created")
    print(f"   - Name: {hub_dest.name}")
    print(f"   - Type: {hub_dest.type}")
    print(f"   - Status: {hub_dest.status}")
except Exception as e:
    print(f"❌ Failed to create Hub destination: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Convert Hub → Backend
print("\nTest 6: Converting Hub → Backend...")
try:
    backend_dest = ModelAdapter.hub_to_backend_rtmp(hub_dest)
    if backend_dest is None:
        print("❌ Conversion returned None")
        sys.exit(1)
    print("✅ Conversion successful")
    print(f"   - Name: {backend_dest.name}")
    print(f"   - URL: {backend_dest.url}")
    print(f"   - Key: {backend_dest.key}")
    print(f"   - Status: {backend_dest.status}")
except Exception as e:
    print(f"❌ Conversion failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Convert Backend → Hub
print("\nTest 7: Converting Backend → Hub...")
try:
    hub_dest_converted = ModelAdapter.backend_rtmp_to_hub(backend_dest)
    if hub_dest_converted is None:
        print("❌ Conversion returned None")
        sys.exit(1)
    print("✅ Conversion successful")
    print(f"   - Name: {hub_dest_converted.name}")
    print(f"   - Type: {hub_dest_converted.type}")
    print(f"   - Stream Key: {hub_dest_converted.stream_key}")
    print(f"   - Status: {hub_dest_converted.status}")
except Exception as e:
    print(f"❌ Conversion failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 8: Extract health
print("\nTest 8: Extracting health from Backend destination...")
try:
    # Simulate some metrics on backend_dest
    backend_dest.bitrate_kbps = 5000
    backend_dest.dropped_frames = 10
    backend_dest.total_frames = 1000
    backend_dest.drop_percentage = 1.0

    health = ModelAdapter.backend_health_to_hub(backend_dest)
    print("✅ Health extracted successfully")
    print(f"   - Connected: {health.is_connected}")
    print(f"   - Streaming: {health.is_streaming}")
    print(f"   - Bitrate: {health.bitrate_kbps} kbps")
    print(f"   - Dropped frames: {health.dropped_frames}")
    print(f"   - Packet loss: {health.packet_loss_percent}%")
except Exception as e:
    print(f"❌ Health extraction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 9: Round-trip conversion
print("\nTest 9: Round-trip conversion test...")
try:
    # Hub → Backend → Hub
    backend_dest2 = ModelAdapter.hub_to_backend_rtmp(hub_dest)
    hub_dest2 = ModelAdapter.backend_rtmp_to_hub(backend_dest2)

    # Verify key fields match
    assert hub_dest.name == hub_dest2.name, "Name mismatch"
    assert hub_dest.url == hub_dest2.url, "URL mismatch"
    assert hub_dest.stream_key == hub_dest2.stream_key, "Stream key mismatch"

    print("✅ Round-trip conversion successful")
    print("   - All key fields preserved")
except Exception as e:
    print(f"❌ Round-trip conversion failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 10: Batch conversion
print("\nTest 10: Batch conversion test...")
try:
    from adapters.model_adapters import convert_hub_destinations_to_backend

    hub_destinations = [
        StreamDestination(
            id="youtube-en",
            name="YouTube EN",
            type=DestinationType.YOUTUBE,
            url="rtmp://a.rtmp.youtube.com/live2",
            stream_key="key-en",
            enabled=True
        ),
        StreamDestination(
            id="youtube-fr",
            name="YouTube FR",
            type=DestinationType.YOUTUBE,
            url="rtmp://a.rtmp.youtube.com/live2",
            stream_key="key-fr",
            enabled=True
        ),
    ]

    backend_destinations = convert_hub_destinations_to_backend(hub_destinations)

    assert len(backend_destinations) == 2, "Should convert both destinations"
    print("✅ Batch conversion successful")
    print(f"   - Converted {len(backend_destinations)} destinations")
except Exception as e:
    print(f"❌ Batch conversion failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("🎉 ALL TESTS PASSED!")
print("=" * 60)
print()
print("✅ Day 1, Task 2 COMPLETE: Model adapters verified working")
print()
print("Next: Day 1, Task 3 - Update modules to use adapters")
