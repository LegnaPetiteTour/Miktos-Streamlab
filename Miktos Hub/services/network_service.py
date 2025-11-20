"""
Network Service - Wraps existing network monitoring

This service provides network testing and monitoring capabilities by wrapping
your existing network.py module.
"""

import sys
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Add existing backend to path
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

try:
    from core.network import NetworkMonitor, BandwidthTester
    NETWORK_AVAILABLE = True
except ImportError as e:
    NetworkMonitor = None
    BandwidthTester = None
    NETWORK_AVAILABLE = False
    logging.warning(f"Network module not available: {e}")

from config import get_config

logger = logging.getLogger(__name__)


class NetworkQuality(Enum):
    """Network quality levels"""
    EXCELLENT = "excellent"  # <50ms latency, <1% loss
    GOOD = "good"            # 50-100ms latency, 1-3% loss
    FAIR = "fair"            # 100-200ms latency, 3-5% loss
    POOR = "poor"            # >200ms latency, >5% loss
    CRITICAL = "critical"    # >500ms latency or >10% loss


@dataclass
class BandwidthTestResult:
    """Result of bandwidth test"""
    timestamp: datetime
    target_bitrate_kbps: float
    achieved_bitrate_kbps: float
    
    # Quality metrics
    average_rtt_ms: float
    jitter_ms: float
    packet_loss_percent: float
    
    # Result
    is_sufficient: bool
    quality: NetworkQuality
    recommendation: str
    
    def get_headroom_percent(self) -> float:
        """Get bandwidth headroom as percentage"""
        if self.target_bitrate_kbps == 0:
            return 0.0
        return ((self.achieved_bitrate_kbps - self.target_bitrate_kbps) / self.target_bitrate_kbps) * 100


@dataclass
class NetworkMetrics:
    """Real-time network metrics"""
    timestamp: datetime
    camera_id: str
    
    # Connection info
    is_connected: bool
    connection_type: str  # "wifi", "lte", "ethernet"
    signal_strength_dbm: Optional[int] = None
    
    # Performance metrics
    upload_bitrate_kbps: float = 0.0
    rtt_ms: float = 0.0
    jitter_ms: float = 0.0
    packet_loss_percent: float = 0.0
    
    # Quality
    quality: NetworkQuality = NetworkQuality.POOR
    
    def is_healthy(self) -> bool:
        """Check if network is healthy"""
        return (
            self.is_connected
            and self.quality in [NetworkQuality.EXCELLENT, NetworkQuality.GOOD]
            and self.packet_loss_percent < 3.0
        )


@dataclass
class PredictionResult:
    """Network stability prediction"""
    will_be_stable: bool
    confidence: float  # 0.0-1.0
    predicted_quality: NetworkQuality
    time_to_degradation_seconds: Optional[float] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class MonitoringSession:
    """Active network monitoring session"""
    
    def __init__(self, camera_id: str, monitor):
        self.camera_id = camera_id
        self._monitor = monitor
        self._active = True
        self.metrics_history: List[NetworkMetrics] = []
    
    async def get_current_metrics(self) -> NetworkMetrics:
        """Get current network metrics"""
        return await self._monitor.get_metrics(self.camera_id)
    
    async def stop(self):
        """Stop monitoring"""
        self._active = False
        await self._monitor.stop_monitoring(self.camera_id)
    
    def is_active(self) -> bool:
        """Check if monitoring is active"""
        return self._active


