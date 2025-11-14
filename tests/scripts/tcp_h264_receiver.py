#!/usr/bin/env python3
"""
Simple TCP H.264 Receiver for Testing Disconnect Detection
Receives H.264 stream from Android StreamLab Camera app
"""

import socket
import sys
import threading
import time
from datetime import datetime

class TCPReceiver:
    def __init__(self, host='0.0.0.0', port=8554):
        self.host = host
        self.port = port
        self.socket = None
        self.client_socket = None
        self.running = False
        self.bytes_received = 0
        self.start_time = None
        
    def start(self):
        """Start the TCP receiver"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            
            print(f"🎥 TCP H.264 Receiver started on {self.host}:{self.port}")
            print("Waiting for Android StreamLab Camera connection...")
            
            self.running = True
            
            while self.running:
                try:
                    self.client_socket, addr = self.socket.accept()
                    print(f"✅ Connected to {addr[0]}:{addr[1]} at {datetime.now()}")
                    self.start_time = time.time()
                    self.bytes_received = 0
                    
                    # Start monitoring thread
                    monitor_thread = threading.Thread(target=self.monitor_stream)
                    monitor_thread.daemon = True
                    monitor_thread.start()
                    
                    # Receive data
                    self.receive_data()
                    
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
    
    def receive_data(self):
        """Receive H.264 data from client"""
        buffer_size = 8192
        last_receive_time = time.time()
        
        try:
            while self.running and self.client_socket:
                try:
                    data = self.client_socket.recv(buffer_size)
                    if not data:
                        print("❌ Client disconnected (no data)")
                        break
                        
                    self.bytes_received += len(data)
                    last_receive_time = time.time()
                    
                    # Simple H.264 frame detection
                    if data.startswith(b'\x00\x00\x00\x01'):
                        frame_type = "Unknown"
                        if len(data) > 4:
                            nalu_type = data[4] & 0x1F
                            if nalu_type == 5:
                                frame_type = "I-Frame (Keyframe)"
                            elif nalu_type == 1:
                                frame_type = "P-Frame"
                            elif nalu_type == 7:
                                frame_type = "SPS (Config)"
                            elif nalu_type == 8:
                                frame_type = "PPS (Config)"
                                
                        if self.bytes_received % (50 * 1024) < len(data):  # Log every ~50KB
                            print(f"📡 Received {frame_type}: {len(data)} bytes (Total: {self.bytes_received/1024:.1f} KB)")
                    
                except socket.timeout:
                    # Check for timeout (no data received)
                    if time.time() - last_receive_time > 15:
                        print("⏰ Timeout: No data received for 15 seconds")
                        break
                except socket.error as e:
                    print(f"❌ Receive error: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Error in receive_data: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
    
    def monitor_stream(self):
        """Monitor stream statistics"""
        last_bytes = 0
        
        while self.running and self.client_socket:
            time.sleep(10)  # Report every 10 seconds
            
            if self.start_time:
                elapsed = time.time() - self.start_time
                rate_kbps = (self.bytes_received * 8) / (elapsed * 1000) if elapsed > 0 else 0
                bytes_per_sec = (self.bytes_received - last_bytes) / 10 if elapsed > 0 else 0
                
                print(f"📊 Stream Stats: {self.bytes_received/1024:.1f} KB received, "
                      f"Rate: {rate_kbps:.1f} Kbps, "
                      f"Current: {bytes_per_sec/1024:.1f} KB/s")
                
                last_bytes = self.bytes_received
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        if self.client_socket:
            self.client_socket.close()
            
        if self.socket:
            self.socket.close()
            
        print("🧹 Receiver cleaned up")

def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8554
    
    print("🎯 TCP H.264 Receiver for Miktos StreamLab Camera")
    print("=" * 50)
    
    receiver = TCPReceiver(port=port)
    
    try:
        receiver.start()
    except KeyboardInterrupt:
        print("\n👋 Shutting down receiver...")
        receiver.cleanup()

if __name__ == "__main__":
    main()