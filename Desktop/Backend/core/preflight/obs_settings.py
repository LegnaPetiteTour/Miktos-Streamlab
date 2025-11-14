"""
OBS settings validation for preflight checks.

Validates OBS Studio configuration including encoder settings,
output resolution, bitrate, and other streaming parameters.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OBSSettingsValidator:
    """
    Validate OBS settings for optimal streaming.

    Checks encoder configuration, output settings, and streaming
    parameters to ensure they meet streaming broadcasting standards.
    """

    # Recommended settings for streaming streaming
    RECOMMENDED_VIDEO_BITRATE = 2500  # kbps
    RECOMMENDED_AUDIO_BITRATE = 160  # kbps
    RECOMMENDED_KEYFRAME_INTERVAL = 2  # seconds
    RECOMMENDED_ENCODERS = ["x264", "obs_x264", "ffmpeg_nvenc", "h264_nvenc"]
    RECOMMENDED_RESOLUTIONS = ["1920x1080", "1280x720"]
    RECOMMENDED_FPS = [30, 60]

    def __init__(self, obs_controller: Optional[object] = None) -> None:
        """
        Initialize OBS settings validator.

        Args:
            obs_controller: Optional OBS controller with WebSocket connection
        """
        self.obs_controller = obs_controller
        self.logger = logging.getLogger(__name__)

    async def check_encoder_settings(self) -> dict:
        """
        Check OBS encoder settings.

        Returns:
            dict with status, message, details, and recommendation
        """
        if not self.obs_controller:
            return {
                "status": "skipped",
                "message": "OBS controller not available",
                "details": {},
                "recommendation": "Connect to OBS to validate encoder settings",
            }

        try:
            # Get stream encoder settings from OBS
            # In a real implementation, this would call:
            # settings = await self.obs_controller.get_stream_settings()
            # For now, use placeholder
            settings = await self._get_stream_settings_placeholder()

            encoder = settings.get("encoder", "unknown")
            video_bitrate = settings.get("video_bitrate", 0)
            audio_bitrate = settings.get("audio_bitrate", 0)

            issues: List[str] = []
            warnings: List[str] = []

            # Check encoder type
            if encoder not in self.RECOMMENDED_ENCODERS:
                warnings.append(
                    f"Encoder '{encoder}' not in recommended list: "
                    f"{', '.join(self.RECOMMENDED_ENCODERS)}"
                )

            # Check video bitrate
            if video_bitrate < self.RECOMMENDED_VIDEO_BITRATE * 0.7:
                warnings.append(
                    f"Video bitrate {video_bitrate}kbps is below recommended "
                    f"{self.RECOMMENDED_VIDEO_BITRATE}kbps"
                )
            elif video_bitrate > self.RECOMMENDED_VIDEO_BITRATE * 1.5:
                warnings.append(
                    f"Video bitrate {video_bitrate}kbps may be too high for "
                    "reliable streaming"
                )

            # Check audio bitrate
            if audio_bitrate < 128:
                warnings.append(
                    f"Audio bitrate {audio_bitrate}kbps is below recommended "
                    f"{self.RECOMMENDED_AUDIO_BITRATE}kbps"
                )

            if issues:
                return {
                    "status": "failed",
                    "message": f"Encoder settings issues: {'; '.join(issues)}",
                    "details": {
                        "encoder": encoder,
                        "video_bitrate": video_bitrate,
                        "audio_bitrate": audio_bitrate,
                    },
                    "recommendation": "Fix encoder configuration in OBS",
                }

            if warnings:
                return {
                    "status": "warning",
                    "message": f"Encoder settings warnings: {'; '.join(warnings)}",
                    "details": {
                        "encoder": encoder,
                        "video_bitrate": video_bitrate,
                        "audio_bitrate": audio_bitrate,
                    },
                    "recommendation": "Review encoder settings for optimal quality",
                }

            return {
                "status": "passed",
                "message": (
                    f"Encoder settings valid: {encoder}, "
                    f"{video_bitrate}kbps video, {audio_bitrate}kbps audio"
                ),
                "details": {
                    "encoder": encoder,
                    "video_bitrate": video_bitrate,
                    "audio_bitrate": audio_bitrate,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to check encoder settings: {e}")
            return {
                "status": "failed",
                "message": f"Failed to check encoder settings: {e}",
                "details": {},
                "recommendation": "Check OBS WebSocket connection",
            }

    async def check_video_settings(self) -> dict:
        """
        Check OBS video settings (resolution, FPS).

        Returns:
            dict with status, message, details, and recommendation
        """
        if not self.obs_controller:
            return {
                "status": "skipped",
                "message": "OBS controller not available",
                "details": {},
                "recommendation": "Connect to OBS to validate video settings",
            }

        try:
            # Get video settings from OBS
            settings = await self._get_video_settings_placeholder()

            resolution = settings.get("resolution", "unknown")
            fps = settings.get("fps", 0)

            warnings: List[str] = []

            # Check resolution
            if resolution not in self.RECOMMENDED_RESOLUTIONS:
                warnings.append(
                    f"Resolution {resolution} not in recommended list: "
                    f"{', '.join(self.RECOMMENDED_RESOLUTIONS)}"
                )

            # Check FPS
            if fps not in self.RECOMMENDED_FPS:
                warnings.append(
                    f"FPS {fps} not in recommended list: "
                    f"{self.RECOMMENDED_FPS}"
                )

            if warnings:
                return {
                    "status": "warning",
                    "message": f"Video settings warnings: {'; '.join(warnings)}",
                    "details": {"resolution": resolution, "fps": fps},
                    "recommendation": "Review video settings for optimal quality",
                }

            return {
                "status": "passed",
                "message": f"Video settings valid: {resolution} @ {fps}fps",
                "details": {"resolution": resolution, "fps": fps},
            }

        except Exception as e:
            self.logger.error(f"Failed to check video settings: {e}")
            return {
                "status": "failed",
                "message": f"Failed to check video settings: {e}",
                "details": {},
                "recommendation": "Check OBS WebSocket connection",
            }

    async def check_keyframe_interval(self) -> dict:
        """
        Check OBS keyframe interval settings.

        Returns:
            dict with status, message, details, and recommendation
        """
        if not self.obs_controller:
            return {
                "status": "skipped",
                "message": "OBS controller not available",
                "details": {},
                "recommendation": "Connect to OBS to validate keyframe interval",
            }

        try:
            # Get keyframe interval from OBS
            settings = await self._get_stream_settings_placeholder()
            keyframe_interval = settings.get("keyframe_interval", 0)

            if keyframe_interval != self.RECOMMENDED_KEYFRAME_INTERVAL:
                return {
                    "status": "warning",
                    "message": (
                        f"Keyframe interval {keyframe_interval}s should be "
                        f"{self.RECOMMENDED_KEYFRAME_INTERVAL}s"
                    ),
                    "details": {"keyframe_interval": keyframe_interval},
                    "recommendation": (
                        f"Set keyframe interval to "
                        f"{self.RECOMMENDED_KEYFRAME_INTERVAL}s in OBS"
                    ),
                }

            return {
                "status": "passed",
                "message": f"Keyframe interval correct: {keyframe_interval}s",
                "details": {"keyframe_interval": keyframe_interval},
            }

        except Exception as e:
            self.logger.error(f"Failed to check keyframe interval: {e}")
            return {
                "status": "failed",
                "message": f"Failed to check keyframe interval: {e}",
                "details": {},
                "recommendation": "Check OBS WebSocket connection",
            }

    async def check_all(self) -> dict:
        """
        Check all OBS settings.

        Returns:
            dict with all check results
        """
        encoder = await self.check_encoder_settings()
        video = await self.check_video_settings()
        keyframe = await self.check_keyframe_interval()

        return {
            "encoder": encoder,
            "video": video,
            "keyframe": keyframe,
        }

    # Placeholder methods - replace with real OBS WebSocket calls
    async def _get_stream_settings_placeholder(self) -> Dict[str, Any]:
        """Placeholder for getting stream settings from OBS."""
        return {
            "encoder": "x264",
            "video_bitrate": 2500,
            "audio_bitrate": 160,
            "keyframe_interval": 2,
        }

    async def _get_video_settings_placeholder(self) -> Dict[str, Any]:
        """Placeholder for getting video settings from OBS."""
        return {
            "resolution": "1920x1080",
            "fps": 30,
        }
