"""
Egress Manager V2 - Dual-Path RTMP + SRT Backup Streaming
==========================================================

Week 5-6 Implementation: Reliable multi-destination streaming with failover

Architecture:
- OBS Studio streams continuously to local NGINX RTMP server
- NGINX relays stream to multiple RTMP destinations (YouTube EN/FR)
- Egress Manager monitors RTMP health and manages failover state
- On RTMP failure: State switches to SRT backup mode (alerting/routing)
- On RTMP recovery: State switches back to RTMP mode

Failover Behavior:
- Monitors RTMP health every 5 seconds
- Triggers failover after 3 consecutive failures (~15 seconds)
- Triggers recovery after 5 consecutive healthy checks (~25 seconds)
- OBS continues streaming to NGINX throughout (no interruption)
- State changes signal to external systems (monitoring, routing, alerting)

Features:
- Dual RTMP streaming (YouTube EN + FR)
- SRT backup destination for failover
- Automatic failover detection and state management
- Health monitoring per destination
- Connection status tracking
- Integration with OBS WebSocket

Author: Miktos StreamLab
Date: November 3, 2025
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Status
# ============================================================================


class DestinationStatus(Enum):
    """Status of a streaming destination"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    FAILED = "failed"


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class RTMPDestination:
    """RTMP streaming destination (e.g., YouTube, Twitch, Facebook)"""

    name: str
    url: str  # e.g., rtmp://a.rtmp.youtube.com/live2
    key: str  # Stream key
    enabled: bool = True

    # Status
    status: DestinationStatus = DestinationStatus.DISCONNECTED
    connected_at: Optional[datetime] = None

    # Health metrics (populated by OBS)
    bitrate_kbps: float = 0.0
    dropped_frames: int = 0
    total_frames: int = 0

    def get_full_url(self) -> str:
        """Get complete RTMP URL with key"""
        return f"{self.url}/{self.key}"

    @property
    def drop_percentage(self) -> float:
        """Calculate drop percentage"""
        if self.total_frames == 0:
            return 0.0
        return (self.dropped_frames / self.total_frames) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        uptime = None
        if self.connected_at:
            uptime = (datetime.now() - self.connected_at).total_seconds()

        return {
            "name": self.name,
            "url": self.url,
            "enabled": self.enabled,
            "status": self.status.value,
            "bitrate_kbps": self.bitrate_kbps,
            "dropped_frames": self.dropped_frames,
            "total_frames": self.total_frames,
            "drop_percentage": self.drop_percentage,
            "uptime_seconds": uptime,
        }


@dataclass
class SRTDestination:
    """SRT (Secure Reliable Transport) backup destination"""

    name: str
    url: str  # e.g., srt://backup.example.com:9000?mode=caller
    enabled: bool = True

    # Status
    status: DestinationStatus = DestinationStatus.DISCONNECTED
    connected_at: Optional[datetime] = None
    is_backup: bool = True  # Mark as backup destination

    # Health metrics
    bitrate_kbps: float = 0.0
    dropped_frames: int = 0
    total_frames: int = 0
    latency_ms: float = 0.0  # SRT-specific: transmission latency

    @property
    def drop_percentage(self) -> float:
        """Calculate drop percentage"""
        if self.total_frames == 0:
            return 0.0
        return (self.dropped_frames / self.total_frames) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        uptime = None
        if self.connected_at:
            uptime = (datetime.now() - self.connected_at).total_seconds()

        return {
            "name": self.name,
            "url": self.url,
            "enabled": self.enabled,
            "status": self.status.value,
            "is_backup": self.is_backup,
            "bitrate_kbps": self.bitrate_kbps,
            "dropped_frames": self.dropped_frames,
            "total_frames": self.total_frames,
            "drop_percentage": self.drop_percentage,
            "latency_ms": self.latency_ms,
            "uptime_seconds": uptime,
        }


