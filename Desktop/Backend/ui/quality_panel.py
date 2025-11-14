"""
Quality Control Panel - Dashboard UI for image quality management

Provides comprehensive quality control interface with real-time monitoring.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (  # type: ignore[import-not-found]
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QComboBox, QGroupBox,
    QProgressBar, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer  # type: ignore[import-not-found]
from PyQt6.QtGui import QFont  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


class QualityMetricWidget(QWidget):
    """
    Widget displaying a single quality metric.

    Shows metric name, score, and status indicator.
    """

    def __init__(self, name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.name = name
        self.score = 0.0
        self.status = "unknown"

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Metric name
        self.name_label = QLabel(self.name)
        self.name_label.setMinimumWidth(100)
        layout.addWidget(self.name_label)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%v/100")
        layout.addWidget(self.progress, 1)

        # Status indicator
        self.status_label = QLabel("●")
        self.status_label.setMinimumWidth(20)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def update_metric(
        self,
        score: float,
        status: str
    ) -> None:
        """
        Update metric display.

        Args:
            score: Metric score (0-100)
            status: Status (good/warning/critical)
        """
        self.score = score
        self.status = status

        # Update progress bar
        self.progress.setValue(int(score))

        # Update status color
        if status == "good":
            color = "#4CAF50"  # Green
        elif status == "warning":
            color = "#FF9800"  # Orange
        elif status == "critical":
            color = "#F44336"  # Red
        else:
            color = "#9E9E9E"  # Gray

        self.status_label.setStyleSheet(f"color: {color}; font-size: 16px;")
        self.progress.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; }}"
        )


class QualityControlSlider(QWidget):
    """
    Slider widget for quality control adjustments.

    Allows manual adjustment of quality parameters.
    """

    valueChanged = pyqtSignal(float)

    def __init__(
        self,
        name: str,
        min_val: float = -1.0,
        max_val: float = 1.0,
        default: float = 0.0,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.default = default

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Label
        self.label = QLabel(self.name)
        self.label.setMinimumWidth(100)
        layout.addWidget(self.label)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(-100)
        self.slider.setMaximum(100)
        self.slider.setValue(int(self.default * 100))
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(20)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider, 1)

        # Value label
        self.value_label = QLabel(f"{self.default:.2f}")
        self.value_label.setMinimumWidth(50)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.value_label)

        # Reset button
        self.reset_btn = QPushButton("↺")
        self.reset_btn.setMaximumWidth(30)
        self.reset_btn.clicked.connect(self.reset)
        layout.addWidget(self.reset_btn)

    def _on_value_changed(self, value: int) -> None:
        """Handle slider value change"""
        # Convert from -100..100 to min_val..max_val
        normalized = value / 100.0
        actual = normalized * (self.max_val - self.min_val) / 2

        self.value_label.setText(f"{actual:.2f}")
        self.valueChanged.emit(actual)

    def reset(self) -> None:
        """Reset slider to default value"""
        self.slider.setValue(int(self.default * 100))

    def get_value(self) -> float:
        """Get current slider value"""
        normalized = self.slider.value() / 100.0
        result: float = normalized * (self.max_val - self.min_val) / 2
        return result


class NVIDIAEffectControl(QWidget):
    """
    Widget for controlling NVIDIA Broadcast effects.

    Provides toggles and intensity controls for AI effects.
    """

    effectChanged = pyqtSignal(str, int)

    def __init__(
        self,
        effect_name: str,
        display_name: str,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.effect_name = effect_name
        self.display_name = display_name

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Enable checkbox
        self.enabled = QCheckBox(self.display_name)
        self.enabled.setMinimumWidth(150)
        self.enabled.stateChanged.connect(self._on_state_changed)
        layout.addWidget(self.enabled)

        # Intensity slider
        self.intensity = QSlider(Qt.Orientation.Horizontal)
        self.intensity.setMinimum(0)
        self.intensity.setMaximum(100)
        self.intensity.setValue(50)
        self.intensity.setEnabled(False)
        self.intensity.valueChanged.connect(self._on_intensity_changed)
        layout.addWidget(self.intensity, 1)

        # Intensity label
        self.intensity_label = QLabel("50%")
        self.intensity_label.setMinimumWidth(40)
        self.intensity_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.intensity_label)

    def _on_state_changed(self, state: int) -> None:
        """Handle checkbox state change"""
        enabled = state == Qt.CheckState.Checked.value
        self.intensity.setEnabled(enabled)

        intensity_val = self.intensity.value() if enabled else 0
        self.effectChanged.emit(self.effect_name, intensity_val)

    def _on_intensity_changed(self, value: int) -> None:
        """Handle intensity slider change"""
        self.intensity_label.setText(f"{value}%")

        if self.enabled.isChecked():
            self.effectChanged.emit(self.effect_name, value)

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable the effect"""
        self.enabled.setChecked(enabled)


