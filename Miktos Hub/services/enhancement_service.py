"""
Enhancement Service - Wraps existing enhancement engine

This service provides audio and video enhancement capabilities by wrapping
your existing enhancement_engine.py module.
"""

import sys
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Add existing backend to path
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

try:
    from core.enhancement_engine import EnhancementEngine, EnhancementPreset
    ENHANCEMENT_AVAILABLE = True
except ImportError as e:
    EnhancementEngine = None
    EnhancementPreset = None
    ENHANCEMENT_AVAILABLE = False
    logging.warning(f"Enhancement engine module not available: {e}")

from config import get_config

logger = logging.getLogger(__name__)


class EnhancementType(Enum):
    """Type of enhancement"""
    AUDIO = "audio"
    VIDEO = "video"
    BOTH = "both"


@dataclass
class PresetInfo:
    """Information about an enhancement preset"""
    id: str
    name: str
    description: str
    type: EnhancementType
    settings: Dict[str, Any]


@dataclass
class EnhancementProfile:
    """Custom enhancement profile"""
    id: str
    name: str
    type: EnhancementType
    
    # Audio settings
    noise_reduction: float = 0.5  # 0.0-1.0
    normalize_audio: bool = True
    target_lufs: float = -16.0
    compression_ratio: float = 3.0
    
    # Video settings
    color_correction: bool = True
    brightness: float = 0.0  # -1.0 to 1.0
    contrast: float = 1.0  # 0.0 to 2.0
    saturation: float = 1.0  # 0.0 to 2.0
    sharpening: float = 0.5  # 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "audio": {
                "noise_reduction": self.noise_reduction,
                "normalize_audio": self.normalize_audio,
                "target_lufs": self.target_lufs,
                "compression_ratio": self.compression_ratio,
            },
            "video": {
                "color_correction": self.color_correction,
                "brightness": self.brightness,
                "contrast": self.contrast,
                "saturation": self.saturation,
                "sharpening": self.sharpening,
            }
        }


