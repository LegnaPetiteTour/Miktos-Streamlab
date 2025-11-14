"""
Quality Analyzer - Real-time video quality analysis

Analyzes video frames for quality metrics:
- Exposure (brightness levels)
- Focus (sharpness/blur detection)
- Color Balance (white balance)
- Noise (grain/noise levels)
- Sharpness (edge definition)
"""
# pyright: reportCallIssue=false, reportArgumentType=false

import cv2
import numpy as np
import logging
from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """Quality metrics"""
    EXPOSURE = "exposure"
    FOCUS = "focus"
    COLOR_BALANCE = "color_balance"
    NOISE = "noise"
    SHARPNESS = "sharpness"


@dataclass
class QualityScore:
    """Quality assessment score"""
    metric: QualityMetric
    value: float  # 0.0 - 1.0
    raw_value: float  # Raw measurement
    status: str  # "good", "warning", "critical"
    recommendation: str

    @property
    def percentage(self) -> float:
        """Get score as percentage"""
        return self.value * 100


@dataclass
class FrameQuality:
    """Complete frame quality assessment"""
    timestamp: float

    # Individual metrics
    exposure: QualityScore
    focus: QualityScore
    color_balance: QualityScore
    noise: QualityScore
    sharpness: QualityScore

    # Overall score
    overall_score: float  # 0-100

    # Dimensions
    width: int
    height: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'overall_score': self.overall_score,
            'metrics': {
                'exposure': {
                    'value': self.exposure.value,
                    'status': self.exposure.status,
                    'recommendation': self.exposure.recommendation
                },
                'focus': {
                    'value': self.focus.value,
                    'status': self.focus.status,
                    'recommendation': self.focus.recommendation
                },
                'color_balance': {
                    'value': self.color_balance.value,
                    'status': self.color_balance.status,
                    'recommendation': self.color_balance.recommendation
                },
                'noise': {
                    'value': self.noise.value,
                    'status': self.noise.status,
                    'recommendation': self.noise.recommendation
                },
                'sharpness': {
                    'value': self.sharpness.value,
                    'status': self.sharpness.status,
                    'recommendation': self.sharpness.recommendation
                }
            },
            'dimensions': {
                'width': self.width,
                'height': self.height
            }
        }


