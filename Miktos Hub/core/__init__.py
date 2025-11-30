"""
Miktos Hub Core Services

Foundation services for the Hub: device registry, stream routing,
session management, processing pipelines, and event bus.
"""

from core.device_registry import DeviceRegistry
from core.stream_router import StreamRouter, Route, RouteState
from core.session_manager import SessionManager
from core.processing_pipeline import (
    ProcessingPipeline,
    ProcessingPipelineManager,
    IMediaProcessor,
)
from core.event_bus import (
    EventBus,
    Event,
    EventPriority,
    EventTypes,
    get_event_bus,
)
from core.interfaces import (
    DeviceRegistryProtocol,
    StreamRouterProtocol,
    SessionManagerProtocol,
    EngineAdapterProtocol,
    ProcessingPipelineProtocol,
    TranscriptionServiceProtocol,
    ExportServiceProtocol,
)

__all__ = [
    # Services
    "DeviceRegistry",
    "StreamRouter",
    "SessionManager",
    "ProcessingPipeline",
    "ProcessingPipelineManager",
    # Event Bus
    "EventBus",
    "Event",
    "EventPriority",
    "EventTypes",
    "get_event_bus",
    # Models
    "Route",
    "RouteState",
    # Interfaces
    "DeviceRegistryProtocol",
    "StreamRouterProtocol",
    "SessionManagerProtocol",
    "EngineAdapterProtocol",
    "ProcessingPipelineProtocol",
    "TranscriptionServiceProtocol",
    "ExportServiceProtocol",
    "IMediaProcessor",
]
