"""
Multi-Destination Broadcast Manager

Manages simultaneous streaming to multiple platforms (YouTube, Facebook, Twitter).
Provides unified control, health monitoring, and failover handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, UTC
from dataclasses import dataclass, field

from core.streaming_platform import (
    StreamingPlatform,
    StreamStatus,
    StreamHealth,
    StreamMetrics
)

logger = logging.getLogger(__name__)


@dataclass
class PlatformStreamStatus:
    """Status of a stream on a specific platform"""
    platform_name: str
    is_active: bool
    status: StreamStatus
    health: StreamHealth
    metrics: StreamMetrics
    error_message: Optional[str] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class MultiStreamMetrics:
    """Aggregated metrics across all platforms"""
    total_viewers: int = 0
    viewers_by_platform: Dict[str, int] = field(default_factory=dict)
    total_uptime: int = 0
    active_platforms: int = 0
    failed_platforms: int = 0
    overall_health: StreamHealth = StreamHealth.UNKNOWN


class MultiDestinationManager:
    """
    Multi-platform streaming manager.

    Features:
    - Simultaneous streaming to multiple platforms
    - Individual platform health monitoring
    - Graceful failover handling
    - Bitrate distribution
    - Unified control interface
    """

    def __init__(self):
        """Initialize multi-destination manager"""
        self.platforms: Dict[str, StreamingPlatform] = {}
        self.platform_status: Dict[str, PlatformStreamStatus] = {}
        self._is_streaming = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_interval = 10.0  # seconds

        logger.info("Multi-destination manager initialized")

    def add_platform(
        self,
        name: str,
        platform: StreamingPlatform
    ) -> None:
        """
        Add a streaming platform.

        Args:
            name: Platform identifier
            platform: Platform instance
        """
        self.platforms[name] = platform
        self.platform_status[name] = PlatformStreamStatus(
            platform_name=name,
            is_active=False,
            status=StreamStatus.IDLE,
            health=StreamHealth.UNKNOWN,
            metrics=StreamMetrics()
        )
        logger.info(f"Added platform: {name}")

    def remove_platform(self, name: str) -> bool:
        """
        Remove a streaming platform.

        Args:
            name: Platform identifier

        Returns:
            True if platform was removed
        """
        if name in self.platforms:
            del self.platforms[name]
            del self.platform_status[name]
            logger.info(f"Removed platform: {name}")
            return True
        return False

    def get_platforms(self) -> List[str]:
        """Get list of platform names"""
        return list(self.platforms.keys())

    def get_active_platforms(self) -> List[str]:
        """Get list of active platform names"""
        return [
            name for name, status in self.platform_status.items()
            if status.is_active
        ]

    async def authenticate_all(self) -> Dict[str, bool]:
        """
        Authenticate all platforms.

        Returns:
            Dictionary of platform names to auth success status
        """
        logger.info("Authenticating all platforms...")

        results = {}
        tasks = []

        for name, platform in self.platforms.items():
            tasks.append(self._authenticate_platform(name, platform))

        auth_results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(self.platforms.keys(), auth_results):
            if isinstance(result, Exception):
                logger.error(f"Auth failed for {name}: {result}")
                results[name] = False
            else:
                results[name] = result

        successful = sum(1 for r in results.values() if r)
        logger.info(
            f"Authentication complete: {successful}/{len(results)} successful"
        )

        return results

    async def _authenticate_platform(
        self,
        name: str,
        platform: StreamingPlatform
    ) -> bool:
        """Authenticate a single platform"""
        try:
            success = await platform.authenticate()
            if success:
                logger.info(f"✅ {name} authenticated")
            else:
                logger.warning(f"❌ {name} authentication failed")
            return success
        except Exception as e:
            logger.error(f"Error authenticating {name}: {e}")
            return False

    async def start_all(
        self,
        title: str,
        description: str = "",
        category: str = "",
        **kwargs
    ) -> Dict[str, bool]:
        """
        Start streaming on all authenticated platforms.

        Args:
            title: Stream title
            description: Stream description
            category: Stream category
            **kwargs: Platform-specific parameters

        Returns:
            Dictionary of platform names to start success status
        """
        logger.info(f"Starting streams on all platforms: {title}")

        results = {}
        tasks = []

        for name, platform in self.platforms.items():
            if platform.is_authenticated():
                tasks.append(
                    self._start_platform_stream(
                        name,
                        platform,
                        title,
                        description,
                        category,
                        **kwargs
                    )
                )
            else:
                logger.warning(f"Skipping {name} - not authenticated")
                results[name] = False

        if not tasks:
            logger.error("No authenticated platforms to start")
            return results

        start_results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(
            [n for n in self.platforms if self.platforms[n].is_authenticated()],
            start_results
        ):
            if isinstance(result, Exception):
                logger.error(f"Start failed for {name}: {result}")
                results[name] = False
                self.platform_status[name].error_message = str(result)
            else:
                results[name] = result
                if result:
                    self.platform_status[name].is_active = True
                    self.platform_status[name].status = StreamStatus.LIVE

        successful = sum(1 for r in results.values() if r)
        logger.info(
            f"Stream start complete: {successful}/{len(results)} successful"
        )

        if successful > 0:
            self._is_streaming = True
            self._start_monitoring()

        return results

    async def _start_platform_stream(
        self,
        name: str,
        platform: StreamingPlatform,
        title: str,
        description: str,
        category: str,
        **kwargs
    ) -> bool:
        """Start stream on a single platform"""
        try:
            success = await platform.start_stream(
                title,
                description,
                category,
                **kwargs
            )
            if success:
                logger.info(f"✅ {name} stream started")
            else:
                logger.warning(f"❌ {name} stream start failed")
            return success
        except Exception as e:
            logger.error(f"Error starting {name}: {e}")
            return False

    async def stop_all(self) -> Dict[str, bool]:
        """
        Stop streaming on all platforms.

        Returns:
            Dictionary of platform names to stop success status
        """
        logger.info("Stopping streams on all platforms...")

        self._stop_monitoring()

        results = {}
        tasks = []

        for name, platform in self.platforms.items():
            if self.platform_status[name].is_active:
                tasks.append(self._stop_platform_stream(name, platform))
            else:
                results[name] = True  # Already stopped

        if tasks:
            stop_results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, result in zip(
                [n for n in self.platforms if self.platform_status[n].is_active],
                stop_results
            ):
                if isinstance(result, Exception):
                    logger.error(f"Stop failed for {name}: {result}")
                    results[name] = False
                else:
                    results[name] = result
                    if result:
                        self.platform_status[name].is_active = False
                        self.platform_status[name].status = StreamStatus.OFFLINE

        self._is_streaming = False

        successful = sum(1 for r in results.values() if r)
        logger.info(
            f"Stream stop complete: {successful}/{len(results)} successful"
        )

        return results

    async def _stop_platform_stream(
        self,
        name: str,
        platform: StreamingPlatform
    ) -> bool:
        """Stop stream on a single platform"""
        try:
            success = await platform.stop_stream()
            if success:
                logger.info(f"✅ {name} stream stopped")
            else:
                logger.warning(f"❌ {name} stream stop failed")
            return success
        except Exception as e:
            logger.error(f"Error stopping {name}: {e}")
            return False

    async def stop_platform(self, name: str) -> bool:
        """
        Stop streaming on a specific platform.

        Args:
            name: Platform name

        Returns:
            True if stopped successfully
        """
        if name not in self.platforms:
            logger.error(f"Platform not found: {name}")
            return False

        platform = self.platforms[name]
        success = await self._stop_platform_stream(name, platform)

        if success:
            self.platform_status[name].is_active = False
            self.platform_status[name].status = StreamStatus.OFFLINE

        # Check if all platforms stopped
        if not any(s.is_active for s in self.platform_status.values()):
            self._is_streaming = False
            self._stop_monitoring()

        return success

    def _start_monitoring(self) -> None:
        """Start background health monitoring"""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(
                self._monitor_platforms()
            )
            logger.info("Started platform monitoring")

    def _stop_monitoring(self) -> None:
        """Stop background health monitoring"""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            logger.info("Stopped platform monitoring")

    async def _monitor_platforms(self) -> None:
        """Background task to monitor platform health"""
        while self._is_streaming:
            try:
                await self._update_all_status()
                await asyncio.sleep(self._monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")

    async def _update_all_status(self) -> None:
        """Update status for all active platforms"""
        tasks = []
        active_platforms = []

        for name, status in self.platform_status.items():
            if status.is_active:
                platform = self.platforms[name]
                tasks.append(self._update_platform_status(name, platform))
                active_platforms.append(name)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _update_platform_status(
        self,
        name: str,
        platform: StreamingPlatform
    ) -> None:
        """Update status for a single platform"""
        try:
            health = await platform.get_stream_health()
            metrics = await platform.get_metrics()

            self.platform_status[name].health = health
            self.platform_status[name].metrics = metrics
            self.platform_status[name].last_updated = datetime.now(UTC)

            # Check for critical health
            if health == StreamHealth.CRITICAL:
                logger.warning(
                    f"⚠️  {name} stream health is CRITICAL"
                )

        except Exception as e:
            logger.error(f"Error updating {name} status: {e}")
            self.platform_status[name].error_message = str(e)

    def get_aggregated_metrics(self) -> MultiStreamMetrics:
        """
        Get aggregated metrics across all platforms.

        Returns:
            Aggregated metrics
        """
        total_viewers = 0
        viewers_by_platform = {}
        active_count = 0
        failed_count = 0
        max_uptime = 0

        health_scores = []

        for name, status in self.platform_status.items():
            if status.is_active:
                active_count += 1
                viewers = status.metrics.viewer_count
                total_viewers += viewers
                viewers_by_platform[name] = viewers

                if status.metrics.uptime_seconds > max_uptime:
                    max_uptime = status.metrics.uptime_seconds

                # Map health to score for aggregation
                health_map = {
                    StreamHealth.EXCELLENT: 5,
                    StreamHealth.GOOD: 4,
                    StreamHealth.FAIR: 3,
                    StreamHealth.POOR: 2,
                    StreamHealth.CRITICAL: 1,
                    StreamHealth.UNKNOWN: 0
                }
                health_scores.append(health_map.get(status.health, 0))

                if status.health in [StreamHealth.CRITICAL, StreamHealth.POOR]:
                    failed_count += 1

        # Calculate overall health
        if health_scores:
            avg_score = sum(health_scores) / len(health_scores)
            if avg_score >= 4.5:
                overall_health = StreamHealth.EXCELLENT
            elif avg_score >= 3.5:
                overall_health = StreamHealth.GOOD
            elif avg_score >= 2.5:
                overall_health = StreamHealth.FAIR
            elif avg_score >= 1.5:
                overall_health = StreamHealth.POOR
            else:
                overall_health = StreamHealth.CRITICAL
        else:
            overall_health = StreamHealth.UNKNOWN

        return MultiStreamMetrics(
            total_viewers=total_viewers,
            viewers_by_platform=viewers_by_platform,
            total_uptime=max_uptime,
            active_platforms=active_count,
            failed_platforms=failed_count,
            overall_health=overall_health
        )

    def get_platform_status(self, name: str) -> Optional[PlatformStreamStatus]:
        """
        Get status for a specific platform.

        Args:
            name: Platform name

        Returns:
            Platform status or None if not found
        """
        return self.platform_status.get(name)

    def get_all_status(self) -> Dict[str, PlatformStreamStatus]:
        """Get status for all platforms"""
        return self.platform_status.copy()

    def is_streaming(self) -> bool:
        """Check if any platform is streaming"""
        return self._is_streaming

    async def close_all(self) -> None:
        """Close all platform connections and stop monitoring"""
        # Stop all streams first
        await self.stop_all()

        # Stop monitoring
        self._stop_monitoring()

        # Clear platform status
        self.platform_status.clear()

        logger.info("All platforms closed")
