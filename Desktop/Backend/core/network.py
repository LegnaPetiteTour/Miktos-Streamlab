"""
Network Monitoring Module
Monitors network conditions for reliable streaming.
"""
import time
import logging
import warnings
import psutil

# Suppress deprecation warnings from speedtest-cli library
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning,
                            module="speedtest")
    import speedtest
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class NetworkStatus(Enum):
    """Network status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    MARGINAL = "marginal"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    upload_speed: float  # Mbps
    download_speed: float  # Mbps
    latency: float  # ms
    jitter: float  # ms
    packet_loss: float  # percentage
    status: NetworkStatus
    timestamp: float

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'upload_speed': round(self.upload_speed, 2),
            'download_speed': round(self.download_speed, 2),
            'latency': round(self.latency, 2),
            'jitter': round(self.jitter, 2),
            'packet_loss': round(self.packet_loss, 2),
            'status': self.status.value,
            'timestamp': self.timestamp
        }


class NetworkMonitor:
    """
    Monitors network performance for streaming

    Features:
    - Upload/download speed testing
    - Latency and jitter monitoring
    - Packet loss detection
    - Real-time status assessment
    - Automatic recommendations
    """

    # Thresholds for streaming quality
    THRESHOLDS = {
        'excellent': {'upload': 8.0, 'latency': 30},
        'good': {'upload': 5.0, 'latency': 50},
        'marginal': {'upload': 3.0, 'latency': 100},
        'poor': {'upload': 1.5, 'latency': 150},
    }

    def __init__(self, test_interval: int = 60):
        """
        Initialize network monitor

        Args:
            test_interval: Seconds between full speed tests (expensive operation)
        """
        self.test_interval = test_interval
        self.last_full_test = 0
        self._cached_metrics: Optional[NetworkMetrics] = None
        self._speedtest_client = None

    def get_metrics(self, force_full_test: bool = False) -> NetworkMetrics:
        """
        Get current network metrics

        Args:
            force_full_test: Force a complete speed test (slow)

        Returns:
            Network metrics
        """
        current_time = time.time()

        # Use cached metrics if recent
        if (not force_full_test and
            self._cached_metrics and
            current_time - self.last_full_test < self.test_interval):
            return self._cached_metrics

        try:
            # Perform full speed test
            logger.info("Performing network speed test...")

            if self._speedtest_client is None:
                self._speedtest_client = speedtest.Speedtest()

            # Get best server
            self._speedtest_client.get_best_server()

            # Test download speed
            download_speed = self._speedtest_client.download() / 1_000_000  # Convert to Mbps

            # Test upload speed
            upload_speed = self._speedtest_client.upload() / 1_000_000  # Convert to Mbps

            # Get latency
            latency = self._speedtest_client.results.ping

            # Estimate jitter (simplified)
            jitter = latency * 0.1  # Rough estimate

            # Get packet loss (simplified - would need ping tests)
            packet_loss = 0.0

            # Determine status
            status = self._assess_status(upload_speed, latency)

            metrics = NetworkMetrics(
                upload_speed=upload_speed,
                download_speed=download_speed,
                latency=latency,
                jitter=jitter,
                packet_loss=packet_loss,
                status=status,
                timestamp=current_time
            )

            self._cached_metrics = metrics
            self.last_full_test = current_time

            logger.info(f"Network test complete: {upload_speed:.1f} Mbps up, "
                       f"{latency:.1f}ms latency - Status: {status.value}")

            return metrics

        except Exception as e:
            logger.error(f"Network test failed: {e}")

            # Return degraded metrics
            return NetworkMetrics(
                upload_speed=0.0,
                download_speed=0.0,
                latency=999.0,
                jitter=999.0,
                packet_loss=100.0,
                status=NetworkStatus.CRITICAL,
                timestamp=current_time
            )

    def _assess_status(self, upload_speed: float, latency: float) -> NetworkStatus:
        """Assess network status based on metrics"""
        if upload_speed >= self.THRESHOLDS['excellent']['upload'] and \
           latency <= self.THRESHOLDS['excellent']['latency']:
            return NetworkStatus.EXCELLENT
        elif upload_speed >= self.THRESHOLDS['good']['upload'] and \
             latency <= self.THRESHOLDS['good']['latency']:
            return NetworkStatus.GOOD
        elif upload_speed >= self.THRESHOLDS['marginal']['upload'] and \
             latency <= self.THRESHOLDS['marginal']['latency']:
            return NetworkStatus.MARGINAL
        elif upload_speed >= self.THRESHOLDS['poor']['upload']:
            return NetworkStatus.POOR
        else:
            return NetworkStatus.CRITICAL

    def get_quick_metrics(self) -> Dict:
        """
        Get quick network metrics without full speed test
        Uses system network statistics
        """
        try:
            net_io = psutil.net_io_counters()

            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors': net_io.errin + net_io.errout,
                'drops': net_io.dropin + net_io.dropout
            }
        except Exception as e:
            logger.error(f"Failed to get quick metrics: {e}")
            return {}

    def is_ready_to_stream(self, min_upload_speed: float = 3.0) -> Tuple[bool, str]:
        """
        Check if network is ready for streaming

        Args:
            min_upload_speed: Minimum required upload speed in Mbps

        Returns:
            (ready, message)
        """
        metrics = self.get_metrics(force_full_test=False)

        if metrics.upload_speed < min_upload_speed:
            return False, f"Upload speed too low: {metrics.upload_speed:.1f} Mbps (need {min_upload_speed} Mbps)"

        if metrics.latency > 150:
            return False, f"Latency too high: {metrics.latency:.0f}ms (need <150ms)"

        if metrics.packet_loss > 5:
            return False, f"Packet loss too high: {metrics.packet_loss:.1f}%"

        if metrics.status == NetworkStatus.CRITICAL:
            return False, "Network status: CRITICAL - check connection"

        return True, f"Network ready: {metrics.upload_speed:.1f} Mbps, {metrics.latency:.0f}ms"

    def get_recommended_bitrate(self) -> int:
        """
        Get recommended streaming bitrate based on network conditions

        Returns:
            Recommended bitrate in kbps
        """
        metrics = self.get_metrics(force_full_test=False)

        # Use 70% of upload speed for safety margin
        available_bitrate = metrics.upload_speed * 0.7 * 1000  # Convert to kbps

        # Cap at reasonable limits
        if available_bitrate > 6000:
            return 6000  # 1080p60
        elif available_bitrate > 4500:
            return 4500  # 1080p30
        elif available_bitrate > 3000:
            return 3000  # 720p60
        elif available_bitrate > 2000:
            return 2000  # 720p30
        else:
            return 1500  # 480p

    def get_status_message(self) -> str:
        """Get human-readable status message"""
        metrics = self.get_metrics(force_full_test=False)

        messages = {
            NetworkStatus.EXCELLENT: f"🟢 Excellent ({metrics.upload_speed:.1f} Mbps) - Ready to stream",
            NetworkStatus.GOOD: f"🟢 Good ({metrics.upload_speed:.1f} Mbps) - Ready to stream",
            NetworkStatus.MARGINAL: f"🟡 Marginal ({metrics.upload_speed:.1f} Mbps) - Consider lower quality",
            NetworkStatus.POOR: f"🟠 Poor ({metrics.upload_speed:.1f} Mbps) - Streaming not recommended",
            NetworkStatus.CRITICAL: f"🔴 Critical - Do not stream"
        }

        return messages.get(metrics.status, "Unknown status")
