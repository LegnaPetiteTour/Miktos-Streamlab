#!/usr/bin/env python3
"""
Miktos StreamLab - Hybrid Desktop+Web Application
=================================================

Runs both:
- PySide6 desktop UI (native Qt window)
- FastAPI web server (browser interface)

Both share the same OBSController instance.
"""

import sys
import os
import asyncio
import argparse
import threading
import webbrowser
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables from .env file in project root
project_root = Path(__file__).parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path)

from obs_controller import OBSController  # noqa: E402
import uvicorn  # noqa: E402
from qasync import QEventLoop  # type: ignore[import-untyped]  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

# Import after path setup
from ui.main_window import MainWindow  # noqa: E402


# Global OBS controller instance (shared between desktop UI and web API)
obs_controller: Optional[OBSController] = None


async def connect_to_obs(
    host: str = "localhost", port: int = 4455, password: str = ""
) -> OBSController:
    """
    Connect to OBS Studio.

    Args:
        host: OBS WebSocket host
        port: OBS WebSocket port
        password: OBS WebSocket password

    Returns:
        Connected OBSController instance
    """
    global obs_controller

    print(f"🎬 Connecting to OBS at {host}:{port}...")
    print(f"   Password provided: {'Yes' if password else 'No'}")
    if password:
        print(f"   Password length: {len(password)} characters")

    obs = OBSController(host=host, port=port, password=password)

    try:
        success = await obs.connect()
        if success:
            print("✅ Connected to OBS Studio")
            obs_controller = obs
            return obs
        else:
            print("⚠️  Could not connect to OBS Studio")
            print("   Make sure OBS is running with WebSocket server enabled")
            print("   (Tools → WebSocket Server Settings)")
            obs_controller = obs  # Store even if disconnected
            return obs
    except Exception as e:
        print(f"❌ Error connecting to OBS: {e}")
        obs_controller = obs
        return obs


def run_fastapi_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """
    Run FastAPI server in a background thread.

    Args:
        host: Server host
        port: Server port
    """
    # Import here to ensure obs_controller is set
    from api import server

    # Share the OBS controller with the API server
    server.set_obs_controller(obs_controller)

    # Share OBS controller with FastAPI
    server.obs_controller = obs_controller

    print(f"🚀 Starting FastAPI server at http://{host}:{port}")

    # Run server
    uvicorn.run(server.app, host=host, port=port, log_level="info")


async def run_desktop_ui(obs: OBSController) -> int:
    """
    Run PySide6 desktop UI with asyncio event loop.

    Args:
        obs: OBSController instance

    Returns:
        Application exit code
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Apply dark theme
    if isinstance(app, QApplication):
        app.setStyle("Fusion")

    # Create main window
    window = MainWindow(obs=obs)
    window.show()

    print("🖥️  Desktop UI started")
    print("   Press Ctrl+C or close window to exit")

    # Keep running until window closes
    try:
        while not window.isHidden():
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        pass

    return 0


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Miktos StreamLab - Hybrid Desktop+Web Application"
    )
    parser.add_argument(
        "--obs-host",
        default="localhost",
        help="OBS WebSocket host (default: localhost)",
    )
    parser.add_argument(
        "--obs-port",
        type=int,
        default=4455,
        help="OBS WebSocket port (default: 4455)",
    )
    parser.add_argument(
        "--obs-password",
        default="",
        help="OBS WebSocket password (default: none)",
    )
    parser.add_argument(
        "--api-host",
        default="0.0.0.0",
        help="FastAPI server host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="FastAPI server port (default: 8000)",
    )
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Run web server only (no desktop UI)",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Run desktop UI only (no web server)",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open web dashboard in browser",
    )

    args = parser.parse_args()

    # Use environment variable as fallback for OBS password
    obs_password = (
        args.obs_password if args.obs_password else os.getenv("OBS_PASSWORD", "")
    )

    print("=" * 60)
    print("🎥 Miktos StreamLab - Professional streaming Broadcasting")
    print("=" * 60)
    print(f"🔑 OBS Password loaded: {'Yes' if obs_password else 'No'}")
    if obs_password:
        print(f"    (Password length: {len(obs_password)} characters)")

    # Create Qt application for event loop
    app = QApplication(sys.argv)

    # Setup qasync event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    async def async_main() -> int:
        # Connect to OBS
        obs = await connect_to_obs(
            host=args.obs_host, port=args.obs_port, password=obs_password
        )

        # Start FastAPI server in background thread (unless --no-api)
        if not args.no_api:
            api_thread = threading.Thread(
                target=run_fastapi_server,
                args=(args.api_host, args.api_port),
                daemon=True,
            )
            api_thread.start()

            # Open browser if requested
            if args.open_browser:
                print(f"🌐 Opening browser to http://localhost:{args.api_port}")
                webbrowser.open(f"http://localhost:{args.api_port}")

        # Run desktop UI (unless --web-only)
        if not args.web_only:
            exit_code = await run_desktop_ui(obs)
            return exit_code
        else:
            # Web-only mode: just keep running
            print("🌐 Web-only mode: Server running")
            print(f"   Open http://localhost:{args.api_port} in your browser")
            print("   Press Ctrl+C to exit")

            # Keep alive
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Shutting down...")
                return 0

    # Run async main
    try:
        with loop:
            exit_code = loop.run_until_complete(async_main())
            sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
