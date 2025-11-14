#!/usr/bin/env python3
"""
TCP H.264 Receiver for Miktos StreamLab Camera (Android)
Receives raw H.264 stream from Samsung S23 FE and displays with FFplay
"""

import socket
import subprocess
import sys
import time

PORT = 8554  # Must match Android app default

def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     Miktos StreamLab - Android Camera Receiver                ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"\n📡 Listening on 0.0.0.0:{PORT}")
    print(f"\n💡 On your Samsung S23 FE:")
    print(f"   1. Open Miktos Camera app")
    print(f"   2. Enter your Mac IP address")
    print(f"   3. Port: {PORT}")
    print(f"   4. Tap START STREAMING\n")
    
    # Create TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)  # 1MB buffer
    sock.bind(('0.0.0.0', PORT))
    sock.listen(1)
    
    print(f"✅ Ready for connection...\n")
    
    conn, addr = sock.accept()
    print(f"✅ Connected from {addr[0]}:{addr[1]}")
    print(f"🎥 Starting video playback...\n")
    
    # Start ffplay with optimized settings for H.264
    ffplay = subprocess.Popen(
        [
            'ffplay',
            '-f', 'h264',           # Input format
            '-i', '-',               # Read from stdin
            '-probesize', '32',      # Fast probe
            '-analyzeduration', '0', # No analysis delay
            '-fflags', 'nobuffer',   # Minimize buffering
            '-flags', 'low_delay',   # Low latency
            '-framedrop',            # Drop if behind
            '-sync', 'ext',          # External sync
            '-vf', 'setpts=N/30/TB', # Force 30fps
            '-window_title', 'Miktos Camera - Samsung S23 FE'
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        bytes_received = 0
        start_time = time.time()
        last_print = time.time()
        
        while True:
            data = conn.recv(131072)  # 128KB chunks
            if not data:
                print("\n⚠️  Connection closed by phone")
                break
            
            bytes_received += len(data)
            
            try:
                ffplay.stdin.write(data)
                ffplay.stdin.flush()
            except BrokenPipeError:
                print("\n⚠️  FFplay closed")
                break
            
            # Print stats every 2 seconds
            now = time.time()
            if now - last_print >= 2.0:
                elapsed = now - start_time
                mbps = (bytes_received * 8) / elapsed / 1_000_000
                print(f"📊 {bytes_received/1_000_000:.1f} MB | {mbps:.2f} Mbps | {elapsed:.0f}s")
                last_print = now
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Cleaning up...")
        try:
            conn.close()
        except:
            pass
        try:
            sock.close()
        except:
            pass
        try:
            ffplay.terminate()
            ffplay.wait(timeout=2)
        except:
            try:
                ffplay.kill()
            except:
                pass
        print("✅ Receiver closed\n")

if __name__ == '__main__':
    # Check if ffplay is available
    try:
        subprocess.run(['ffplay', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL,
                      check=True)
    except:
        print("❌ Error: ffplay not found")
        print("\nInstall FFmpeg:")
        print("  brew install ffmpeg")
        sys.exit(1)
    
    main()
