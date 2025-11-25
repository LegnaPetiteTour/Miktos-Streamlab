#!/usr/bin/env python3
"""
End-to-End Workflow Test for Sony a7 IV
========================================

This script tests the complete workflow:
1. Connect to Sony a7 IV camera
2. Create a live session
3. Configure OBS scenes
4. Set up streaming destinations
5. Verify the full production workflow

Prerequisites:
- Sony a7 IV connected via USB or network (with Imaging Edge Mobile app)
- OBS Studio installed and running
- Streaming destinations configured (YouTube, Twitch, etc.)
"""

import requests
import time
from typing import Optional

# API Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"


class Colors:
    """Terminal colors for better output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_step(step: str, message: str) -> None:
    """Print formatted step message"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}[{step}]{Colors.END} {message}")


def print_success(message: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_warning(message: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_info(message: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")


class E2ETest:
    """End-to-End workflow test"""

    def __init__(self) -> None:
        self.session_id: Optional[str] = None
        self.camera_id: Optional[str] = None
        self.scene_ids: list[str] = []
        self.destination_ids: list[str] = []

    def check_server_health(self) -> bool:
        """Check if the API server is running"""
        print_step("STEP 1", "Checking server health...")
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print_success(f"Server is running: {health.get('status')}")
                version = health.get('version', 'unknown')
                print_info(f"Server version: {version}")
                return True
            else:
                print_error(f"Server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print_error("Cannot connect to server at http://localhost:8000")
            print_info("Start the server with: python main.py")
            return False
        except Exception as e:
            print_error(f"Health check failed: {e}")
            return False

    def discover_sony_camera(self) -> Optional[str]:
        """
        Discover Sony a7 IV camera.

        Sony cameras can be discovered via:
        - USB connection (appears as USB device)
        - Network (via Imaging Edge Mobile app)
        - RTSP stream (if configured)
        """
        print_step("STEP 2", "Discovering Sony a7 IV camera...")

        # First, check if any cameras are already registered
        try:
            response = requests.get(f"{API_BASE}/cameras/")
            if response.status_code == 200:
                cameras = response.json()
                if cameras:
                    print_info(f"Found {len(cameras)} registered camera(s)")
                    for cam in cameras:
                        print(f"  - {cam['name']} ({cam['camera_id'][:8]}...)")
                        name_lower = cam['name'].lower()
                        if 'sony' in name_lower or 'a7' in name_lower:
                            self.camera_id = cam['camera_id']
                            cam_name = cam['name']
                            print_success(
                                f"Using existing Sony camera: {cam_name}"
                            )
                            return self.camera_id
        except Exception as e:
            print_warning(f"Could not fetch cameras: {e}")

        # Manual camera setup note
        print_warning("No Sony camera found.")
        print_info("\n" + "="*60)
        print_info("CAMERA SETUP REQUIRED")
        print_info("="*60)
        print_info("\nTo use your Sony a7 IV via USB:")
        print_info("1. Download Sony Imaging Edge Webcam:")
        print_info("   https://support.d-imaging.sony.co.jp/app/webcam/en/")
        print_info("2. Install and launch the software")
        print_info("3. Enable 'USB Streaming' in camera menu:")
        print_info("   Network → USB Connection → USB Streaming: ON")
        print_info("4. Restart your camera")
        print_info("5. Camera will appear as 'Imaging Edge Webcam'")
        print_info("\nAlternatively, connect via:")
        print_info("  - HDMI capture card (best quality)")
        print_info("  - Network via Imaging Edge Mobile app")
        print_info("\n" + "="*60)

        print_info("\nFor now, creating a test/placeholder camera...")

        # Create a placeholder camera ID for testing
        import uuid
        self.camera_id = f"sony-a7iv-{str(uuid.uuid4())[:8]}"
        print_success(f"Test camera ID created: {self.camera_id[:24]}...")
        print_warning(
            "Note: This is a placeholder. "
            "Real camera functionality requires hardware setup."
        )
        return self.camera_id

    def create_session(self) -> Optional[str]:
        """Create a new streaming session"""
        print_step("STEP 3", "Creating streaming session...")

        session_data = {
            "name": "Sony a7 IV Test Session",
            "description": "E2E workflow test with Sony a7 IV camera",
            "camera_ids": [self.camera_id] if self.camera_id else []
        }

        try:
            response = requests.post(
                f"{API_BASE}/sessions/",
                json=session_data
            )
            if response.status_code == 200:
                session = response.json()
                self.session_id = session['session_id']
                print_success(f"Session created: {session['name']}")
                if self.session_id:
                    print_info(f"Session ID: {self.session_id[:16]}...")
                print_info(f"State: {session['state']}")
                return self.session_id
            else:
                print_error(f"Failed to create session: {response.text}")
                return None
        except Exception as e:
            print_error(f"Error creating session: {e}")
            return None

    def configure_obs_scenes(self) -> bool:
        """Configure OBS scenes for the session"""
        print_step("STEP 4", "Configuring OBS scenes...")

        if not self.session_id:
            print_error("No session ID available")
            return False

        # Check OBS status first
        try:
            response = requests.get(f"{API_BASE}/obs/status")
            if response.status_code == 200:
                obs_status = response.json()
                if not obs_status.get('connected'):
                    print_warning("OBS is not connected")
                    print_info(
                        "Make sure OBS Studio is running "
                        "with WebSocket enabled"
                    )
                    print_info("In OBS: Tools → WebSocket Server Settings")
                    return False
                print_success(f"OBS connected: {obs_status.get('version')}")
            else:
                print_warning("Could not check OBS status")
        except Exception as e:
            print_warning(f"OBS status check failed: {e}")

        # Create scenes
        scenes_to_create = [
            {
                "name": "Full Frame",
                "layout": "fullscreen",
                "sources": [
                    {
                        "type": "camera",
                        "camera_id": self.camera_id,
                        "position": {
                            "x": 0,
                            "y": 0,
                            "width": 1920,
                            "height": 1080
                        }
                    }
                ]
            },
            {
                "name": "Picture in Picture",
                "layout": "pip",
                "sources": [
                    {
                        "type": "camera",
                        "camera_id": self.camera_id,
                        "position": {
                            "x": 100,
                            "y": 100,
                            "width": 640,
                            "height": 360
                        }
                    }
                ]
            }
        ]

        for scene_config in scenes_to_create:
            try:
                scene_config['session_id'] = self.session_id
                response = requests.post(
                    f"{API_BASE}/scenes/",
                    json=scene_config
                )
                if response.status_code == 200:
                    scene = response.json()
                    self.scene_ids.append(scene['scene_id'])
                    print_success(f"Created scene: {scene['name']}")
                else:
                    scene_name = scene_config['name']
                    print_warning(
                        f"Could not create scene '{scene_name}': "
                        f"{response.text}"
                    )
            except Exception as e:
                print_warning(f"Error creating scene: {e}")

        return len(self.scene_ids) > 0

    def setup_streaming_destinations(self) -> bool:
        """Set up streaming destinations"""
        print_step("STEP 5", "Setting up streaming destinations...")

        if not self.session_id:
            print_error("No session ID available")
            return False

        print_info("\nConfigure streaming destinations:")
        print("  1. YouTube")
        print("  2. Twitch")
        print("  3. Facebook Live")
        print("  4. Custom RTMP")
        print("  5. Skip this step")

        choice = input("\nSelect destination (1-5): ").strip()

        if choice == "5":
            print_info("Skipping destination setup")
            return True

        destination_data = {
            "session_id": self.session_id,
            "platform": "",
            "url": "",
            "stream_key": ""
        }

        if choice == "1":
            destination_data["name"] = "YouTube Stream"
            destination_data["platform"] = "youtube"
            destination_data["url"] = "rtmp://a.rtmp.youtube.com/live2"
            stream_key = input("Enter YouTube stream key: ").strip()
            destination_data["stream_key"] = stream_key

        elif choice == "2":
            destination_data["name"] = "Twitch Stream"
            destination_data["platform"] = "twitch"
            destination_data["url"] = "rtmp://live.twitch.tv/app"
            stream_key = input("Enter Twitch stream key: ").strip()
            destination_data["stream_key"] = stream_key

        elif choice == "3":
            destination_data["name"] = "Facebook Live"
            destination_data["platform"] = "facebook"
            url = input("Enter Facebook RTMP URL: ").strip()
            stream_key = input("Enter Facebook stream key: ").strip()
            destination_data["url"] = url
            destination_data["stream_key"] = stream_key

        elif choice == "4":
            destination_data["name"] = "Custom RTMP"
            destination_data["platform"] = "custom"
            url = input("Enter RTMP URL: ").strip()
            stream_key = input("Enter stream key (if required): ").strip()
            destination_data["url"] = url
            if stream_key:
                destination_data["stream_key"] = stream_key
        else:
            print_error("Invalid selection")
            return False

        # Create the destination
        try:
            response = requests.post(
                f"{API_BASE}/streaming/destinations",
                json=destination_data
            )
            if response.status_code == 200:
                dest = response.json()
                self.destination_ids.append(dest['destination_id'])
                print_success(f"Destination configured: {dest['name']}")
                return True
            else:
                print_error(f"Failed to create destination: {response.text}")
                return False
        except Exception as e:
            print_error(f"Error creating destination: {e}")
            return False

    def test_workflow(self) -> bool:
        """Test the complete workflow"""
        print_step("STEP 6", "Testing workflow...")

        if not self.session_id:
            print_error("No session available for testing")
            return False

        # Get session details
        try:
            response = requests.get(f"{API_BASE}/sessions/{self.session_id}")
            if response.status_code == 200:
                session = response.json()
                print_success("Session retrieved successfully")
                print_info(f"Session: {session['name']}")
                print_info(f"State: {session['state']}")
                camera_count = len(session.get('camera_ids', []))
                print_info(f"Cameras: {camera_count}")
                scene_count = len(session.get('scene_ids', []))
                print_info(f"Scenes: {scene_count}")
                dest_count = len(session.get('destination_ids', []))
                print_info(f"Destinations: {dest_count}")
            else:
                print_warning(f"Could not retrieve session: {response.text}")
        except Exception as e:
            print_warning(f"Error retrieving session: {e}")

        # Test scene switching (if scenes exist)
        if self.scene_ids:
            print_info("\nTesting scene switching...")
            for scene_id in self.scene_ids:
                try:
                    response = requests.post(
                        f"{API_BASE}/scenes/{scene_id}/activate"
                    )
                    if response.status_code == 200:
                        print_success(f"Activated scene: {scene_id[:8]}...")
                        time.sleep(1)  # Brief pause between switches
                except Exception as e:
                    print_warning(f"Scene activation failed: {e}")

        return True

    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.HEADER}TEST SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}\n")

        if self.session_id:
            print_success(f"Session ID: {self.session_id}")
        else:
            print_error("No session created")

        if self.camera_id:
            print_success(f"Camera ID: {self.camera_id}")
        else:
            print_error("No camera registered")

        if self.scene_ids:
            print_success(f"Scenes created: {len(self.scene_ids)}")
        else:
            print_warning("No scenes created")

        if self.destination_ids:
            dest_count = len(self.destination_ids)
            print_success(f"Destinations configured: {dest_count}")
        else:
            print_warning("No destinations configured")

        print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
        session_url = f"{BASE_URL}/sessions/{self.session_id}"
        print(f"  1. View session in browser: {session_url}")
        print(f"  2. API documentation: {BASE_URL}/docs")
        print("  3. Start streaming via API or OBS")

        print(f"\n{Colors.BOLD}Cleanup:{Colors.END}")
        delete_cmd = (
            f"  Delete session: curl -X DELETE "
            f"{API_BASE}/sessions/{self.session_id}"
        )
        print(delete_cmd)

    def run(self):
        """Run the complete E2E test"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}")
        title = "Sony a7 IV End-to-End Workflow Test"
        print(f"{Colors.BOLD}{Colors.HEADER}{title}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}\n")

        # Step 1: Check server
        if not self.check_server_health():
            print_error("\nTest aborted: Server is not running")
            return False

        # Step 2: Discover camera
        if not self.discover_sony_camera():
            print_error("\nTest aborted: Could not discover/register camera")
            return False

        # Step 3: Create session
        if not self.create_session():
            print_error("\nTest aborted: Could not create session")
            return False

        # Step 4: Configure OBS scenes
        self.configure_obs_scenes()  # Non-critical, continue even if fails

        # Step 5: Setup destinations
        self.setup_streaming_destinations()  # Non-critical

        # Step 6: Test workflow
        self.test_workflow()

        # Print summary
        self.print_summary()

        complete_msg = f"{Colors.GREEN}{Colors.BOLD}✅ E2E Test Complete!"
        print(f"\n{complete_msg}{Colors.END}\n")
        return True


if __name__ == "__main__":
    test = E2ETest()
    try:
        test.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