class NetworkService:
    """
    Network monitoring and testing service.
    
    Provides bandwidth testing, real-time network monitoring,
    and stability predictions for streaming.
    
    Example:
        ```python
        service = NetworkService()
        
        # Pre-flight bandwidth test
        result = await service.test_bandwidth(
            target_bitrate=6000  # 6 Mbps
        )
        
        if result.is_sufficient:
            print(f"Network ready: {result.achieved_bitrate_kbps/1000:.1f} Mbps")
        else:
            print(f"WARNING: {result.recommendation}")
        
        # Start monitoring
        session = await service.start_monitoring("phone-001")
        
        # Check metrics periodically
        while True:
            metrics = await session.get_current_metrics()
            print(f"Upload: {metrics.upload_bitrate_kbps/1000:.1f} Mbps")
            print(f"Quality: {metrics.quality.value}")
            
            if not metrics.is_healthy():
                print("WARNING: Network degrading!")
            
            await asyncio.sleep(5)
        ```
    """
    
    def __init__(self):
        if not NETWORK_AVAILABLE:
            raise RuntimeError("Network module not available - check backend installation")
        
        config = get_config()
        
        self._tester = BandwidthTester()
        self._monitor = NetworkMonitor(
            check_interval=config.camera.health_check_interval_seconds
        )
        
        # Active monitoring sessions
        self._monitoring_sessions: Dict[str, MonitoringSession] = {}
        
        logger.info("Network service initialized")
    
    async def test_bandwidth(
        self,
        target_bitrate: float,
        duration: float = 10.0,
        test_host: str = "8.8.8.8",
    ) -> BandwidthTestResult:
        """
        Test upload bandwidth to verify streaming capacity.
        
        Args:
            target_bitrate: Target bitrate in kbps (e.g., 6000 for 6 Mbps)
            duration: Test duration in seconds
            test_host: Host to test against
            
        Returns:
            Bandwidth test result with recommendations
        """
        logger.info(f"Starting bandwidth test (target: {target_bitrate/1000:.1f} Mbps, duration: {duration}s)")
        
        try:
            # Run test via existing tester
            result = await self._tester.test_upload(
                target_bitrate_kbps=target_bitrate,
                duration_seconds=duration,
                host=test_host,
            )
            
            # Extract metrics
            achieved = result.get("achieved_bitrate_kbps", 0.0)
            rtt = result.get("average_rtt_ms", 0.0)
            jitter = result.get("jitter_ms", 0.0)
            loss = result.get("packet_loss_percent", 0.0)
            
            # Determine if sufficient
            is_sufficient = (
                achieved >= target_bitrate * 0.9  # Allow 10% margin
                and loss < 3.0  # Less than 3% loss
                and rtt < 200.0  # Less than 200ms RTT
            )
            
            # Determine quality
            quality = self._classify_network_quality(rtt, loss)
            
            # Generate recommendation
            if is_sufficient:
                headroom = ((achieved - target_bitrate) / target_bitrate) * 100
                recommendation = f"Network ready for streaming ({headroom:.0f}% headroom)"
            else:
                issues = []
                if achieved < target_bitrate:
                    issues.append(f"insufficient bandwidth ({achieved/1000:.1f}/{target_bitrate/1000:.1f} Mbps)")
                if loss >= 3.0:
                    issues.append(f"high packet loss ({loss:.1f}%)")
                if rtt >= 200.0:
                    issues.append(f"high latency ({rtt:.0f}ms)")
                
                recommendation = f"Network not ready: {', '.join(issues)}"
            
            test_result = BandwidthTestResult(
                timestamp=datetime.now(),
                target_bitrate_kbps=target_bitrate,
                achieved_bitrate_kbps=achieved,
                average_rtt_ms=rtt,
                jitter_ms=jitter,
                packet_loss_percent=loss,
                is_sufficient=is_sufficient,
                quality=quality,
                recommendation=recommendation,
            )
            
            logger.info(
                f"Bandwidth test complete: {achieved/1000:.1f} Mbps achieved, "
                f"quality={quality.value}, sufficient={is_sufficient}"
            )
            
            return test_result
            
        except Exception as e:
            logger.error(f"Bandwidth test failed: {e}", exc_info=True)
            raise
    
    async def start_monitoring(self, camera_id: str) -> MonitoringSession:
        """
        Start real-time network monitoring for a camera.
        
        Args:
            camera_id: Camera to monitor
            
        Returns:
            Monitoring session
        """
        logger.info(f"Starting network monitoring for camera {camera_id}")
        
        if camera_id in self._monitoring_sessions:
            logger.warning(f"Already monitoring camera {camera_id}, returning existing session")
            return self._monitoring_sessions[camera_id]
        
        try:
            # Start monitoring via existing monitor
            await self._monitor.start_monitoring(camera_id)
            
            # Create session
            session = MonitoringSession(camera_id, self._monitor)
            self._monitoring_sessions[camera_id] = session
            
            logger.info(f"Monitoring started for camera {camera_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}", exc_info=True)
            raise
    
    async def stop_monitoring(self, camera_id: str) -> None:
        """
        Stop network monitoring for a camera.
        
        Args:
            camera_id: Camera to stop monitoring
        """
        logger.info(f"Stopping network monitoring for camera {camera_id}")
        
        if camera_id not in self._monitoring_sessions:
            logger.warning(f"No monitoring session for camera {camera_id}")
            return
        
        session = self._monitoring_sessions[camera_id]
        await session.stop()
        
        del self._monitoring_sessions[camera_id]
        
        logger.info(f"Monitoring stopped for camera {camera_id}")
    
    async def get_metrics(self, camera_id: str) -> NetworkMetrics:
        """
        Get current network metrics for a camera.
        
        Args:
            camera_id: Camera to get metrics for
            
        Returns:
            Current network metrics
        """
        try:
            # Get metrics from monitor
            raw_metrics = await self._monitor.get_metrics(camera_id)
            
            # Map to our metrics format
            metrics = NetworkMetrics(
                timestamp=datetime.now(),
                camera_id=camera_id,
                is_connected=raw_metrics.get("is_connected", False),
                connection_type=raw_metrics.get("connection_type", "unknown"),
                signal_strength_dbm=raw_metrics.get("signal_strength_dbm"),
                upload_bitrate_kbps=raw_metrics.get("upload_bitrate_kbps", 0.0),
                rtt_ms=raw_metrics.get("rtt_ms", 0.0),
                jitter_ms=raw_metrics.get("jitter_ms", 0.0),
                packet_loss_percent=raw_metrics.get("packet_loss_percent", 0.0),
                quality=self._classify_network_quality(
                    raw_metrics.get("rtt_ms", 0.0),
                    raw_metrics.get("packet_loss_percent", 0.0),
                ),
            )
            
            # Store in session history if monitoring
            if camera_id in self._monitoring_sessions:
                session = self._monitoring_sessions[camera_id]
                session.metrics_history.append(metrics)
                
                # Keep only last 100 metrics
                if len(session.metrics_history) > 100:
                    session.metrics_history = session.metrics_history[-100:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}", exc_info=True)
            raise
    
    async def predict_stability(
        self,
        camera_id: str,
        duration_minutes: float = 5.0,
    ) -> PredictionResult:
        """
        Predict network stability based on historical metrics.
        
        Args:
            camera_id: Camera to predict for
            duration_minutes: How far ahead to predict
            
        Returns:
            Prediction result
        """
        logger.info(f"Predicting network stability for camera {camera_id} ({duration_minutes} minutes ahead)")
        
        if camera_id not in self._monitoring_sessions:
            raise RuntimeError(f"No monitoring session for camera {camera_id}")
        
        session = self._monitoring_sessions[camera_id]
        history = session.metrics_history
        
        if len(history) < 5:
            # Not enough data
            return PredictionResult(
                will_be_stable=True,
                confidence=0.3,
                predicted_quality=NetworkQuality.FAIR,
                recommendations=["Not enough historical data for accurate prediction"],
            )
        
        # Analyze trends
        recent = history[-10:]  # Last 10 metrics
        
        # Calculate trends
        bitrate_trend = self._calculate_trend([m.upload_bitrate_kbps for m in recent])
        rtt_trend = self._calculate_trend([m.rtt_ms for m in recent])
        loss_trend = self._calculate_trend([m.packet_loss_percent for m in recent])
        
        # Current quality
        current = recent[-1]
        current_quality = current.quality
        
        # Predict future quality
        will_degrade = (
            bitrate_trend < -100  # Dropping >100 kbps per sample
            or rtt_trend > 10  # Increasing >10ms per sample
            or loss_trend > 0.5  # Increasing >0.5% per sample
        )
        
        if will_degrade:
            predicted_quality = NetworkQuality.POOR
            will_be_stable = False
            confidence = 0.7
            time_to_degradation = 60.0  # 1 minute estimate
            recommendations = [
                "Network degradation detected",
                "Consider reducing bitrate",
                "Check for competing network traffic",
            ]
        else:
            predicted_quality = current_quality
            will_be_stable = current_quality in [NetworkQuality.EXCELLENT, NetworkQuality.GOOD]
            confidence = 0.8
            time_to_degradation = None
            recommendations = []
            
            if current_quality == NetworkQuality.FAIR:
                recommendations.append("Network stable but marginal - monitor closely")
        
        result = PredictionResult(
            will_be_stable=will_be_stable,
            confidence=confidence,
            predicted_quality=predicted_quality,
            time_to_degradation_seconds=time_to_degradation,
            recommendations=recommendations,
        )
        
        logger.info(
            f"Prediction: stable={will_be_stable}, quality={predicted_quality.value}, "
            f"confidence={confidence:.1f}"
        )
        
        return result
    
    def _classify_network_quality(self, rtt_ms: float, loss_percent: float) -> NetworkQuality:
        """Classify network quality based on metrics"""
        if rtt_ms < 50 and loss_percent < 1.0:
            return NetworkQuality.EXCELLENT
        elif rtt_ms < 100 and loss_percent < 3.0:
            return NetworkQuality.GOOD
        elif rtt_ms < 200 and loss_percent < 5.0:
            return NetworkQuality.FAIR
        elif rtt_ms < 500 and loss_percent < 10.0:
            return NetworkQuality.POOR
        else:
            return NetworkQuality.CRITICAL
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate simple linear trend"""
        if len(values) < 2:
            return 0.0
        
        # Simple slope calculation
        n = len(values)
        x_avg = (n - 1) / 2
        y_avg = sum(values) / n
        
        numerator = sum((i - x_avg) * (values[i] - y_avg) for i in range(n))
        denominator = sum((i - x_avg) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def get_active_sessions(self) -> List[str]:
        """Get list of cameras being monitored"""
        return list(self._monitoring_sessions.keys())
    
    def is_monitoring(self, camera_id: str) -> bool:
        """Check if camera is being monitored"""
        return camera_id in self._monitoring_sessions
    
    def is_available(self) -> bool:
        """Check if network module is available"""
        return NETWORK_AVAILABLE