@dataclass
class EgressConfig:
    """Configuration for egress destinations"""

    rtmp_destinations: List[RTMPDestination] = field(default_factory=list)
    srt_destinations: List[SRTDestination] = field(default_factory=list)

    @property
    def all_destinations(self) -> List:
        """Get all destinations (RTMP + SRT)"""
        return self.rtmp_destinations + self.srt_destinations

    @classmethod
    def from_env(cls) -> "EgressConfig":
        """
        Load configuration from environment variables.

        Expected environment variables:
        - YOUTUBE_EN_STREAM_KEY: YouTube English channel stream key
        - YOUTUBE_FR_STREAM_KEY: YouTube French channel stream key
        - SRT_BACKUP_URL: SRT backup server URL (optional)

        Returns:
            EgressConfig with configured destinations
        """
        load_dotenv()

        rtmp_destinations = []
        srt_destinations = []

        # YouTube EN
        youtube_en_key = os.getenv("YOUTUBE_EN_STREAM_KEY")
        if youtube_en_key:
            rtmp_destinations.append(
                RTMPDestination(
                    name="YouTube EN",
                    url="rtmp://a.rtmp.youtube.com/live2",
                    key=youtube_en_key,
                    enabled=True,
                )
            )
            logger.info("Configured YouTube EN destination")
        else:
            logger.warning("YOUTUBE_EN_STREAM_KEY not found in environment")

        # YouTube FR
        youtube_fr_key = os.getenv("YOUTUBE_FR_STREAM_KEY")
        if youtube_fr_key:
            rtmp_destinations.append(
                RTMPDestination(
                    name="YouTube FR",
                    url="rtmp://a.rtmp.youtube.com/live2",
                    key=youtube_fr_key,
                    enabled=True,
                )
            )
            logger.info("Configured YouTube FR destination")
        else:
            logger.warning("YOUTUBE_FR_STREAM_KEY not found in environment")

        # SRT Backup
        srt_backup_url = os.getenv("SRT_BACKUP_URL")
        if srt_backup_url:
            srt_destinations.append(
                SRTDestination(
                    name="SRT Backup",
                    url=srt_backup_url,
                    enabled=True,
                    is_backup=True,
                )
            )
            logger.info(f"Configured SRT backup destination: {srt_backup_url}")
        else:
            logger.info("No SRT backup configured (optional)")

        if not rtmp_destinations and not srt_destinations:
            logger.error(
                "No streaming destinations configured! "
                "Please set YOUTUBE_EN_STREAM_KEY and/or "
                "YOUTUBE_FR_STREAM_KEY in .env file"
            )

        return cls(
            rtmp_destinations=rtmp_destinations,
            srt_destinations=srt_destinations,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "rtmp_destinations": [dest.to_dict() for dest in self.rtmp_destinations],
            "srt_destinations": [dest.to_dict() for dest in self.srt_destinations],
            "total_destinations": len(self.all_destinations),
            "enabled_destinations": sum(1 for d in self.all_destinations if d.enabled),
        }


# ============================================================================
# Egress Manager
# ============================================================================


