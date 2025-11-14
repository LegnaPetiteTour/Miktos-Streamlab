"""
Audio monitoring for preflight validation.

Monitors audio levels, detects clipping, and validates audio
configuration for streaming.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AudioLevelSample:
    """Single audio level sample."""

    source_name: str
    level_db: float
    peak_db: float
    timestamp: float


@dataclass
class AudioCheckResult:
    """Results from audio monitoring."""

    source_name: str
    average_level_db: float
    peak_level_db: float
    clipping_detected: bool
    sample_rate: int
    channels: int
    samples_count: int


class AudioMonitor:
    """
    Monitor audio levels for streaming readiness.

    Checks audio levels via OBS WebSocket API to detect clipping,
    low levels, and configuration issues.
    """

    # Audio level thresholds (in dB)
    MIN_LEVEL_DB = -60.0  # Minimum acceptable average level
    RECOMMENDED_LEVEL_DB = -20.0  # Recommended average level
    CLIPPING_THRESHOLD_DB = -3.0  # Level that indicates clipping risk
    MAX_LEVEL_DB = 0.0  # Digital maximum (0 dB)

    # Sample rates
    RECOMMENDED_SAMPLE_RATES = [44100, 48000]

    def __init__(self, obs_controller: Optional[object] = None) -> None:
        """
        Initialize audio monitor.

        Args:
            obs_controller: Optional OBS controller with WebSocket connection
        """
        self.obs_controller = obs_controller
        self.logger = logging.getLogger(__name__)

    async def check_audio_sources(self) -> dict:
        """
        Check if audio sources are configured in OBS.

        Returns:
            dict with status, message, details, and recommendation
        """
        if not self.obs_controller:
            return {
                "status": "skipped",
                "message": "OBS controller not available",
                "details": {},
                "recommendation": "Connect to OBS to validate audio sources",
            }

        try:
            # Get audio sources from OBS
            # In real implementation:
            # sources = await self.obs_controller.get_audio_sources()
            sources = await self._get_audio_sources_placeholder()

            if not sources:
                return {
                    "status": "failed",
                    "message": "No audio sources configured",
                    "details": {"source_count": 0},
                    "recommendation": "Add at least one audio source in OBS",
                }

            return {
                "status": "passed",
                "message": f"Audio sources configured: {len(sources)} found",
                "details": {
                    "source_count": len(sources),
                    "sources": sources,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to check audio sources: {e}")
            return {
                "status": "failed",
                "message": f"Failed to check audio sources: {e}",
                "details": {},
                "recommendation": "Check OBS WebSocket connection",
            }

    async def check_audio_levels(self, duration_seconds: float = 3.0) -> dict:
        """
        Check audio levels for clipping and proper levels.

        Args:
            duration_seconds: How long to monitor audio

        Returns:
            dict with status, message, details, and recommendation
        """
        if not self.obs_controller:
            return {
                "status": "skipped",
                "message": "OBS controller not available",
                "details": {},
                "recommendation": "Connect to OBS to monitor audio levels",
            }

        try:
            # Monitor audio levels
            # In real implementation:
            # result = await self._monitor_levels(duration_seconds)
            result = await self._monitor_levels_placeholder()

            issues: List[str] = []
            warnings: List[str] = []

            # Check for clipping
            if result.clipping_detected:
                issues.append(
                    f"Clipping detected on '{result.source_name}' "
                    f"(peak: {result.peak_level_db:.1f}dB)"
                )

            # Check if level is too low
            if result.average_level_db < self.MIN_LEVEL_DB:
                warnings.append(
                    f"Low audio level on '{result.source_name}' "
                    f"({result.average_level_db:.1f}dB)"
                )

            # Check if peak is too high (close to clipping)
            peak_too_high = result.peak_level_db > self.CLIPPING_THRESHOLD_DB
            if peak_too_high and not result.clipping_detected:
                warnings.append(
                    f"Audio levels near clipping on '{result.source_name}' "
                    f"(peak: {result.peak_level_db:.1f}dB)"
                )

            if issues:
                return {
                    "status": "failed",
                    "message": f"Audio issues: {'; '.join(issues)}",
                    "details": {
                        "source": result.source_name,
                        "average_db": result.average_level_db,
                        "peak_db": result.peak_level_db,
                        "clipping": result.clipping_detected,
                    },
                    "recommendation": "Reduce audio gain to prevent clipping",
                }

            if warnings:
                return {
                    "status": "warning",
                    "message": f"Audio warnings: {'; '.join(warnings)}",
                    "details": {
                        "source": result.source_name,
                        "average_db": result.average_level_db,
                        "peak_db": result.peak_level_db,
                    },
                    "recommendation": "Adjust audio levels for optimal quality",
                }

            return {
                "status": "passed",
                "message": (
                    f"Audio levels good: "
                    f"{result.average_level_db:.1f}dB avg, "
                    f"{result.peak_level_db:.1f}dB peak"
                ),
                "details": {
                    "source": result.source_name,
                    "average_db": result.average_level_db,
                    "peak_db": result.peak_level_db,
                    "sample_rate": result.sample_rate,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to check audio levels: {e}")
            return {
                "status": "failed",
                "message": f"Failed to check audio levels: {e}",
                "details": {},
                "recommendation": "Check OBS WebSocket connection",
            }

    async def check_sample_rate(self) -> dict:
        """
        Check if audio sample rate is appropriate for streaming.

        Returns:
            dict with status, message, details, and recommendation
        """
        if not self.obs_controller:
            return {
                "status": "skipped",
                "message": "OBS controller not available",
                "details": {},
                "recommendation": "Connect to OBS to check sample rate",
            }

        try:
            # Get sample rate from OBS
            # In real implementation:
            # sample_rate = await self.obs_controller.get_sample_rate()
            sample_rate = await self._get_sample_rate_placeholder()

            if sample_rate not in self.RECOMMENDED_SAMPLE_RATES:
                return {
                    "status": "warning",
                    "message": (
                        f"Sample rate {sample_rate}Hz not recommended "
                        f"(use {self.RECOMMENDED_SAMPLE_RATES[0]} or "
                        f"{self.RECOMMENDED_SAMPLE_RATES[1]}Hz)"
                    ),
                    "details": {"sample_rate": sample_rate},
                    "recommendation": (
                        f"Set sample rate to {self.RECOMMENDED_SAMPLE_RATES[1]}Hz "
                        "in OBS audio settings"
                    ),
                }

            return {
                "status": "passed",
                "message": f"Sample rate appropriate: {sample_rate}Hz",
                "details": {"sample_rate": sample_rate},
            }

        except Exception as e:
            self.logger.error(f"Failed to check sample rate: {e}")
            return {
                "status": "failed",
                "message": f"Failed to check sample rate: {e}",
                "details": {},
                "recommendation": "Check OBS WebSocket connection",
            }

    async def check_all(self) -> dict:
        """
        Check all audio settings and levels.

        Returns:
            dict with all check results
        """
        sources = await self.check_audio_sources()
        levels = await self.check_audio_levels()
        sample_rate = await self.check_sample_rate()

        return {
            "sources": sources,
            "levels": levels,
            "sample_rate": sample_rate,
        }

    # Placeholder methods - replace with real OBS WebSocket calls
    async def _get_audio_sources_placeholder(self) -> List[str]:
        """Placeholder for getting audio sources from OBS."""
        return ["Microphone", "Desktop Audio"]

    async def _monitor_levels_placeholder(self) -> AudioCheckResult:
        """Placeholder for monitoring audio levels."""
        return AudioCheckResult(
            source_name="Microphone",
            average_level_db=-18.5,
            peak_level_db=-6.2,
            clipping_detected=False,
            sample_rate=48000,
            channels=2,
            samples_count=100,
        )

    async def _get_sample_rate_placeholder(self) -> int:
        """Placeholder for getting sample rate from OBS."""
        return 48000
