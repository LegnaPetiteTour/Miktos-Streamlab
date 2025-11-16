#!/usr/bin/env python3
"""
Simple TCP H.264 Receiver for StreamLab Camera
Receives raw H.264 stream and plays with FFplay
"""

import socket
import subprocess

PORT = 9001


def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║          StreamLab Camera - TCP H.264 Receiver                ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"\n📡 Listening on port {PORT}...")
    print("\n💡 In your iPhone app:")
    print("   IP: 192.168.2.36")
    print(f"   Port: {PORT}")
    print("   Tap START STREAMING\n")

    # Create TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', PORT))
    sock.listen(1)

    print("✅ Waiting for connection...\n")

    conn, addr = sock.accept()
    print(f"✅ Connected from {addr[0]}:{addr[1]}")
    print("🎥 Starting video playback...\n")

    # Start ffplay to display H.264 stream
    ffplay = subprocess.Popen(
        ['ffplay', '-f', 'h264', '-i', '-', '-framedrop'],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        bytes_received = 0
        while True:
            data = conn.recv(65536)
            if not data:
                break

            bytes_received += len(data)
            ffplay.stdin.write(data)

            # Print progress every 1MB
            if bytes_received % 1000000 < 65536:
                mbps = (bytes_received * 8) / 1000000
                mb = bytes_received / 1000000
                print(f"📊 Received: {mb:.1f} MB ({mbps:.1f} Mbps)")

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        conn.close()
        sock.close()
        ffplay.terminate()
        print("\n✅ Receiver closed")


if __name__ == '__main__':
    main()
