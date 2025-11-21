"""
Multi-Platform Streaming Module

Wraps the existing egress_v2.py multi-destination manager to provide
unified streaming control through the Hub architecture.

Features:
- Stream to multiple platforms simultaneously
- Health monitoring per destination
- Automatic failover (RTMP → SRT backup)
- Dual YouTube channel support
- Unified start/stop interface
"""

import sys
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Add existing backend to path (must be before backend imports)
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

try:
    from core.egress_v2 import MultiDestinationManager
    from core.egress_v2 import StreamDestination as BackendStreamDest
    from core.multi_destination_manager import (
        DestinationHealth as BackendDestHealth
    )
    STREAMING_AVAILABLE = True
except ImportError as e:
    MultiDestinationManager = None
    BackendStreamDest = None
    BackendDestHealth = None
    STREAMING_AVAILABLE = False
    logging.warning(f"Streaming modules not available: {e}")

# Hub imports (after sys.path modification)
from config import get_config  # noqa: E402
from models import (  # noqa: E402
    StreamDestination,
    DestinationType,
    DestinationStatus,
    DestinationHealth,
)
from core import SessionManager, EventBus  # noqa: E402


logger = logging.getLogger(__name__)


class StreamStatus(Enum):
    """Overall stream status"""
    IDLE = "idle"
    STARTING = "starting"
    LIVE = "live"
    DEGRADED = "degraded"  # Some destinations failing
    FAILED = "failed"
    STOPPING = "stopping"


@dataclass
class StreamHealth:
    """Complete streaming health across all destinations"""
    session_id: str
    overall_status: StreamStatus
    destinations: Dict[str, 'DestinationHealth']

    # Aggregated metrics
    total_destinations: int
    healthy_destinations: int
    failed_destinations: int

    # Performance
    avg_bitrate_kbps: float
    avg_fps: float
    total_dropped_frames: int

    # Failover status
    using_backup: bool
    backup_destinations: List[str]

    timestamp: datetime

    def is_healthy(self) -> bool:
        """Check if streaming is healthy overall"""
        return (
            self.overall_status == StreamStatus.LIVE
            and self.failed_destinations == 0
        )

    def get_degraded_destinations(self) -> List[str]:
        """Get list of destinations with issues"""
        degraded = []
        for dest_id, health in self.destinations.items():
            if health.status not in ["healthy", "live"]:
                degraded.append(dest_id)
        return degraded


