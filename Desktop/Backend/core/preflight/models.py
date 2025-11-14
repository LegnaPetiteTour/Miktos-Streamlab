"""
Data models for preflight validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PreflightStatus(Enum):
    """Status of a preflight validation check."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class ValidationCheck(Enum):
    """Types of validation checks performed during preflight."""

    # OBS Settings
    OBS_CONNECTION = "obs_connection"
    OBS_VERSION = "obs_version"
    OBS_SETTINGS = "obs_settings"

    # Stream Configuration
    STREAM_DESTINATION = "stream_destination"
    STREAM_KEY = "stream_key"
    RTMP_CONNECTION = "rtmp_connection"

    # Scene & Source Validation
    SCENES_AVAILABLE = "scenes_available"
    SOURCES_CONFIGURED = "sources_configured"
    AUDIO_SOURCES = "audio_sources"

    # Network & Performance
    BANDWIDTH_TEST = "bandwidth_test"
    NETWORK_LATENCY = "network_latency"
    NETWORK_STABILITY = "network_stability"

    # Audio Validation
    AUDIO_LEVELS = "audio_levels"
    AUDIO_DEVICES = "audio_devices"

    # System Resources
    CPU_USAGE = "cpu_usage"
    MEMORY_AVAILABLE = "memory_available"
    DISK_SPACE = "disk_space"


@dataclass
class CheckResult:
    """Result of a single validation check."""

    check: ValidationCheck
    status: PreflightStatus
    message: str
    details: Optional[dict] = None
    recommendation: Optional[str] = None


@dataclass
class PreflightResult:
    """Complete preflight validation result."""

    overall_status: PreflightStatus
    checks: list[CheckResult] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    can_stream: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def duration(self) -> Optional[float]:
        """Calculate duration of preflight checks."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def passed_checks(self) -> list[CheckResult]:
        """Get all checks that passed."""
        return [c for c in self.checks if c.status == PreflightStatus.PASSED]

    @property
    def failed_checks(self) -> list[CheckResult]:
        """Get all checks that failed."""
        return [c for c in self.checks if c.status == PreflightStatus.FAILED]

    @property
    def warning_checks(self) -> list[CheckResult]:
        """Get all checks with warnings."""
        return [c for c in self.checks if c.status == PreflightStatus.WARNING]

    def get_summary(self) -> dict:
        """Get a summary of the preflight results."""
        return {
            "overall_status": self.overall_status.value,
            "can_stream": self.can_stream,
            "total_checks": len(self.checks),
            "passed": len(self.passed_checks),
            "warnings": len(self.warning_checks),
            "failed": len(self.failed_checks),
            "duration": self.duration,
        }
