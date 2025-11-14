"""
Egress Manager - Multi-destination streaming with automatic failover

This module provides robust streaming to multiple destinations
(RTMP, SRT, WHIP) with automatic health monitoring and failover.

Architecture:
- Abstract EgressDestination base class for different protocols
- RTMPDestination for YouTube, Twitch, Facebook
- SRTDestination for resilient relay backup
- EgressManager orchestrates destinations and handles failover

Key Features:
- Dual-path streaming (primary + backup)
- Automatic failover on connection issues
- Health monitoring (packet loss, RTT, bitrate)
- Slate display during failover
- Automatic recovery attempts
- Comprehensive logging

Author: Miktos StreamLab Team
License: MIT
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports
try:
    import ffmpeg  # type: ignore  # ffmpeg-python lacks type stubs
except ImportError:
    ffmpeg = None
    logging.warning(
        "ffmpeg-python not installed. RTMP streaming will be limited."
    )

# Local imports
from src.core.logger import get_logger

# Import SlateManager for failover display
try:
    import sys
    # Add project root to path to import slate_manager
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from slate_manager import SlateManager  # type: ignore
    SLATE_AVAILABLE = True
except ImportError:
    SlateManager = None  # type: ignore
    SLATE_AVAILABLE = False
    logging.warning(
        "SlateManager not available. "
        "Failover slate display will be disabled."
    )

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class DestinationStatus(Enum):
    """Status of a streaming destination"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    FAILING = "failing"
    FAILED = "failed"
    RECOVERING = "recovering"


class DestinationType(Enum):
    """Type of streaming destination"""
    RTMP = "rtmp"
    SRT = "srt"
    WHIP = "whip"  # WebRTC HTTP Ingestion Protocol (future)


@dataclass
class DestinationHealth:
    """Health metrics for a streaming destination"""
    name: str
    destination_type: DestinationType
    status: DestinationStatus
    connected: bool

    # Network metrics
    bitrate_actual: float = 0.0  # Mbps
    bitrate_target: float = 0.0  # Mbps
    bitrate_variance_pct: float = 0.0

    # Connection quality
    rtt_ms: float = 0.0  # Round-trip time
    jitter_ms: float = 0.0  # Jitter
    packet_loss_pct: float = 0.0
    dropped_frames: int = 0

    # Timing
    connected_at: Optional[datetime] = None
    last_health_check: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0.0

    # Issues
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def is_healthy(self) -> bool:
        """Check if destination is healthy"""
        if not self.connected:
            return False
        if self.packet_loss_pct > 5.0:
            return False
        if self.rtt_ms > 500:
            return False
        if self.bitrate_variance_pct > 40:
            return False
        return True

    def is_failing(self) -> bool:
        """Check if destination is failing (needs attention)"""
        if not self.connected:
            return True
        if self.packet_loss_pct > 3.0:
            return True
        if self.rtt_ms > 300:
            return True
        if self.dropped_frames > 30:  # per second
            return True
        return False


@dataclass
class FailoverConfig:
    """Configuration for automatic failover"""
    enabled: bool = True

    # Trigger thresholds
    trigger_packet_loss_pct: float = 5.0
    trigger_rtt_ms: float = 500.0
    trigger_duration_sec: float = 10.0  # How long issue must persist
    trigger_dropped_frames: int = 50  # Dropped frames per check

    # Recovery behavior
    retry_interval_sec: float = 30.0
    max_retry_attempts: int = 10

    # Slate configuration
    show_slate: bool = True
    slate_text: str = "Technical Difficulties - Please Stand By"
    slate_duration_sec: float = 5.0  # Duration of slate fade-in


