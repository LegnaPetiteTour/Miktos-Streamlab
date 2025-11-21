"""
Event Bus - Pub/Sub system for loose coupling

This allows components to communicate without direct dependencies.
Example: Session Manager emits "session_started" event, and both
the UI and Recording Service can react to it independently.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Priority levels for event processing"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """
    An event in the system

    Events have:
    - type: What happened (e.g., "camera_connected", "session_started")
    - data: Relevant information
    - source: What component emitted it
    - timestamp: When it occurred
    """
    type: str
    data: Dict[str, Any]
    source: str
    timestamp: datetime
    priority: EventPriority = EventPriority.NORMAL
    id: str = ""

    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = f"evt_{uuid.uuid4().hex[:8]}"


class EventHandler:
    """Wrapper for an event handler function"""

    def __init__(
        self,
        callback: Callable,
        event_type: str,
        priority: EventPriority = EventPriority.NORMAL
    ):
        self.callback = callback
        self.event_type = event_type
        self.priority = priority
        self.is_async = asyncio.iscoroutinefunction(callback)

    async def handle(self, event: Event) -> None:
        """Execute the handler"""
        if self.is_async:
            await self.callback(event)
        else:
            self.callback(event)


class EventBus:
    """
    Central event bus for the system

    Usage:
        # Subscribe to events
        event_bus.subscribe("camera_connected", on_camera_connected)

        # Emit events
        event_bus.emit(Event(
            type="camera_connected",
            data={"camera_id": "cam_1"},
            source="device_registry"
        ))
    """

    def __init__(self):
        # Handlers organized by event type
        self._handlers: Dict[str, List[EventHandler]] = {}

        # Event history for debugging
        self._event_history: List[Event] = []
        self._max_history = 1000

        # Flag for processing events
        self._processing = False

        logger.info("EventBus initialized")

    def subscribe(
        self,
        event_type: str,
        callback: Callable,
        priority: EventPriority = EventPriority.NORMAL
    ) -> int:
        """
        Subscribe to an event type

        Args:
            event_type: Type of event to listen for (e.g., "camera_connected")
            callback: Function to call when event occurs
            priority: Handler priority (higher priority = runs first)

        Returns:
            Handler ID (for unsubscribing)
        """
        handler = EventHandler(callback, event_type, priority)

        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)

        # Sort by priority (highest first)
        self._handlers[event_type].sort(
            key=lambda h: h.priority.value,
            reverse=True
        )

        logger.debug(
            f"Subscribed to '{event_type}' with priority "
            f"{priority.name}"
        )
        return id(handler)

    def unsubscribe(self, event_type: str, handler_id: int) -> bool:
        """
        Unsubscribe from an event

        Args:
            event_type: Event type
            handler_id: ID returned from subscribe()

        Returns:
            True if unsubscribed
        """
        if event_type not in self._handlers:
            return False

        original_count = len(self._handlers[event_type])
        self._handlers[event_type] = [
            h for h in self._handlers[event_type]
            if id(h) != handler_id
        ]

        removed = len(self._handlers[event_type]) < original_count

        if removed:
            logger.debug(f"Unsubscribed from '{event_type}'")

        return removed

    async def publish(
        self,
        event_type: str,
        data: dict,
        source: str = "system"
    ) -> None:
        """
        Publish an event (convenience method)

        Args:
            event_type: Type of event (e.g., "camera_connected")
            data: Event data
            source: Event source
        """
        event = Event(
            type=event_type,
            data=data,
            source=source,
            timestamp=datetime.now()
        )
        await self.emit(event)

    async def emit(self, event: Event) -> None:
        """
        Emit an event to all subscribers

        Args:
            event: Event to emit
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Get handlers for this event type
        handlers = self._handlers.get(event.type, [])

        if not handlers:
            logger.debug(f"No handlers for event type: {event.type}")
            return

        logger.debug(f"Emitting event: {event.type} from {event.source}")

        # Execute all handlers
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler for '{event.type}': {e}",
                    exc_info=True
                )

    def emit_sync(self, event: Event) -> None:
        """
        Emit an event synchronously (for non-async contexts)

        Args:
            event: Event to emit
        """
        asyncio.create_task(self.emit(event))

    async def emit_and_wait(self, event: Event, timeout: float = 5.0) -> bool:
        """
        Emit an event and wait for all handlers to complete

        Args:
            event: Event to emit
            timeout: Max time to wait in seconds

        Returns:
            True if all handlers completed within timeout
        """
        try:
            await asyncio.wait_for(self.emit(event), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Event processing timeout for: {event.type}")
            return False

    def get_history(
            self,
            event_type: Optional[str] = None,
            limit: int = 100
    ) -> List[Event]:
        """
        Get event history

        Args:
            event_type: Filter by event type (optional)
            limit: Max number of events to return

        Returns:
            List of recent events
        """
        if event_type:
            filtered = [e for e in self._event_history if e.type == event_type]
            return filtered[-limit:]

        return self._event_history[-limit:]

    def clear_history(self) -> None:
        """Clear event history"""
        count = len(self._event_history)
        self._event_history.clear()
        logger.info(f"Cleared {count} events from history")

    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type"""
        return len(self._handlers.get(event_type, []))

    def list_event_types(self) -> List[str]:
        """List all event types with subscribers"""
        return list(self._handlers.keys())


# Singleton instance
_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


# Common event types (for documentation and type safety)
class EventTypes:
    """Standard event types in the system"""

    # Session events
    SESSION_CREATED = "session_created"
    SESSION_STARTED = "session_started"
    SESSION_PAUSED = "session_paused"
    SESSION_RESUMED = "session_resumed"
    SESSION_ENDED = "session_ended"

    # Camera events
    CAMERA_CONNECTED = "camera_connected"
    CAMERA_DISCONNECTED = "camera_disconnected"
    CAMERA_ERROR = "camera_error"
    CAMERA_BATTERY_LOW = "camera_battery_low"
    CAMERA_THERMAL_WARNING = "camera_thermal_warning"

    # Stream events
    STREAM_STARTED = "stream_started"
    STREAM_STOPPED = "stream_stopped"
    STREAM_ERROR = "stream_error"
    STREAM_QUALITY_DEGRADED = "stream_quality_degraded"

    # Recording events
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_ERROR = "recording_error"

    # Scene events
    SCENE_SWITCHED = "scene_switched"
    SCENE_TRANSITION_STARTED = "scene_transition_started"
    SCENE_TRANSITION_COMPLETED = "scene_transition_completed"

    # Health events
    HEALTH_CHECK_PASSED = "health_check_passed"
    HEALTH_CHECK_FAILED = "health_check_failed"
    SYSTEM_OVERLOAD = "system_overload"

    # Processing events
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_ERROR = "processing_error"
