"""
Services - High-level wrappers around existing backend modules

All services follow the same pattern:
1. Import existing backend module
2. Provide cleaner, more intuitive API
3. Handle errors and logging consistently
4. Return structured data models
"""

from .transcription_service import TranscriptionService
from .quality_service import QualityService, QualityAnalysis, QualityIssue
from .enhancement_service import EnhancementService, EnhancementProfile, EnhancementType
from .network_service import NetworkService, NetworkMetrics, NetworkQuality, BandwidthTestResult
from .recording_service import RecordingService, RecordingConfig, RecordingMode, RecordingInfo
from .export_service import ExportService, AspectRatio, ExportQuality, PlatformPreset

__all__ = [
    # Services
    "TranscriptionService",
    "QualityService",
    "EnhancementService",
    "NetworkService",
    "RecordingService",
    "ExportService",
    
    # Data models - Quality
    "QualityAnalysis",
    "QualityIssue",
    
    # Data models - Enhancement
    "EnhancementProfile",
    "EnhancementType",
    
    # Data models - Network
    "NetworkMetrics",
    "NetworkQuality",
    "BandwidthTestResult",
    
    # Data models - Recording
    "RecordingConfig",
    "RecordingMode",
    "RecordingInfo",
    
    # Data models - Export
    "AspectRatio",
    "ExportQuality",
    "PlatformPreset",
]
