#!/usr/bin/env python3
"""
Slate Display Manager for Miktos StreamLab
Manages professional "Technical Difficulties" slate with smooth transitions
"""

import asyncio
from typing import Optional, Any
from enum import Enum


class SlateMessage(Enum):
    """Pre-defined slate messages for common scenarios"""

    # Failover scenarios
    TECHNICAL_DIFFICULTIES = (
        "We are experiencing technical difficulties. Please stand by."
    )
    STREAM_SWITCHING = "Switching to backup stream"
    STREAM_RECONNECTING = "Reconnecting to stream"

    # Scheduled events
    SCHEDULED_MAINTENANCE = (
        "Scheduled maintenance in progress. Stream will resume shortly."
    )
    STREAM_STARTING = "Stream starting shortly"
    STREAM_ENDING = "Stream ending soon"
    STREAM_ENDED = "This stream has ended. Thank you for watching."

    # Time-based messages
    RETURN_5_MIN = "Stream will return in approximately 5 minutes"
    RETURN_10_MIN = "Stream will return in approximately 10 minutes"
    RETURN_30_MIN = "Stream will return in approximately 30 minutes"

    # Break messages
    SHORT_BREAK = "We'll be right back after a short break"
    INTERMISSION = "Intermission - Stream will resume shortly"

    # Custom placeholder
    CUSTOM = "custom"


class SlateManager:
    """Manages slate display with smooth transitions and dynamic messaging"""

    def __init__(self, obs_controller: Any) -> None:
        """
        Initialize slate manager

        Args:
            obs_controller: OBSController instance
        """
        self.obs = obs_controller
        self.slate_scene_name = "Technical Difficulties"
        self.message_source_name = "Message"
        self.previous_scene: Optional[str] = None
        self.slate_active = False

    async def show_slate(
        self,
        message: Optional[str] = None,
        subtitle: Optional[str] = None,
        duration: Optional[float] = None
    ) -> bool:
        """
        Display the slate with optional custom message

        Args:
            message: Custom message text (updates the "Message" source)
            subtitle: Optional subtitle text
            duration: If set, auto-hide slate after this many seconds

        Returns:
            bool: True if slate was displayed successfully
        """
        try:
            # Save current scene if not already slate
            if not self.slate_active:
                current = await self.obs.get_current_scene()
                if isinstance(current, str):
                    self.previous_scene = current
                elif isinstance(current, dict):
                    self.previous_scene = current.get(
                        'sceneName', 'Camera Scene'
                    )
                else:
                    self.previous_scene = str(getattr(
                        current, 'name', 'Camera Scene'
                    ))

            # Update message if provided
            if message:
                await self.update_message(message)

            # Switch to slate scene
            success = await self.obs.switch_scene(
                self.slate_scene_name
            )

            if success:
                self.slate_active = True
                msg = message or 'Technical Difficulties'
                print(f"✓ Slate displayed: {msg}")

                # Auto-hide if duration specified
                if duration:
                    await asyncio.sleep(duration)
                    await self.hide_slate()

            return bool(success)

        except Exception as e:
            print(f"❌ Failed to show slate: {e}")
            return False

    async def hide_slate(self) -> bool:
        """
        Hide the slate and return to previous scene

        Returns:
            bool: True if slate was hidden successfully
        """
        try:
            if not self.slate_active:
                print("ℹ Slate is not currently active")
                return True

            if self.previous_scene:
                success = await self.obs.switch_scene(
                    self.previous_scene
                )
                if success:
                    self.slate_active = False
                    print(
                        f"✓ Slate hidden, returned to: "
                        f"{self.previous_scene}"
                    )
                    return True

            return False

        except Exception as e:
            print(f"❌ Failed to hide slate: {e}")
            return False

    async def update_message(self, message: str) -> bool:
        """
        Update the message text on the slate

        Args:
            message: New message text

        Returns:
            bool: True if message was updated successfully
        """
        try:
            success = await self.obs.update_text_source(
                self.message_source_name,
                message
            )
            if success:
                print(f"✓ Updated slate message: {message}")
            return bool(success)

        except Exception as e:
            print(f"⚠ Could not update message: {e}")
            return False

    async def flash_slate(self, message: str, duration: float = 3.0) -> bool:
        """
        Show slate briefly then auto-hide

        Args:
            message: Message to display
            duration: How long to show slate (seconds)

        Returns:
            bool: True if successful
        """
        return await self.show_slate(message, duration=duration)

    def is_slate_active(self) -> bool:
        """Check if slate is currently displayed"""
        return self.slate_active

    async def get_slate_scene_sources(self) -> list:
        """
        Get all sources in the slate scene

        Returns:
            list: List of source names
        """
        try:
            items = await self.obs.get_scene_items(self.slate_scene_name)
            sources = []
            for item in items:
                source_name = item.get("sourceName", "Unknown")
                sources.append(source_name)
            return sources

        except Exception as e:
            print(f"⚠ Could not get slate sources: {e}")
            return []

    async def show_preset_message(
        self,
        preset: SlateMessage,
        duration: Optional[float] = None
    ) -> bool:
        """
        Show slate with a preset message

        Args:
            preset: SlateMessage enum value
            duration: Optional auto-hide duration

        Returns:
            bool: True if successful
        """
        return await self.show_slate(preset.value, duration=duration)
