"""
Test Quality Panel UI - Demonstration of quality controls

Shows quality panel with simulated data.
"""

import sys
import logging
from typing import Dict, Any

# Add src to path
sys.path.insert(0, '/Users/atorrella/Desktop/Miktos Streamlab/src')

from PyQt6.QtWidgets import (  # type: ignore[import-not-found]  # noqa: E402
    QApplication,
    QMainWindow
)
from PyQt6.QtCore import QTimer  # type: ignore[import-not-found]  # noqa: E402

from ui.quality_panel import QualityPanel  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QualityPanelDemo(QMainWindow):
    """Demo window for quality panel"""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Quality Control Panel - Demo")
        self.setGeometry(100, 100, 600, 800)

        # Create quality panel
        self.quality_panel = QualityPanel(self)
        self.setCentralWidget(self.quality_panel)

        # Connect signals
        self.quality_panel.presetApplied.connect(self._on_preset_applied)
        self.quality_panel.adjustmentChanged.connect(
            self._on_adjustment_changed
        )
        self.quality_panel.nvEffectChanged.connect(
            self._on_nv_effect_changed
        )
        self.quality_panel.autoEnhanceRequested.connect(
            self._on_auto_enhance
        )
        self.quality_panel.resetRequested.connect(self._on_reset)

        # Simulate NVIDIA status
        self.quality_panel.update_nvidia_status(True, "NVIDIA RTX 3080")

        # Simulate WebSocket connection
        self.quality_panel.set_websocket_connected(True)

        # Start simulated quality updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._simulate_quality_update)
        self.update_timer.start(2000)  # Update every 2 seconds

        # Initial update
        self._simulate_quality_update()

        logger.info("Quality panel demo started")

    def _simulate_quality_update(self) -> None:
        """Simulate quality update from WebSocket"""
        import random
        from datetime import datetime, UTC

        # Generate random quality data
        quality_data: Dict[str, Any] = {
            'overall_score': random.uniform(70, 95),
            'status': random.choice(['good', 'warning']),
            'timestamp': datetime.now(UTC).isoformat() + 'Z',
            'scores': {
                'exposure': {
                    'score': random.uniform(75, 95),
                    'status': 'good'
                },
                'focus': {
                    'score': random.uniform(70, 90),
                    'status': random.choice(['good', 'warning'])
                },
                'color_balance': {
                    'score': random.uniform(75, 95),
                    'status': 'good'
                },
                'noise': {
                    'score': random.uniform(80, 95),
                    'status': 'good'
                },
                'sharpness': {
                    'score': random.uniform(70, 90),
                    'status': random.choice(['good', 'warning'])
                }
            },
            'recommendations': []
        }

        self.quality_panel.update_quality(quality_data)

    def _on_preset_applied(self, preset_name: str) -> None:
        """Handle preset applied"""
        logger.info(f"Preset applied: {preset_name}")

    def _on_adjustment_changed(self, adj_type: str, value: float) -> None:
        """Handle adjustment changed"""
        logger.info(f"Adjustment: {adj_type} = {value:.2f}")

    def _on_nv_effect_changed(self, effect: str, intensity: int) -> None:
        """Handle NVIDIA effect changed"""
        logger.info(f"NVIDIA effect: {effect} = {intensity}%")

    def _on_auto_enhance(self) -> None:
        """Handle auto-enhance requested"""
        logger.info("Auto-enhance requested")

    def _on_reset(self) -> None:
        """Handle reset requested"""
        logger.info("Reset requested")


def main() -> None:
    """Run quality panel demo"""
    app = QApplication(sys.argv)

    demo = QualityPanelDemo()
    demo.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
