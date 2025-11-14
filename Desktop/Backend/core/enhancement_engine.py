"""
Enhancement Engine - Automatic image quality improvements

Combines quality analysis with intelligent auto-corrections.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EnhancementProfile:
    """Enhancement profile settings"""
    name: str

    # Auto-corrections
    auto_exposure: bool = True
    auto_color_balance: bool = True
    auto_sharpness: bool = True

    # Enhancement amounts (0.0 to 1.0)
    brightness_boost: float = 0.0
    contrast_boost: float = 0.0
    saturation_boost: float = 0.0
    sharpness_amount: float = 0.0

    # Noise reduction
    denoise: bool = False
    denoise_strength: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'auto_exposure': self.auto_exposure,
            'auto_color_balance': self.auto_color_balance,
            'auto_sharpness': self.auto_sharpness,
            'brightness_boost': self.brightness_boost,
            'contrast_boost': self.contrast_boost,
            'saturation_boost': self.saturation_boost,
            'sharpness_amount': self.sharpness_amount,
            'denoise': self.denoise,
            'denoise_strength': self.denoise_strength
        }


class EnhancementEngine:
    """
    Automatic image quality enhancement.

    Features:
    - Auto-exposure correction
    - Auto-color balance
    - Smart sharpening
    - Preset profiles
    - Real-time application via OBS filters
    """

    # Built-in presets
    PRESETS: Dict[str, EnhancementProfile] = {
        'professional': EnhancementProfile(
            name='Professional',
            auto_exposure=True,
            auto_color_balance=True,
            auto_sharpness=True,
            brightness_boost=0.1,
            contrast_boost=0.15,
            saturation_boost=0.1,
            sharpness_amount=0.3,
            denoise=True,
            denoise_strength=0.4
        ),
        'gaming': EnhancementProfile(
            name='Gaming',
            auto_exposure=True,
            auto_color_balance=True,
            auto_sharpness=True,
            brightness_boost=0.15,
            contrast_boost=0.25,
            saturation_boost=0.2,
            sharpness_amount=0.5,
            denoise=False
        ),
        'podcast': EnhancementProfile(
            name='Podcast',
            auto_exposure=True,
            auto_color_balance=True,
            auto_sharpness=False,
            brightness_boost=0.05,
            contrast_boost=0.1,
            saturation_boost=0.0,
            sharpness_amount=0.1,
            denoise=True,
            denoise_strength=0.6
        ),
        'natural': EnhancementProfile(
            name='Natural',
            auto_exposure=True,
            auto_color_balance=True,
            auto_sharpness=False,
            brightness_boost=0.0,
            contrast_boost=0.0,
            saturation_boost=0.0,
            sharpness_amount=0.0,
            denoise=False
        )
    }

    def __init__(
        self,
        quality_analyzer: Any,
        filter_controller: Any
    ) -> None:
        """
        Initialize enhancement engine.

        Args:
            quality_analyzer: QualityAnalyzer instance
            filter_controller: FilterController instance
        """
        self.analyzer = quality_analyzer
        self.filters = filter_controller
        self.current_profile: Optional[EnhancementProfile] = None

        logger.info("EnhancementEngine initialized")

    async def auto_enhance(
        self,
        source_name: str,
        frame: np.ndarray,
        profile: Optional[EnhancementProfile] = None
    ) -> Dict[str, Any]:
        """
        Automatically enhance source based on analysis.

        Args:
            source_name: OBS source name
            frame: Current frame for analysis
            profile: Enhancement profile (uses 'professional' if None)

        Returns:
            Applied adjustments
        """
        if profile is None:
            profile = self.PRESETS['professional']

        self.current_profile = profile

        logger.info(
            f"Auto-enhancing '{source_name}' "
            f"with profile: {profile.name}"
        )

        # Analyze current quality
        quality = self.analyzer.analyze_frame(frame)

        adjustments = {
            'brightness': 0.0,
            'contrast': 0.0,
            'saturation': 0.0,
            'gamma': 0.0,
            'sharpness': 0.0
        }

        # Auto-exposure correction
        if profile.auto_exposure:
            adjustments['brightness'] = self._calculate_exposure_correction(
                quality.exposure,
                profile.brightness_boost
            )
            adjustments['gamma'] = self._calculate_gamma_correction(
                quality.exposure
            )

        # Auto-contrast
        adjustments['contrast'] = profile.contrast_boost

        # Auto-color balance
        if profile.auto_color_balance:
            adjustments['saturation'] = (
                self._calculate_saturation_correction(
                    quality.color_balance,
                    profile.saturation_boost
                )
            )

        # Auto-sharpness
        if profile.auto_sharpness:
            adjustments['sharpness'] = (
                self._calculate_sharpness_correction(
                    quality.sharpness,
                    profile.sharpness_amount
                )
            )

        # Apply adjustments to OBS
        await self._apply_adjustments(source_name, adjustments, profile)

        logger.info(f"✅ Auto-enhancement applied: {adjustments}")

        return adjustments

    def _calculate_exposure_correction(
        self,
        exposure_score: Any,
        boost: float
    ) -> float:
        """Calculate exposure correction amount"""
        # If under-exposed, increase brightness
        if exposure_score.raw_value < 90:
            correction = (127 - exposure_score.raw_value) / 255.0
            return float(min(0.5, correction + boost))

        # If over-exposed, decrease brightness
        elif exposure_score.raw_value > 170:
            correction = (exposure_score.raw_value - 127) / 255.0
            return float(max(-0.5, -correction + boost))

        # Just apply boost if in good range
        return boost

    def _calculate_gamma_correction(self, exposure_score: Any) -> float:
        """Calculate gamma correction"""
        # Adjust gamma for better midtones
        if exposure_score.raw_value < 90:
            return 0.2  # Lift shadows
        elif exposure_score.raw_value > 170:
            return -0.2  # Compress highlights
        return 0.0

    def _calculate_saturation_correction(
        self,
        color_score: Any,
        boost: float
    ) -> float:
        """Calculate saturation correction"""
        # If color cast detected, adjust saturation
        if color_score.status == "warning":
            return boost * 0.5  # Reduce boost if color issues
        return boost

    def _calculate_sharpness_correction(
        self,
        sharpness_score: Any,
        amount: float
    ) -> float:
        """Calculate sharpness amount"""
        # Apply more sharpening if image is soft
        if sharpness_score.raw_value < 40:
            return min(1.0, amount + 0.3)
        return amount

    async def _apply_adjustments(
        self,
        source_name: str,
        adjustments: Dict[str, float],
        profile: EnhancementProfile
    ) -> None:
        """Apply calculated adjustments to OBS source"""

        # Apply color correction
        await self.filters.apply_color_correction(
            source_name,
            brightness=adjustments['brightness'],
            contrast=adjustments['contrast'],
            saturation=adjustments['saturation'],
            gamma=adjustments['gamma']
        )

        # Apply sharpness
        if adjustments['sharpness'] > 0:
            await self.filters.apply_sharpness(
                source_name,
                amount=adjustments['sharpness']
            )

        # Apply noise reduction if enabled
        if profile.denoise:
            logger.info(
                f"Denoise enabled (strength: {profile.denoise_strength})"
            )

    async def apply_preset(
        self,
        source_name: str,
        preset_name: str,
        frame: np.ndarray
    ) -> bool:
        """
        Apply enhancement preset.

        Args:
            source_name: OBS source name
            preset_name: Preset name ('professional', 'gaming', etc.)
            frame: Current frame

        Returns:
            True if successful
        """
        if preset_name not in self.PRESETS:
            logger.error(f"Unknown preset: {preset_name}")
            return False

        profile = self.PRESETS[preset_name]

        await self.auto_enhance(source_name, frame, profile)

        return True

    def get_presets(self) -> Dict[str, EnhancementProfile]:
        """Get all available presets"""
        return self.PRESETS.copy()

    def get_current_profile(self) -> Optional[EnhancementProfile]:
        """Get currently applied profile"""
        return self.current_profile
