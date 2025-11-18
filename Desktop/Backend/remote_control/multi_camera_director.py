#!/usr/bin/env python3
"""
Multi-Camera Director UI

Production-ready multi-camera control interface with:
- Live camera tiles with health indicators
- START/STOP/PAUSE/RESUME buttons per camera
- Battery, thermal, and network status badges
- Active camera highlighting
- Click to switch active camera
- Thermal alerts and auto-actions
"""

import asyncio
import websockets
import json
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class ThermalState(Enum):
    """Thermal state levels"""
    OK = "OK"
    WARM = "WARM"
    HOT = "HOT"
    CRITICAL = "CRITICAL"


@dataclass
class CameraStatus:
    """Camera status data"""
    camera_id: str
    state: str = "stopped"
    is_streaming: bool = False
    is_paused: bool = False
    battery_level: int = 0
    network_type: str = "UNKNOWN"
    thermal_state: str = "OK"
    current_bitrate_mbps: float = 0.0
    uptime_seconds: int = 0
    frame_count: int = 0
    server_ip: str = ""
    server_port: int = 0
    last_update: float = 0.0


class CameraTile(ttk.Frame):
    """Individual camera control tile"""
    
    def __init__(self, parent, camera_id: str, on_command: Callable):
        super().__init__(parent, relief='ridge', borderwidth=2)
        self.camera_id = camera_id
        self.on_command = on_command
        self.status = CameraStatus(camera_id=camera_id)
        self.is_active = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create tile UI elements"""
        
        # Header: Camera ID + Active Indicator
        header = ttk.Frame(self)
        header.pack(fill='x', padx=5, pady=5)
        
        self.camera_label = ttk.Label(
            header,
            text=f"📱 {self.camera_id[:8]}...",
            font=('Arial', 12, 'bold')
        )
        self.camera_label.pack(side='left')
        
        self.active_indicator = ttk.Label(
            header,
            text="",
            font=('Arial', 10)
        )
        self.active_indicator.pack(side='right')
        
        # Status Display
        status_frame = ttk.Frame(self)
        status_frame.pack(fill='x', padx=5, pady=2)
        
        self.status_label = ttk.Label(
            status_frame,
            text="⚪ OFFLINE",
            font=('Arial', 10)
        )
        self.status_label.pack()
        
        # Health Indicators
        health_frame = ttk.Frame(self)
        health_frame.pack(fill='x', padx=5, pady=5)
        
        self.battery_label = ttk.Label(health_frame, text="🔋 --%")
        self.battery_label.grid(row=0, column=0, sticky='w', padx=2)
        
        self.thermal_label = ttk.Label(health_frame, text="")
        self.thermal_label.grid(row=0, column=1, sticky='w', padx=2)
        
        self.network_label = ttk.Label(health_frame, text="📵 OFFLINE")
        self.network_label.grid(row=1, column=0, sticky='w', padx=2)
        
        self.bitrate_label = ttk.Label(health_frame, text="📊 0.0 Mbps")
        self.bitrate_label.grid(row=1, column=1, sticky='w', padx=2)
        
        # Uptime
        self.uptime_label = ttk.Label(
            health_frame,
            text="⏱️  --:--",
            font=('Arial', 8)
        )
        self.uptime_label.grid(row=2, column=0, columnspan=2, pady=2)
        
        # Control Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        self.start_btn = ttk.Button(
            btn_frame,
            text="▶ START",
            command=lambda: self.on_command(self.camera_id, "START")
        )
        self.start_btn.grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        
        self.pause_btn = ttk.Button(
            btn_frame,
            text="⏸ PAUSE",
            command=lambda: self.on_command(self.camera_id, "PAUSE"),
            state='disabled'
        )
        self.pause_btn.grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        
        self.resume_btn = ttk.Button(
            btn_frame,
            text="▶ RESUME",
            command=lambda: self.on_command(self.camera_id, "RESUME"),
            state='disabled'
        )
        self.resume_btn.grid(row=1, column=0, padx=2, pady=2, sticky='ew')
        
        self.stop_btn = ttk.Button(
            btn_frame,
            text="⏹ STOP",
            command=lambda: self.on_command(self.camera_id, "STOP"),
            state='disabled'
        )
        self.stop_btn.grid(row=1, column=1, padx=2, pady=2, sticky='ew')
        
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        # Studio Mode Buttons
        studio_frame = ttk.Frame(self)
        studio_frame.pack(fill='x', padx=5, pady=2)
        
        self.studio_on_btn = ttk.Button(
            studio_frame,
            text="🌙 Studio ON",
            command=lambda: self.on_command(self.camera_id, "ENTER_STUDIO_MODE")
        )
        self.studio_on_btn.grid(row=0, column=0, padx=2, sticky='ew')
        
        self.studio_off_btn = ttk.Button(
            studio_frame,
            text="💡 Studio OFF",
            command=lambda: self.on_command(self.camera_id, "EXIT_STUDIO_MODE")
        )
        self.studio_off_btn.grid(row=0, column=1, padx=2, sticky='ew')
        
        studio_frame.columnconfigure(0, weight=1)
        studio_frame.columnconfigure(1, weight=1)
        
        # Make Active Button
        self.active_btn = ttk.Button(
            self,
            text="✨ MAKE ACTIVE",
            command=lambda: self.on_command(self.camera_id, "MAKE_ACTIVE")
        )
        self.active_btn.pack(fill='x', padx=5, pady=5)
    
    def update_status(self, status: CameraStatus):
        """Update tile with new status"""
        self.status = status
        
        # State indicator
        state_icons = {
            "stopped": "⚪ STOPPED",
            "starting": "🟡 STARTING",
            "running": "🟢 LIVE",
            "paused": "🟡 PAUSED",
            "disconnected": "🔴 DISCONNECTED",
            "error": "❌ ERROR"
        }
        self.status_label.config(text=state_icons.get(status.state, "⚪ OFFLINE"))
        
        # Battery
        battery_icon = "⚡" if status.battery_level > 80 else "🔋"
        self.battery_label.config(text=f"{battery_icon} {status.battery_level}%")
        
        # Thermal
        thermal_icons = {
            "OK": "",
            "WARM": "🌡️ WARM",
            "HOT": "🔥 HOT",
            "CRITICAL": "☠️ CRITICAL"
        }
        thermal_text = thermal_icons.get(status.thermal_state, "")
        self.thermal_label.config(
            text=thermal_text,
            foreground='red' if status.thermal_state in ['HOT', 'CRITICAL'] else 'orange' if status.thermal_state == 'WARM' else 'black'
        )
        
        # Network
        network_icons = {
            "LAN_WIFI": "📶 WiFi",
            "INET_WIFI": "📶 WiFi",
            "LTE_CELLULAR": "📱 LTE",
            "UNKNOWN": "📵 OFFLINE"
        }
        self.network_label.config(text=network_icons.get(status.network_type, "📵 OFFLINE"))
        
        # Bitrate
        self.bitrate_label.config(text=f"📊 {status.current_bitrate_mbps:.1f} Mbps")
        
        # Uptime
        if status.uptime_seconds > 0:
            hours = status.uptime_seconds // 3600
            mins = (status.uptime_seconds % 3600) // 60
            secs = status.uptime_seconds % 60
            self.uptime_label.config(text=f"⏱️  {hours:02d}:{mins:02d}:{secs:02d}")
        else:
            self.uptime_label.config(text="⏱️  --:--")
        
        # Update button states
        is_running = status.state == "running"
        is_paused = status.state == "paused"
        is_stopped = status.state in ["stopped", "disconnected", "error"]
        
        self.start_btn.config(state='normal' if is_stopped else 'disabled')
        self.pause_btn.config(state='normal' if is_running else 'disabled')
        self.resume_btn.config(state='normal' if is_paused else 'disabled')
        self.stop_btn.config(state='normal' if (is_running or is_paused) else 'disabled')
    
    def set_active(self, active: bool):
        """Mark this camera as active"""
        self.is_active = active
        
        if active:
            self.config(relief='solid', borderwidth=4)
            self.active_indicator.config(text="⭐ ACTIVE", foreground='green')
            self.active_btn.config(state='disabled')
        else:
            self.config(relief='ridge', borderwidth=2)
            self.active_indicator.config(text="")
            self.active_btn.config(state='normal')


class MultiCameraDirectorApp:
    """Main application window"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("StreamLab Multi-Camera Director")
        self.root.geometry("1000x700")
        
        self.ws_uri = "ws://192.168.2.36:9001"  # Controller port
        self.websocket = None
        self.camera_tiles: Dict[str, CameraTile] = {}
        self.active_camera: Optional[str] = None
        
        self._create_ui()
        
        # Start WebSocket connection
        asyncio.create_task(self.connect_websocket())
    
    def _create_ui(self):
        """Create main UI"""
        
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(
            header,
            text="📹 StreamLab Multi-Camera Director",
            font=('Arial', 16, 'bold')
        ).pack(side='left')
        
        self.connection_label = ttk.Label(
            header,
            text="🔴 Disconnected",
            font=('Arial', 10)
        )
        self.connection_label.pack(side='right')
        
        # Camera tiles container
        tiles_container = ttk.Frame(self.root)
        tiles_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create scrollable canvas
        canvas = tk.Canvas(tiles_container)
        scrollbar = ttk.Scrollbar(tiles_container, orient="vertical", command=canvas.yview)
        self.tiles_frame = ttk.Frame(canvas)
        
        self.tiles_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.tiles_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Log area
        log_frame = ttk.LabelFrame(self.root, text="Event Log")
        log_frame.pack(fill='both', padx=10, pady=10, expand=False)
        
        self.log_text = tk.Text(log_frame, height=8, state='disabled')
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scroll.pack(side='right', fill='y')
    
    def log(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
    
    async def connect_websocket(self):
        """Connect to WebSocket server"""
        while True:
            try:
                self.log(f"Connecting to {self.ws_uri}...")
                async with websockets.connect(self.ws_uri) as websocket:
                    self.websocket = websocket
                    self.connection_label.config(text="🟢 Connected", foreground='green')
                    self.log("✅ Connected to remote control server")
                    
                    # Listen for messages
                    async for message in websocket:
                        await self.handle_message(message)
                        
            except Exception as e:
                self.connection_label.config(text="🔴 Disconnected", foreground='red')
                self.log(f"❌ Connection error: {e}")
                await asyncio.sleep(5)  # Retry after 5 seconds
    
    async def handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'camera_list':
                cameras = data.get('cameras', [])
                self.log(f"📱 Cameras online: {len(cameras)}")
                for camera_id in cameras:
                    if camera_id not in self.camera_tiles:
                        self.add_camera_tile(camera_id)
            
            elif msg_type == 'status':
                camera_id = data.get('camera_id')
                status_data = data.get('data', {})
                
                if camera_id and camera_id in self.camera_tiles:
                    status = CameraStatus(
                        camera_id=camera_id,
                        state=status_data.get('state', 'stopped'),
                        is_streaming=status_data.get('is_streaming', False),
                        is_paused=status_data.get('is_paused', False),
                        battery_level=status_data.get('battery_level', 0),
                        network_type=status_data.get('network_type', 'UNKNOWN'),
                        thermal_state=status_data.get('thermal_state', 'OK'),
                        current_bitrate_mbps=status_data.get('current_bitrate_mbps', 0.0),
                        uptime_seconds=status_data.get('uptime_seconds', 0),
                        frame_count=status_data.get('frame_count', 0),
                        server_ip=status_data.get('server_ip', ''),
                        server_port=status_data.get('server_port', 0),
                        last_update=datetime.now().timestamp()
                    )
                    
                    self.camera_tiles[camera_id].update_status(status)
                    
                    # Check for thermal alerts
                    self.check_thermal_alerts(camera_id, status)
            
            elif msg_type == 'command_result':
                self.log(f"✅ Command result: {data.get('status')}")
                
        except Exception as e:
            self.log(f"❌ Error processing message: {e}")
    
    def check_thermal_alerts(self, camera_id: str, status: CameraStatus):
        """Check for thermal issues and alert user"""
        thermal = status.thermal_state
        
        if thermal == "HOT":
            self.log(f"🔥 WARNING: Camera {camera_id[:8]} is HOT - quality reduced")
        elif thermal == "CRITICAL":
            self.log(f"☠️ CRITICAL: Camera {camera_id[:8]} thermal emergency!")
            messagebox.showwarning(
                "Thermal Critical",
                f"Camera {camera_id[:8]} is at CRITICAL temperature!\n\n"
                "Consider switching to another camera or stopping this stream."
            )
    
    def add_camera_tile(self, camera_id: str):
        """Add a new camera tile"""
        tile = CameraTile(self.tiles_frame, camera_id, self.send_command)
        tile.pack(side='left', padx=10, pady=10, fill='both')
        self.camera_tiles[camera_id] = tile
        self.log(f"📱 Added camera: {camera_id[:8]}...")
    
    def send_command(self, camera_id: str, command: str):
        """Send command to camera"""
        if command == "MAKE_ACTIVE":
            self.set_active_camera(camera_id)
            return
        
        asyncio.create_task(self._send_command_async(camera_id, command))
    
    async def _send_command_async(self, camera_id: str, command: str):
        """Send command via WebSocket"""
        if not self.websocket:
            self.log("❌ Not connected to server")
            return
        
        message = {
            "type": "command",
            "camera_id": camera_id,
            "command": command,
            "params": {}
        }
        
        # Add server IP/port for START command
        if command == "START":
            message["params"] = {
                "server_ip": "192.168.2.36",
                "server_port": 8554
            }
        
        try:
            await self.websocket.send(json.dumps(message))
            self.log(f"📤 Sent {command} to {camera_id[:8]}...")
        except Exception as e:
            self.log(f"❌ Failed to send command: {e}")
    
    def set_active_camera(self, camera_id: str):
        """Set active camera and pause others"""
        self.log(f"✨ Switching to camera {camera_id[:8]}...")
        
        for cid, tile in self.camera_tiles.items():
            if cid == camera_id:
                tile.set_active(True)
                # Resume if paused
                if tile.status.state == "paused":
                    asyncio.create_task(self._send_command_async(cid, "RESUME"))
            else:
                tile.set_active(False)
                # Pause if running
                if tile.status.state == "running":
                    asyncio.create_task(self._send_command_async(cid, "PAUSE"))
        
        self.active_camera = camera_id
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


async def main():
    """Main entry point"""
    app = MultiCameraDirectorApp()
    
    # Run Tkinter in async loop
    while True:
        app.root.update()
        await asyncio.sleep(0.01)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
