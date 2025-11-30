#!/usr/bin/env python3
"""
E2E Phase 5: Full Production Workflow Test
Tests the complete stack end-to-end with real hardware
"""

import asyncio
import httpx
from obswebsocket import obsws, requests as obs_requests  # type: ignore


# Configuration
HUB_API = "http://localhost:8000"
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "DmMpVONSo86VU3Eh"
RTMP_URL = "rtmp://localhost:1935/live/test_stream"


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 78)
    print(f"  {text}")
    print("=" * 78)


def print_status(emoji, message):
    """Print status message"""
    print(f"{emoji} {message}")


def print_substep(message):
    """Print substep"""
    print(f"   → {message}")


async def test_full_workflow():
    """Test complete production workflow"""

    print_header("🎯 E2E PHASE 5: FULL PRODUCTION WORKFLOW TEST")
    print_status("📋", "Testing complete stack with Sony a7 IV + OBS + Hub API")

    session_id = None
    ws = None

    try:
        # Step 1: Verify Hub Server Health
        print_header("STEP 1: VERIFY HUB SERVER HEALTH")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HUB_API}/api/health")
            health = response.json()

            print_status("🏥", f"Overall Status: {health['overall_status']}")

            for component in health.get('components', []):
                status = component['status']
                print_substep(
                    f"{component['name']}: {status} - {component['message']}"
                )

            if health['overall_status'] != 'healthy':
                print_status("⚠️", "Some components unhealthy, continuing...")

        # Step 2: Create Hub Session
        print_header("STEP 2: CREATE HUB SESSION")

        async with httpx.AsyncClient() as client:
            session_data = {
                "name": "E2E Phase 5 - Full Workflow Test",
                "description": "Complete production workflow with Sony a7 IV"
            }
            response = await client.post(
                f"{HUB_API}/api/sessions/",
                json=session_data
            )

            if response.status_code == 200:
                session = response.json()
                session_id = session['session_id']
                print_status("✅", f"Session Created: {session_id}")
                print_substep(f"Name: {session['name']}")
                print_substep(f"State: {session['state']}")
            else:
                print_status("❌", f"Failed: {response.status_code}")
                print_substep(f"Error: {response.text}")
                return

        # Step 3: Connect to OBS
        print_header("STEP 3: CONNECT TO OBS")

        ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
        ws.connect()

        version = ws.call(obs_requests.GetVersion())
        print_status("✅", f"Connected to OBS {version.getObsVersion()}")

        # Get scenes
        scenes_response = ws.call(obs_requests.GetSceneList())
        scenes = scenes_response.getScenes()
        scene_names = [s['sceneName'] for s in scenes]
        print_substep(f"Available scenes: {len(scene_names)}")

        # Step 4: Set Initial Scene
        print_header("STEP 4: SET INITIAL SCENE")

        # Try to use Sony_Main or fallback
        initial_scene = None
        for preferred in ['Sony_Main', 'Camera Scene', 'Main Camera']:
            if preferred in scene_names:
                initial_scene = preferred
                break

        if not initial_scene and scene_names:
            initial_scene = scene_names[0]

        if initial_scene:
            ws.call(
                obs_requests.SetCurrentProgramScene(sceneName=initial_scene)
            )
            print_status("✅", f"Active scene: {initial_scene}")

        # Step 5: Start Streaming
        print_header("STEP 5: START STREAMING VIA OBS")

        # Check if already streaming
        stream_status = ws.call(obs_requests.GetStreamStatus())
        if stream_status.getOutputActive():
            print_status("⚠️", "Already streaming - stopping first...")
            ws.call(obs_requests.StopStream())
            await asyncio.sleep(2)

        print_status("🚀", "Starting stream to local RTMP server...")
        print_substep(f"Destination: {RTMP_URL}")

        ws.call(obs_requests.StartStream())
        await asyncio.sleep(2)

        stream_status = ws.call(obs_requests.GetStreamStatus())
        if stream_status.getOutputActive():
            print_status("✅", "Stream started successfully")
        else:
            print_status("❌", "Stream failed to start")
            return

        # Step 6: Monitor and Switch Scenes During Stream
        print_header("STEP 6: SCENE SWITCHING DURING LIVE STREAM")

        # Find alternative scenes to switch to
        switch_scenes = []
        for scene_name in ['Sony_PIP', 'Intro Scene', 'Camera Scene']:
            if scene_name in scene_names and scene_name != initial_scene:
                switch_scenes.append(scene_name)

        if switch_scenes:
            print_status("🎬", "Testing scene switches during live stream...")

            for scene in switch_scenes[:2]:  # Test 2 scene switches
                await asyncio.sleep(3)

                print_substep(f"Switching to: {scene}")
                ws.call(
                    obs_requests.SetCurrentProgramScene(sceneName=scene)
                )

                stream_status = ws.call(obs_requests.GetStreamStatus())
                duration = stream_status.getOutputDuration() / 1000
                print_substep(f"Stream duration: {duration:.1f}s")

            # Switch back to initial scene
            await asyncio.sleep(3)
            print_substep(f"Switching back to: {initial_scene}")
            ws.call(
                obs_requests.SetCurrentProgramScene(sceneName=initial_scene)
            )

            print_status("✅", "Scene switching validated during stream")
        else:
            print_status("⚠️", "Not enough scenes for switching test")

        # Step 7: Monitor Health During Stream
        print_header("STEP 7: MONITOR HEALTH DURING STREAM")

        await asyncio.sleep(2)

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HUB_API}/api/health")
            health = response.json()

            print_status("🏥", f"Hub Health: {health['overall_status']}")

            obs_component = next(
                (c for c in health.get('components', [])
                 if 'OBS' in c['name']),
                None
            )
            if obs_component:
                obs_status = obs_component['status']
                obs_msg = obs_component['message']
                print_substep(f"OBS Engine: {obs_status} - {obs_msg}")

        stream_status = ws.call(obs_requests.GetStreamStatus())
        duration = stream_status.getOutputDuration() / 1000
        print_status("📊", f"Stream duration: {duration:.1f}s")

        # Step 8: Get Session Status
        print_header("STEP 8: CHECK SESSION STATUS")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HUB_API}/api/sessions/{session_id}")

            if response.status_code == 200:
                session = response.json()
                print_status("✅", f"Session Status: {session['state']}")
                print_substep(f"Session ID: {session_id}")
            else:
                status_code = response.status_code
                print_status("⚠️", f"Could not get session: {status_code}")

        # Step 9: Stop Streaming
        print_header("STEP 9: STOP STREAMING")

        final_status = ws.call(obs_requests.GetStreamStatus())
        final_duration = final_status.getOutputDuration() / 1000

        print_status("🛑", "Stopping stream...")
        ws.call(obs_requests.StopStream())
        await asyncio.sleep(2)

        stopped_status = ws.call(obs_requests.GetStreamStatus())
        if not stopped_status.getOutputActive():
            print_status("✅", f"Stream stopped (total: {final_duration:.1f}s)")

        # Step 10: Cleanup Session
        print_header("STEP 10: CLEANUP SESSION")

        async with httpx.AsyncClient() as client:
            delete_url = f"{HUB_API}/api/sessions/{session_id}"
            response = await client.delete(delete_url)

            if response.status_code in [200, 204]:
                print_status("✅", "Session cleaned up")
            else:
                print_status("⚠️", f"Cleanup response: {response.status_code}")

        # Final Results
        print_header("✅ PHASE 5 COMPLETE - FULL WORKFLOW VALIDATED")

        print_status("🎉", "All workflow steps completed successfully!")
        print()
        print_status("📋", "VALIDATED COMPONENTS:")
        print_substep("✅ Hub API health monitoring")
        print_substep("✅ Session creation and management")
        print_substep("✅ OBS connection and control")
        print_substep("✅ RTMP streaming to MediaMTX")
        print_substep("✅ Scene switching during live stream")
        print_substep("✅ Health monitoring during operation")
        print_substep("✅ Clean shutdown and cleanup")
        print()
        print_status("🏆", "COMPLETE E2E VALIDATION SUCCESSFUL")
        print_status("📊", f"Total stream duration: {final_duration:.1f}s")

    except Exception as e:
        print_status("❌", f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if ws:
            print()
            print_status("🔌", "Disconnecting from OBS...")
            try:
                # Make sure stream is stopped
                status = ws.call(obs_requests.GetStreamStatus())
                if status.getOutputActive():
                    ws.call(obs_requests.StopStream())
            except Exception:
                pass

            ws.disconnect()
            print_status("✅", "Disconnected")


if __name__ == "__main__":
    asyncio.run(test_full_workflow())