@dataclass
class FailoverMetrics:
    """
    Metrics tracking for failover events

    Provides insight into:
    - Number and frequency of failovers
    - Slate display duration
    - Recovery success rate
    - System reliability
    """
    # Failover counts
    total_failovers: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0

    # Timing metrics
    total_failover_duration_sec: float = 0.0
    total_slate_duration_sec: float = 0.0
    last_failover_at: Optional[datetime] = None
    last_recovery_at: Optional[datetime] = None

    # Current state tracking
    current_failover_start: Optional[datetime] = None
    current_slate_start: Optional[datetime] = None

    def record_failover_start(self) -> None:
        """Record the start of a failover event"""
        self.total_failovers += 1
        self.last_failover_at = datetime.now()
        self.current_failover_start = datetime.now()

    def record_failover_end(self, success: bool = True) -> None:
        """Record the end of a failover event"""
        if self.current_failover_start:
            duration = (
                datetime.now() - self.current_failover_start
            ).total_seconds()
            self.total_failover_duration_sec += duration
            self.current_failover_start = None

        if success:
            self.successful_recoveries += 1
            self.last_recovery_at = datetime.now()
        else:
            self.failed_recoveries += 1

    def record_slate_start(self) -> None:
        """Record when slate display begins"""
        self.current_slate_start = datetime.now()

    def record_slate_end(self) -> None:
        """Record when slate display ends"""
        if self.current_slate_start:
            duration = (
                datetime.now() - self.current_slate_start
            ).total_seconds()
            self.total_slate_duration_sec += duration
            self.current_slate_start = None

    @property
    def average_failover_duration_sec(self) -> float:
        """Calculate average failover duration"""
        if self.total_failovers == 0:
            return 0.0
        return self.total_failover_duration_sec / self.total_failovers

    @property
    def average_slate_duration_sec(self) -> float:
        """Calculate average slate display duration"""
        if self.total_failovers == 0:
            return 0.0
        return self.total_slate_duration_sec / self.total_failovers

    @property
    def recovery_success_rate(self) -> float:
        """Calculate recovery success rate (0-100)"""
        total_recoveries = self.successful_recoveries + self.failed_recoveries
        if total_recoveries == 0:
            return 100.0
        return (self.successful_recoveries / total_recoveries) * 100.0

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary for logging/monitoring"""
        return {
            "total_failovers": self.total_failovers,
            "successful_recoveries": self.successful_recoveries,
            "failed_recoveries": self.failed_recoveries,
            "recovery_success_rate_pct": round(self.recovery_success_rate, 2),
            "avg_failover_duration_sec": round(
                self.average_failover_duration_sec, 2
            ),
            "avg_slate_duration_sec": round(
                self.average_slate_duration_sec, 2
            ),
            "total_failover_time_sec": round(
                self.total_failover_duration_sec, 2
            ),
            "total_slate_time_sec": round(self.total_slate_duration_sec, 2),
            "last_failover": (
                self.last_failover_at.isoformat()
                if self.last_failover_at else None
            ),
            "last_recovery": (
                self.last_recovery_at.isoformat()
                if self.last_recovery_at else None
            ),
        }


@dataclass
class EgressConfig:
    """Configuration for egress manager"""
    primary_destination: Dict
    backup_destination: Optional[Dict] = None
    failover: FailoverConfig = field(default_factory=FailoverConfig)

    # Health monitoring
    health_check_interval_sec: float = 5.0
    health_log_interval_sec: float = 60.0  # Log health every N seconds


# ============================================================================
# Abstract Base Classes
# ============================================================================

class EgressDestination(ABC):
    """
    Abstract base class for streaming destinations

    Subclasses implement specific protocols (RTMP, SRT, WHIP)
    """

    def __init__(self, name: str, destination_type: DestinationType):
        self.name = name
        self.destination_type = destination_type
        self.status = DestinationStatus.DISCONNECTED
        self.logger = get_logger(f"{__name__}.{name}")

        # Metrics
        self._connected_at: Optional[datetime] = None
        self._bitrate_target: float = 0.0
        self._bitrate_samples: List[float] = []
        self._rtt_samples: List[float] = []
        self._packet_loss_samples: List[float] = []

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the streaming destination

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the streaming destination

        Returns:
            bool: True if disconnection clean, False if errors
        """
        pass

    @abstractmethod
    async def start_streaming(self) -> bool:
        """
        Start sending stream data

        Returns:
            bool: True if streaming started, False otherwise
        """
        pass

    @abstractmethod
    async def stop_streaming(self) -> bool:
        """
        Stop sending stream data

        Returns:
            bool: True if streaming stopped, False if errors
        """
        pass

    @abstractmethod
    async def get_health(self) -> DestinationHealth:
        """
        Get current health metrics

        Returns:
            DestinationHealth: Current health status
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection without starting stream

        Returns:
            bool: True if connection test passed
        """
        pass

    def _update_metrics(self, bitrate: float, rtt: float, packet_loss: float):
        """Update internal metrics (rolling average)"""
        self._bitrate_samples.append(bitrate)
        self._rtt_samples.append(rtt)
        self._packet_loss_samples.append(packet_loss)

        # Keep only last 60 samples (1 minute at 1 sample/second)
        if len(self._bitrate_samples) > 60:
            self._bitrate_samples.pop(0)
            self._rtt_samples.pop(0)
            self._packet_loss_samples.pop(0)

    def _get_average_metrics(self) -> tuple:
        """Get average of collected metrics"""
        if not self._bitrate_samples:
            return 0.0, 0.0, 0.0

        avg_bitrate = sum(self._bitrate_samples) / len(
            self._bitrate_samples
        )
        avg_rtt = sum(self._rtt_samples) / len(self._rtt_samples)
        avg_packet_loss = sum(self._packet_loss_samples) / len(
            self._packet_loss_samples
        )

        return avg_bitrate, avg_rtt, avg_packet_loss


