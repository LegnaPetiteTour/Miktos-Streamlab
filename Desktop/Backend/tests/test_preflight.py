"""
Tests for the preflight validation system.
"""

import pytest

from src.core.preflight import (
    PreflightResult,
    PreflightStatus,
    PreflightValidator,
    ValidationCheck,
)
from src.core.preflight.models import CheckResult


class TestPreflightModels:
    """Test data models for preflight validation."""

    def test_preflight_status_enum(self):
        """Test PreflightStatus enum values."""
        assert PreflightStatus.PENDING.value == "pending"
        assert PreflightStatus.RUNNING.value == "running"
        assert PreflightStatus.PASSED.value == "passed"
        assert PreflightStatus.WARNING.value == "warning"
        assert PreflightStatus.FAILED.value == "failed"
        assert PreflightStatus.SKIPPED.value == "skipped"

    def test_validation_check_enum(self):
        """Test ValidationCheck enum has expected values."""
        assert ValidationCheck.OBS_CONNECTION.value == "obs_connection"
        assert ValidationCheck.BANDWIDTH_TEST.value == "bandwidth_test"
        assert ValidationCheck.AUDIO_LEVELS.value == "audio_levels"

    def test_check_result_creation(self):
        """Test creating a CheckResult."""
        result = CheckResult(
            check=ValidationCheck.OBS_CONNECTION,
            status=PreflightStatus.PASSED,
            message="OBS connected successfully",
        )

        assert result.check == ValidationCheck.OBS_CONNECTION
        assert result.status == PreflightStatus.PASSED
        assert result.message == "OBS connected successfully"
        assert result.details is None
        assert result.recommendation is None

    def test_check_result_with_details(self):
        """Test CheckResult with additional details."""
        result = CheckResult(
            check=ValidationCheck.BANDWIDTH_TEST,
            status=PreflightStatus.WARNING,
            message="Bandwidth marginally acceptable",
            details={"bandwidth_mbps": 3.5, "recommended_mbps": 5.0},
            recommendation="Consider upgrading internet connection",
        )

        assert result.details is not None
        assert result.details["bandwidth_mbps"] == 3.5
        assert result.recommendation == "Consider upgrading internet connection"

    def test_preflight_result_creation(self):
        """Test creating a PreflightResult."""
        result = PreflightResult(overall_status=PreflightStatus.PENDING)

        assert result.overall_status == PreflightStatus.PENDING
        assert len(result.checks) == 0
        assert result.can_stream is False
        assert len(result.warnings) == 0
        assert len(result.errors) == 0

    def test_preflight_result_duration(self):
        """Test duration calculation."""
        result = PreflightResult(
            overall_status=PreflightStatus.PASSED,
            start_time=100.0,
            end_time=105.5,
        )

        assert result.duration == 5.5

    def test_preflight_result_duration_none(self):
        """Test duration when times not set."""
        result = PreflightResult(overall_status=PreflightStatus.PENDING)

        assert result.duration is None

    def test_preflight_result_passed_checks(self):
        """Test filtering passed checks."""
        result = PreflightResult(overall_status=PreflightStatus.PASSED)
        result.checks = [
            CheckResult(
                ValidationCheck.OBS_CONNECTION,
                PreflightStatus.PASSED,
                "OK",
            ),
            CheckResult(
                ValidationCheck.BANDWIDTH_TEST,
                PreflightStatus.WARNING,
                "Low",
            ),
            CheckResult(
                ValidationCheck.AUDIO_LEVELS,
                PreflightStatus.PASSED,
                "OK",
            ),
        ]

        passed = result.passed_checks
        assert len(passed) == 2
        assert all(c.status == PreflightStatus.PASSED for c in passed)

    def test_preflight_result_failed_checks(self):
        """Test filtering failed checks."""
        result = PreflightResult(overall_status=PreflightStatus.FAILED)
        result.checks = [
            CheckResult(
                ValidationCheck.OBS_CONNECTION,
                PreflightStatus.PASSED,
                "OK",
            ),
            CheckResult(
                ValidationCheck.STREAM_DESTINATION,
                PreflightStatus.FAILED,
                "Unreachable",
            ),
            CheckResult(
                ValidationCheck.AUDIO_LEVELS,
                PreflightStatus.FAILED,
                "Too low",
            ),
        ]

        failed = result.failed_checks
        assert len(failed) == 2
        assert all(c.status == PreflightStatus.FAILED for c in failed)

    def test_preflight_result_warning_checks(self):
        """Test filtering warning checks."""
        result = PreflightResult(overall_status=PreflightStatus.WARNING)
        result.checks = [
            CheckResult(
                ValidationCheck.OBS_CONNECTION,
                PreflightStatus.PASSED,
                "OK",
            ),
            CheckResult(
                ValidationCheck.BANDWIDTH_TEST,
                PreflightStatus.WARNING,
                "Low",
            ),
            CheckResult(
                ValidationCheck.CPU_USAGE,
                PreflightStatus.WARNING,
                "High",
            ),
        ]

        warnings = result.warning_checks
        assert len(warnings) == 2
        assert all(c.status == PreflightStatus.WARNING for c in warnings)

    def test_preflight_result_summary(self):
        """Test getting result summary."""
        result = PreflightResult(
            overall_status=PreflightStatus.PASSED,
            start_time=100.0,
            end_time=105.0,
            can_stream=True,
        )
        result.checks = [
            CheckResult(
                ValidationCheck.OBS_CONNECTION,
                PreflightStatus.PASSED,
                "OK",
            ),
            CheckResult(
                ValidationCheck.BANDWIDTH_TEST,
                PreflightStatus.WARNING,
                "Low",
            ),
            CheckResult(
                ValidationCheck.STREAM_DESTINATION,
                PreflightStatus.PASSED,
                "OK",
            ),
        ]

        summary = result.get_summary()

        assert summary["overall_status"] == "passed"
        assert summary["can_stream"] is True
        assert summary["total_checks"] == 3
        assert summary["passed"] == 2
        assert summary["warnings"] == 1
        assert summary["failed"] == 0
        assert summary["duration"] == 5.0


