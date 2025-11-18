#!/usr/bin/env python3
"""
TCP H.264 Receiver with Live Preview using ffplay
Receives H.264 stream from Android StreamLab Camera app and displays it
"""

import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
import signal


class TCPReceiverWithPreview:
    def __init__(self, host='0.0.0.0', port=8554, show_preview=True):
        self.host = host
        self.port = port
        self.show_preview = show_preview
        self.socket = None
        self.client_socket = None
        self.running = False
        self.bytes_received = 0
        self.start_time = None
        self.ffplay_process = None

    def start(self):
        """Start the TCP receiver"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)

            print("🎥 TCP H.264 Receiver with Live Preview")
            print(f"📡 Listening on {self.host}:{self.port}")
            print("=" * 60)
            print("Waiting for Android StreamLab Camera connection...")

            self.running = True

            while self.running:
                try:
                    self.client_socket, addr = self.socket.accept()
                    print(
                        f"\n✅ Connected to {
                            addr[0]}:{
                            addr[1]} at {
                            datetime.now()}")
                    print("🚀 Starting live preview window...")
                    self.start_time = time.time()
                    self.bytes_received = 0

                    # Start ffplay for live preview
                    if self.show_preview:
                        self.start_ffplay()

                    # Start monitoring thread
                    monitor_thread = threading.Thread(
                        target=self.monitor_stream)
                    monitor_thread.daemon = True
                    monitor_thread.start()

                    # Receive and process data
                    self.receive_data()

                    # After disconnection, clean up and wait for next
                    # connection
                    print("\n🔄 Connection closed. Cleaning up...")
                    if self.ffplay_process:
                        try:
                            self.ffplay_process.stdin.close()
                            self.ffplay_process.terminate()
                            self.ffplay_process.wait(timeout=2)
                            self.ffplay_process = None
                            print("✅ Preview window closed")
                        except Exception as e:
                            print(f"⚠️  Error closing preview: {e}")

                    print(
                        "🔄 Ready for reconnection. Waiting for next stream...")
                    print("=" * 60)

                except socket.error as e:
                    if self.running:
                        print(f"❌ Socket error: {e}")
                        time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Receiver stopped by user")
        except Exception as e:
            print(f"❌ Error starting receiver: {e}")
        finally:
            self.cleanup()

    def start_ffplay(self):
        """Start ffplay process to display the stream"""
        try:
            # ffplay command to read H.264 from stdin and display
            cmd = [
                'ffplay',
                '-f', 'h264',  # Input format is raw H.264
                '-fflags', 'nobuffer',  # Minimize buffering
                '-flags', 'low_delay',  # Low delay mode
                '-framedrop',  # Drop frames if needed
                '-probesize', '32',     # Minimal probe size
                '-analyzeduration', '0',  # Don't analyze, start immediately
                '-sync', 'ext',         # External sync
                '-vf', 'setpts=0',      # Reset presentation timestamps
                '-window_title', 'Miktos Camera Stream',  # Window title
                '-'                     # Read from stdin
            ]

            self.ffplay_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            print(f"🎬 Preview window opened (PID: {self.ffplay_process.pid})")

        except FileNotFoundError:
            print("⚠️  ffplay not found. Install with: brew install ffmpeg")
            print("📝 Stream will be received but not displayed")
            self.show_preview = False
        except Exception as e:
            print(f"⚠️  Could not start preview: {e}")
            self.show_preview = False

    def receive_data(self):
        """Receive H.264 data and pipe to ffplay"""
        buffer_size = 8192
        last_receive_time = time.time()
        frame_count = 0
        last_frame_time = time.time()
        current_fps = 0.0
        # 30 second timeout for PAUSE mode compatibility (1 fps freeze frames)
        self.client_socket.settimeout(30.0)
        print(f"📊 Socket timeout set to 30 seconds (supports PAUSE mode at 1 fps)")

        try:
            while self.running and self.client_socket:
                try:
                    data = self.client_socket.recv(buffer_size)
                    current_time = time.time()
                    if not data:
                        elapsed = current_time - last_receive_time
                        print(f"\n❌ [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Client disconnected (no data) - last data {elapsed:.1f}s ago")
                        break

                    self.bytes_received += len(data)
                    time_since_last = current_time - last_receive_time
                    last_receive_time = current_time
                    
                    # Log every data receive with timestamp and delta
                    if time_since_last > 0.5:  # Log if gap > 500ms
                        print(f"📦 [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Received {len(data)} bytes (gap: {time_since_last:.3f}s)")

                    # Send data to ffplay for display
                    if (self.show_preview and self.ffplay_process and
                            self.ffplay_process.stdin):
                        try:
                            self.ffplay_process.stdin.write(data)
                            self.ffplay_process.stdin.flush()
                        except BrokenPipeError:
                            print("⚠️  Preview window closed")
                            self.show_preview = False

                    # Detect frame types for logging
                    if data.startswith(b'\x00\x00\x00\x01'):
                        frame_count += 1
                        frame_time_delta = current_time - last_frame_time
                        last_frame_time = current_time
                        current_fps = 1.0 / frame_time_delta if frame_time_delta > 0 else 0
                        
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
                        mode_indicator = "🟡 PAUSED" if current_fps < 2 else "🟢 LIVE"
                        
                        # Log every frame with detailed info
                        elapsed = current_time - self.start_time
                        avg_fps = (frame_count / elapsed if elapsed > 0 else 0)
                        mbps = ((self.bytes_received * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0)
                        
                        print(
                            f"🎬 [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {mode_indicator} | "
                            f"{frame_type} | Frame #{frame_count} | "
                            f"Current: {current_fps:.1f} fps | Avg: {avg_fps:.1f} fps | "
                            f"Delta: {frame_time_delta:.3f}s | Size: {len(data)} bytes | "
                            f"Bitrate: {mbps:.2f} Mbps")

                except socket.timeout:
                    # Check for timeout (no data received for a while)
                    elapsed_since_data = time.time() - last_receive_time
                    if elapsed_since_data > 25:
                        print(
                            f"\n⏰ [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
                            f"Timeout: No data for {elapsed_since_data:.1f}s - "
                            f"client disconnected or stopped")
                        break
                    else:
                        # Log periodic timeout checks for visibility
                        print(f"⏱️  [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Socket timeout check - last data {elapsed_since_data:.1f}s ago (waiting...)")
                    continue
                except socket.error as e:
                    print(f"\n❌ Receive error: {e}")
                    break

        except Exception as e:
            print(f"\n❌ Error in receive_data: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None

    def monitor_stream(self):
        """Monitor stream health"""
        last_bytes = 0
        check_count = 0

        while self.running and self.client_socket:
            time.sleep(5)  # Check every 5 seconds
            check_count += 1

            # Full report every 30 seconds
            if self.start_time and check_count % 6 == 0:
                elapsed = time.time() - self.start_time
                avg_kbps = (self.bytes_received * 8) / \
                    (elapsed * 1000) if elapsed > 0 else 0
                current_kbps = (
                    (self.bytes_received - last_bytes) * 8) / (5 * 1000)

                print(f"\n{'=' * 60}")
                print("📈 30-Second Report:")
                print(
                    f"   Total Data: "
                    f"{self.bytes_received / 1024 / 1024:.2f} MB")
                print(
                    f"   Average Bitrate: {avg_kbps:.1f} Kbps "
                    f"({avg_kbps / 1000:.2f} Mbps)")
                print(
                    f"   Current Bitrate: {current_kbps:.1f} Kbps "
                    f"({current_kbps / 1000:.2f} Mbps)")
                print(f"   Duration: {elapsed:.1f} seconds")
                print(f"{'=' * 60}\n")

                last_bytes = self.bytes_received

    def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up...")
        self.running = False

        if self.ffplay_process:
            try:
                self.ffplay_process.stdin.close()
                self.ffplay_process.terminate()
                self.ffplay_process.wait(timeout=2)
                print("✅ Preview window closed")
            except Exception as e:
                print(f"⚠️  Error closing preview: {e}")

        if self.client_socket:
            self.client_socket.close()

        if self.socket:
            self.socket.close()

        if self.start_time:
            elapsed = time.time() - self.start_time
            print("\n📊 Final Statistics:")
            print(f"   Duration: {elapsed:.1f} seconds")
            print(
                "   Total Data: "
                f"{self.bytes_received / 1024 / 1024:.2f} MB")
            print(
                "   Average Bitrate: "
                f"{(self.bytes_received * 8) /
                   (elapsed * 1_000_000):.2f} Mbps")

        print("👋 Receiver stopped")


def main():
    port = 8554
    show_preview = True

    # Parse command line arguments
    if '--no-preview' in sys.argv:
        show_preview = False

    if '--help' in sys.argv or '-h' in sys.argv:
        print(
            "Usage: python3 tcp_h264_receiver_with_preview.py "
            "[--no-preview] [PORT]")
        print("\nOptions:")
        print("  --no-preview    Don't open preview window (just log stats)")
        print("  PORT            Port number (default: 8554)")
        print("\nRequires ffplay (install: brew install ffmpeg)")
        sys.exit(0)

    for arg in sys.argv[1:]:
        if arg.isdigit():
            port = int(arg)

    print("=" * 60)
    print("🎥 Miktos StreamLab Camera - TCP H.264 Receiver")
    print("=" * 60)

    if show_preview:
        print("📺 Live preview enabled (press Q in preview window to close)")
    else:
        print("📊 Statistics-only mode (no preview)")

    print()

    receiver = TCPReceiverWithPreview(port=port, show_preview=show_preview)

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\n⚠️  Interrupt received, shutting down...")
        receiver.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        receiver.start()
    except KeyboardInterrupt:
        pass
    finally:
        receiver.cleanup()


if __name__ == "__main__":
    main()