# ============================================================================
# RTMP Destination Implementation
# ============================================================================

class RTMPDestination(EgressDestination):
    """
    RTMP streaming destination (YouTube, Twitch, Facebook, etc.)

    Uses FFmpeg for RTMP streaming. OBS handles encoding,
    we just monitor the RTMP connection health.
    """

    def __init__(self, name: str, url: str, stream_key: str,
                 bitrate_mbps: float = 6.0):
        super().__init__(name, DestinationType.RTMP)
        self.url = url
        self.stream_key = stream_key  # Should be encrypted in config
        self.bitrate_mbps = bitrate_mbps

        self._process: Optional[asyncio.subprocess.Process] = None

    async def connect(self) -> bool:
        """Connect to RTMP server (via OBS)"""
        try:
            self.logger.info(f"Connecting to RTMP destination: {self.url}")
            self.status = DestinationStatus.CONNECTING

            # In practice, OBS handles the RTMP connection
            # We just validate the URL and key format
            if not self.url.startswith("rtmp://") and not self.url.startswith(
                "rtmps://"
            ):
                self.logger.error(f"Invalid RTMP URL: {self.url}")
                self.status = DestinationStatus.FAILED
                return False

            if not self.stream_key:
                self.logger.error("Stream key is empty")
                self.status = DestinationStatus.FAILED
                return False

            # Connection is handled by OBS, we mark as connected
            self.status = DestinationStatus.CONNECTED
            self._connected_at = datetime.now()
            self.logger.info("RTMP destination connected")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to RTMP: {e}", exc_info=True)
            self.status = DestinationStatus.FAILED
            return False

    async def disconnect(self) -> bool:
        """Disconnect from RTMP server"""
        try:
            self.logger.info("Disconnecting from RTMP destination")

            # OBS handles disconnection
            self.status = DestinationStatus.DISCONNECTED
            self._connected_at = None
            self.logger.info("RTMP destination disconnected")
            return True

        except Exception as e:
            self.logger.error(
                f"Error disconnecting from RTMP: {e}", exc_info=True
            )
            return False

    async def start_streaming(self) -> bool:
        """Start RTMP streaming (via OBS)"""
        try:
            if self.status != DestinationStatus.CONNECTED:
                self.logger.error("Cannot start streaming - not connected")
                return False

            self.logger.info("Starting RTMP streaming")
            self.status = DestinationStatus.STREAMING
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to start RTMP streaming: {e}", exc_info=True
            )
            return False

    async def stop_streaming(self) -> bool:
        """Stop RTMP streaming"""
        try:
            self.logger.info("Stopping RTMP streaming")
            self.status = DestinationStatus.CONNECTED
            return True

        except Exception as e:
            self.logger.error(
                f"Error stopping RTMP streaming: {e}", exc_info=True
            )
            return False

    async def test_connection(self) -> bool:
        """Test RTMP connection without streaming"""
        try:
            # Could implement a lightweight RTMP handshake test
            # For now, just validate URL format
            return self.url.startswith("rtmp://") or self.url.startswith(
                "rtmps://"
            )
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    async def get_health(self) -> DestinationHealth:
        """Get current RTMP health"""
        # In reality, we would get these metrics from OBS WebSocket API
        # For now, return simulated healthy metrics

        avg_bitrate, avg_rtt, avg_packet_loss = self._get_average_metrics()

        # Calculate variance from target
        bitrate_variance = 0.0
        if self._bitrate_target > 0:
            bitrate_variance = (
                abs(avg_bitrate - self._bitrate_target)
                / self._bitrate_target
                * 100
            )

        health = DestinationHealth(
            name=self.name,
            destination_type=self.destination_type,
            status=self.status,
            connected=self.status
            in [DestinationStatus.CONNECTED, DestinationStatus.STREAMING],
            bitrate_actual=avg_bitrate,
            bitrate_target=self._bitrate_target,
            bitrate_variance_pct=bitrate_variance,
            rtt_ms=avg_rtt,
            packet_loss_pct=avg_packet_loss,
            connected_at=self._connected_at,
            last_health_check=datetime.now()
        )

        # Add warnings/issues based on metrics
        if health.packet_loss_pct > 3.0:
            health.warnings.append(
                f"High packet loss: {health.packet_loss_pct:.1f}%"
            )
        if health.rtt_ms > 300:
            health.warnings.append(f"High latency: {health.rtt_ms:.0f}ms")
        if health.bitrate_variance_pct > 20:
            health.warnings.append(
                f"Bitrate variance: {health.bitrate_variance_pct:.1f}%"
            )

        if health.is_failing():
            health.issues.append("Connection is failing")
            self.status = DestinationStatus.FAILING

        return health