class TestPreflightValidator:
    """Test PreflightValidator functionality."""

    @pytest.mark.asyncio
    async def test_validator_creation(self):
        """Test creating a PreflightValidator."""
        validator = PreflightValidator()

        assert validator is not None
        assert validator.obs_controller is None

    @pytest.mark.asyncio
    async def test_validator_with_obs_controller(self):
        """Test creating validator with OBS controller."""

        class MockOBSController:
            pass

        controller = MockOBSController()
        validator = PreflightValidator(obs_controller=controller)

        assert validator.obs_controller is controller

    @pytest.mark.asyncio
    async def test_run_all_checks_basic(self):
        """Test running all preflight checks."""
        validator = PreflightValidator()
        result = await validator.run_all_checks()

        assert isinstance(result, PreflightResult)
        assert result.overall_status in [
            PreflightStatus.PASSED,
            PreflightStatus.WARNING,
            PreflightStatus.FAILED,
        ]
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.duration is not None
        assert result.duration >= 0

    @pytest.mark.asyncio
    async def test_run_checks_with_obs_controller(self):
        """Test running checks with OBS controller."""

        class MockOBSController:
            is_connected = True

        controller = MockOBSController()
        validator = PreflightValidator(obs_controller=controller)
        result = await validator.run_all_checks()

        assert isinstance(result, PreflightResult)
        # Should have multiple checks
        assert len(result.checks) > 0

    @pytest.mark.asyncio
    async def test_run_checks_skip_optional(self):
        """Test running checks with optional checks skipped."""
        validator = PreflightValidator()
        result = await validator.run_all_checks(skip_optional=True)

        assert isinstance(result, PreflightResult)
        # Should have fewer checks when skipping optional
        assert len(result.checks) > 0

    @pytest.mark.asyncio
    async def test_obs_connection_check_no_controller(self):
        """Test OBS connection check without controller."""
        validator = PreflightValidator()
        result = PreflightResult(overall_status=PreflightStatus.PENDING)

        await validator._check_obs_connection(result)

        assert len(result.checks) == 1
        check = result.checks[0]
        assert check.check == ValidationCheck.OBS_CONNECTION
        assert check.status == PreflightStatus.FAILED
        assert "not initialized" in check.message.lower()

    @pytest.mark.asyncio
    async def test_obs_connection_check_with_controller(self):
        """Test OBS connection check with valid controller."""

        class MockOBSController:
            is_connected = True

        controller = MockOBSController()
        validator = PreflightValidator(obs_controller=controller)
        result = PreflightResult(overall_status=PreflightStatus.PENDING)

        await validator._check_obs_connection(result)

        assert len(result.checks) == 1
        check = result.checks[0]
        assert check.check == ValidationCheck.OBS_CONNECTION
        assert check.status == PreflightStatus.PASSED

    @pytest.mark.asyncio
    async def test_determine_overall_status_all_passed(self):
        """Test overall status when all checks pass."""
        validator = PreflightValidator()
        result = PreflightResult(overall_status=PreflightStatus.PENDING)
        result.checks = [
            CheckResult(
                ValidationCheck.OBS_CONNECTION,
                PreflightStatus.PASSED,
                "OK",
            ),
            CheckResult(
                ValidationCheck.BANDWIDTH_TEST,
                PreflightStatus.PASSED,
                "OK",
            ),
        ]

        validator._determine_overall_status(result)

        assert result.overall_status == PreflightStatus.PASSED
        assert result.can_stream is True

    @pytest.mark.asyncio
    async def test_determine_overall_status_with_warnings(self):
        """Test overall status with warnings."""
        validator = PreflightValidator()
        result = PreflightResult(overall_status=PreflightStatus.PENDING)
        result.checks = [
            CheckResult(
                ValidationCheck.OBS_CONNECTION,
                PreflightStatus.PASSED,
                "OK",
            ),
            CheckResult(
                ValidationCheck.BANDWIDTH_TEST,
                PreflightStatus.WARNING,
                "Low bandwidth",
            ),
        ]

        validator._determine_overall_status(result)

        assert result.overall_status == PreflightStatus.WARNING
        assert result.can_stream is True
        assert len(result.warnings) == 1

    @pytest.mark.asyncio
    async def test_determine_overall_status_with_failures(self):
        """Test overall status with failures."""
        validator = PreflightValidator()
        result = PreflightResult(overall_status=PreflightStatus.PENDING)
        result.checks = [
            CheckResult(
                ValidationCheck.OBS_CONNECTION,
                PreflightStatus.FAILED,
                "Not connected",
            ),
            CheckResult(
                ValidationCheck.BANDWIDTH_TEST,
                PreflightStatus.PASSED,
                "OK",
            ),
        ]

        validator._determine_overall_status(result)

        assert result.overall_status == PreflightStatus.FAILED
        assert result.can_stream is False
