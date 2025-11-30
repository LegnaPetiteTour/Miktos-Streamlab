"""
Quality Service - Wraps existing quality analyzer

This service provides video quality analysis capabilities by wrapping
your existing quality_analyzer.py module.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Setup Backend integration
from config.backend_integration import setup_backend_path
setup_backend_path()

try:
    from core.quality_analyzer import QualityAnalyzer  # type: ignore
    QUALITY_ANALYZER_AVAILABLE = True
except ImportError as e:
    QualityAnalyzer = None
    QUALITY_ANALYZER_AVAILABLE = False
    logging.warning(f"Quality analyzer module not available: {e}")


logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """A detected quality issue"""
    type: str  # "exposure", "focus", "noise", "color"
    severity: str  # "low", "medium", "high", "critical"
    message: str
    recommendation: str
    metric_value: Optional[float] = None


@dataclass
class QualityAnalysis:
    """Complete quality analysis result"""
    timestamp: datetime
    camera_id: str
    overall_score: float  # 0.0 - 100.0

    # Individual metrics
    exposure_score: float
    focus_score: float
    noise_score: float
    color_score: float

    # Detected issues
    issues: List[QualityIssue]

    # Raw metrics
    raw_metrics: Dict[str, Any]

    def is_acceptable(self) -> bool:
        """Check if quality is acceptable (>70%)"""
        return self.overall_score >= 70.0

    def get_critical_issues(self) -> List[QualityIssue]:
        """Get only critical issues"""
        return [i for i in self.issues if i.severity == "critical"]


@dataclass
class ComparisonReport:
    """Comparison of multiple cameras"""
    cameras: List[str]
    analyses: Dict[str, QualityAnalysis]
    best_camera: str
    worst_camera: str
    recommendations: List[str]


class QualityService:
    """
    Video quality analysis service.

    Analyzes video streams for exposure, focus, noise, and color issues.
    Provides recommendations for improvement.

    Example:
        ```python
        service = QualityService()

        # Analyze a camera's stream
        analysis = await service.analyze_stream(
            camera_id="phone-001",
            duration=5.0  # 5 seconds
        )

        print(f"Overall score: {analysis.overall_score}/100")

        if not analysis.is_acceptable():
            print("Issues found:")
            for issue in analysis.issues:
                print(f"  - {issue.type}: {issue.message}")
                print(f"    Fix: {issue.recommendation}")
        ```
    """

    def __init__(self):
        if not QUALITY_ANALYZER_AVAILABLE:
            logger.warning(
                "Quality analyzer module not available - "
                "service will operate in limited mode"
            )
            self._analyzer = None
            self._exposure_threshold = 0.7
            self._focus_threshold = 0.7
            self._noise_threshold = 0.7
            self._color_threshold = 0.7
            return

        self._analyzer = QualityAnalyzer()

        # Quality thresholds
        self._exposure_threshold = 0.7  # 70%
        self._focus_threshold = 0.7
        self._noise_threshold = 0.7
        self._color_threshold = 0.7

        logger.info("Quality service initialized")

    async def analyze_frame(
        self,
        frame_data: Any,
        camera_id: str
    ) -> QualityAnalysis:
        """
        Analyze a single video frame.

        Args:
            frame_data: Frame data (numpy array or similar)
            camera_id: ID of camera this frame is from

        Returns:
            Quality analysis result
        """
        logger.debug(f"Analyzing frame from camera: {camera_id}")

        try:
            # Call existing quality analyzer
            metrics = await self._analyzer.analyze_frame(frame_data)

            # Extract metrics
            exposure_score = metrics.get("exposure_score", 0.0) * 100
            focus_score = metrics.get("focus_score", 0.0) * 100
            noise_score = metrics.get("noise_score", 0.0) * 100
            color_score = metrics.get("color_score", 0.0) * 100

            # Calculate overall score (weighted average)
            overall_score = (
                exposure_score * 0.3 +
                focus_score * 0.3 +
                noise_score * 0.2 +
                color_score * 0.2
            )

            # Detect issues
            issues = self._detect_issues(
                exposure_score,
                focus_score,
                noise_score,
                color_score,
                metrics
            )

            analysis = QualityAnalysis(
                timestamp=datetime.now(),
                camera_id=camera_id,
                overall_score=overall_score,
                exposure_score=exposure_score,
                focus_score=focus_score,
                noise_score=noise_score,
                color_score=color_score,
                issues=issues,
                raw_metrics=metrics,
            )

            logger.info(f"Frame analysis complete: {overall_score:.1f}/100")
            return analysis

        except Exception as e:
            logger.error(f"Frame analysis failed: {e}", exc_info=True)
            raise

    async def analyze_stream(
        self,
        camera_id: str,
        duration: float = 5.0,
        sample_interval: float = 1.0,
    ) -> QualityAnalysis:
        """
        Analyze a video stream over time.

        Args:
            camera_id: Camera to analyze
            duration: How long to analyze (seconds)
            sample_interval: How often to sample frames (seconds)

        Returns:
            Aggregated quality analysis
        """
        logger.info(
            f"Starting stream analysis for camera {camera_id} "
            f"(duration={duration}s)"
        )

        try:
            # Call existing analyzer's stream analysis
            metrics = await self._analyzer.analyze_stream(
                camera_id=camera_id,
                duration=duration,
                sample_interval=sample_interval,
            )

            # Process results similar to single frame
            exposure_score = metrics.get("avg_exposure_score", 0.0) * 100
            focus_score = metrics.get("avg_focus_score", 0.0) * 100
            noise_score = metrics.get("avg_noise_score", 0.0) * 100
            color_score = metrics.get("avg_color_score", 0.0) * 100

            overall_score = (
                exposure_score * 0.3 +
                focus_score * 0.3 +
                noise_score * 0.2 +
                color_score * 0.2
            )

            issues = self._detect_issues(
                exposure_score,
                focus_score,
                noise_score,
                color_score,
                metrics
            )

            analysis = QualityAnalysis(
                timestamp=datetime.now(),
                camera_id=camera_id,
                overall_score=overall_score,
                exposure_score=exposure_score,
                focus_score=focus_score,
                noise_score=noise_score,
                color_score=color_score,
                issues=issues,
                raw_metrics=metrics,
            )

            logger.info(f"Stream analysis complete: {overall_score:.1f}/100")
            return analysis

        except Exception as e:
            logger.error(f"Stream analysis failed: {e}", exc_info=True)
            raise

    def _detect_issues(
        self,
        exposure_score: float,
        focus_score: float,
        noise_score: float,
        color_score: float,
        metrics: Dict[str, Any],
    ) -> List[QualityIssue]:
        """
        Detect quality issues and generate recommendations.

        Args:
            exposure_score: Exposure quality (0-100)
            focus_score: Focus quality (0-100)
            noise_score: Noise level (0-100, higher is better)
            color_score: Color quality (0-100)
            metrics: Raw analyzer metrics

        Returns:
            List of detected issues
        """
        issues = []

        # Check exposure
        if exposure_score < self._exposure_threshold * 100:
            if exposure_score < 30:
                severity = "critical"
                message = "Severely underexposed or overexposed"
                recommendation = "Adjust camera exposure settings or lighting"
            elif exposure_score < 50:
                severity = "high"
                message = "Poor exposure levels"
                recommendation = "Increase/decrease exposure by 1-2 stops"
            else:
                severity = "medium"
                message = "Suboptimal exposure"
                recommendation = "Fine-tune exposure for better image quality"

            issues.append(QualityIssue(
                type="exposure",
                severity=severity,
                message=message,
                recommendation=recommendation,
                metric_value=exposure_score,
            ))

        # Check focus
        if focus_score < self._focus_threshold * 100:
            if focus_score < 30:
                severity = "critical"
                message = "Image severely out of focus"
                recommendation = "Tap to focus on subject or clean camera lens"
            elif focus_score < 50:
                severity = "high"
                message = "Image soft/blurry"
                recommendation = "Enable auto-focus or manually adjust focus"
            else:
                severity = "medium"
                message = "Slight focus issues"
                recommendation = "Fine-tune focus for sharper image"

            issues.append(QualityIssue(
                type="focus",
                severity=severity,
                message=message,
                recommendation=recommendation,
                metric_value=focus_score,
            ))

        # Check noise
        if noise_score < self._noise_threshold * 100:
            if noise_score < 30:
                severity = "critical"
                message = "Extreme image noise/grain"
                recommendation = "Improve lighting significantly or lower ISO"
            elif noise_score < 50:
                severity = "high"
                message = "High noise levels"
                recommendation = "Add more light or enable noise reduction"
            else:
                severity = "medium"
                message = "Moderate noise present"
                recommendation = "Consider applying noise reduction filter"

            issues.append(QualityIssue(
                type="noise",
                severity=severity,
                message=message,
                recommendation=recommendation,
                metric_value=noise_score,
            ))

        # Check color
        if color_score < self._color_threshold * 100:
            if color_score < 30:
                severity = "high"
                message = "Poor color accuracy"
                recommendation = "Adjust white balance or color temperature"
            elif color_score < 50:
                severity = "medium"
                message = "Color cast detected"
                recommendation = "Fine-tune white balance settings"
            else:
                severity = "low"
                message = "Slight color issues"
                recommendation = "Consider color correction in post"

            issues.append(QualityIssue(
                type="color",
                severity=severity,
                message=message,
                recommendation=recommendation,
                metric_value=color_score,
            ))

        return issues

    async def compare_cameras(
        self,
        camera_ids: List[str],
        duration: float = 5.0,
    ) -> ComparisonReport:
        """
        Compare quality across multiple cameras.

        Args:
            camera_ids: List of cameras to compare
            duration: Analysis duration per camera

        Returns:
            Comparison report
        """
        logger.info(f"Comparing {len(camera_ids)} cameras")

        analyses = {}

        for camera_id in camera_ids:
            try:
                analysis = await self.analyze_stream(camera_id, duration)
                analyses[camera_id] = analysis
            except Exception as e:
                logger.error(f"Failed to analyze camera {camera_id}: {e}")

        if not analyses:
            raise RuntimeError("No cameras could be analyzed")

        # Find best and worst
        sorted_cameras = sorted(
            analyses.items(),
            key=lambda x: x[1].overall_score,
            reverse=True
        )

        best_camera = sorted_cameras[0][0]
        worst_camera = sorted_cameras[-1][0]

        # Generate recommendations
        recommendations = []

        worst_analysis = analyses[worst_camera]
        if worst_analysis.exposure_score < 50:
            recommendations.append(
                f"Camera {worst_camera}: Adjust exposure "
                f"(currently {worst_analysis.exposure_score:.0f}/100)"
            )

        if worst_analysis.focus_score < 50:
            recommendations.append(
                f"Camera {worst_camera}: Improve focus "
                f"(currently {worst_analysis.focus_score:.0f}/100)"
            )

        # Check for consistency
        scores = [a.overall_score for a in analyses.values()]
        if max(scores) - min(scores) > 30:
            recommendations.append(
                "Large quality variance between cameras - "
                "consider matching settings"
            )

        report = ComparisonReport(
            cameras=camera_ids,
            analyses=analyses,
            best_camera=best_camera,
            worst_camera=worst_camera,
            recommendations=recommendations,
        )

        logger.info(
            f"Comparison complete - Best: {best_camera} "
            f"({analyses[best_camera].overall_score:.1f}), "
            f"Worst: {worst_camera} "
            f"({analyses[worst_camera].overall_score:.1f})"
        )

        return report

    def get_recommendations(self, analysis: QualityAnalysis) -> List[str]:
        """
        Get prioritized recommendations based on analysis.

        Args:
            analysis: Quality analysis result

        Returns:
            List of actionable recommendations
        """
        recommendations = []

        # Sort issues by severity
        critical = [i for i in analysis.issues if i.severity == "critical"]
        high = [i for i in analysis.issues if i.severity == "high"]
        medium = [i for i in analysis.issues if i.severity == "medium"]

        # Add critical issues first
        for issue in critical:
            recommendations.append(
                f"CRITICAL - {issue.type}: {issue.recommendation}"
            )

        for issue in high:
            recommendations.append(
                f"Important - {issue.type}: {issue.recommendation}"
            )

        for issue in medium:
            recommendations.append(
                f"Suggested - {issue.type}: {issue.recommendation}"
            )

        # Add general recommendations if quality is good
        if analysis.overall_score >= 80 and not recommendations:
            recommendations.append("Quality is excellent - no changes needed")
        elif analysis.overall_score >= 70 and not recommendations:
            recommendations.append(
                "Quality is acceptable - minor improvements possible")

        return recommendations

    def is_available(self) -> bool:
        """Check if quality analyzer is available"""
        return QUALITY_ANALYZER_AVAILABLE
