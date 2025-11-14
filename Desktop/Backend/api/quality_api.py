"""
Quality API - REST endpoints for image quality control

Provides HTTP endpoints for quality analysis and control.
"""

import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Request models
class AnalyzeRequest(BaseModel):
    """Request to analyze quality"""
    source_name: str


class EnhanceRequest(BaseModel):
    """Request to enhance quality"""
    source_name: str
    preset: Optional[str] = 'professional'


class PresetRequest(BaseModel):
    """Request to apply preset"""
    source_name: str
    preset_name: str


class AdjustRequest(BaseModel):
    """Request to adjust quality"""
    source_name: str
    adjustment_type: str
    value: float


class SavePresetRequest(BaseModel):
    """Request to save preset"""
    name: str
    description: str
    category: str
    source_name: str


class NVBroadcastRequest(BaseModel):
    """Request to configure NVIDIA Broadcast"""
    source_name: str
    effect: str
    intensity: int


class QualityAPI:
    """
    REST API for image quality control.

    Endpoints:
    - POST /quality/analyze - Analyze current quality
    - POST /quality/auto-enhance - Auto-enhance
    - POST /quality/apply-preset - Apply preset
    - POST /quality/adjust - Manual adjustment
    - POST /quality/reset - Reset adjustments
    - POST /quality/save-preset - Save custom preset
    - GET /quality/presets - List presets
    - GET /quality/presets/{name} - Get specific preset
    - DELETE /quality/presets/{name} - Delete preset
    - POST /quality/nvidia - Configure NVIDIA Broadcast
    """

    def __init__(
        self,
        quality_analyzer: Any,
        enhancement_engine: Any,
        preset_manager: Any,
        nvidia_broadcast: Any,
        filter_controller: Any
    ) -> None:
        """
        Initialize quality API.

        Args:
            quality_analyzer: QualityAnalyzer instance
            enhancement_engine: EnhancementEngine instance
            preset_manager: PresetManager instance
            nvidia_broadcast: NVBroadcastSDK instance
            filter_controller: FilterController instance
        """
        self.analyzer = quality_analyzer
        self.enhancement = enhancement_engine
        self.presets = preset_manager
        self.nvidia = nvidia_broadcast
        self.filters = filter_controller

        self.router = APIRouter(prefix="/quality", tags=["quality"])
        self._setup_routes()

        logger.info("QualityAPI initialized")

    def _setup_routes(self) -> None:
        """Setup API routes"""

        @self.router.post("/analyze")
        async def analyze_quality(request: AnalyzeRequest) -> Dict[str, Any]:
            """Analyze current image quality"""
            try:
                # In production, would capture frame from OBS source
                # For now, return simulated quality data
                import numpy as np  # noqa: F401

                # Simulate frame capture
                test_frame = np.random.randint(
                    100,
                    150,
                    (480, 640, 3),
                    dtype=np.uint8
                )

                quality = self.analyzer.analyze_frame(test_frame)

                return quality.to_dict()  # type: ignore[no-any-return]

            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.post("/auto-enhance")
        async def auto_enhance(request: EnhanceRequest) -> Dict[str, Any]:
            """Auto-enhance image quality"""
            try:
                import numpy as np  # noqa: F401

                # Simulate frame
                test_frame = np.random.randint(
                    100,
                    150,
                    (480, 640, 3),
                    dtype=np.uint8
                )

                # Apply enhancement
                adjustments = await self.enhancement.auto_enhance(
                    request.source_name,
                    test_frame,
                    None  # Use default preset
                )

                return {
                    'success': True,
                    'adjustments_applied': adjustments
                }

            except Exception as e:
                logger.error(f"Enhancement failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.post("/apply-preset")
        async def apply_preset(request: PresetRequest) -> dict:
            """Apply quality preset"""
            try:
                preset = self.presets.get_preset(request.preset_name)

                if not preset:
                    raise HTTPException(
                        status_code=404,
                        detail="Preset not found"
                    )

                # Apply preset settings via filter controller
                await self.filters.apply_color_correction(
                    request.source_name,
                    **preset.color_correction
                )

                await self.filters.apply_sharpness(
                    request.source_name,
                    preset.sharpness
                )

                return {
                    'success': True,
                    'preset': preset.to_dict()
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Apply preset failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.post("/adjust")
        async def adjust_quality(request: AdjustRequest) -> dict:
            """Manual quality adjustment"""
            try:
                # Apply adjustment based on type
                if request.adjustment_type == 'brightness':
                    await self.filters.apply_color_correction(
                        request.source_name,
                        brightness=request.value
                    )
                elif request.adjustment_type == 'contrast':
                    await self.filters.apply_color_correction(
                        request.source_name,
                        contrast=request.value
                    )
                elif request.adjustment_type == 'saturation':
                    await self.filters.apply_color_correction(
                        request.source_name,
                        saturation=request.value
                    )
                elif request.adjustment_type == 'sharpness':
                    await self.filters.apply_sharpness(
                        request.source_name,
                        amount=request.value
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown adjustment type: "
                        f"{request.adjustment_type}"
                    )

                return {
                    'success': True,
                    'adjustment_type': request.adjustment_type,
                    'value': request.value
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Adjustment failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.post("/reset")
        async def reset_adjustments(request: AnalyzeRequest) -> dict:
            """Reset all adjustments"""
            try:
                await self.filters.reset_filters(request.source_name)

                return {'success': True}

            except Exception as e:
                logger.error(f"Reset failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.post("/save-preset")
        async def save_preset(request: SavePresetRequest) -> dict:
            """Save custom preset"""
            try:
                # Get current filter settings
                # In production, would query actual OBS filters
                current_settings = {
                    'color_correction': {
                        'brightness': 0.0,
                        'contrast': 0.0,
                        'saturation': 0.0,
                        'gamma': 0.0
                    },
                    'sharpness': 0.0,
                    'noise_reduction': False,
                    'enhancement_profile': 'custom',
                    'nvidia_noise_removal': 0,
                    'nvidia_background_blur': 0
                }

                preset = self.presets.create_preset_from_current(
                    request.name,
                    request.description,
                    request.category,
                    current_settings
                )

                if preset:
                    return {
                        'success': True,
                        'preset': preset.to_dict()
                    }
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create preset"
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Save preset failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.get("/presets")
        async def list_presets(category: Optional[str] = None) -> dict:
            """List all presets"""
            try:
                presets = self.presets.list_presets(category)

                return {
                    'presets': [p.to_dict() for p in presets],
                    'categories': self.presets.get_preset_categories()
                }

            except Exception as e:
                logger.error(f"List presets failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.get("/presets/{name}")
        async def get_preset(name: str) -> dict:
            """Get specific preset"""
            try:
                preset = self.presets.get_preset(name)

                if not preset:
                    raise HTTPException(
                        status_code=404,
                        detail="Preset not found"
                    )

                return preset.to_dict()  # type: ignore[no-any-return]

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Get preset failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.delete("/presets/{name}")
        async def delete_preset(name: str) -> dict:
            """Delete custom preset"""
            try:
                success = self.presets.delete_preset(name)

                if success:
                    return {'success': True}
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot delete preset"
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Delete preset failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.post("/nvidia")
        async def configure_nvidia(request: NVBroadcastRequest) -> dict:
            """Configure NVIDIA Broadcast"""
            try:
                if not self.nvidia.available:
                    raise HTTPException(
                        status_code=400,
                        detail="NVIDIA Broadcast not available"
                    )

                # Convert intensity percentage (0-100) to enum (0-3)
                from core.nvidia_broadcast import NVBroadcastIntensity

                if request.intensity == 0:
                    intensity_enum = NVBroadcastIntensity.OFF
                elif request.intensity <= 33:
                    intensity_enum = NVBroadcastIntensity.LOW
                elif request.intensity <= 66:
                    intensity_enum = NVBroadcastIntensity.MEDIUM
                else:
                    intensity_enum = NVBroadcastIntensity.HIGH

                # Apply NVIDIA effect based on type
                if request.effect == 'noise_removal':
                    success = self.nvidia.apply_noise_removal(
                        request.source_name,
                        intensity_enum
                    )
                elif request.effect == 'background_blur':
                    success = self.nvidia.apply_background_blur(
                        request.source_name,
                        intensity_enum
                    )
                elif request.effect == 'auto_frame':
                    success = self.nvidia.apply_auto_frame(
                        request.source_name,
                        request.intensity > 0
                    )
                elif request.effect == 'eye_contact':
                    success = self.nvidia.apply_eye_contact(
                        request.source_name,
                        request.intensity > 0
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown effect: {request.effect}"
                    )

                return {
                    'success': success,
                    'effect': request.effect,
                    'intensity': request.intensity
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"NVIDIA config failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e

        @self.router.get("/nvidia/status")
        async def nvidia_status() -> Dict[str, Any]:
            """Get NVIDIA Broadcast status"""
            try:
                return self.nvidia.get_gpu_info()  # type: ignore[no-any-return]

            except Exception as e:
                logger.error(f"NVIDIA status failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                ) from e
