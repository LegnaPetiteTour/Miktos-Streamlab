"""
Modules - High-level feature orchestrators

Modules combine multiple core services and service wrappers
to provide complete features.

Each module:
1. Orchestrates multiple services
2. Handles complex workflows
3. Emits events for monitoring
4. Provides high-level APIs
"""

from .multi_camera_manager import MultiCameraManager, DiscoveryMethod, DiscoveryEvent
from .multi_platform_streaming import MultiPlatformStreaming, StreamStatus, StreamHealth
from .obs_orchestrator import OBSOrchestrator, TransitionType, SceneTemplate

__all__ = [
    # Modules
    "MultiCameraManager",
    "MultiPlatformStreaming",
    "OBSOrchestrator",
    
    # Data models - Camera Manager
    "DiscoveryMethod",
    "DiscoveryEvent",
    
    # Data models - Streaming
    "StreamStatus",
    "StreamHealth",
    
    # Data models - OBS
    "TransitionType",
    "SceneTemplate",
]