class QualityPanel(QWidget):
    """
    Main quality control panel.

    Provides comprehensive quality monitoring and control interface.
    """

    # Signals
    presetApplied = pyqtSignal(str)
    adjustmentChanged = pyqtSignal(str, float)
    nvEffectChanged = pyqtSignal(str, int)
    autoEnhanceRequested = pyqtSignal()
    resetRequested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.current_quality: Optional[Dict[str, Any]] = None
        self.websocket_connected = False

        self._setup_ui()
        self._setup_update_timer()

        logger.info("QualityPanel initialized")

    def _setup_ui(self) -> None:
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("Image Quality Controls")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Overall quality section
        self._create_overall_section(layout)

        # Metrics section
        self._create_metrics_section(layout)

        # Preset section
        self._create_preset_section(layout)

        # Manual controls section
        self._create_manual_controls_section(layout)

        # NVIDIA controls section
        self._create_nvidia_section(layout)

        # Status bar
        self._create_status_bar(layout)

        layout.addStretch()

    def _create_overall_section(self, parent_layout: QVBoxLayout) -> None:
        """Create overall quality section"""
        group = QGroupBox("Overall Quality")
        layout = QVBoxLayout(group)

        # Overall score
        score_layout = QHBoxLayout()

        self.overall_label = QLabel("Overall Score:")
        score_layout.addWidget(self.overall_label)

        self.overall_score = QLabel("--/100")
        score_font = QFont()
        score_font.setPointSize(24)
        score_font.setBold(True)
        self.overall_score.setFont(score_font)
        score_layout.addWidget(self.overall_score)

        score_layout.addStretch()

        # Status indicator
        self.overall_status = QLabel("●")
        self.overall_status.setStyleSheet(
            "color: #9E9E9E; font-size: 32px;"
        )
        score_layout.addWidget(self.overall_status)

        layout.addLayout(score_layout)

        # Progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        self.overall_progress.setValue(0)
        self.overall_progress.setTextVisible(False)
        self.overall_progress.setMinimumHeight(20)
        layout.addWidget(self.overall_progress)

        parent_layout.addWidget(group)

    def _create_metrics_section(self, parent_layout: QVBoxLayout) -> None:
        """Create quality metrics section"""
        group = QGroupBox("Quality Metrics")
        layout = QVBoxLayout(group)

        # Create metric widgets
        self.metrics = {
            'exposure': QualityMetricWidget("Exposure"),
            'focus': QualityMetricWidget("Focus"),
            'color_balance': QualityMetricWidget("Color Balance"),
            'noise': QualityMetricWidget("Noise"),
            'sharpness': QualityMetricWidget("Sharpness")
        }

        for metric in self.metrics.values():
            layout.addWidget(metric)

        parent_layout.addWidget(group)

    def _create_preset_section(self, parent_layout: QVBoxLayout) -> None:
        """Create preset selection section"""
        group = QGroupBox("Quality Presets")
        layout = QHBoxLayout(group)

        # Preset selector
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Professional",
            "Gaming",
            "Podcast",
            "Cinematic",
            "Low Light"
        ])
        layout.addWidget(self.preset_combo, 1)

        # Apply button
        apply_btn = QPushButton("Apply Preset")
        apply_btn.clicked.connect(self._on_apply_preset)
        layout.addWidget(apply_btn)

        # Auto-enhance button
        auto_btn = QPushButton("Auto Enhance")
        auto_btn.clicked.connect(self._on_auto_enhance)
        layout.addWidget(auto_btn)

        # Reset button
        reset_btn = QPushButton("Reset All")
        reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(reset_btn)

        parent_layout.addWidget(group)

    def _create_manual_controls_section(
        self,
        parent_layout: QVBoxLayout
    ) -> None:
        """Create manual adjustment controls section"""
        group = QGroupBox("Manual Adjustments")
        layout = QVBoxLayout(group)

        # Create control sliders
        self.controls = {
            'brightness': QualityControlSlider(
                "Brightness",
                -0.5, 0.5, 0.0
            ),
            'contrast': QualityControlSlider(
                "Contrast",
                -0.5, 0.5, 0.0
            ),
            'saturation': QualityControlSlider(
                "Saturation",
                -0.5, 0.5, 0.0
            ),
            'sharpness': QualityControlSlider(
                "Sharpness",
                0.0, 1.0, 0.0
            )
        }

        for name, control in self.controls.items():
            control.valueChanged.connect(
                lambda value, n=name: self._on_adjustment_changed(n, value)
            )
            layout.addWidget(control)

        parent_layout.addWidget(group)

    def _create_nvidia_section(self, parent_layout: QVBoxLayout) -> None:
        """Create NVIDIA Broadcast controls section"""
        group = QGroupBox("NVIDIA Broadcast Effects")
        layout = QVBoxLayout(group)

        # NVIDIA status
        self.nvidia_status_label = QLabel("Status: Checking...")
        layout.addWidget(self.nvidia_status_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Create effect controls
        self.nvidia_effects = {
            'noise_removal': NVIDIAEffectControl(
                'noise_removal',
                'Noise Removal'
            ),
            'background_blur': NVIDIAEffectControl(
                'background_blur',
                'Background Blur'
            ),
            'auto_frame': NVIDIAEffectControl(
                'auto_frame',
                'Auto Frame'
            ),
            'eye_contact': NVIDIAEffectControl(
                'eye_contact',
                'Eye Contact'
            )
        }

        for effect in self.nvidia_effects.values():
            effect.effectChanged.connect(self._on_nvidia_effect_changed)
            layout.addWidget(effect)

        parent_layout.addWidget(group)

    def _create_status_bar(self, parent_layout: QVBoxLayout) -> None:
        """Create status bar"""
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet(
            "QLabel { padding: 5px; background-color: #f0f0f0; "
            "border-radius: 3px; }"
        )
        parent_layout.addWidget(self.status_bar)

    def _setup_update_timer(self) -> None:
        """Setup periodic update timer"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_timestamp)
        self.update_timer.start(1000)  # Update every second

    def _on_apply_preset(self) -> None:
        """Handle apply preset button click"""
        preset_name = self.preset_combo.currentText().lower()
        self.presetApplied.emit(preset_name)
        self._update_status(f"Applied preset: {preset_name}")

    def _on_auto_enhance(self) -> None:
        """Handle auto enhance button click"""
        self.autoEnhanceRequested.emit()
        self._update_status("Auto-enhancement applied")

    def _on_reset(self) -> None:
        """Handle reset button click"""
        # Reset all sliders
        for control in self.controls.values():
            control.reset()

        # Disable NVIDIA effects
        for effect in self.nvidia_effects.values():
            effect.set_enabled(False)

        self.resetRequested.emit()
        self._update_status("All adjustments reset")

    def _on_adjustment_changed(self, name: str, value: float) -> None:
        """Handle manual adjustment change"""
        self.adjustmentChanged.emit(name, value)

    def _on_nvidia_effect_changed(self, effect: str, intensity: int) -> None:
        """Handle NVIDIA effect change"""
        self.nvEffectChanged.emit(effect, intensity)

    def _update_timestamp(self) -> None:
        """Update status bar timestamp"""
        if self.current_quality:
            timestamp = self.current_quality.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    elapsed = (datetime.now(dt.tzinfo) - dt).total_seconds()
                    self._update_status(
                        f"Last update: {elapsed:.0f}s ago"
                    )
                except Exception:
                    pass

    def update_quality(self, quality_data: Dict[str, Any]) -> None:
        """
        Update quality display with new data.

        Args:
            quality_data: Quality analysis data
        """
        self.current_quality = quality_data

        # Update overall score
        overall_score = quality_data.get('overall_score', 0)
        overall_status = quality_data.get('status', 'unknown')

        self.overall_score.setText(f"{overall_score:.1f}/100")
        self.overall_progress.setValue(int(overall_score))

        # Update overall status color
        if overall_status == "good":
            color = "#4CAF50"
        elif overall_status == "warning":
            color = "#FF9800"
        elif overall_status == "critical":
            color = "#F44336"
        else:
            color = "#9E9E9E"

        self.overall_status.setStyleSheet(
            f"color: {color}; font-size: 32px;"
        )
        self.overall_progress.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; }}"
        )

        # Update individual metrics
        scores = quality_data.get('scores', {})
        for metric_name, widget in self.metrics.items():
            metric_data = scores.get(metric_name, {})
            score = metric_data.get('score', 0)
            status = metric_data.get('status', 'unknown')
            widget.update_metric(score, status)

    def update_nvidia_status(self, available: bool, gpu_name: str = "") -> None:
        """
        Update NVIDIA status display.

        Args:
            available: Whether NVIDIA is available
            gpu_name: GPU name if available
        """
        if available:
            status_text = f"✓ Available: {gpu_name}"
            color = "#4CAF50"

            # Enable effect controls
            for effect in self.nvidia_effects.values():
                effect.setEnabled(True)
        else:
            status_text = "✗ Not Available (GPU required)"
            color = "#F44336"

            # Disable effect controls
            for effect in self.nvidia_effects.values():
                effect.setEnabled(False)

        self.nvidia_status_label.setText(status_text)
        self.nvidia_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def set_websocket_connected(self, connected: bool) -> None:
        """
        Update WebSocket connection status.

        Args:
            connected: Whether WebSocket is connected
        """
        self.websocket_connected = connected

        if connected:
            self._update_status("Live monitoring active")
        else:
            self._update_status("Live monitoring disconnected")

    def _update_status(self, message: str) -> None:
        """
        Update status bar message.

        Args:
            message: Status message
        """
        self.status_bar.setText(message)
        logger.debug(f"Status: {message}")