class EgressManagerV2:
    """
    Simplified egress manager for Week 5-6 dual-path RTMP streaming.

    Features:
    - Dual RTMP streaming (YouTube EN + FR)
    - Health monitoring per destination
    - Connection status tracking
    - Background health monitoring

    Note: OBS WebSocket doesn't natively support multiple RTMP outputs.
          This requires either:
          1. OBS Multiple Output Plugin
          2. NGINX RTMP relay (recommended for Week 5-6)
          3. External RTMP relay/splitter
    """

    def __init__(self, obs_controller: Any, config: Optional[EgressConfig] = None):
        """
        Initialize egress manager.

        Args:
            obs_controller: OBS controller instance
            config: Egress configuration (loads from env if not provided)
        """
        self.obs = obs_controller
        self.config = config or EgressConfig.from_env()

        self.streaming = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self._monitor_count = 0

        # Failover state tracking
        self._using_srt_backup = False
        self._rtmp_failure_count = 0
        self._rtmp_recovery_count = 0
        self._last_failover_time: Optional[datetime] = None
        self._last_recovery_time: Optional[datetime] = None

        # Failover thresholds
        self.RTMP_FAILURE_THRESHOLD = 3  # Consecutive failures before failover
        self.RTMP_RECOVERY_THRESHOLD = 5  # Consecutive healthy checks before recovery
        self.DROP_RATE_FAILURE_THRESHOLD = 10.0  # 10% drop rate
        self.ZERO_BITRATE_THRESHOLD = 30  # 30 seconds of zero bitrate

        logger.info(
            f"EgressManagerV2 initialized with " f"{len(self.config.all_destinations)} destinations"
        )
        for dest in self.config.all_destinations:
            url = dest.url if hasattr(dest, "url") else dest.get_full_url()
            logger.info(f"  - {dest.name}: {url}")

    async def start_streaming(self) -> bool:
        """
        Start streaming to all enabled destinations.

        Note: With NGINX RTMP relay, you only need to start OBS streaming
              to localhost, and NGINX will handle pushing to multiple
              destinations.

        Returns:
            True if streaming started successfully
        """
        if self.streaming:
            logger.warning("Already streaming")
            return False

        try:
            logger.info("Starting streaming to all destinations...")

            # Start OBS streaming
            # (Configure OBS to stream to NGINX relay: rtmp://localhost/live)
            success = await self.obs.start_streaming()
            if not success:
                logger.error("Failed to start OBS streaming")
                return False

            self.streaming = True

            # Mark all enabled destinations as streaming
            for dest in self.config.all_destinations:
                if dest.enabled:
                    dest.status = DestinationStatus.STREAMING
                    dest.connected_at = datetime.now()
                    logger.info(f"Streaming started to {dest.name}")

            # Start health monitoring
            self.monitoring_task = asyncio.create_task(self._monitor_health())

            logger.info("✅ Streaming started successfully to all destinations")
            return True

        except Exception as e:
            logger.error(f"Failed to start streaming: {e}", exc_info=True)
            return False

    async def stop_streaming(self) -> bool:
        """
        Stop streaming to all destinations.

        Returns:
            True if streaming stopped successfully
        """
        if not self.streaming:
            logger.warning("Not currently streaming")
            return False

        try:
            logger.info("Stopping streaming...")

            # Stop health monitoring
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    logger.debug("Health monitoring task cancelled")

            # Stop OBS streaming
            await self.obs.stop_streaming()

            self.streaming = False

            # Mark all destinations as disconnected
            for dest in self.config.all_destinations:
                dest.status = DestinationStatus.DISCONNECTED
                dest.connected_at = None
                logger.info(f"Stopped streaming to {dest.name}")

            logger.info("✅ Streaming stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to stop streaming: {e}", exc_info=True)
            return False

    async def get_health(self) -> Dict[str, Any]:
        """
        Get current health status of all destinations.

        Returns:
            Dictionary with health metrics for all destinations
        """
        if not self.streaming:
            return {
                "streaming": False,
                "destinations": [dest.to_dict() for dest in self.config.all_destinations],
            }

        # Get OBS stream stats
        try:
            stats = await self.obs.get_stream_stats()

            # Update all destinations with OBS stats
            # (Since we're using NGINX relay, all destinations get same stats)
            if stats:
                # Calculate bitrate in kbps from bytes and duration
                bitrate_kbps = 0.0
                if stats.duration_seconds > 0:
                    bitrate_kbps = (stats.bytes_sent * 8) / (stats.duration_seconds * 1000)

                for dest in self.config.all_destinations:
                    if dest.enabled and dest.status == DestinationStatus.STREAMING:
                        dest.bitrate_kbps = bitrate_kbps
                        dest.dropped_frames = stats.dropped_frames
                        dest.total_frames = stats.total_frames

        except Exception as e:
            logger.error(f"Failed to get OBS stats: {e}", exc_info=True)

        # Build health report
        health = {
            "streaming": self.streaming,
            "destinations": [dest.to_dict() for dest in self.config.all_destinations],
            "summary": {
                "total": len(self.config.all_destinations),
                "enabled": sum(1 for d in self.config.all_destinations if d.enabled),
                "streaming": sum(
                    1
                    for d in self.config.all_destinations
                    if d.status == DestinationStatus.STREAMING
                ),
                "failed": sum(
                    1 for d in self.config.all_destinations if d.status == DestinationStatus.FAILED
                ),
            },
        }

        return health

    def _check_rtmp_health(self) -> bool:
        """
        Check if RTMP destinations are healthy.

        Returns:
            True if at least one RTMP destination is healthy
        """
        if not self.config.rtmp_destinations:
            return False

        healthy_count = 0
        for dest in self.config.rtmp_destinations:
            if not dest.enabled:
                continue

            # Check if destination is healthy
            is_healthy = (
                dest.status == DestinationStatus.STREAMING
                and dest.drop_percentage < self.DROP_RATE_FAILURE_THRESHOLD
                and dest.bitrate_kbps > 0
            )

            if is_healthy:
                healthy_count += 1

        # Consider RTMP healthy if at least one destination is healthy
        return healthy_count > 0

    async def _failover_to_srt(self) -> bool:
        """
        Switch to SRT backup destination.

        Returns:
            True if failover successful
        """
        if self._using_srt_backup:
            logger.warning("Already using SRT backup")
            return False

        if not self.config.srt_destinations:
            logger.error("No SRT backup configured - cannot failover")
            return False

        srt_backup = self.config.srt_destinations[0]
        if not srt_backup.enabled:
            logger.error(f"SRT backup '{srt_backup.name}' is disabled - cannot failover")
            return False

        logger.warning(f"🔄 FAILOVER: Switching to SRT backup '{srt_backup.name}'")

        try:
            # In NGINX-based architecture, we keep OBS streaming to NGINX
            # The failover is a state/monitoring change, not a stream switch
            # External systems (NGINX, SRT relay) would handle actual routing

            # Mark state change
            self._using_srt_backup = True
            self._last_failover_time = datetime.now()

            # Mark RTMP destinations as failed
            for dest in self.config.rtmp_destinations:
                if dest.enabled:
                    dest.status = DestinationStatus.FAILED

            # Mark SRT as streaming (for monitoring/alerting purposes)
            srt_backup.status = DestinationStatus.STREAMING
            srt_backup.connected_at = datetime.now()

            logger.info(
                f"✅ Failover state activated - RTMP marked as failed, "
                f"SRT backup '{srt_backup.name}' is standby target"
            )
            logger.info(
                f"📡 OBS continues streaming to NGINX - "
                f"External routing should direct to: {srt_backup.url}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to switch to SRT backup: {e}", exc_info=True)
            self._using_srt_backup = False
            return False

    async def _recover_to_rtmp(self) -> bool:
        """
        Switch back to RTMP destinations after recovery.

        Returns:
            True if recovery successful
        """
        if not self._using_srt_backup:
            logger.warning("Not using SRT backup - nothing to recover from")
            return False

        logger.info("🔄 RECOVERY: Switching back to RTMP destinations")

        try:
            # In NGINX-based architecture, OBS stays streaming to NGINX
            # Recovery is a state change - mark RTMP as healthy again

            # Mark state change
            self._using_srt_backup = False
            self._last_recovery_time = datetime.now()

            # Mark SRT as disconnected (no longer needed as backup)
            for srt_dest in self.config.srt_destinations:
                srt_dest.status = DestinationStatus.DISCONNECTED
                srt_dest.connected_at = None

            # Mark RTMP destinations as streaming again
            for rtmp_dest in self.config.rtmp_destinations:
                if rtmp_dest.enabled:
                    rtmp_dest.status = DestinationStatus.STREAMING
                    rtmp_dest.connected_at = datetime.now()

            logger.info(
                "✅ Recovery complete - RTMP destinations marked healthy, " "SRT backup standby"
            )
            logger.info(
                "📡 OBS continues streaming to NGINX - " "External routing restored to RTMP"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to recover to RTMP: {e}", exc_info=True)
            self._using_srt_backup = True
            return False

    async def _monitor_health(self) -> None:
        """
        Background task to monitor health and handle automatic failover.

        Monitors RTMP health and automatically switches to SRT backup if:
        - Drop rate exceeds 10%
        - Connection is lost
        - Bitrate is zero for extended period

        Also monitors for RTMP recovery and switches back when stable.
        """
        logger.info("Health monitoring started (5-second interval)")

        try:
            while self.streaming:
                health = await self.get_health()

                # Check RTMP health for failover decisions
                rtmp_healthy = self._check_rtmp_health()

                if not self._using_srt_backup:
                    # Currently using RTMP - check if we need to failover
                    if not rtmp_healthy:
                        self._rtmp_failure_count += 1
                        self._rtmp_recovery_count = 0

                        logger.warning(
                            f"RTMP unhealthy (failure count: "
                            f"{self._rtmp_failure_count}/"
                            f"{self.RTMP_FAILURE_THRESHOLD})"
                        )

                        if self._rtmp_failure_count >= self.RTMP_FAILURE_THRESHOLD:
                            # Trigger failover to SRT
                            logger.error(
                                "⚠️ RTMP failure threshold reached - "
                                "initiating failover to SRT backup"
                            )
                            await self._failover_to_srt()
                            self._rtmp_failure_count = 0
                    else:
                        # RTMP is healthy - reset failure counter
                        if self._rtmp_failure_count > 0:
                            logger.info("RTMP recovered - resetting failure counter")
                        self._rtmp_failure_count = 0
                        self._rtmp_recovery_count = 0

                else:
                    # Currently using SRT backup - check if RTMP has recovered
                    if rtmp_healthy:
                        self._rtmp_recovery_count += 1
                        self._rtmp_failure_count = 0

                        logger.info(
                            f"RTMP recovery detected (recovery count: "
                            f"{self._rtmp_recovery_count}/"
                            f"{self.RTMP_RECOVERY_THRESHOLD})"
                        )

                        if self._rtmp_recovery_count >= self.RTMP_RECOVERY_THRESHOLD:
                            # Trigger recovery to RTMP
                            logger.info(
                                "✅ RTMP recovery threshold reached - " "switching back to RTMP"
                            )
                            await self._recover_to_rtmp()
                            self._rtmp_recovery_count = 0
                    else:
                        # RTMP still unhealthy - reset recovery counter
                        if self._rtmp_recovery_count > 0:
                            logger.debug(
                                "RTMP recovery interrupted - " "resetting recovery counter"
                            )
                        self._rtmp_recovery_count = 0
                        self._rtmp_failure_count = 0

                # Check for individual destination issues
                for dest_health in health["destinations"]:
                    drop_pct = dest_health["drop_percentage"]
                    name = dest_health["name"]

                    if drop_pct > 5.0:
                        dropped = dest_health["dropped_frames"]
                        total = dest_health["total_frames"]
                        logger.error(
                            f"{name}: HIGH drop rate {drop_pct:.1f}% " f"({dropped}/{total} frames)"
                        )
                    elif drop_pct > 1.0:
                        logger.warning(f"{name}: Elevated drop rate {drop_pct:.1f}%")

                # Log summary every 30 seconds
                self._monitor_count += 1

                if self._monitor_count % 6 == 0:  # Every 30 seconds
                    streaming = health["summary"]["streaming"]
                    enabled = health["summary"]["enabled"]
                    backup_status = "SRT BACKUP" if self._using_srt_backup else "RTMP"
                    logger.info(
                        f"Health Summary: {streaming}/{enabled} "
                        f"destinations streaming [{backup_status}]"
                    )

                # Wait before next check
                await asyncio.sleep(5.0)

        except asyncio.CancelledError:
            logger.info("Health monitoring stopped")
        except Exception as e:
            logger.error(f"Health monitoring error: {e}", exc_info=True)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        return self.config.to_dict()

    def get_failover_status(self) -> Dict[str, Any]:
        """
        Get current failover status and statistics.

        Returns:
            Dictionary with failover state information
        """
        return {
            "using_srt_backup": self._using_srt_backup,
            "rtmp_failure_count": self._rtmp_failure_count,
            "rtmp_recovery_count": self._rtmp_recovery_count,
            "last_failover_time": (
                self._last_failover_time.isoformat() if self._last_failover_time else None
            ),
            "last_recovery_time": (
                self._last_recovery_time.isoformat() if self._last_recovery_time else None
            ),
            "thresholds": {
                "failure_threshold": self.RTMP_FAILURE_THRESHOLD,
                "recovery_threshold": self.RTMP_RECOVERY_THRESHOLD,
                "drop_rate_threshold": self.DROP_RATE_FAILURE_THRESHOLD,
                "zero_bitrate_threshold": self.ZERO_BITRATE_THRESHOLD,
            },
        }

    def is_streaming(self) -> bool:
        """Check if currently streaming"""
        return self.streaming