class MultiPlatformStreaming:
    """
    Multi-platform streaming orchestrator.

    Wraps the existing egress_v2.py multi-destination manager to provide
    unified streaming control through the Hub architecture.

    Supports:
    - YouTube (primary + secondary channels)
    - Facebook Live
    - Twitter/X Live
    - Twitch
    - Custom RTMP destinations
    - SRT backup failover

    Example:
        ```python
        streaming = MultiPlatformStreaming(session_manager)

        # Configure destinations
        await streaming.configure_destinations(
            session_id="show-001",
            destinations=[
                {
                    "platform": "youtube",
                    "stream_key": "xxx",
                    "label": "YouTube EN"
                },
                {
                    "platform": "youtube",
                    "stream_key": "yyy",
                    "label": "YouTube FR"
                },
                {"platform": "facebook", "stream_key": "zzz"},
            ]
        )

        # Start streaming
        await streaming.start_stream("show-001")

        # Monitor health
        health = await streaming.get_health("show-001")
        print(f"Status: {health.overall_status.value}")
        print(
            f"Healthy: {health.healthy_destinations}/"
            f"{health.total_destinations}"
        )

        # Stop streaming
        await streaming.stop_stream("show-001")
        ```
    """

    def __init__(
        self,
        session_manager: SessionManager,
        event_bus: Optional[EventBus] = None,
    ):
        if not STREAMING_AVAILABLE:
            logger.warning(
                "Streaming modules not available - "
                "module will operate in limited mode"
            )
            self._session_manager = session_manager
            self._event_bus = event_bus or EventBus()
            self._egress = None
            self._active_streams: Dict[str, StreamStatus] = {}
            self._health_monitoring_tasks: Dict[str, asyncio.Task[None]] = {}
            return

        self._session_manager = session_manager
        self._event_bus = event_bus or EventBus()

        config = get_config()

        # Multi-destination manager from existing backend
        self._egress = MultiDestinationManager(
            failover_enabled=config.streaming.enable_failover,
            health_check_interval=(
                config.streaming.health_check_interval_seconds
            ),
        )

        # Track active streams per session
        self._active_streams = {}

        # Health monitoring tasks
        self._health_monitoring_tasks = {}

        logger.info("Multi-platform streaming initialized")

    async def configure_destinations(
        self,
        session_id: str,
        destinations: List[Dict[str, Any]],
    ) -> bool:
        """
        Configure streaming destinations for a session.

        Args:
            session_id: Session to configure
            destinations: List of destination configurations
                Each should have:
                - platform: "youtube", "facebook", "twitter", "twitch", "rtmp"
                - stream_key: Platform stream key
                - label: Optional friendly name
                - backup_enabled: Optional backup failover

        Returns:
            True if configured successfully
        """
        logger.info(
            f"Configuring {
                len(destinations)} destinations for session {session_id}")

        # Get session
        session = self._session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return False

        try:
            # Clear existing destinations
            session.destinations.clear()

            # Configure each destination
            for dest_config in destinations:
                platform = dest_config.get("platform", "rtmp")
                stream_key = dest_config.get("stream_key")
                label = dest_config.get("label", f"{platform.title()} Stream")

                if not stream_key:
                    logger.error(f"No stream key provided for {label}")
                    continue

                # Get platform-specific RTMP URL
                rtmp_url = self._get_platform_rtmp_url(platform, stream_key)

                # Create destination
                platform_lower = platform.lower()
                if platform_lower in [
                    "youtube", "facebook", "twitter", "twitch", "linkedin"
                ]:
                    dest_type = DestinationType(platform_lower)
                else:
                    dest_type = DestinationType.CUSTOM_RTMP

                destination = StreamDestination(
                    id=f"{session_id}_{platform}_{len(session.destinations)}",
                    name=label,
                    type=dest_type,
                    url=rtmp_url,
                    stream_key=stream_key,
                    is_backup=False,
                    enabled=True,
                    status=DestinationStatus.IDLE,
                )

                session.destinations.append(destination)

                logger.info(f"Added destination: {label}")

            logger.info(f"Configured {len(session.destinations)} destinations")

            # Emit event
            await self._event_bus.publish("destinations_configured", {
                "session_id": session_id,
                "destination_count": len(session.destinations),
                "timestamp": datetime.now().isoformat(),
            })

            return True

        except Exception as e:
            logger.error(
                f"Failed to configure destinations: {e}",
                exc_info=True)
            return False

    def _get_platform_rtmp_url(self, platform: str, stream_key: str) -> str:
        """Get RTMP ingest URL for platform."""
        urls = {
            "youtube": f"rtmp://a.rtmp.youtube.com/live2/{stream_key}",
            "facebook": (
                f"rtmps://live-api-s.facebook.com:443/rtmp/"
                f"{stream_key}"
            ),
            "twitter": f"rtmp://va.pscp.tv:80/x/{stream_key}",
            "twitch": f"rtmp://live.twitch.tv/app/{stream_key}",
        }

        # Return platform URL or assume custom RTMP
        return urls.get(platform.lower(),
                        f"rtmp://custom-server/live/{stream_key}")

    def _get_backup_url(self) -> str:
        """Get SRT backup URL from configuration."""
        config = get_config()
        backup_host = config.streaming.srt_backup_host or "localhost"
        backup_port = config.streaming.srt_backup_port or 9000
        return f"srt://{backup_host}:{backup_port}"

    async def start_stream(
        self,
        session_id: str,
        start_recording: bool = True,
    ) -> bool:
        """
        Start streaming for a session.

        Args:
            session_id: Session to start streaming
            start_recording: Whether to also start recording

        Returns:
            True if started successfully
        """
        logger.info(f"Starting stream for session: {session_id}")

        # Get session
        session = self._session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return False

        if not session.destinations:
            logger.error(
                f"No destinations configured for session: {session_id}")
            return False

        if session_id in self._active_streams:
            logger.warning(f"Stream already active for session: {session_id}")
            return False

        try:
            # Update status
            self._active_streams[session_id] = StreamStatus.STARTING

            # Emit event
            await self._event_bus.publish("stream_starting", {
                "session_id": session_id,
                "destination_count": len(session.destinations),
                "timestamp": datetime.now().isoformat(),
            })

            # Start streaming via egress manager
            for destination in session.destinations:
                try:
                    if self._egress is None:
                        logger.error("Egress manager not available")
                        destination.status = DestinationStatus.ERROR
                        continue

                    # Configure destination in egress
                    await self._egress.add_destination(
                        dest_id=destination.id,
                        rtmp_url=destination.rtmp_url,
                        backup_url=destination.backup_url,
                    )

                    # Start streaming to destination
                    await self._egress.start_destination(destination.id)

                    destination.status = DestinationStatus.LIVE
                    logger.info(f"Started streaming to: {destination.name}")

                except Exception as e:
                    logger.error(
                        f"Failed to start destination {
                            destination.name}: {e}")
                    destination.status = DestinationStatus.ERROR

            # Update overall status
            healthy_count = sum(
                1 for d in session.destinations
                if d.status == DestinationStatus.LIVE
            )

            if healthy_count == 0:
                self._active_streams[session_id] = StreamStatus.FAILED
                logger.error("All destinations failed to start")
                return False
            elif healthy_count < len(session.destinations):
                self._active_streams[session_id] = StreamStatus.DEGRADED
                logger.warning(
                    f"Started with degraded status "
                    f"({healthy_count}/{len(session.destinations)})"
                )
            else:
                self._active_streams[session_id] = StreamStatus.LIVE
                logger.info(
                    f"Stream started successfully "
                    f"({healthy_count} destinations)"
                )

            # Start health monitoring
            await self._start_health_monitoring(session_id)

            # Emit success event
            await self._event_bus.publish("stream_started", {
                "session_id": session_id,
                "status": self._active_streams[session_id].value,
                "healthy_destinations": healthy_count,
                "total_destinations": len(session.destinations),
                "timestamp": datetime.now().isoformat(),
            })

            return True

        except Exception as e:
            logger.error(f"Failed to start stream: {e}", exc_info=True)
            self._active_streams[session_id] = StreamStatus.FAILED

            await self._event_bus.publish("stream_failed", {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })

            return False

    async def stop_stream(self, session_id: str) -> bool:
        """
        Stop streaming for a session.

        Args:
            session_id: Session to stop streaming

        Returns:
            True if stopped successfully
        """
        logger.info(f"Stopping stream for session: {session_id}")

        if session_id not in self._active_streams:
            logger.warning(f"No active stream for session: {session_id}")
            return False

        # Get session
        session = self._session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return False

        try:
            # Update status
            self._active_streams[session_id] = StreamStatus.STOPPING

            # Emit event
            await self._event_bus.publish("stream_stopping", {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            })

            # Stop health monitoring
            await self._stop_health_monitoring(session_id)

            # Stop all destinations
            for destination in session.destinations:
                try:
                    if self._egress is None:
                        logger.error("Egress manager not available")
                        continue

                    await self._egress.stop_destination(destination.id)
                    await self._egress.remove_destination(destination.id)

                    destination.status = DestinationStatus.IDLE
                    logger.info(f"Stopped streaming to: {destination.name}")

                except Exception as e:
                    logger.error(
                        f"Error stopping destination {
                            destination.name}: {e}")

            # Remove from active streams
            del self._active_streams[session_id]

            logger.info("Stream stopped successfully")

            # Emit success event
            await self._event_bus.publish("stream_stopped", {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            })

            return True

        except Exception as e:
            logger.error(f"Failed to stop stream: {e}", exc_info=True)
            return False

    async def get_health(self, session_id: str) -> Optional[StreamHealth]:
        """
        Get current streaming health for a session.

        Args:
            session_id: Session to check

        Returns:
            Stream health or None if not streaming
        """
        if session_id not in self._active_streams:
            return None

        # Get session
        session = self._session_manager.get_session(session_id)
        if not session:
            return None

        try:
            # Get health from egress manager
            destination_health = {}
            total_bitrate = 0.0
            total_fps = 0.0
            total_dropped = 0
            healthy_count = 0
            failed_count = 0
            using_backup = False
            backup_destinations = []

            for destination in session.destinations:
                try:
                    if self._egress is None:
                        logger.error("Egress manager not available")
                        failed_count += 1
                        continue

                    health = await self._egress.get_destination_health(
                        destination.id
                    )
                    destination_health[destination.id] = health

                    # Aggregate metrics
                    total_bitrate += health.get("bitrate_kbps", 0)
                    total_fps += health.get("fps", 0)
                    total_dropped += health.get("dropped_frames", 0)

                    # Count status
                    if health.get("status") == "healthy":
                        healthy_count += 1
                    elif health.get("status") == "failed":
                        failed_count += 1

                    # Check failover
                    if health.get("using_backup", False):
                        using_backup = True
                        backup_destinations.append(destination.id)

                except Exception as e:
                    logger.error(
                        f"Failed to get health for {
                            destination.id}: {e}")
                    failed_count += 1

            # Determine overall status
            if failed_count == len(session.destinations):
                overall_status = StreamStatus.FAILED
            elif failed_count > 0:
                overall_status = StreamStatus.DEGRADED
            else:
                overall_status = self._active_streams[session_id]

            # Calculate averages
            dest_count = len(session.destinations)
            avg_bitrate = total_bitrate / dest_count if dest_count > 0 else 0.0
            avg_fps = total_fps / dest_count if dest_count > 0 else 0.0

            health = StreamHealth(
                session_id=session_id,
                overall_status=overall_status,
                destinations=destination_health,
                total_destinations=dest_count,
                healthy_destinations=healthy_count,
                failed_destinations=failed_count,
                avg_bitrate_kbps=avg_bitrate,
                avg_fps=avg_fps,
                total_dropped_frames=total_dropped,
                using_backup=using_backup,
                backup_destinations=backup_destinations,
                timestamp=datetime.now(),
            )

            return health

        except Exception as e:
            logger.error(f"Failed to get stream health: {e}", exc_info=True)
            return None

    async def _start_health_monitoring(self, session_id: str) -> None:
        """Start monitoring stream health."""
        if session_id in self._health_monitoring_tasks:
            logger.warning(f"Already monitoring session: {session_id}")
            return

        logger.info(f"Starting health monitoring for session: {session_id}")

        task = asyncio.create_task(self._health_monitoring_loop(session_id))
        self._health_monitoring_tasks[session_id] = task

    async def _stop_health_monitoring(self, session_id: str) -> None:
        """Stop monitoring stream health."""
        if session_id not in self._health_monitoring_tasks:
            return

        logger.info(f"Stopping health monitoring for session: {session_id}")

        task = self._health_monitoring_tasks[session_id]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        del self._health_monitoring_tasks[session_id]

    async def _health_monitoring_loop(self, session_id: str) -> None:
        """Monitor stream health continuously."""
        config = get_config()
        interval = config.streaming.health_check_interval_seconds or 5.0

        logger.debug(
            f"Health monitoring loop started for session: {session_id}")

        while True:
            try:
                # Get health
                health = await self.get_health(session_id)

                if not health:
                    logger.warning(f"No health data for session: {session_id}")
                    break

                # Emit health update event
                await self._event_bus.publish("stream_health_updated", {
                    "session_id": session_id,
                    "status": health.overall_status.value,
                    "healthy_destinations": health.healthy_destinations,
                    "total_destinations": health.total_destinations,
                    "avg_bitrate_kbps": health.avg_bitrate_kbps,
                    "avg_fps": health.avg_fps,
                    "dropped_frames": health.total_dropped_frames,
                    "using_backup": health.using_backup,
                    "timestamp": health.timestamp.isoformat(),
                })

                # Check for critical issues
                if health.overall_status == StreamStatus.FAILED:
                    logger.error(f"Stream failed for session: {session_id}")

                    await self._event_bus.publish("stream_health_critical", {
                        "session_id": session_id,
                        "reason": "all_destinations_failed",
                        "timestamp": datetime.now().isoformat(),
                    })

                elif health.overall_status == StreamStatus.DEGRADED:
                    degraded = health.get_degraded_destinations()
                    logger.warning(
                        f"Stream degraded for session {session_id}: "
                        f"{len(degraded)} failed destinations"
                    )

                    await self._event_bus.publish("stream_health_degraded", {
                        "session_id": session_id,
                        "failed_destinations": degraded,
                        "timestamp": datetime.now().isoformat(),
                    })

                # Wait before next check
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Health monitoring error for {session_id}: {e}",
                    exc_info=True)
                await asyncio.sleep(interval)

        logger.debug(
            f"Health monitoring loop stopped for session: {session_id}")

    def is_streaming(self, session_id: str) -> bool:
        """Check if session is currently streaming."""
        return session_id in self._active_streams

    def get_stream_status(self, session_id: str) -> Optional[StreamStatus]:
        """Get current stream status."""
        return self._active_streams.get(session_id)

    def list_active_streams(self) -> List[str]:
        """Get list of sessions currently streaming."""
        return list(self._active_streams.keys())

    async def shutdown(self) -> None:
        """Shutdown and clean up resources."""
        logger.info("Shutting down multi-platform streaming")

        # Stop all active streams
        sessions = list(self._active_streams.keys())
        for session_id in sessions:
            await self.stop_stream(session_id)

        logger.info("Multi-platform streaming shutdown complete")
