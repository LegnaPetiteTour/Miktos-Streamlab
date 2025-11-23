#!/usr/bin/env python3
"""
Multi-Camera H.264 Stream Receiver

Receives H.264 streams from multiple phone cameras simultaneously.
Features:
- Accept multiple camera connections on different ports
- Detect PAUSE state (frame rate < 2 fps)
- Display live preview for active camera
- Show freeze frame or slate for paused cameras
- Support camera switching
"""

import socket
from socket import socket as Socket
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class CameraState(Enum):
    """Camera streaming state"""
    DISCONNECTED = "disconnected"
    LIVE = "live"
    PAUSED = "paused"


@dataclass
class CameraStream:
    """Individual camera stream info"""
    camera_id: str
    port: int
    socket: Optional[Socket] = None
    client_socket: Optional[Socket] = None
    thread: Optional[threading.Thread] = None
    state: CameraState = CameraState.DISCONNECTED
    bytes_received: int = 0
    frame_count: int = 0
    current_fps: float = 0.0
    last_frame_time: float = 0.0
    start_time: float = 0.0
    ffplay_process: Optional[subprocess.Popen] = None


class MultiCameraReceiver:
    """Multi-camera H.264 stream receiver"""

    def __init__(self, base_port: int = 8554, num_cameras: int = 3):
        """
        Initialize multi-camera receiver

        Args:
            base_port: Starting port (cameras will use base_port,
                       base_port+1, etc.)
            num_cameras: Number of camera slots to create
        """
        self.base_port = base_port
        self.num_cameras = num_cameras
        self.cameras: Dict[int, CameraStream] = {}
        self.active_camera_port: Optional[int] = None
        self.running = True

        print("\n" + "="*70)
        print("📹 StreamLab Multi-Camera Receiver")
        print("="*70)
        print(f"\nInitializing {num_cameras} camera slots:")

        for i in range(num_cameras):
            port = base_port + i
            camera_id = f"Camera {i+1}"
            self.cameras[port] = CameraStream(
                camera_id=camera_id,
                port=port
            )
            print(f"  • {camera_id}: Port {port}")

        print("\n✅ Ready to accept connections")
        print("📱 Configure phones to stream to:")
        print("   Server IP: <this-machine-ip>")
        print(
            f"   Ports: {base_port} - {base_port + num_cameras - 1}\n"
        )

    def start(self):
        """Start listening on all camera ports"""
        threads = []

        for port, camera in self.cameras.items():
            thread = threading.Thread(
                target=self._listen_on_port,
                args=(port,),
                daemon=True
            )
            thread.start()
            threads.append(thread)

        print("🎬 All receivers started - waiting for connections...")
        print("   Press Ctrl+C to stop\n")

        try:
            # Monitor status
            while self.running:
                time.sleep(5)
                self._print_status()
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping receivers...")
            self.running = False

            for port, camera in self.cameras.items():
                if camera.ffplay_process:
                    camera.ffplay_process.terminate()
                if camera.client_socket:
                    camera.client_socket.close()
                if camera.socket:
                    camera.socket.close()

            print("👋 Goodbye!\n")

    def _listen_on_port(self, port: int):
        """Listen for connections on a specific port"""
        camera = self.cameras[port]

        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind(('0.0.0.0', port))
            server_socket.listen(1)
            camera.socket = server_socket

            while self.running:
                try:
                    server_socket.settimeout(1.0)
                    client_socket, client_address = server_socket.accept()

                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    print(
                        f"\n[{timestamp}] 🔗 {camera.camera_id} "
                        f"connected from {client_address}"
                    )

                    camera.client_socket = client_socket
                    camera.state = CameraState.LIVE
                    camera.start_time = time.time()
                    camera.bytes_received = 0
                    camera.frame_count = 0

                    # Start ffplay for preview if first/active camera
                    if self.active_camera_port is None:
                        self.active_camera_port = port
                        camera.ffplay_process = self._start_preview(
                            camera.camera_id
                        )

                    # Receive data
                    self._receive_data(port)

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(
                            f"❌ {camera.camera_id} error: {e}"
                        )

        finally:
            server_socket.close()

    def _start_preview(
        self, camera_id: str
    ) -> Optional[subprocess.Popen]:
        """Start ffplay preview window"""
        try:
            process = subprocess.Popen(
                [
                    'ffplay',
                    '-f', 'h264',
                    '-probesize', '32',
                    '-analyzeduration', '0',
                    '-fflags', 'nobuffer',
                    '-flags', 'low_delay',
                    '-framedrop',
                    '-window_title', f'StreamLab - {camera_id}',
                    '-i', 'pipe:0'
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return process
        except Exception as e:
            print(
                f"⚠️  Could not start preview for {camera_id}: {e}"
            )
            return None

    def _receive_data(self, port: int):
        """Receive and process H.264 stream data"""
        camera = self.cameras[port]
        client_socket = camera.client_socket

        if not client_socket:
            return

        buffer_size = 4096
        last_receive_time = time.time()
        last_frame_time = time.time()
        frame_count = 0
        current_fps = 0.0

        # 30 second timeout for PAUSE mode compatibility
        client_socket.settimeout(30.0)

        try:
            while self.running and client_socket:
                try:
                    data = client_socket.recv(buffer_size)
                    current_time = time.time()

                    if not data:
                        elapsed = current_time - last_receive_time
                        timestamp = (
                            datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        )
                        print(
                            f"\n[{timestamp}] ❌ {camera.camera_id} "
                            f"disconnected (no data) - last data "
                            f"{elapsed:.1f}s ago"
                        )
                        break

                    camera.bytes_received += len(data)
                    last_receive_time = current_time

                    # Send to ffplay if active camera
                    if (port == self.active_camera_port and
                            camera.ffplay_process and
                            camera.ffplay_process.stdin):
                        try:
                            camera.ffplay_process.stdin.write(data)
                            camera.ffplay_process.stdin.flush()
                        except BrokenPipeError:
                            print(
                                f"⚠️  {camera.camera_id} preview "
                                "window closed"
                            )
                            camera.ffplay_process = None

                    # Detect frames for FPS calculation
                    if data.startswith(b'\x00\x00\x00\x01'):
                        frame_count += 1
                        frame_time_delta = current_time - last_frame_time
                        last_frame_time = current_time
                        current_fps = (
                            1.0 / frame_time_delta
                            if frame_time_delta > 0
                            else 0
                        )

                        camera.frame_count = frame_count
                        camera.current_fps = current_fps
                        camera.last_frame_time = current_time

                        # Detect frame type
                        frame_type = "Unknown"
                        if len(data) > 4:
                            nalu_type = data[4] & 0x1F
                            if nalu_type == 5:
                                frame_type = "I-Frame (keyframe)"
                            elif nalu_type == 1:
                                frame_type = "P-Frame"
                            elif nalu_type == 7:
                                frame_type = "SPS"
                            elif nalu_type == 8:
                                frame_type = "PPS"

                        # Detect PAUSE mode (frame rate < 2 fps)
                        if current_fps < 2:
                            if camera.state != CameraState.PAUSED:
                                camera.state = CameraState.PAUSED
                                timestamp = (
                                    datetime.now().strftime(
                                        '%H:%M:%S.%f'
                                    )[:-3]
                                )
                                print(
                                    f"\n[{timestamp}] ⏸️  "
                                    f"{camera.camera_id} PAUSED "
                                    f"(freeze frame mode - "
                                    f"{current_fps:.1f} fps)"
                                )
                        else:
                            if camera.state == CameraState.PAUSED:
                                camera.state = CameraState.LIVE
                                timestamp = (
                                    datetime.now().strftime(
                                        '%H:%M:%S.%f'
                                    )[:-3]
                                )
                                print(
                                    f"\n[{timestamp}] ▶️  "
                                    f"{camera.camera_id} RESUMED "
                                    f"(live mode - {current_fps:.1f} fps)"
                                )

                        # Log frame (every 30th frame or if paused)
                        if frame_count % 30 == 0 or current_fps < 2:
                            mode_indicator = (
                                "🟡 PAUSED" if current_fps < 2
                                else "🟢 LIVE"
                            )

                            elapsed = current_time - camera.start_time
                            avg_fps = (
                                frame_count / elapsed if elapsed > 0
                                else 0
                            )
                            mbps = (
                                (camera.bytes_received * 8) /
                                (elapsed * 1_000_000)
                                if elapsed > 0 else 0
                            )

                            timestamp = (
                                datetime.now().strftime(
                                    '%H:%M:%S.%f'
                                )[:-3]
                            )
                            print(
                                f"🎬 [{timestamp}] "
                                f"{camera.camera_id} | "
                                f"{mode_indicator} | "
                                f"{frame_type} | "
                                f"Frame #{frame_count} | "
                                f"Current: {current_fps:.1f} fps | "
                                f"Avg: {avg_fps:.1f} fps | "
                                f"Delta: {frame_time_delta:.3f}s | "
                                f"Size: {len(data)} bytes | "
                                f"Bitrate: {mbps:.2f} Mbps"
                            )

                except socket.timeout:
                    # Check for timeout
                    elapsed_since_data = time.time() - last_receive_time
                    if elapsed_since_data > 25:
                        timestamp = (
                            datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        )
                        print(
                            f"\n[{timestamp}] ⏰ "
                            f"{camera.camera_id} Timeout: No data for "
                            f"{elapsed_since_data:.1f}s - "
                            "client disconnected or stopped"
                        )
                        break
                    continue

                except socket.error as e:
                    timestamp = (
                        datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    )
                    print(
                        f"\n[{timestamp}] ❌ {camera.camera_id} "
                        f"receive error: {e}"
                    )
                    break

        finally:
            # Cleanup
            camera.state = CameraState.DISCONNECTED
            if camera.client_socket:
                camera.client_socket.close()
                camera.client_socket = None

            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(
                f"\n[{timestamp}] 📊 {camera.camera_id} "
                "session ended"
            )
            print(f"   Frames: {frame_count}")
            print(
                f"   Data: "
                f"{camera.bytes_received / 1_000_000:.2f} MB"
            )

            if camera.start_time > 0:
                duration = time.time() - camera.start_time
                print(f"   Duration: {duration:.1f}s")

    def _print_status(self):
        """Print current status of all cameras"""
        print("\n" + "─"*70)
        print("📊 Camera Status:")

        for port, camera in self.cameras.items():
            state_icon = {
                CameraState.DISCONNECTED: "⚪",
                CameraState.LIVE: "🟢",
                CameraState.PAUSED: "🟡"
            }.get(camera.state, "⚪")

            active_marker = (
                "⭐" if port == self.active_camera_port else "  "
            )

            if camera.state != CameraState.DISCONNECTED:
                uptime = (
                    time.time() - camera.start_time
                    if camera.start_time > 0 else 0
                )
                mbps = (
                    (camera.bytes_received * 8) / (uptime * 1_000_000)
                    if uptime > 0 else 0
                )

                print(
                    f"{active_marker} {state_icon} "
                    f"{camera.camera_id} (Port {port}): "
                    f"{camera.state.value.upper()} | "
                    f"FPS: {camera.current_fps:.1f} | "
                    f"Frames: {camera.frame_count} | "
                    f"Bitrate: {mbps:.2f} Mbps | "
                    f"Uptime: {uptime:.0f}s"
                )
            else:
                print(
                    f"{active_marker} {state_icon} "
                    f"{camera.camera_id} (Port {port}): "
                    "Waiting for connection..."
                )

        print("─"*70)

    def switch_active_camera(self, port: int):
        """Switch active camera preview"""
        if port not in self.cameras:
            print(f"❌ Invalid camera port: {port}")
            return

        if port == self.active_camera_port:
            print(
                f"ℹ️  {self.cameras[port].camera_id} is already active"
            )
            return

        # Close old preview
        if self.active_camera_port:
            old_camera = self.cameras[self.active_camera_port]
            if old_camera.ffplay_process:
                old_camera.ffplay_process.terminate()
                old_camera.ffplay_process = None

        # Start new preview
        self.active_camera_port = port
        camera = self.cameras[port]

        if camera.state != CameraState.DISCONNECTED:
            camera.ffplay_process = self._start_preview(camera.camera_id)
            print(f"✨ Switched to {camera.camera_id}")
        else:
            print(f"⚠️  {camera.camera_id} is not connected")


def main():
    """Main entry point"""
    import sys

    # Parse arguments
    base_port = 8554
    num_cameras = 3

    if len(sys.argv) > 1:
        try:
            base_port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            num_cameras = int(sys.argv[2])
        except ValueError:
            print(f"Invalid camera count: {sys.argv[2]}")
            sys.exit(1)

    receiver = MultiCameraReceiver(
        base_port=base_port, num_cameras=num_cameras
    )
    receiver.start()


if __name__ == "__main__":
    main()