# ============================================================================
# SRT Destination Implementation
# ============================================================================

class SRTDestination(EgressDestination):
    """
    SRT (Secure Reliable Transport) streaming destination

    Used for resilient backup streaming over unreliable networks.
    Provides forward error correction and automatic retransmission.
    """

    def __init__(self, name: str, url: str, latency_ms: int = 2000):
        super().__init__(name, DestinationType.SRT)
        self.url = url
        self.latency_ms = latency_ms

        # SRT-specific settings
        self.passphrase: Optional[str] = None
        self.pbkeylen: int = 16  # AES key length (16, 24, 32)

    async def connect(self) -> bool:
        """Connect to SRT relay"""
        try:
            self.logger.info(f"Connecting to SRT destination: {self.url}")
            self.status = DestinationStatus.CONNECTING

            # Validate SRT URL format
            if not self.url.startswith("srt://"):
                self.logger.error(f"Invalid SRT URL: {self.url}")
                self.status = DestinationStatus.FAILED
                return False

            # TODO: Implement actual SRT connection via libsrt or FFmpeg
            # For now, mark as connected (implementation in Phase 2)
            self.logger.warning(
                "SRT support is in development - simulating connection"
            )

            self.status = DestinationStatus.CONNECTED
            self._connected_at = datetime.now()
            self.logger.info(
                f"SRT destination connected (latency: {self.latency_ms}ms)"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to SRT: {e}", exc_info=True)
            self.status = DestinationStatus.FAILED
            return False

    async def disconnect(self) -> bool:
        """Disconnect from SRT relay"""
        try:
            self.logger.info("Disconnecting from SRT destination")
            self.status = DestinationStatus.DISCONNECTED
            self._connected_at = None
            return True
        except Exception as e:
            self.logger.error(
                f"Error disconnecting from SRT: {e}", exc_info=True
            )
            return False

    async def start_streaming(self) -> bool:
        """Start SRT streaming"""
        try:
            if self.status != DestinationStatus.CONNECTED:
                self.logger.error("Cannot start streaming - not connected")
                return False

            self.logger.info("Starting SRT streaming")
            self.status = DestinationStatus.STREAMING
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to start SRT streaming: {e}", exc_info=True
            )
            return False

    async def stop_streaming(self) -> bool:
        """Stop SRT streaming"""
        try:
            self.logger.info("Stopping SRT streaming")
            self.status = DestinationStatus.CONNECTED
            return True
        except Exception as e:
            self.logger.error(
                f"Error stopping SRT streaming: {e}", exc_info=True
            )
            return False

    async def test_connection(self) -> bool:
        """Test SRT connection"""
        try:
            # TODO: Implement SRT connection test
            return self.url.startswith("srt://")
        except Exception as e:
            self.logger.error(f"SRT connection test failed: {e}")
            return False

    async def get_health(self) -> DestinationHealth:
        """Get current SRT health"""
        # SRT provides detailed statistics
        # We'll implement full monitoring later

        avg_bitrate, avg_rtt, avg_packet_loss = self._get_average_metrics()

        health = DestinationHealth(
            name=self.name,
            destination_type=self.destination_type,
            status=self.status,
            connected=self.status
            in [DestinationStatus.CONNECTED, DestinationStatus.STREAMING],
            bitrate_actual=avg_bitrate,
            rtt_ms=avg_rtt,
            packet_loss_pct=avg_packet_loss,
            connected_at=self._connected_at,
            last_health_check=datetime.now()
        )

        return health


