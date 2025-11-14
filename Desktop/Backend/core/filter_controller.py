"""
Filter Controller - Apply filters to OBS sources

Manages OBS source filters for image quality control.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FilterType(Enum):
    """OBS filter types"""
    COLOR_CORRECTION = "color_correction_filter"
    COLOR_GRADE = "color_grade_filter"
    SHARPNESS = "sharpness_filter"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    SATURATION = "saturation"
    GAMMA = "gamma"
    NOISE_SUPPRESS = "noise_suppress_filter"
    GAIN = "gain_filter"


@dataclass
class FilterSettings:
    """Filter settings"""
    filter_type: FilterType
    enabled: bool = True
    settings: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.settings is None:
            self.settings = {}


class FilterController:
    """
    Controls OBS filters on sources.

    Features:
    - Add/remove filters
    - Adjust filter settings
    - Preset configurations
    - Real-time adjustments
    """

    def __init__(self, obs_controller: Any) -> None:
        """
        Initialize filter controller.

        Args:
            obs_controller: OBS controller instance
        """
        self.obs = obs_controller
        logger.info("FilterController initialized")

    async def add_filter(
        self,
        source_name: str,
        filter_name: str,
        filter_type: FilterType,
        settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add filter to source.

        Args:
            source_name: Source name
            filter_name: Name for the filter
            filter_type: Type of filter
            settings: Filter settings

        Returns:
            True if added successfully
        """
        try:
            logger.info(
                f"Adding filter '{filter_name}' "
                f"({filter_type.value}) to '{source_name}'"
            )

            # Create filter
            request = {
                "sourceName": source_name,
                "filterName": filter_name,
                "filterKind": filter_type.value,
                "filterSettings": settings or {}
            }

            await self.obs.call("CreateSourceFilter", request)

            logger.info(f"✅ Filter added: {filter_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add filter: {e}")
            return False

    async def remove_filter(
        self,
        source_name: str,
        filter_name: str
    ) -> bool:
        """
        Remove filter from source.

        Args:
            source_name: Source name
            filter_name: Filter name

        Returns:
            True if removed successfully
        """
        try:
            logger.info(
                f"Removing filter '{filter_name}' from '{source_name}'"
            )

            request = {
                "sourceName": source_name,
                "filterName": filter_name
            }

            await self.obs.call("RemoveSourceFilter", request)

            logger.info(f"✅ Filter removed: {filter_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove filter: {e}")
            return False

    async def set_filter_enabled(
        self,
        source_name: str,
        filter_name: str,
        enabled: bool
    ) -> bool:
        """
        Enable/disable filter.

        Args:
            source_name: Source name
            filter_name: Filter name
            enabled: Enable/disable

        Returns:
            True if successful
        """
        try:
            request = {
                "sourceName": source_name,
                "filterName": filter_name,
                "filterEnabled": enabled
            }

            await self.obs.call("SetSourceFilterEnabled", request)

            action = 'Enabled' if enabled else 'Disabled'
            logger.info(f"{action} filter: {filter_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to toggle filter: {e}")
            return False

    async def set_filter_settings(
        self,
        source_name: str,
        filter_name: str,
        settings: Dict[str, Any]
    ) -> bool:
        """
        Update filter settings.

        Args:
            source_name: Source name
            filter_name: Filter name
            settings: New settings

        Returns:
            True if successful
        """
        try:
            request = {
                "sourceName": source_name,
                "filterName": filter_name,
                "filterSettings": settings
            }

            await self.obs.call("SetSourceFilterSettings", request)

            logger.info(f"Updated filter settings: {filter_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update filter settings: {e}")
            return False

    async def get_filter_settings(
        self,
        source_name: str,
        filter_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current filter settings.

        Args:
            source_name: Source name
            filter_name: Filter name

        Returns:
            Filter settings or None
        """
        try:
            request = {
                "sourceName": source_name,
                "filterName": filter_name
            }

            result = await self.obs.call("GetSourceFilter", request)

            return result.get("filterSettings", {})  # type: ignore

        except Exception as e:
            logger.error(f"Failed to get filter settings: {e}")
            return None

    async def list_filters(
        self,
        source_name: str
    ) -> List[Dict[str, Any]]:
        """
        List all filters on source.

        Args:
            source_name: Source name

        Returns:
            List of filter info
        """
        try:
            request = {"sourceName": source_name}

            result = await self.obs.call("GetSourceFilterList", request)

            return result.get("filters", [])  # type: ignore

        except Exception as e:
            logger.error(f"Failed to list filters: {e}")
            return []

    async def apply_color_correction(
        self,
        source_name: str,
        brightness: float = 0.0,  # -1.0 to 1.0
        contrast: float = 0.0,    # -1.0 to 1.0
        saturation: float = 0.0,  # -1.0 to 1.0
        gamma: float = 0.0        # -3.0 to 3.0
    ) -> bool:
        """
        Apply color correction filter.

        Args:
            source_name: Source name
            brightness: Brightness adjustment
            contrast: Contrast adjustment
            saturation: Saturation adjustment
            gamma: Gamma adjustment

        Returns:
            True if successful
        """
        settings = {
            "brightness": brightness,
            "contrast": contrast,
            "saturation": saturation,
            "gamma": gamma
        }

        # Check if filter exists
        filters = await self.list_filters(source_name)
        filter_exists = any(
            f["filterName"] == "color_correction" for f in filters
        )

        if filter_exists:
            # Update existing
            return await self.set_filter_settings(
                source_name,
                "color_correction",
                settings
            )
        else:
            # Create new
            return await self.add_filter(
                source_name,
                "color_correction",
                FilterType.COLOR_CORRECTION,
                settings
            )

    async def apply_sharpness(
        self,
        source_name: str,
        amount: float = 0.5  # 0.0 to 1.0
    ) -> bool:
        """
        Apply sharpness filter.

        Args:
            source_name: Source name
            amount: Sharpness amount (0.0 = none, 1.0 = max)

        Returns:
            True if successful
        """
        settings = {
            "sharpness": amount
        }

        filters = await self.list_filters(source_name)
        filter_exists = any(
            f["filterName"] == "sharpness" for f in filters
        )

        if filter_exists:
            return await self.set_filter_settings(
                source_name,
                "sharpness",
                settings
            )
        else:
            return await self.add_filter(
                source_name,
                "sharpness",
                FilterType.SHARPNESS,
                settings
            )

    async def reset_filters(self, source_name: str) -> bool:
        """
        Reset all adjustments to default.

        Args:
            source_name: Source name

        Returns:
            True if successful
        """
        try:
            # Reset color correction to defaults
            await self.apply_color_correction(
                source_name,
                brightness=0.0,
                contrast=0.0,
                saturation=0.0,
                gamma=0.0
            )

            # Reset sharpness
            await self.apply_sharpness(source_name, amount=0.0)

            logger.info(f"✅ Filters reset for '{source_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to reset filters: {e}")
            return False
