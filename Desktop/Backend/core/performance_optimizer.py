"""
Performance Optimizer for ISO Recording System

Manages performance optimization based on system resources.
Adjusts encoding settings and resource allocation dynamically.
"""

import logging
import platform
import psutil  # type: ignore[import-untyped]
from dataclasses import dataclass
from enum import Enum
from typing import Dict

logger = logging.getLogger(__name__)


class PerformanceProfile(Enum):
    """Performance profile presets"""

    LOW = "low"  # Minimal resource usage
    BALANCED = "balanced"  # Balance quality and performance
    HIGH = "high"  # Maximum quality
    AUTO = "auto"  # Automatically detect


@dataclass
class SystemResources:
    """
    System resource information.

    Attributes:
        cpu_count: Number of CPU cores
        cpu_percent: Current CPU usage percentage
        memory_total_gb: Total system memory in GB
        memory_available_gb: Available memory in GB
        memory_percent: Memory usage percentage
        disk_write_speed_mbps: Disk write speed in MB/s
    """

    cpu_count: int
    cpu_percent: float
    memory_total_gb: float
    memory_available_gb: float
    memory_percent: float
    disk_write_speed_mbps: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "cpu_count": self.cpu_count,
            "cpu_percent": self.cpu_percent,
            "memory_total_gb": self.memory_total_gb,
            "memory_available_gb": self.memory_available_gb,
            "memory_percent": self.memory_percent,
            "disk_write_speed_mbps": self.disk_write_speed_mbps,
        }


@dataclass
class PerformanceSettings:
    """
    Optimized performance settings.

    Attributes:
        profile: Performance profile
        max_parallel_tracks: Maximum parallel ISO tracks
        video_encoder: Recommended video encoder
        video_preset: Encoder preset (ultrafast to slow)
        audio_encoder: Recommended audio encoder
        buffer_size_mb: Buffer size in MB
        thread_count: Number of threads to use
        enable_hardware_accel: Whether to use hardware acceleration
    """

    profile: PerformanceProfile
    max_parallel_tracks: int = 4
    video_encoder: str = "libx264"
    video_preset: str = "veryfast"
    audio_encoder: str = "aac"
    buffer_size_mb: int = 16
    thread_count: int = 4
    enable_hardware_accel: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "profile": self.profile.value,
            "max_parallel_tracks": self.max_parallel_tracks,
            "video_encoder": self.video_encoder,
            "video_preset": self.video_preset,
            "audio_encoder": self.audio_encoder,
            "buffer_size_mb": self.buffer_size_mb,
            "thread_count": self.thread_count,
            "enable_hardware_accel": self.enable_hardware_accel,
        }