class EnhancementService:
    """
    Audio and video enhancement service.
    
    Provides real-time and post-processing enhancement capabilities
    including noise reduction, audio normalization, color correction,
    and sharpening.
    
    Example:
        ```python
        service = EnhancementService()
        
        # List available presets
        presets = service.list_presets()
        print(f"Available: {[p.name for p in presets]}")
        
        # Apply preset to camera
        await service.apply_preset(
            camera_id="phone-001",
            preset_name="broadcast"
        )
        
        # Create custom profile
        profile = service.create_profile(
            name="My Custom Profile",
            config={
                "noise_reduction": 0.8,
                "brightness": 0.2,
                "saturation": 1.2,
            }
        )
        
        # Apply custom profile
        await service.enable_enhancement(
            camera_id="phone-001",
            profile_id=profile.id
        )
        ```
    """
    
    def __init__(self):
        if not ENHANCEMENT_AVAILABLE:
            raise RuntimeError("Enhancement engine module not available - check backend installation")
        
        config = get_config()
        
        self._engine = EnhancementEngine(
            enable_gpu=config.processing.enable_gpu_acceleration,
            gpu_device_id=config.processing.gpu_device_id,
        )
        
        # Store custom profiles
        self._custom_profiles: Dict[str, EnhancementProfile] = {}
        
        # Track active enhancements per camera
        self._active_enhancements: Dict[str, str] = {}  # camera_id -> profile_id
        
        logger.info("Enhancement service initialized")
    
    def list_presets(self) -> List[PresetInfo]:
        """
        List all available enhancement presets.
        
        Returns:
            List of preset information
        """
        presets = []
        
        # Get presets from enhancement engine
        try:
            engine_presets = self._engine.list_presets()
            
            for preset in engine_presets:
                presets.append(PresetInfo(
                    id=preset.id,
                    name=preset.name,
                    description=preset.description,
                    type=self._map_preset_type(preset.type),
                    settings=preset.settings,
                ))
            
            logger.debug(f"Listed {len(presets)} presets")
            
        except Exception as e:
            logger.error(f"Failed to list presets: {e}")
        
        return presets
    
    def get_preset(self, preset_name: str) -> Optional[PresetInfo]:
        """
        Get a specific preset by name.
        
        Args:
            preset_name: Name of preset
            
        Returns:
            Preset info or None if not found
        """
        presets = self.list_presets()
        
        for preset in presets:
            if preset.name.lower() == preset_name.lower():
                return preset
        
        return None
    
    async def apply_preset(
        self,
        camera_id: str,
        preset_name: str,
    ) -> bool:
        """
        Apply an enhancement preset to a camera.
        
        Args:
            camera_id: Camera to enhance
            preset_name: Name of preset to apply
            
        Returns:
            True if applied successfully
        """
        logger.info(f"Applying preset '{preset_name}' to camera {camera_id}")
        
        try:
            # Get preset
            preset = self.get_preset(preset_name)
            if not preset:
                logger.error(f"Preset not found: {preset_name}")
                return False
            
            # Apply via engine
            success = await self._engine.apply_preset(
                source_id=camera_id,
                preset_id=preset.id,
            )
            
            if success:
                self._active_enhancements[camera_id] = preset.id
                logger.info(f"Preset applied successfully")
            else:
                logger.error(f"Failed to apply preset")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to apply preset: {e}", exc_info=True)
            return False
    
    def create_profile(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> EnhancementProfile:
        """
        Create a custom enhancement profile.
        
        Args:
            name: Profile name
            config: Enhancement configuration
            
        Returns:
            Created profile
        """
        import uuid
        
        profile_id = f"profile_{uuid.uuid4().hex[:8]}"
        
        # Determine type based on config
        has_audio = any(k in config for k in ["noise_reduction", "normalize_audio", "target_lufs"])
        has_video = any(k in config for k in ["brightness", "contrast", "saturation", "sharpening"])
        
        if has_audio and has_video:
            profile_type = EnhancementType.BOTH
        elif has_audio:
            profile_type = EnhancementType.AUDIO
        else:
            profile_type = EnhancementType.VIDEO
        
        # Create profile with config
        profile = EnhancementProfile(
            id=profile_id,
            name=name,
            type=profile_type,
            **config
        )
        
        self._custom_profiles[profile_id] = profile
        
        logger.info(f"Created enhancement profile: {name} ({profile_id})")
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[EnhancementProfile]:
        """
        Get a custom profile.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Profile or None if not found
        """
        return self._custom_profiles.get(profile_id)
    
    def list_profiles(self) -> List[EnhancementProfile]:
        """List all custom profiles"""
        return list(self._custom_profiles.values())
    
    async def enable_enhancement(
        self,
        camera_id: str,
        profile_id: str,
    ) -> bool:
        """
        Enable enhancement using a custom profile.
        
        Args:
            camera_id: Camera to enhance
            profile_id: Profile to use
            
        Returns:
            True if enabled successfully
        """
        logger.info(f"Enabling enhancement profile {profile_id} for camera {camera_id}")
        
        profile = self.get_profile(profile_id)
        if not profile:
            logger.error(f"Profile not found: {profile_id}")
            return False
        
        try:
            # Apply via engine
            success = await self._engine.apply_custom_profile(
                source_id=camera_id,
                profile=profile.to_dict(),
            )
            
            if success:
                self._active_enhancements[camera_id] = profile_id
                logger.info(f"Enhancement enabled")
            else:
                logger.error(f"Failed to enable enhancement")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to enable enhancement: {e}", exc_info=True)
            return False
    
    async def disable_enhancement(self, camera_id: str) -> bool:
        """
        Disable enhancement for a camera.
        
        Args:
            camera_id: Camera to disable enhancement for
            
        Returns:
            True if disabled successfully
        """
        logger.info(f"Disabling enhancement for camera {camera_id}")
        
        try:
            success = await self._engine.disable_enhancement(camera_id)
            
            if success:
                if camera_id in self._active_enhancements:
                    del self._active_enhancements[camera_id]
                logger.info(f"Enhancement disabled")
            else:
                logger.error(f"Failed to disable enhancement")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to disable enhancement: {e}", exc_info=True)
            return False
    
    def get_active_enhancement(self, camera_id: str) -> Optional[str]:
        """
        Get the active enhancement profile for a camera.
        
        Args:
            camera_id: Camera to check
            
        Returns:
            Profile ID or None if no enhancement active
        """
        return self._active_enhancements.get(camera_id)
    
    def is_enhanced(self, camera_id: str) -> bool:
        """Check if camera has enhancement enabled"""
        return camera_id in self._active_enhancements
    
    async def update_profile_settings(
        self,
        profile_id: str,
        settings: Dict[str, Any],
    ) -> bool:
        """
        Update settings for a custom profile.
        
        Args:
            profile_id: Profile to update
            settings: New settings to apply
            
        Returns:
            True if updated successfully
        """
        profile = self.get_profile(profile_id)
        if not profile:
            logger.error(f"Profile not found: {profile_id}")
            return False
        
        # Update profile settings
        for key, value in settings.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        logger.info(f"Updated profile {profile_id}")
        
        # If this profile is active on any cameras, reapply it
        for camera_id, active_profile_id in self._active_enhancements.items():
            if active_profile_id == profile_id:
                logger.info(f"Reapplying updated profile to camera {camera_id}")
                await self.enable_enhancement(camera_id, profile_id)
        
        return True
    
    def _map_preset_type(self, engine_type: str) -> EnhancementType:
        """Map engine preset type to service type"""
        engine_type_lower = engine_type.lower()
        
        if "audio" in engine_type_lower and "video" in engine_type_lower:
            return EnhancementType.BOTH
        elif "audio" in engine_type_lower:
            return EnhancementType.AUDIO
        else:
            return EnhancementType.VIDEO
    
    def is_available(self) -> bool:
        """Check if enhancement engine is available"""
        return ENHANCEMENT_AVAILABLE
