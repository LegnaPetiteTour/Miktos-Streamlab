"""
System resource monitoring for preflight validation.

Checks CPU usage, memory availability, and disk space to ensure
the system has sufficient resources for streaming.
"""

import logging
import os
import platform
import shutil
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SystemResources:
    """System resource information."""

    cpu_percent: float
    memory_total_gb: float
    memory_available_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_free_gb: float
    disk_percent: float
    platform: str
    cpu_count: int


class SystemResourceChecker:
    """
    Check system resources for streaming readiness.

    Monitors CPU, memory, and disk space to determine if the system
    has sufficient resources for streaming.
    """

    # Recommended minimums for streaming
    MIN_MEMORY_GB = 2.0
    MIN_DISK_GB = 5.0
    MAX_CPU_PERCENT = 80.0
    MAX_MEMORY_PERCENT = 85.0
    MAX_DISK_PERCENT = 90.0

    def __init__(self) -> None:
        """Initialize the system resource checker."""
        self.logger = logging.getLogger(__name__)

    def get_system_resources(self) -> SystemResources:
        """
        Get current system resource information.

        Returns:
            SystemResources with current system state
        """
        try:
            # Try to import psutil if available
            try:
                import psutil  # type: ignore[import-untyped]

                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                memory_total_gb = memory.total / (1024**3)
                memory_available_gb = memory.available / (1024**3)
                memory_percent = memory.percent

            except ImportError:
                # Fallback: basic checks without psutil
                self.logger.warning("psutil not available, using basic resource checks")
                cpu_percent = 0.0
                memory_total_gb = 0.0
                memory_available_gb = 0.0
                memory_percent = 0.0

            # Disk space (works without psutil)
            disk_usage = shutil.disk_usage("/")
            disk_total_gb = disk_usage.total / (1024**3)
            disk_free_gb = disk_usage.free / (1024**3)
            disk_percent = (
                (disk_usage.used / disk_usage.total) * 100
                if disk_usage.total > 0
                else 0.0
            )

            # System info
            system_platform = platform.system()
            cpu_count = os.cpu_count() or 0

            return SystemResources(
                cpu_percent=cpu_percent,
                memory_total_gb=memory_total_gb,
                memory_available_gb=memory_available_gb,
                memory_percent=memory_percent,
                disk_total_gb=disk_total_gb,
                disk_free_gb=disk_free_gb,
                disk_percent=disk_percent,
                platform=system_platform,
                cpu_count=cpu_count,
            )

        except Exception as e:
            self.logger.error(f"Error getting system resources: {e}")
            # Return empty resources on error
            return SystemResources(
                cpu_percent=0.0,
                memory_total_gb=0.0,
                memory_available_gb=0.0,
                memory_percent=0.0,
                disk_total_gb=0.0,
                disk_free_gb=0.0,
                disk_percent=0.0,
                platform=platform.system(),
                cpu_count=os.cpu_count() or 0,
            )

    def check_cpu(self, resources: Optional[SystemResources] = None) -> dict:
        """
        Check if CPU usage is acceptable for streaming.

        Args:
            resources: Optional pre-fetched resources

        Returns:
            dict with status, message, and details
        """
        if resources is None:
            resources = self.get_system_resources()

        if resources.cpu_percent == 0.0:
            # psutil not available
            return {
                "status": "warning",
                "message": "Unable to check CPU usage (psutil not installed)",
                "details": {"cpu_count": resources.cpu_count},
                "recommendation": "Install psutil for accurate CPU monitoring",
            }

        if resources.cpu_percent > self.MAX_CPU_PERCENT:
            return {
                "status": "warning",
                "message": f"High CPU usage: {resources.cpu_percent:.1f}%",
                "details": {
                    "cpu_percent": resources.cpu_percent,
                    "cpu_count": resources.cpu_count,
                    "threshold": self.MAX_CPU_PERCENT,
                },
                "recommendation": "Close unnecessary applications before streaming",
            }

        return {
            "status": "passed",
            "message": f"CPU usage acceptable: {resources.cpu_percent:.1f}%",
            "details": {
                "cpu_percent": resources.cpu_percent,
                "cpu_count": resources.cpu_count,
            },
        }

    def check_memory(self, resources: Optional[SystemResources] = None) -> dict:
        """
        Check if available memory is sufficient for streaming.

        Args:
            resources: Optional pre-fetched resources

        Returns:
            dict with status, message, and details
        """
        if resources is None:
            resources = self.get_system_resources()

        if resources.memory_total_gb == 0.0:
            # psutil not available
            return {
                "status": "warning",
                "message": "Unable to check memory (psutil not installed)",
                "details": {},
                "recommendation": "Install psutil for accurate memory monitoring",
            }

        if resources.memory_available_gb < self.MIN_MEMORY_GB:
            return {
                "status": "failed",
                "message": (
                    f"Insufficient memory: "
                    f"{resources.memory_available_gb:.1f}GB available"
                ),
                "details": {
                    "available_gb": resources.memory_available_gb,
                    "total_gb": resources.memory_total_gb,
                    "percent_used": resources.memory_percent,
                    "minimum_gb": self.MIN_MEMORY_GB,
                },
                "recommendation": "Close applications to free up memory",
            }

        if resources.memory_percent > self.MAX_MEMORY_PERCENT:
            return {
                "status": "warning",
                "message": f"High memory usage: {resources.memory_percent:.1f}%",
                "details": {
                    "available_gb": resources.memory_available_gb,
                    "total_gb": resources.memory_total_gb,
                    "percent_used": resources.memory_percent,
                },
                "recommendation": "Consider closing applications to free up memory",
            }

        return {
            "status": "passed",
            "message": (
                f"Memory sufficient: "
                f"{resources.memory_available_gb:.1f}GB available"
            ),
            "details": {
                "available_gb": resources.memory_available_gb,
                "total_gb": resources.memory_total_gb,
                "percent_used": resources.memory_percent,
            },
        }

    def check_disk_space(self, resources: Optional[SystemResources] = None) -> dict:
        """
        Check if disk space is sufficient for streaming/recording.

        Args:
            resources: Optional pre-fetched resources

        Returns:
            dict with status, message, and details
        """
        if resources is None:
            resources = self.get_system_resources()

        if resources.disk_free_gb < self.MIN_DISK_GB:
            return {
                "status": "warning",
                "message": (f"Low disk space: {resources.disk_free_gb:.1f}GB free"),
                "details": {
                    "free_gb": resources.disk_free_gb,
                    "total_gb": resources.disk_total_gb,
                    "percent_used": resources.disk_percent,
                    "minimum_gb": self.MIN_DISK_GB,
                },
                "recommendation": "Free up disk space before recording",
            }

        if resources.disk_percent > self.MAX_DISK_PERCENT:
            return {
                "status": "warning",
                "message": f"Disk nearly full: {resources.disk_percent:.1f}% used",
                "details": {
                    "free_gb": resources.disk_free_gb,
                    "total_gb": resources.disk_total_gb,
                    "percent_used": resources.disk_percent,
                },
                "recommendation": "Free up disk space to prevent recording issues",
            }

        return {
            "status": "passed",
            "message": f"Disk space sufficient: {resources.disk_free_gb:.1f}GB free",
            "details": {
                "free_gb": resources.disk_free_gb,
                "total_gb": resources.disk_total_gb,
                "percent_used": resources.disk_percent,
            },
        }

    def check_all(self) -> dict:
        """
        Check all system resources at once.

        Returns:
            dict with all check results
        """
        resources = self.get_system_resources()

        return {
            "resources": resources,
            "cpu": self.check_cpu(resources),
            "memory": self.check_memory(resources),
            "disk": self.check_disk_space(resources),
        }
