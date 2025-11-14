"""
Health Metrics - Centralized health data aggregation
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Deque

logger = logging.getLogger(__name__)


@dataclass
class MetricSample:
    """Single sample of a metric at a point in time"""

    timestamp: datetime
    value: float

    def age_seconds(self) -> float:
        """Get age of sample in seconds"""
        return (datetime.now() - self.timestamp).total_seconds()


@dataclass
class MetricSeries:
    """Time series of a metric with statistics"""

    name: str
    unit: str  # e.g., "kbps", "fps", "%", "ms"
    samples: Deque[MetricSample] = field(
        default_factory=lambda: deque(maxlen=300)
    )  # 5 min at 1 sample/sec

    def add(self, value: float) -> None:
        """Add new sample"""
        self.samples.append(MetricSample(datetime.now(), value))

    def get_current(self) -> Optional[float]:
        """Get most recent value"""
        return self.samples[-1].value if self.samples else None

    def get_average(self, last_n: Optional[int] = None) -> Optional[float]:
        """Get average over last N samples (or all if None)"""
        if not self.samples:
            return None

        samples = list(self.samples)[-last_n:] if last_n else list(self.samples)
        return sum(s.value for s in samples) / len(samples)

    def get_min_max(
        self, last_n: Optional[int] = None
    ) -> tuple[Optional[float], Optional[float]]:
        """Get min/max over last N samples"""
        if not self.samples:
            return None, None

        samples = list(self.samples)[-last_n:] if last_n else list(self.samples)
        values = [s.value for s in samples]
        return min(values), max(values)

    def get_trend(self, window: int = 30) -> str:
        """
        Get trend direction over window samples.
        Returns: 'rising', 'falling', 'stable'
        """
        if len(self.samples) < window:
            return "stable"

        recent = list(self.samples)[-window:]
        first_half_avg = sum(s.value for s in recent[: window // 2]) / (window // 2)
        second_half_avg = (
            sum(s.value for s in recent[window // 2 :]) / (window - window // 2)
        )

        diff_pct = (
            ((second_half_avg - first_half_avg) / first_half_avg) * 100
            if first_half_avg > 0
            else 0
        )

        if diff_pct > 5:
            return "rising"
        elif diff_pct < -5:
            return "falling"
        else:
            return "stable"

    def get_samples_for_chart(
        self, max_points: int = 60
    ) -> List[tuple[datetime, float]]:
        """Get samples formatted for charting"""
        samples = list(self.samples)

        if len(samples) <= max_points:
            return [(s.timestamp, s.value) for s in samples]

        # Downsample
        step = len(samples) // max_points
        return [
            (samples[i].timestamp, samples[i].value)
            for i in range(0, len(samples), step)
        ]


@dataclass
class StreamHealth:
    """Complete stream health snapshot"""

    timestamp: datetime = field(default_factory=datetime.now)

    # Streaming state
    streaming: bool = False
    uptime_seconds: float = 0.0

    # OBS metrics
    bitrate_kbps: float = 0.0
    fps: float = 0.0
    dropped_frames: int = 0
    total_frames: int = 0
    cpu_usage: float = 0.0
    gpu_usage: float = 0.0
    memory_mb: float = 0.0

    # Network metrics
    rtt_ms: float = 0.0
    jitter_ms: float = 0.0
    packet_loss_pct: float = 0.0

    # Destinations
    destinations: List[Dict[str, Any]] = field(default_factory=list)

    # Failover state
    failover_state: str = "normal"
    failover_active: bool = False

    @property
    def drop_percentage(self) -> float:
        """Calculate overall drop percentage"""
        if self.total_frames == 0:
            return 0.0
        return (self.dropped_frames / self.total_frames) * 100


class HealthAggregator:
    """
    Aggregates health metrics from multiple sources.

    Polls OBS, Egress, Network, Failover controllers and maintains
    time series for visualization.
    """

    def __init__(
        self,
        obs_controller: Any,
        egress_manager: Any,
        failover_controller: Optional[Any] = None,
        poll_interval: float = 1.0,
    ) -> None:
        """
        Initialize health aggregator.

        Args:
            obs_controller: OBS controller instance
            egress_manager: Egress manager instance
            failover_controller: Failover controller instance (optional)
            poll_interval: How often to poll sources (seconds)
        """
        self.obs = obs_controller
        self.egress = egress_manager
        self.failover = failover_controller
        self.poll_interval = poll_interval

        # Time series
        self.metrics: Dict[str, MetricSeries] = {
            "bitrate_kbps": MetricSeries("Bitrate", "kbps"),
            "fps": MetricSeries("FPS", "fps"),
            "drop_percentage": MetricSeries("Dropped Frames", "%"),
            "cpu_usage": MetricSeries("CPU Usage", "%"),
            "gpu_usage": MetricSeries("GPU Usage", "%"),
            "memory_mb": MetricSeries("Memory", "MB"),
            "rtt_ms": MetricSeries("Round-Trip Time", "ms"),
            "jitter_ms": MetricSeries("Jitter", "ms"),
            "packet_loss_pct": MetricSeries("Packet Loss", "%"),
        }

        # Current snapshot
        self.current_health: Optional[StreamHealth] = None
        self.stream_start_time: Optional[datetime] = None

        # Background task
        self.polling_task: Optional[asyncio.Task] = None
        self.running = False

        logger.info("HealthAggregator initialized")

    async def start(self) -> None:
        """Start polling for metrics"""
        if self.running:
            logger.warning("HealthAggregator already running")
            return

        logger.info(
            f"Starting health aggregation (poll interval: {self.poll_interval}s)"
        )
        self.running = True
        self.polling_task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Stop polling"""
        if not self.running:
            return

        logger.info("Stopping health aggregation")
        self.running = False

        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
            self.polling_task = None

    async def _poll_loop(self) -> None:
        """Main polling loop"""
        logger.info("Health polling started")

        try:
            while self.running:
                try:
                    # Collect metrics
                    health = await self._collect_health()
                    self.current_health = health

                    # Update time series
                    if health.streaming:
                        self.metrics["bitrate_kbps"].add(health.bitrate_kbps)
                        self.metrics["fps"].add(health.fps)
                        self.metrics["drop_percentage"].add(health.drop_percentage)
                        self.metrics["cpu_usage"].add(health.cpu_usage)
                        self.metrics["gpu_usage"].add(health.gpu_usage)
                        self.metrics["memory_mb"].add(health.memory_mb)
                        self.metrics["rtt_ms"].add(health.rtt_ms)
                        self.metrics["jitter_ms"].add(health.jitter_ms)
                        self.metrics["packet_loss_pct"].add(health.packet_loss_pct)

                except Exception as e:
                    logger.error(f"Error collecting health metrics: {e}")

                # Wait for next poll
                await asyncio.sleep(self.poll_interval)

        except asyncio.CancelledError:
            logger.info("Health polling cancelled")
            raise
        except Exception as e:
            logger.error(f"Health polling error: {e}", exc_info=True)

    async def _collect_health(self) -> StreamHealth:
        """Collect current health from all sources"""
        health = StreamHealth()

        try:
            # Get OBS stats
            if self.obs and await self.obs.is_connected():
                stats = await self.obs.get_stream_stats()

                health.streaming = stats.get("output_active", False)
                health.bitrate_kbps = stats.get("kbits_per_sec", 0.0)
                health.fps = stats.get("fps", 0.0)
                health.dropped_frames = stats.get("num_dropped_frames", 0)
                health.total_frames = stats.get("num_total_frames", 0)

                # Get system stats
                system_stats = await self.obs.get_stats()
                health.cpu_usage = system_stats.get("cpu_usage", 0.0)
                # Note: GPU usage might not be available from OBS WebSocket
                health.memory_mb = system_stats.get("memory_usage", 0.0) / (1024 * 1024)

                # Track uptime
                if health.streaming:
                    if self.stream_start_time is None:
                        self.stream_start_time = datetime.now()
                    health.uptime_seconds = (
                        datetime.now() - self.stream_start_time
                    ).total_seconds()
                else:
                    self.stream_start_time = None

            # Get egress health
            if self.egress:
                egress_health = await self.egress.get_health()
                health.destinations = egress_health.get("destinations", [])

            # Get failover state
            if self.failover:
                failover_state = self.failover.get_current_state()
                health.failover_state = failover_state.get("state", "normal")
                health.failover_active = failover_state.get("failover_active", False)

            # Network metrics (placeholder - would integrate with network monitor)
            # health.rtt_ms = await self.get_rtt()
            # health.jitter_ms = await self.get_jitter()
            # health.packet_loss_pct = await self.get_packet_loss()

        except Exception as e:
            logger.error(f"Error collecting health: {e}")

        return health

    def get_current_health(self) -> Optional[StreamHealth]:
        """Get current health snapshot"""
        return self.current_health

    def get_metric_series(self, metric_name: str) -> Optional[MetricSeries]:
        """Get time series for a specific metric"""
        return self.metrics.get(metric_name)

    def get_all_metrics(self) -> Dict[str, MetricSeries]:
        """Get all metric time series"""
        return self.metrics.copy()

    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of current health"""
        if not self.current_health:
            return {"status": "unknown", "streaming": False}

        health = self.current_health

        # Calculate overall health status
        status = "healthy"
        issues = []

        if health.drop_percentage > 5.0:
            status = "critical"
            issues.append(f"High drop rate: {health.drop_percentage:.1f}%")
        elif health.drop_percentage > 1.0:
            status = "warning"
            issues.append(f"Elevated drops: {health.drop_percentage:.1f}%")

        if health.cpu_usage > 90:
            status = "critical" if status != "critical" else status
            issues.append(f"High CPU: {health.cpu_usage:.0f}%")
        elif health.cpu_usage > 75:
            status = "warning" if status == "healthy" else status
            issues.append("CPU usage elevated")

        if health.failover_active:
            status = "warning" if status == "healthy" else status
            issues.append("Running on backup")

        return {
            "status": status,
            "streaming": health.streaming,
            "uptime_seconds": health.uptime_seconds,
            "failover_state": health.failover_state,
            "issues": issues,
            "metrics": {
                "bitrate_kbps": health.bitrate_kbps,
                "fps": health.fps,
                "drop_percentage": health.drop_percentage,
                "cpu_usage": health.cpu_usage,
            },
        }
