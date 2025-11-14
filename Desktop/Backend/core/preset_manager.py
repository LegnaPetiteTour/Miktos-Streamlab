"""
Preset Manager - Save and load filter configurations

Manages filter presets for quick quality adjustments.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FilterPreset:
    """Complete filter preset"""
    name: str
    description: str
    category: str  # 'professional', 'gaming', 'creative', 'custom'

    # Filter settings
    color_correction: Dict[str, float]
    sharpness: float
    noise_reduction: bool

    # Enhancement profile
    enhancement_profile: str

    # NVIDIA Broadcast settings
    nvidia_noise_removal: int
    nvidia_background_blur: int

    # Metadata
    created_at: str
    author: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterPreset":
        """Create from dictionary"""
        return cls(**data)


class PresetManager:
    """
    Manages filter presets.

    Features:
    - Save/load presets
    - Built-in presets
    - Custom user presets
    - Import/export
    """

    # Built-in presets
    BUILTIN_PRESETS: Dict[str, FilterPreset] = {
        'professional': FilterPreset(
            name='Professional',
            description='Clean, professional look for business',
            category='professional',
            color_correction={
                'brightness': 0.1,
                'contrast': 0.15,
                'saturation': 0.1,
                'gamma': 0.0
            },
            sharpness=0.3,
            noise_reduction=True,
            enhancement_profile='professional',
            nvidia_noise_removal=2,
            nvidia_background_blur=0,
            created_at=datetime.now().isoformat(),
            author='Miktos StreamLab'
        ),
        'gaming': FilterPreset(
            name='Gaming',
            description='Vibrant, punchy colors for gaming streams',
            category='gaming',
            color_correction={
                'brightness': 0.15,
                'contrast': 0.25,
                'saturation': 0.2,
                'gamma': 0.1
            },
            sharpness=0.5,
            noise_reduction=False,
            enhancement_profile='gaming',
            nvidia_noise_removal=1,
            nvidia_background_blur=0,
            created_at=datetime.now().isoformat(),
            author='Miktos StreamLab'
        ),
        'podcast': FilterPreset(
            name='Podcast',
            description='Natural look with clean audio',
            category='professional',
            color_correction={
                'brightness': 0.05,
                'contrast': 0.1,
                'saturation': 0.0,
                'gamma': 0.0
            },
            sharpness=0.1,
            noise_reduction=True,
            enhancement_profile='podcast',
            nvidia_noise_removal=3,
            nvidia_background_blur=0,
            created_at=datetime.now().isoformat(),
            author='Miktos StreamLab'
        ),
        'cinematic': FilterPreset(
            name='Cinematic',
            description='Film-like look with depth',
            category='creative',
            color_correction={
                'brightness': -0.05,
                'contrast': 0.2,
                'saturation': -0.1,
                'gamma': -0.1
            },
            sharpness=0.2,
            noise_reduction=False,
            enhancement_profile='natural',
            nvidia_noise_removal=0,
            nvidia_background_blur=2,
            created_at=datetime.now().isoformat(),
            author='Miktos StreamLab'
        ),
        'low_light': FilterPreset(
            name='Low Light',
            description='Optimized for dim environments',
            category='professional',
            color_correction={
                'brightness': 0.3,
                'contrast': 0.1,
                'saturation': 0.05,
                'gamma': 0.3
            },
            sharpness=0.4,
            noise_reduction=True,
            enhancement_profile='professional',
            nvidia_noise_removal=3,
            nvidia_background_blur=0,
            created_at=datetime.now().isoformat(),
            author='Miktos StreamLab'
        )
    }

    def __init__(self, presets_dir: Optional[Path] = None) -> None:
        """
        Initialize preset manager.

        Args:
            presets_dir: Directory for custom presets
        """
        if presets_dir is None:
            presets_dir = Path.home() / ".miktos" / "presets"

        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)

        # Load custom presets
        self.custom_presets: Dict[str, FilterPreset] = {}
        self._load_custom_presets()

        logger.info(f"PresetManager initialized: {self.presets_dir}")

    def _load_custom_presets(self) -> None:
        """Load custom presets from disk"""
        try:
            for preset_file in self.presets_dir.glob("*.json"):
                with open(preset_file) as f:
                    data = json.load(f)

                preset = FilterPreset.from_dict(data)
                self.custom_presets[preset.name.lower()] = preset

            logger.info(
                f"Loaded {len(self.custom_presets)} custom preset(s)"
            )

        except Exception as e:
            logger.error(f"Failed to load custom presets: {e}")

    def get_preset(self, name: str) -> Optional[FilterPreset]:
        """
        Get preset by name.

        Args:
            name: Preset name

        Returns:
            FilterPreset or None
        """
        name_lower = name.lower()

        # Check built-in first
        if name_lower in self.BUILTIN_PRESETS:
            return self.BUILTIN_PRESETS[name_lower]

        # Check custom
        if name_lower in self.custom_presets:
            return self.custom_presets[name_lower]

        return None

    def list_presets(
        self,
        category: Optional[str] = None
    ) -> List[FilterPreset]:
        """
        List all presets.

        Args:
            category: Filter by category (optional)

        Returns:
            List of presets
        """
        all_presets = {**self.BUILTIN_PRESETS, **self.custom_presets}

        presets = list(all_presets.values())

        if category:
            presets = [p for p in presets if p.category == category]

        return presets

    def save_preset(
        self,
        preset: FilterPreset,
        overwrite: bool = False
    ) -> bool:
        """
        Save custom preset.

        Args:
            preset: Preset to save
            overwrite: Overwrite if exists

        Returns:
            True if saved successfully
        """
        try:
            preset_file = (
                self.presets_dir / f"{preset.name.lower()}.json"
            )

            if preset_file.exists() and not overwrite:
                logger.warning(f"Preset already exists: {preset.name}")
                return False

            with open(preset_file, 'w') as f:
                json.dump(preset.to_dict(), f, indent=2)

            self.custom_presets[preset.name.lower()] = preset

            logger.info(f"✅ Preset saved: {preset.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save preset: {e}")
            return False

    def delete_preset(self, name: str) -> bool:
        """
        Delete custom preset.

        Args:
            name: Preset name

        Returns:
            True if deleted successfully
        """
        name_lower = name.lower()

        # Cannot delete built-in presets
        if name_lower in self.BUILTIN_PRESETS:
            logger.error("Cannot delete built-in preset")
            return False

        try:
            preset_file = self.presets_dir / f"{name_lower}.json"

            if preset_file.exists():
                preset_file.unlink()

            if name_lower in self.custom_presets:
                del self.custom_presets[name_lower]

            logger.info(f"✅ Preset deleted: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete preset: {e}")
            return False

    def export_preset(
        self,
        name: str,
        export_path: Path
    ) -> bool:
        """
        Export preset to file.

        Args:
            name: Preset name
            export_path: Export file path

        Returns:
            True if exported successfully
        """
        preset = self.get_preset(name)

        if not preset:
            logger.error(f"Preset not found: {name}")
            return False

        try:
            with open(export_path, 'w') as f:
                json.dump(preset.to_dict(), f, indent=2)

            logger.info(f"✅ Preset exported: {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export preset: {e}")
            return False

    def import_preset(
        self,
        import_path: Path
    ) -> Optional[FilterPreset]:
        """
        Import preset from file.

        Args:
            import_path: Import file path

        Returns:
            Imported preset or None
        """
        try:
            with open(import_path) as f:
                data = json.load(f)

            preset = FilterPreset.from_dict(data)

            # Save as custom preset
            self.save_preset(preset, overwrite=True)

            logger.info(f"✅ Preset imported: {preset.name}")
            return preset

        except Exception as e:
            logger.error(f"Failed to import preset: {e}")
            return None

    def get_preset_categories(self) -> List[str]:
        """
        Get all available preset categories.

        Returns:
            List of category names
        """
        all_presets = {**self.BUILTIN_PRESETS, **self.custom_presets}
        categories = set(p.category for p in all_presets.values())
        return sorted(categories)

    def create_preset_from_current(
        self,
        name: str,
        description: str,
        category: str,
        current_settings: Dict[str, Any]
    ) -> Optional[FilterPreset]:
        """
        Create preset from current filter settings.

        Args:
            name: Preset name
            description: Preset description
            category: Preset category
            current_settings: Current filter settings

        Returns:
            Created preset or None
        """
        try:
            preset = FilterPreset(
                name=name,
                description=description,
                category=category,
                color_correction=current_settings.get(
                    'color_correction',
                    {
                        'brightness': 0.0,
                        'contrast': 0.0,
                        'saturation': 0.0,
                        'gamma': 0.0
                    }
                ),
                sharpness=current_settings.get('sharpness', 0.0),
                noise_reduction=current_settings.get(
                    'noise_reduction',
                    False
                ),
                enhancement_profile=current_settings.get(
                    'enhancement_profile',
                    'custom'
                ),
                nvidia_noise_removal=current_settings.get(
                    'nvidia_noise_removal',
                    0
                ),
                nvidia_background_blur=current_settings.get(
                    'nvidia_background_blur',
                    0
                ),
                created_at=datetime.now().isoformat(),
                author='User'
            )

            if self.save_preset(preset):
                return preset

            return None

        except Exception as e:
            logger.error(f"Failed to create preset: {e}")
            return None
