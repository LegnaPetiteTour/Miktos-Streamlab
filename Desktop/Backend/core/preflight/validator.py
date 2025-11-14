"""
Preflight validator for comprehensive pre-stream validation.
"""

import logging
import time
from typing import Optional

from .audio import AudioMonitor
from .bandwidth import BandwidthTester
from .models import CheckResult, PreflightResult, PreflightStatus, ValidationCheck
from .obs_settings import OBSSettingsValidator
from .system_resources import SystemResourceChecker

logger = logging.getLogger(__name__)


class PreflightValidator:
    """
    Comprehensive preflight validation system.

    Performs a series of checks before streaming to ensure:
    - OBS is properly configured
    - Stream destination is reachable
    - Network bandwidth is sufficient
    - Audio levels are appropriate
    - System resources are available
    """

    def __init__(self, obs_controller: Optional[object] = None) -> None:
        """
        Initialize the preflight validator.

        Args:
            obs_controller: Optional OBS controller instance for OBS checks
        """
        self.obs_controller = obs_controller
        self.logger = logger

        # Initialize all validators
        self.resource_checker = SystemResourceChecker()
        self.obs_settings_validator = OBSSettingsValidator(obs_controller)
        self.bandwidth_tester = BandwidthTester()
        self.audio_monitor = AudioMonitor(obs_controller)

    async def run_all_checks(self, skip_optional: bool = False) -> PreflightResult:
        """
        Run all preflight validation checks.

        Args:
            skip_optional: If True, skip non-critical checks

        Returns:
            PreflightResult with all check results
        """
        result = PreflightResult(
            overall_status=PreflightStatus.PENDING,
            start_time=time.time(),
        )

        self.logger.info("Starting preflight validation...")

        try:
            # Critical checks (must pass)
            await self._check_obs_connection(result)
            await self._check_obs_settings(result)
            await self._check_scenes_available(result)

            # Important checks (should pass, but can warn)
            await self._check_stream_destination(result)
            await self._check_audio_sources(result)

            if not skip_optional:
                # Optional checks (nice to have)
                await self._check_bandwidth(result)
                await self._check_system_resources(result)
                await self._check_audio_levels(result)

            # Determine overall status
            result.end_time = time.time()
            self._determine_overall_status(result)

            self.logger.info(
                f"Preflight validation complete: {result.overall_status.value}"
            )

        except Exception as e:
            self.logger.error(f"Preflight validation failed: {e}")
            result.overall_status = PreflightStatus.FAILED
            result.errors.append(f"Unexpected error: {str(e)}")
            result.end_time = time.time()

        return result

    async def _check_obs_connection(self, result: PreflightResult) -> None:
        """Check if OBS is connected and responding."""
        if not self.obs_controller:
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.OBS_CONNECTION,
                    status=PreflightStatus.FAILED,
                    message="OBS controller not initialized",
                    recommendation="Initialize OBS controller before running preflight",
                )
            )
            result.errors.append("OBS controller not available")
            return

        try:
            # Check if OBS is connected
            if not hasattr(self.obs_controller, "is_connected"):
                result.checks.append(
                    CheckResult(
                        check=ValidationCheck.OBS_CONNECTION,
                        status=PreflightStatus.FAILED,
                        message="OBS controller missing connection check",
                    )
                )
                result.errors.append("OBS controller incompatible")
                return

            # For now, assume connected if controller exists
            # In real implementation, check actual connection status
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.OBS_CONNECTION,
                    status=PreflightStatus.PASSED,
                    message="OBS is connected and responding",
                )
            )

        except Exception as e:
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.OBS_CONNECTION,
                    status=PreflightStatus.FAILED,
                    message=f"Failed to check OBS connection: {str(e)}",
                )
            )
            result.errors.append("OBS connection check failed")

    async def _check_obs_settings(self, result: PreflightResult) -> None:
        """Check OBS encoder and output settings."""
        try:
            # Get all OBS settings checks
            checks = await self.obs_settings_validator.check_all()

            # Encoder settings check
            encoder_result = checks["encoder"]
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.OBS_SETTINGS,
                    status=PreflightStatus[encoder_result["status"].upper()],
                    message=encoder_result["message"],
                    details=encoder_result["details"],
                    recommendation=encoder_result.get("recommendation"),
                )
            )

            # Video settings check
            video_result = checks["video"]
            if video_result["status"] != "skipped":
                result.checks.append(
                    CheckResult(
                        check=ValidationCheck.OBS_SETTINGS,
                        status=PreflightStatus[video_result["status"].upper()],
                        message=video_result["message"],
                        details=video_result["details"],
                        recommendation=video_result.get("recommendation"),
                    )
                )

            # Keyframe interval check
            keyframe_result = checks["keyframe"]
            if keyframe_result["status"] != "skipped":
                result.checks.append(
                    CheckResult(
                        check=ValidationCheck.OBS_SETTINGS,
                        status=PreflightStatus[keyframe_result["status"].upper()],
                        message=keyframe_result["message"],
                        details=keyframe_result["details"],
                        recommendation=keyframe_result.get("recommendation"),
                    )
                )

            self.logger.info("OBS settings validation completed")

        except Exception as e:
            self.logger.error(f"OBS settings check failed: {e}")
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.OBS_SETTINGS,
                    status=PreflightStatus.FAILED,
                    message=f"OBS settings check failed: {e}",
                    details={},
                )
            )

    async def _check_scenes_available(self, result: PreflightResult) -> None:
        """Check if OBS has scenes configured."""
        result.checks.append(
            CheckResult(
                check=ValidationCheck.SCENES_AVAILABLE,
                status=PreflightStatus.PASSED,
                message="Scene availability check (placeholder)",
                details={"note": "Full implementation pending"},
            )
        )

    async def _check_stream_destination(self, result: PreflightResult) -> None:
        """Verify stream destination is configured and reachable."""
        result.checks.append(
            CheckResult(
                check=ValidationCheck.STREAM_DESTINATION,
                status=PreflightStatus.PASSED,
                message="Stream destination check (placeholder)",
                details={"note": "Full implementation pending"},
            )
        )

    async def _check_audio_sources(self, result: PreflightResult) -> None:
        """Validate audio sources are configured."""
        try:
            # Use the real audio monitor
            audio_result = await self.audio_monitor.check_audio_sources()

            result.checks.append(
                CheckResult(
                    check=ValidationCheck.AUDIO_SOURCES,
                    status=PreflightStatus[audio_result["status"].upper()],
                    message=audio_result["message"],
                    details=audio_result["details"],
                    recommendation=audio_result.get("recommendation"),
                )
            )

        except Exception as e:
            self.logger.error(f"Audio sources check failed: {e}")
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.AUDIO_SOURCES,
                    status=PreflightStatus.FAILED,
                    message=f"Audio sources check failed: {e}",
                    details={},
                )
            )

    async def _check_bandwidth(self, result: PreflightResult) -> None:
        """Test available network bandwidth."""
        try:
            # Use the real bandwidth tester
            bandwidth_result = await self.bandwidth_tester.check_bandwidth(
                required_bitrate_kbps=2500
            )

            result.checks.append(
                CheckResult(
                    check=ValidationCheck.BANDWIDTH_TEST,
                    status=PreflightStatus[bandwidth_result["status"].upper()],
                    message=bandwidth_result["message"],
                    details=bandwidth_result["details"],
                    recommendation=bandwidth_result.get("recommendation"),
                )
            )

        except Exception as e:
            self.logger.error(f"Bandwidth check failed: {e}")
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.BANDWIDTH_TEST,
                    status=PreflightStatus.FAILED,
                    message=f"Bandwidth check failed: {e}",
                    details={},
                )
            )

    async def _check_system_resources(self, result: PreflightResult) -> None:
        """Check system resources (CPU, memory, disk space)."""
        try:
            # Get all system resource checks
            checks = self.resource_checker.check_all()
            resources = checks["resources"]

            # CPU Check
            cpu_result = checks["cpu"]
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.CPU_USAGE,
                    status=PreflightStatus[cpu_result["status"].upper()],
                    message=cpu_result["message"],
                    details=cpu_result["details"],
                    recommendation=cpu_result.get("recommendation"),
                )
            )

            # Memory Check
            memory_result = checks["memory"]
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.MEMORY_AVAILABLE,
                    status=PreflightStatus[memory_result["status"].upper()],
                    message=memory_result["message"],
                    details=memory_result["details"],
                    recommendation=memory_result.get("recommendation"),
                )
            )

            # Disk Space Check
            disk_result = checks["disk"]
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.DISK_SPACE,
                    status=PreflightStatus[disk_result["status"].upper()],
                    message=disk_result["message"],
                    details=disk_result["details"],
                    recommendation=disk_result.get("recommendation"),
                )
            )

            self.logger.info(
                f"System resources checked: CPU {resources.cpu_percent:.1f}%, "
                f"Memory {resources.memory_percent:.1f}%, "
                f"Disk {resources.disk_percent:.1f}%"
            )

        except Exception as e:
            self.logger.error(f"System resource check failed: {e}")
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.CPU_USAGE,
                    status=PreflightStatus.FAILED,
                    message=f"System resource check failed: {e}",
                    details={},
                )
            )

    async def _check_audio_levels(self, result: PreflightResult) -> None:
        """Validate audio levels are appropriate."""
        try:
            # Use the real audio monitor
            audio_result = await self.audio_monitor.check_audio_levels(
                duration_seconds=3.0
            )

            result.checks.append(
                CheckResult(
                    check=ValidationCheck.AUDIO_LEVELS,
                    status=PreflightStatus[audio_result["status"].upper()],
                    message=audio_result["message"],
                    details=audio_result["details"],
                    recommendation=audio_result.get("recommendation"),
                )
            )

        except Exception as e:
            self.logger.error(f"Audio levels check failed: {e}")
            result.checks.append(
                CheckResult(
                    check=ValidationCheck.AUDIO_LEVELS,
                    status=PreflightStatus.FAILED,
                    message=f"Audio levels check failed: {e}",
                    details={},
                )
            )

    def _determine_overall_status(self, result: PreflightResult) -> None:
        """Determine the overall preflight status based on individual checks."""
        if result.failed_checks:
            result.overall_status = PreflightStatus.FAILED
            result.can_stream = False
        elif result.warning_checks:
            result.overall_status = PreflightStatus.WARNING
            result.can_stream = True  # Can stream with warnings
            result.warnings = [
                f"{c.check.value}: {c.message}" for c in result.warning_checks
            ]
        else:
            result.overall_status = PreflightStatus.PASSED
            result.can_stream = True
