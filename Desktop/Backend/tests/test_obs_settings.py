"""
Tests for OBS settings validation.
"""

import pytest

from src.core.preflight.obs_settings import OBSSettingsValidator


class TestOBSSettingsValidator:
    """Test OBS settings validation."""

    @pytest.mark.asyncio
    async def test_validator_creation(self):
        """Test creating OBS settings validator."""
        validator = OBSSettingsValidator()
        assert validator is not None
        assert validator.obs_controller is None

    @pytest.mark.asyncio
    async def test_validator_with_controller(self):
        """Test creating validator with OBS controller."""
        mock_controller = object()
        validator = OBSSettingsValidator(mock_controller)
        assert validator.obs_controller is mock_controller

    @pytest.mark.asyncio
    async def test_check_encoder_no_controller(self):
        """Test encoder check without controller."""
        validator = OBSSettingsValidator()
        result = await validator.check_encoder_settings()

        assert result["status"] == "skipped"
        assert "not available" in result["message"]

    @pytest.mark.asyncio
    async def test_check_encoder_with_controller(self):
        """Test encoder check with controller."""
        mock_controller = object()
        validator = OBSSettingsValidator(mock_controller)
        result = await validator.check_encoder_settings()

        assert result["status"] in ["passed", "warning", "failed"]
        assert "message" in result
        assert "details" in result

    @pytest.mark.asyncio
    async def test_check_video_no_controller(self):
        """Test video check without controller."""
        validator = OBSSettingsValidator()
        result = await validator.check_video_settings()

        assert result["status"] == "skipped"
        assert "not available" in result["message"]

    @pytest.mark.asyncio
    async def test_check_video_with_controller(self):
        """Test video check with controller."""
        mock_controller = object()
        validator = OBSSettingsValidator(mock_controller)
        result = await validator.check_video_settings()

        assert result["status"] in ["passed", "warning", "failed"]
        assert "message" in result
        assert "details" in result

    @pytest.mark.asyncio
    async def test_check_keyframe_no_controller(self):
        """Test keyframe check without controller."""
        validator = OBSSettingsValidator()
        result = await validator.check_keyframe_interval()

        assert result["status"] == "skipped"
        assert "not available" in result["message"]

    @pytest.mark.asyncio
    async def test_check_keyframe_with_controller(self):
        """Test keyframe check with controller."""
        mock_controller = object()
        validator = OBSSettingsValidator(mock_controller)
        result = await validator.check_keyframe_interval()

        assert result["status"] in ["passed", "warning", "failed"]
        assert "message" in result
        assert "details" in result

    @pytest.mark.asyncio
    async def test_check_all_no_controller(self):
        """Test checking all settings without controller."""
        validator = OBSSettingsValidator()
        results = await validator.check_all()

        assert "encoder" in results
        assert "video" in results
        assert "keyframe" in results
        assert results["encoder"]["status"] == "skipped"
        assert results["video"]["status"] == "skipped"
        assert results["keyframe"]["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_check_all_with_controller(self):
        """Test checking all settings with controller."""
        mock_controller = object()
        validator = OBSSettingsValidator(mock_controller)
        results = await validator.check_all()

        assert "encoder" in results
        assert "video" in results
        assert "keyframe" in results
        assert all(
            r["status"] in ["passed", "warning", "failed"]
            for r in results.values()
        )

    @pytest.mark.asyncio
    async def test_placeholder_stream_settings(self):
        """Test placeholder stream settings."""
        mock_controller = object()
        validator = OBSSettingsValidator(mock_controller)
        settings = await validator._get_stream_settings_placeholder()

        assert "encoder" in settings
        assert "video_bitrate" in settings
        assert "audio_bitrate" in settings
        assert "keyframe_interval" in settings

    @pytest.mark.asyncio
    async def test_placeholder_video_settings(self):
        """Test placeholder video settings."""
        mock_controller = object()
        validator = OBSSettingsValidator(mock_controller)
        settings = await validator._get_video_settings_placeholder()

        assert "resolution" in settings
        assert "fps" in settings

    def test_recommended_constants(self):
        """Test that recommended constants are set."""
        validator = OBSSettingsValidator()

        assert validator.RECOMMENDED_VIDEO_BITRATE == 2500
        assert validator.RECOMMENDED_AUDIO_BITRATE == 160
        assert validator.RECOMMENDED_KEYFRAME_INTERVAL == 2
        assert len(validator.RECOMMENDED_ENCODERS) > 0
        assert len(validator.RECOMMENDED_RESOLUTIONS) > 0
        assert len(validator.RECOMMENDED_FPS) > 0