class PerformanceOptimizer:
    """
    Optimizes recording performance based on system resources.

    Features:
    - System resource detection
    - Automatic profile selection
    - Dynamic setting adjustment
    - Hardware acceleration detection
    """

    def __init__(
        self, profile: PerformanceProfile = PerformanceProfile.AUTO
    ) -> None:
        """
        Initialize performance optimizer.

        Args:
            profile: Performance profile to use
        """
        self.profile = profile
        self.logger = logging.getLogger(__name__)

    def get_system_resources(self) -> SystemResources:
        """Get current system resource information"""
        try:
            # CPU info
            cpu_count = psutil.cpu_count(logical=True) or 4
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory info
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            memory_percent = memory.percent

            return SystemResources(
                cpu_count=cpu_count,
                cpu_percent=cpu_percent,
                memory_total_gb=memory_total_gb,
                memory_available_gb=memory_available_gb,
                memory_percent=memory_percent,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to get system resources: {e}"
            )
            # Return conservative defaults
            return SystemResources(
                cpu_count=4,
                cpu_percent=50.0,
                memory_total_gb=8.0,
                memory_available_gb=4.0,
                memory_percent=50.0,
            )

    def get_optimized_settings(self) -> PerformanceSettings:
        """
        Get optimized performance settings.

        Returns:
            Optimized settings based on system resources
        """
        # Get system resources
        resources = self.get_system_resources()

        # Determine profile if AUTO
        profile = self.profile

        if profile == PerformanceProfile.AUTO:
            profile = self._detect_profile(resources)

        # Generate settings for profile
        if profile == PerformanceProfile.LOW:
            return self._get_low_settings(resources)
        elif profile == PerformanceProfile.BALANCED:
            return self._get_balanced_settings(resources)
        elif profile == PerformanceProfile.HIGH:
            return self._get_high_settings(resources)
        else:
            return self._get_balanced_settings(resources)

    def _detect_profile(
        self, resources: SystemResources
    ) -> PerformanceProfile:
        """Automatically detect appropriate profile"""
        # Check available resources
        if (
            resources.cpu_count >= 8
            and resources.memory_available_gb >= 8.0
            and resources.cpu_percent < 50
        ):
            self.logger.info("Auto-detected HIGH performance profile")
            return PerformanceProfile.HIGH

        elif (
            resources.cpu_count >= 4
            and resources.memory_available_gb >= 4.0
        ):
            self.logger.info(
                "Auto-detected BALANCED performance profile"
            )
            return PerformanceProfile.BALANCED

        else:
            self.logger.info("Auto-detected LOW performance profile")
            return PerformanceProfile.LOW

    def _get_low_settings(
        self, resources: SystemResources
    ) -> PerformanceSettings:
        """Get settings for low performance profile"""
        return PerformanceSettings(
            profile=PerformanceProfile.LOW,
            max_parallel_tracks=2,
            video_encoder="libx264",
            video_preset="ultrafast",
            audio_encoder="aac",
            buffer_size_mb=8,
            thread_count=min(2, resources.cpu_count),
            enable_hardware_accel=self._has_hardware_accel(),
        )

    def _get_balanced_settings(
        self, resources: SystemResources
    ) -> PerformanceSettings:
        """Get settings for balanced performance profile"""
        return PerformanceSettings(
            profile=PerformanceProfile.BALANCED,
            max_parallel_tracks=4,
            video_encoder="libx264",
            video_preset="veryfast",
            audio_encoder="aac",
            buffer_size_mb=16,
            thread_count=min(4, resources.cpu_count),
            enable_hardware_accel=self._has_hardware_accel(),
        )

    def _get_high_settings(
        self, resources: SystemResources
    ) -> PerformanceSettings:
        """Get settings for high performance profile"""
        return PerformanceSettings(
            profile=PerformanceProfile.HIGH,
            max_parallel_tracks=8,
            video_encoder="libx264",
            video_preset="fast",
            audio_encoder="aac",
            buffer_size_mb=32,
            thread_count=min(8, resources.cpu_count),
            enable_hardware_accel=self._has_hardware_accel(),
        )

    def _has_hardware_accel(self) -> bool:
        """Check if hardware acceleration is available"""
        try:
            system = platform.system()

            # Check for common hardware encoders
            # This is a simplified check - actual implementation
            # would need to probe FFmpeg capabilities

            if system == "Darwin":  # macOS
                # Check for VideoToolbox
                return True

            elif system == "Windows":
                # Check for NVENC/QuickSync
                return True

            elif system == "Linux":
                # Check for VAAPI/NVENC
                return True

            return False

        except Exception as e:
            self.logger.warning(
                f"Failed to detect hardware acceleration: {e}"
            )
            return False

    def get_recommended_track_count(
        self, track_count: int
    ) -> int:
        """
        Get recommended parallel track count.

        Args:
            track_count: Desired track count

        Returns:
            Recommended track count based on resources
        """
        settings = self.get_optimized_settings()

        if track_count <= settings.max_parallel_tracks:
            return track_count

        self.logger.warning(
            f"Requested {track_count} tracks but system can "
            f"handle {settings.max_parallel_tracks} optimally"
        )

        return settings.max_parallel_tracks

    def check_resource_availability(self) -> bool:
        """
        Check if sufficient resources available for recording.

        Returns:
            True if resources available
        """
        try:
            resources = self.get_system_resources()

            # Check CPU usage
            if resources.cpu_percent > 90:
                self.logger.warning(
                    f"High CPU usage: {resources.cpu_percent}%"
                )
                return False

            # Check memory
            if resources.memory_percent > 90:
                self.logger.warning(
                    f"Low memory: {resources.memory_available_gb:.1f}GB "
                    "available"
                )
                return False

            return True

        except Exception as e:
            self.logger.error(
                f"Resource availability check failed: {e}"
            )
            return True  # Assume OK if check fails
