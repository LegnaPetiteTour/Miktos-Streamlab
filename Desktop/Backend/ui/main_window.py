"""
Miktos StreamLab - Main Window
==============================

PySide6 main window with asyncio integration.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QStatusBar,
    QGroupBox,
    QGridLayout,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QCloseEvent

# Import backend
sys.path.append(str(Path(__file__).parent.parent))
from obs_controller import OBSController, StreamingStatus  # noqa: E402


class MainWindow(QMainWindow):
    """
    Main application window for Miktos StreamLab.

    Features:
    - Scene management
    - Streaming control
    - Health monitoring
    - Direct Python backend integration (no HTTP)
    """

    # Qt signals for async updates
    health_updated = Signal(dict)
    scene_changed = Signal(str)
    streaming_status_changed = Signal(bool)

    def __init__(self, obs: Optional[OBSController] = None):
        """
        Initialize main window.

        Args:
            obs: OBS controller instance (shared with FastAPI)
        """
        super().__init__()

        # Backend integration
        self.obs = obs
        self.is_streaming = False

        # Setup UI
        self.setWindowTitle("Miktos StreamLab - Professional streaming Broadcasting")
        self.setMinimumSize(1200, 800)

        # Setup central widget
        self._setup_ui()

        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        status = (
            "Ready" if obs and obs.status.value == "connected" else "OBS Disconnected"
        )  # noqa: E501
        self.status_bar.showMessage(status)

        # Setup update timers
        self._setup_timers()

        # Connect signals
        self.health_updated.connect(self._on_health_updated)
        self.scene_changed.connect(self._on_scene_changed)
        self.streaming_status_changed.connect(self._on_streaming_status_changed)

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel - Scenes
        scenes_panel = self._create_scenes_panel()
        main_layout.addWidget(scenes_panel, 1)

        # Center panel - Preview
        preview_panel = self._create_preview_panel()
        main_layout.addWidget(preview_panel, 2)

        # Right panel - Health & Controls
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel, 1)

    def _create_scenes_panel(self) -> QGroupBox:
        """Create the scenes list panel"""
        group = QGroupBox("Scenes")
        layout = QVBoxLayout(group)

        # Scene list
        self.scene_list = QListWidget()
        self.scene_list.itemClicked.connect(self._on_scene_clicked)
        layout.addWidget(self.scene_list)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Scenes")
        refresh_btn.clicked.connect(lambda: asyncio.create_task(self._load_scenes()))
        layout.addWidget(refresh_btn)

        return group

    def _create_preview_panel(self) -> QGroupBox:
        """Create the preview panel"""
        group = QGroupBox("Preview")
        layout = QVBoxLayout(group)

        # Preview placeholder
        preview_label = QLabel("🎥 Stream Preview")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet(
            """
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #333;
                border-radius: 8px;
                color: #666;
                font-size: 24px;
                padding: 40px;
            }
        """
        )
        preview_label.setMinimumHeight(400)
        layout.addWidget(preview_label, 1)

        # Current scene info
        self.scene_info_label = QLabel("Scene: None")
        self.scene_info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.scene_info_label)

        # Stream status
        self.stream_status_label = QLabel("● Offline")
        self.stream_status_label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.stream_status_label)

        return group

    def _create_control_panel(self) -> QGroupBox:
        """Create the control panel with health metrics and buttons"""
        group = QGroupBox("Control & Monitoring")
        layout = QVBoxLayout(group)

        # Health metrics
        health_group = QGroupBox("Stream Health")
        health_layout = QGridLayout(health_group)

        self.fps_label = QLabel("FPS: --")
        self.cpu_label = QLabel("CPU: --")
        self.dropped_label = QLabel("Dropped: --")
        self.network_label = QLabel("Network: --")

        health_layout.addWidget(QLabel("📊"), 0, 0)
        health_layout.addWidget(self.fps_label, 0, 1)
        health_layout.addWidget(QLabel("💻"), 1, 0)
        health_layout.addWidget(self.cpu_label, 1, 1)
        health_layout.addWidget(QLabel("📉"), 2, 0)
        health_layout.addWidget(self.dropped_label, 2, 1)
        health_layout.addWidget(QLabel("🌐"), 3, 0)
        health_layout.addWidget(self.network_label, 3, 1)

        layout.addWidget(health_group)

        # Control buttons
        controls_group = QGroupBox("Stream Control")
        controls_layout = QVBoxLayout(controls_group)

        self.start_btn = QPushButton("🟢 Start Streaming")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2d7d2d;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3a9d3a;
            }
            QPushButton:disabled {
                background-color: #555;
            }
        """
        )
        self.start_btn.clicked.connect(
            lambda: asyncio.create_task(self._start_streaming())
        )
        controls_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("🔴 Stop Streaming")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #7d2d2d;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #9d3a3a;
            }
            QPushButton:disabled {
                background-color: #555;
            }
        """
        )
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(
            lambda: asyncio.create_task(self._stop_streaming())
        )
        controls_layout.addWidget(self.stop_btn)

        layout.addWidget(controls_group)

        # Web dashboard button
        web_btn = QPushButton("🌐 Open Web Dashboard")
        web_btn.clicked.connect(self._open_web_dashboard)
        layout.addWidget(web_btn)

        layout.addStretch()

        return group

    def _setup_timers(self) -> None:
        """Setup periodic update timers"""
        # Health update timer (every 2 seconds)
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(
            lambda: asyncio.create_task(self._update_health())
        )
        self.health_timer.start(2000)

        # Initial load
        asyncio.create_task(self._initial_load())

    async def _initial_load(self) -> None:
        """Load initial data"""
        await self._load_scenes()
        await self._update_health()

    async def _load_scenes(self) -> None:
        """Load scenes from OBS"""
        if not self.obs or self.obs.status.value != "connected":
            return

        try:
            scenes = await self.obs.get_scenes()
            current_scene = await self.obs.get_current_scene()

            # Update scene list
            self.scene_list.clear()
            for scene in scenes:
                prefix = "▶ " if scene.is_current else "  "
                item = QListWidgetItem(f"{prefix}{scene.name}")
                if scene.is_current:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setForeground(QColor("#4a9eff"))
                self.scene_list.addItem(item)

            # Update scene info
            if current_scene:
                self.scene_info_label.setText(f"Scene: {current_scene}")
                self.scene_changed.emit(current_scene)

        except Exception as e:
            print(f"Error loading scenes: {e}")

    async def _update_health(self) -> None:
        """Update health metrics"""
        if not self.obs or self.obs.status.value != "connected":
            self.health_updated.emit(
                {"fps": 0, "cpu_usage": 0, "dropped_frames": 0, "connected": False}
            )
            return

        try:
            health = await self.obs.get_health()
            self.health_updated.emit(health)

            # Update streaming status
            status = await self.obs.get_streaming_status()
            is_streaming = status == StreamingStatus.ACTIVE
            if is_streaming != self.is_streaming:
                self.is_streaming = is_streaming
                self.streaming_status_changed.emit(is_streaming)

        except Exception as e:
            print(f"Error updating health: {e}")

    def _on_health_updated(self, health: dict) -> None:
        """Handle health update signal"""
        self.fps_label.setText(f"FPS: {health.get('fps', 0):.1f}")
        self.cpu_label.setText(f"CPU: {health.get('cpu_usage', 0):.1f}%")
        self.dropped_label.setText(f"Dropped: {health.get('dropped_frames', 0)}")

        connected = health.get("connected", False)
        if connected:
            self.network_label.setText("Network: ✅ Connected")
            self.network_label.setStyleSheet("color: green;")
        else:
            self.network_label.setText("Network: ❌ Disconnected")
            self.network_label.setStyleSheet("color: red;")

    def _on_scene_changed(self, scene_name: str) -> None:
        """Handle scene change signal"""
        self.scene_info_label.setText(f"Scene: {scene_name}")

    def _on_streaming_status_changed(self, is_streaming: bool) -> None:
        """Handle streaming status change signal"""
        if is_streaming:
            self.stream_status_label.setText("● Live")
            self.stream_status_label.setStyleSheet(
                "color: #ff4444; font-size: 14px; font-weight: bold;"
            )
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            self.stream_status_label.setText("● Offline")
            self.stream_status_label.setStyleSheet("color: #888; font-size: 14px;")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def _on_scene_clicked(self, item: QListWidgetItem) -> None:
        """Handle scene click"""
        scene_name = item.text().strip().replace("▶ ", "").replace("  ", "")
        asyncio.create_task(self._switch_scene(scene_name))

    async def _switch_scene(self, scene_name: str) -> None:
        """Switch to a different scene"""
        if not self.obs or self.obs.status.value != "connected":
            return

        try:
            await self.obs.switch_scene(scene_name)
            await self._load_scenes()
            self.status_bar.showMessage(f"Switched to scene: {scene_name}", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"Error switching scene: {e}", 5000)

    async def _start_streaming(self) -> None:
        """Start streaming"""
        if not self.obs or self.obs.status.value != "connected":
            self.status_bar.showMessage("OBS not connected!", 5000)
            return

        try:
            self.status_bar.showMessage("Starting stream...", 3000)
            success = await self.obs.start_streaming()
            if success:
                self.status_bar.showMessage("Stream started successfully!", 5000)
            else:
                self.status_bar.showMessage("Failed to start stream", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"Error starting stream: {e}", 5000)

    async def _stop_streaming(self) -> None:
        """Stop streaming"""
        if not self.obs or self.obs.status.value != "connected":
            return

        try:
            self.status_bar.showMessage("Stopping stream...", 3000)
            success = await self.obs.stop_streaming()
            if success:
                self.status_bar.showMessage("Stream stopped successfully!", 5000)
            else:
                self.status_bar.showMessage("Failed to stop stream", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"Error stopping stream: {e}", 5000)

    def _open_web_dashboard(self) -> None:
        """Open web dashboard in browser"""
        import webbrowser

        webbrowser.open("http://localhost:8000")
        self.status_bar.showMessage("Opening web dashboard...", 3000)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event"""
        # Stop timers
        self.health_timer.stop()

        # Accept close
        event.accept()