# ============================================================================
# Egress Manager - Orchestrates all destinations
# ============================================================================

class EgressManager:
    """
    Manages multiple streaming destinations with automatic failover

    Features:
    - Dual-path streaming (primary + backup)
    - Continuous health monitoring
    - Automatic failover on issues
    - Slate display during failover
    - Recovery attempts
    - Comprehensive logging
    """

    def __init__(self, config: EgressConfig, obs_controller=None):
        """
        Initialize egress manager

        Args:
            config: EgressConfig with primary/backup destinations
            obs_controller: OBS WebSocket controller (optional)
        """
        self.config = config
        self.obs = obs_controller
        self.logger = get_logger(__name__)

        # Initialize SlateManager if OBS controller is available
        self.slate_manager: Optional["SlateManager"] = None  # type: ignore
        if SLATE_AVAILABLE and obs_controller and SlateManager:
            try:
                self.slate_manager = SlateManager(obs_controller)
                self.logger.info(
                    "SlateManager initialized for failover display"
                )
            except Exception as e:
                self.logger.warning(
                    f"Failed to initialize SlateManager: {e}. "
                    "Slate display will be unavailable."
                )

        # Destinations
        self.primary: Optional[EgressDestination] = None
        self.backup: Optional[EgressDestination] = None
        self.active_destination: Optional[EgressDestination] = None

        # State
        self.streaming: bool = False
        self.failover_active: bool = False
        self.recovery_attempts: int = 0

        # Metrics tracking
        self.metrics = FailoverMetrics()

        # Tasks
        self._monitor_task: Optional[asyncio.Task] = None
        self._health_log_task: Optional[asyncio.Task] = None

        # Initialize destinations from config
        self._initialize_destinations()

    def _initialize_destinations(self):
        """Create destination instances from configuration"""
        try:
            # Create primary destination
            primary_config = self.config.primary_destination
            if primary_config["type"] == "rtmp":
                self.primary = RTMPDestination(
                    name="primary",
                    url=primary_config["url"],
                    stream_key=primary_config["key"],
                    bitrate_mbps=primary_config.get("bitrate_mbps", 6.0)
                )
            elif primary_config["type"] == "srt":
                self.primary = SRTDestination(
                    name="primary",
                    url=primary_config["url"],
                    latency_ms=primary_config.get("latency_ms", 2000)
                )

            # Create backup destination if configured
            if self.config.backup_destination:
                backup_config = self.config.backup_destination
                if backup_config["type"] == "rtmp":
                    self.backup = RTMPDestination(
                        name="backup",
                        url=backup_config["url"],
                        stream_key=backup_config["key"],
                        bitrate_mbps=backup_config.get("bitrate_mbps", 6.0)
                    )
                elif backup_config["type"] == "srt":
                    self.backup = SRTDestination(
                        name="backup",
                        url=backup_config["url"],
                        latency_ms=backup_config.get("latency_ms", 2000)
                    )

            assert self.primary is not None  # Type guard
            primary_type = self.primary.destination_type.value
            backup_msg = ""
            if self.backup:
                backup_type = self.backup.destination_type.value
                backup_msg = f" and {backup_type} backup"
            self.logger.info(
                f"Initialized egress manager with {primary_type} primary"
                f"{backup_msg}"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to initialize destinations: {e}",
                exc_info=True
            )
            raise

    async def start_streaming(self) -> bool:
        """
        Start streaming to all configured destinations

        Returns:
            bool: True if streaming started successfully
        """
        try:
            self.logger.info("Starting streaming to egress destinations")

            assert self.primary is not None  # Type guard
            # Connect primary
            if not await self.primary.connect():
                self.logger.error("Failed to connect primary destination")
                return False

            # Start streaming on primary
            if not await self.primary.start_streaming():
                self.logger.error("Failed to start streaming on primary")
                return False

            self.active_destination = self.primary
            self.streaming = True

            # Connect backup (if configured) but don't start streaming yet
            if self.backup:
                if await self.backup.connect():
                    self.logger.info(
                        "Backup destination connected and on standby"
                    )
                else:
                    self.logger.warning("Failed to connect backup destination")

            # Start monitoring
            self._monitor_task = asyncio.create_task(
                self._monitor_health()
            )
            self._health_log_task = asyncio.create_task(
                self._log_health_periodically()
            )

            self.logger.info("Streaming started successfully")

            return True

        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}", exc_info=True)
            return False

    async def stop_streaming(self) -> bool:
        """
        Stop streaming to all destinations

        Returns:
            bool: True if stopped successfully
        """
        try:
            self.logger.info("Stopping streaming")
            self.streaming = False

            # Cancel monitoring tasks
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass

            if self._health_log_task:
                self._health_log_task.cancel()
                try:
                    await self._health_log_task
                except asyncio.CancelledError:
                    pass

            # Stop and disconnect all destinations
            if self.primary:
                await self.primary.stop_streaming()
                await self.primary.disconnect()

            if self.backup:
                await self.backup.stop_streaming()
                await self.backup.disconnect()

            self.active_destination = None
            self.failover_active = False

            self.logger.info("Streaming stopped")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping streaming: {e}", exc_info=True)
            return False

    async def _monitor_health(self):
        """Continuous health monitoring loop"""
        try:
            interval = self.config.health_check_interval_sec
            consecutive_failures = 0

            while self.streaming:
                try:
                    # Check active destination health
                    if self.active_destination:
                        health = await self.active_destination.get_health()

                        if health.is_failing():
                            consecutive_failures += 1
                            self.logger.warning(
                                f"Health check failed "
                                f"({consecutive_failures}): "
                                f"packet_loss={health.packet_loss_pct:.1f}%, "
                                f"rtt={health.rtt_ms:.0f}ms"
                            )

                            # Failover after consecutive failures
                            failure_duration = (
                                consecutive_failures * interval
                            )
                            trigger_sec = (
                                self.config.failover.trigger_duration_sec
                            )
                            if failure_duration >= trigger_sec:
                                self.logger.error(
                                    "Failover threshold reached"
                                )
                                await self._initiate_failover()
                                consecutive_failures = 0
                        else:
                            # Reset counter on healthy check
                            if consecutive_failures > 0:
                                self.logger.info(
                                    "Health check passed, "
                                    "resetting failure counter"
                                )
                            consecutive_failures = 0

                    await asyncio.sleep(interval)

                except Exception as e:
                    self.logger.error(
                        f"Error in health monitoring: {e}",
                        exc_info=True
                    )
                    await asyncio.sleep(interval)

        except asyncio.CancelledError:
            self.logger.info("Health monitoring task cancelled")
        except Exception as e:
            self.logger.error(f"Health monitoring crashed: {e}", exc_info=True)

    async def _initiate_failover(self):
        """
        Initiate failover to backup destination

        Steps:
        1. Show slate on primary (if configured)
        2. Switch to backup destination
        3. Log failover event
        4. Start recovery attempts for primary
        """
        if not self.config.failover.enabled:
            self.logger.warning("Failover disabled in config - not switching")
            return

        if not self.backup:
            self.logger.error(
                "No backup destination configured - cannot failover"
            )
            return

        if self.failover_active:
            self.logger.warning("Failover already active")
            return

        try:
            self.logger.critical("🚨 INITIATING FAILOVER TO BACKUP 🚨")
            self.failover_active = True

            # Record failover start in metrics
            self.metrics.record_failover_start()

            # Step 1: Show slate (if OBS controller available)
            if self.config.failover.show_slate and self.obs:
                await self._show_slate()

            # Step 2: Switch to backup
            if self.backup.status != DestinationStatus.STREAMING:
                if await self.backup.start_streaming():
                    self.active_destination = self.backup
                    self.logger.info(
                        "Failover successful - now streaming to backup"
                    )
                else:
                    self.logger.error("Failed to start streaming on backup")
                    self.metrics.record_failover_end(success=False)
                    return

            # Step 3: Log event with metrics
            self.logger.info("Failover complete", extra={
                "event": "failover",
                "from": "primary",
                "to": "backup",
                "timestamp": datetime.now().isoformat(),
                "failover_count": self.metrics.total_failovers
            })

            # Step 4: Start recovery task
            asyncio.create_task(self._attempt_primary_recovery())

        except Exception as e:
            self.logger.error(f"Failover failed: {e}", exc_info=True)
            self.failover_active = False
            self.metrics.record_failover_end(success=False)

    async def _show_slate(self):
        """Display 'Technical Difficulties' slate"""
        try:
            if not self.slate_manager:
                self.logger.warning("SlateManager not available, skipping")
                return

            self.logger.info("Displaying technical difficulties slate")

            # Record slate start in metrics
            self.metrics.record_slate_start()

            # Get custom slate text from config or use default
            message = self.config.failover.slate_text
            if message:
                await self.slate_manager.show_slate(
                    message=message,
                    auto_hide=False
                )
            else:
                # Use preset TECHNICAL_DIFFICULTIES message
                await self.slate_manager.show_preset_message(
                    "TECHNICAL_DIFFICULTIES",
                    auto_hide=False
                )

            self.logger.info("Slate display successful")

        except Exception as e:
            self.logger.error(f"Failed to show slate: {e}", exc_info=True)

    async def _hide_slate(self):
        """Hide the technical difficulties slate"""
        try:
            if not self.slate_manager:
                return

            self.logger.info("Hiding technical difficulties slate")
            await self.slate_manager.hide_slate()

            # Record slate end in metrics
            self.metrics.record_slate_end()

            self.logger.info("Slate hidden successfully")

        except Exception as e:
            self.logger.error(f"Failed to hide slate: {e}", exc_info=True)

    async def _attempt_primary_recovery(self):
        """
        Attempt to recover primary destination


        Tries to reconnect at intervals, up to max_retry_attempts
        """
        try:
            retry_interval = self.config.failover.retry_interval_sec
            max_attempts = self.config.failover.max_retry_attempts

            self.recovery_attempts = 0

            assert self.primary is not None  # Type guard
            while (
                self.streaming
                and self.failover_active
                and self.recovery_attempts < max_attempts
            ):
                self.recovery_attempts += 1
                self.logger.info(
                    f"Recovery attempt "
                    f"{self.recovery_attempts}/{max_attempts}"
                )

                # Try to reconnect primary
                await self.primary.disconnect()
                await asyncio.sleep(2)  # Brief pause

                if await self.primary.connect():
                    self.logger.info("Primary reconnected, testing health")
                    await asyncio.sleep(5)  # Wait for stability

                    health = await self.primary.get_health()
                    if health.is_healthy():
                        self.logger.info(
                            "Primary is healthy - switching back"
                        )
                        await self._complete_failover_recovery()
                        return
                    else:
                        self.logger.warning(
                            "Primary reconnected but still unhealthy"
                        )

                await asyncio.sleep(retry_interval)

            if self.recovery_attempts >= max_attempts:
                self.logger.error(
                    f"Primary recovery failed after "
                    f"{max_attempts} attempts"
                )

        except Exception as e:
            self.logger.error(
                f"Error in recovery attempts: {e}",
                exc_info=True
            )

    async def _complete_failover_recovery(self):
        """Complete recovery back to primary"""
        try:
            self.logger.info("Completing failover recovery to primary")

            assert self.primary is not None  # Type guard
            assert self.backup is not None  # Type guard
            # Ensure primary is connected before attempting to start
            if self.primary.status != DestinationStatus.CONNECTED:
                self.logger.info("Reconnecting primary before recovery")
                if not await self.primary.connect():
                    self.logger.error(
                        "Failed to reconnect primary during recovery"
                    )
                    return

            # Start streaming on primary
            if await self.primary.start_streaming():
                # Stop backup
                await self.backup.stop_streaming()

                # Hide slate if it was shown
                if self.config.failover.show_slate:
                    await self._hide_slate()

                # Switch active destination
                self.active_destination = self.primary
                self.failover_active = False
                self.recovery_attempts = 0

                # Record successful recovery in metrics
                self.metrics.record_failover_end(success=True)

                self.logger.info(
                    "✅ Recovery complete - streaming on primary"
                )

                # Log event with metrics summary
                metrics_summary = self.metrics.get_summary()
                self.logger.info("Failover recovery complete", extra={
                    "event": "recovery",
                    "from": "backup",
                    "to": "primary",
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics_summary
                })
            else:
                self.logger.error("Failed to restart primary after recovery")
                # Don't end the failover event yet, keep trying

        except Exception as e:
            self.logger.error(
                f"Failed to complete recovery: {e}",
                exc_info=True
            )

    async def _log_health_periodically(self):
        """Log health metrics at regular intervals"""
        try:
            interval = self.config.health_log_interval_sec

            while self.streaming:
                try:
                    if self.active_destination:
                        health = await self.active_destination.get_health()
                        self.logger.info(

                            f"Health: {health.name} | "
                            f"bitrate={health.bitrate_actual:.1f}Mbps | "
                            f"rtt={health.rtt_ms:.0f}ms | "
                            f"loss={health.packet_loss_pct:.2f}% | "
                            f"status={health.status.value}",
                            extra={"health_metrics": health}
                        )

                    await asyncio.sleep(interval)

                except Exception as e:
                    self.logger.error(f"Error logging health: {e}")
                    await asyncio.sleep(interval)

        except asyncio.CancelledError:
            self.logger.info("Health logging task cancelled")

    async def get_status(self) -> Dict:
        """
        Get current egress status

        Returns:
            Dict with status of all destinations
        """
        status = {
            "streaming": self.streaming,
            "failover_active": self.failover_active,
            "recovery_attempts": self.recovery_attempts,
            "active_destination": (
                self.active_destination.name
                if self.active_destination
                else None
            ),
            "primary": (
                await self.primary.get_health()
                if self.primary
                else None
            ),
            "backup": await self.backup.get_health() if self.backup else None
        }
        return status

    def get_failover_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive failover metrics

        Returns:
            Dict with failover statistics including:
            - Total failover count
            - Recovery success rate
            - Average failover/slate duration
            - Recent failover timestamps

        Example:
            >>> metrics = manager.get_failover_metrics()
            >>> print(f"Total failovers: {metrics['total_failovers']}")
            >>> print(f"Success rate: {metrics['recovery_success_rate_pct']}%")
        """
        return self.metrics.get_summary()

    def log_failover_metrics(self) -> None:
        """
        Log current failover metrics for monitoring

        Useful for periodic metrics logging or debugging
        """
        metrics = self.get_failover_metrics()
        self.logger.info("Failover Metrics Summary", extra=metrics)


# ============================================================================
# Factory Functions
# ============================================================================


def create_rtmp_destination(
    name: str,
    url: str,
    key: str,
    bitrate_mbps: float = 6.0
) -> RTMPDestination:
    """
    Factory function for RTMP destinations

    Args:
        name: Destination name (e.g., "youtube", "twitch")
        url: RTMP URL (e.g., "rtmp://a.rtmp.youtube.com/live2")
        key: Stream key (encrypted)
        bitrate_mbps: Target bitrate in Mbps

    Returns:
        RTMPDestination instance
    """
    return RTMPDestination(name, url, key, bitrate_mbps)


def create_srt_destination(
    name: str,
    url: str,
    latency_ms: int = 2000
) -> SRTDestination:
    """
    Factory function for SRT destinations


    Args:
        name: Destination name (e.g., "srt-relay")
        url: SRT URL (e.g., "srt://relay.example.com:9998")
        latency_ms: SRT latency in milliseconds

    Returns:
        SRTDestination instance
    """
    return SRTDestination(name, url, latency_ms)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    """
    Example usage of egress manager
    """

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example configuration
    config = EgressConfig(
        primary_destination={
            "type": "rtmp",
            "url": "rtmp://a.rtmp.youtube.com/live2",
            "key": "YOUR_STREAM_KEY_HERE",
            "bitrate_mbps": 6.0
        },
        backup_destination={
            "type": "srt",
            "url": "srt://relay.example.com:9998",
            "latency_ms": 2000
        },
        failover=FailoverConfig(
            enabled=True,
            trigger_packet_loss_pct=5.0,
            trigger_rtt_ms=500.0,
            trigger_duration_sec=10.0,
            retry_interval_sec=30.0
        )
    )

    async def main():
        # Create egress manager
        manager = EgressManager(config)

        # Start streaming
        if await manager.start_streaming():
            print("✅ Streaming started")

            # Stream for 30 seconds (demo)
            await asyncio.sleep(30)

            # Get status
            status = await manager.get_status()
            print(f"Status: {status}")

            # Stop streaming
            await manager.stop_streaming()
            print("✅ Streaming stopped")
        else:
            print("❌ Failed to start streaming")

    # Run
    asyncio.run(main())