class QualityAnalyzer:
    """
    Analyzes video frame quality in real-time.

    Features:
    - Exposure detection (under/over-exposed)
    - Focus/sharpness analysis
    - Color balance assessment
    - Noise level detection
    - Overall quality scoring
    """

    def __init__(self) -> None:
        """Initialize quality analyzer"""
        logger.info("QualityAnalyzer initialized")

    def analyze_frame(self, frame: np.ndarray) -> FrameQuality:
        """
        Analyze a video frame.

        Args:
            frame: BGR image (OpenCV format)

        Returns:
            FrameQuality assessment
        """
        import time
        timestamp = time.time()

        # Analyze each metric
        exposure = self._analyze_exposure(frame)
        focus = self._analyze_focus(frame)
        color_balance = self._analyze_color_balance(frame)
        noise = self._analyze_noise(frame)
        sharpness = self._analyze_sharpness(frame)

        # Calculate overall score
        overall = self._calculate_overall_score(
            exposure, focus, color_balance, noise, sharpness
        )

        h, w = frame.shape[:2]

        return FrameQuality(
            timestamp=timestamp,
            exposure=exposure,
            focus=focus,
            color_balance=color_balance,
            noise=noise,
            sharpness=sharpness,
            overall_score=overall,
            width=w,
            height=h
        )

    def _analyze_exposure(self, frame: np.ndarray) -> QualityScore:
        """Analyze frame exposure"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Calculate mean brightness
        mean_brightness = float(np.mean(gray))

        # Normalize to 0-1 (optimal around 127)
        # Score: 1.0 at optimal, 0.0 at extremes
        optimal = 127
        distance = abs(mean_brightness - optimal) / optimal
        score = max(0.0, 1.0 - distance)

        # Determine status
        if mean_brightness < 60:
            status = "critical"
            recommendation = (
                "Scene is under-exposed. Increase lighting or gain."
            )
        elif mean_brightness < 90:
            status = "warning"
            recommendation = (
                "Scene is slightly dark. "
                "Consider increasing brightness."
            )
        elif mean_brightness > 200:
            status = "critical"
            recommendation = (
                "Scene is over-exposed. Reduce lighting or gain."
            )
        elif mean_brightness > 170:
            status = "warning"
            recommendation = (
                "Scene is slightly bright. "
                "Consider reducing exposure."
            )
        else:
            status = "good"
            recommendation = "Exposure is optimal."

        return QualityScore(
            metric=QualityMetric.EXPOSURE,
            value=score,
            raw_value=mean_brightness,
            status=status,
            recommendation=recommendation
        )

    def _analyze_focus(self, frame: np.ndarray) -> QualityScore:
        """Analyze frame focus/sharpness using Laplacian variance"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Laplacian variance (higher = sharper)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = float(laplacian.var())

        # Normalize (typical range: 0-500)
        score = min(1.0, variance / 500.0)

        # Determine status
        if variance < 50:
            status = "critical"
            recommendation = "Image is out of focus or very blurry."
        elif variance < 100:
            status = "warning"
            recommendation = "Image could be sharper. Check camera focus."
        else:
            status = "good"
            recommendation = "Focus is good."

        return QualityScore(
            metric=QualityMetric.FOCUS,
            value=score,
            raw_value=variance,
            status=status,
            recommendation=recommendation
        )

    def _analyze_color_balance(self, frame: np.ndarray) -> QualityScore:
        """Analyze color balance (white balance)"""
        # Calculate mean of each channel
        b_mean = float(np.mean(frame[:, :, 0]))
        g_mean = float(np.mean(frame[:, :, 1]))
        r_mean = float(np.mean(frame[:, :, 2]))

        # Calculate deviation from gray (equal RGB)
        avg = (b_mean + g_mean + r_mean) / 3

        # Color cast detection
        b_dev = abs(b_mean - avg)
        g_dev = abs(g_mean - avg)
        r_dev = abs(r_mean - avg)

        max_dev = max(b_dev, g_dev, r_dev)

        # Score: 1.0 = perfect balance, 0.0 = severe cast
        score = max(0.0, 1.0 - (max_dev / 50.0))

        # Determine color cast
        if b_dev == max_dev:
            cast = "blue"
        elif r_dev == max_dev:
            cast = "red/warm"
        else:
            cast = "green"

        # Status
        if max_dev > 30:
            status = "warning"
            recommendation = (
                f"Strong {cast} color cast detected. "
                "Adjust white balance."
            )
        elif max_dev > 15:
            status = "warning"
            recommendation = (
                f"Slight {cast} tint. "
                "Consider white balance adjustment."
            )
        else:
            status = "good"
            recommendation = "Color balance is good."

        return QualityScore(
            metric=QualityMetric.COLOR_BALANCE,
            value=score,
            raw_value=max_dev,
            status=status,
            recommendation=recommendation
        )

    def _analyze_noise(self, frame: np.ndarray) -> QualityScore:
        """Estimate noise level"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Use standard deviation of Laplacian as noise estimate
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        noise_estimate = float(np.std(laplacian))

        # Normalize (typical range: 0-50)
        score = max(0.0, 1.0 - (noise_estimate / 50.0))

        # Status
        if noise_estimate > 30:
            status = "critical"
            recommendation = (
                "High noise level. "
                "Improve lighting or use denoising."
            )
        elif noise_estimate > 20:
            status = "warning"
            recommendation = "Moderate noise. Consider better lighting."
        else:
            status = "good"
            recommendation = "Noise level is acceptable."

        return QualityScore(
            metric=QualityMetric.NOISE,
            value=score,
            raw_value=noise_estimate,
            status=status,
            recommendation=recommendation
        )

    def _analyze_sharpness(self, frame: np.ndarray) -> QualityScore:
        """Analyze image sharpness"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Use Sobel edge detection
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

        # Edge magnitude
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        sharpness = float(np.mean(magnitude))

        # Normalize (typical range: 0-100)
        score = min(1.0, sharpness / 100.0)

        # Status
        if sharpness < 20:
            status = "warning"
            recommendation = (
                "Image lacks sharpness. "
                "Check focus or add sharpening filter."
            )
        elif sharpness > 80:
            status = "warning"
            recommendation = "Image may be over-sharpened."
        else:
            status = "good"
            recommendation = "Sharpness is good."

        return QualityScore(
            metric=QualityMetric.SHARPNESS,
            value=score,
            raw_value=sharpness,
            status=status,
            recommendation=recommendation
        )

    def _calculate_overall_score(
        self,
        exposure: QualityScore,
        focus: QualityScore,
        color_balance: QualityScore,
        noise: QualityScore,
        sharpness: QualityScore
    ) -> float:
        """Calculate weighted overall quality score (0-100)"""

        # Weights (sum to 1.0)
        weights = {
            'exposure': 0.30,
            'focus': 0.25,
            'color_balance': 0.20,
            'noise': 0.15,
            'sharpness': 0.10
        }

        weighted_sum = (
            exposure.value * weights['exposure'] +
            focus.value * weights['focus'] +
            color_balance.value * weights['color_balance'] +
            noise.value * weights['noise'] +
            sharpness.value * weights['sharpness']
        )

        return weighted_sum * 100  # Convert to 0-100

    def get_quick_assessment(
        self,
        frame: np.ndarray
    ) -> Dict[str, Any]:
        """
        Quick assessment without full analysis.
        Returns basic metrics only.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        return {
            'brightness': float(np.mean(gray)),
            'contrast': float(np.std(gray)),
            'sharpness': float(cv2.Laplacian(gray, cv2.CV_64F).var())
        }
