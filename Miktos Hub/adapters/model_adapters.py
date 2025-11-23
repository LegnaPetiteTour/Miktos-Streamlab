"""
Model Adapters - Bridge Hub models to Backend models

This module provides adapters to translate between the new Hub architecture models
and the existing Backend models. This allows the Hub to use the battle-tested
Backend code without modifying it.

Translations:
- Hub.StreamDestination ↔ Backend.RTMPDestination
- Hub.DestinationHealth ↔ Backend health metrics (embedded in RTMPDestination)
- Hub.DestinationStatus ↔ Backend.DestinationStatus (enum mapping)

Author: Miktos StreamLab
Date: November 21, 2024
"""

from typing import Dict, Any, Optional
from datetime import datetime
import sys
import logging

logger = logging.getLogger(__name__)

# Hub imports
from models import (
    StreamDestination,
    DestinationType,
    DestinationStatus as HubDestStatus,
    DestinationHealth
)

# Backend imports - Add backend to path
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)
    logger.info(f"Added {BACKEND_PATH} to sys.path")

try:
    from core.egress_v2 import (
        RTMPDestination,
        SRTDestination,
        DestinationStatus as BackendDestStatus
    )
    BACKEND_AVAILABLE = True
    logger.info("Backend models imported successfully")
except ImportError as e:
    RTMPDestination = None
    SRTDestination = None
    BackendDestStatus = None
    BACKEND_AVAILABLE = False
    logger.warning(f"Backend models not available: {e}")


class ModelAdapter:
    """
    Translates between Hub and Backend models.
    
    This adapter allows the Hub to use existing Backend code without
    modifying either the Hub or Backend models.
    
    Example:
        ```python
        # Convert Hub model to Backend model
        hub_dest = StreamDestination(
            id="youtube-en",
            name="YouTube EN",
            type=DestinationType.YOUTUBE,
            url="rtmp://a.rtmp.youtube.com/live2",
            stream_key="my-key",
            enabled=True
        )
        
        backend_dest = ModelAdapter.hub_to_backend_rtmp(hub_dest)
        # Now backend_dest can be used with egress_v2.py
        ```
    """
    
    @staticmethod
    def is_available() -> bool:
        """Check if Backend models are available"""
        return BACKEND_AVAILABLE
    
    @staticmethod
    def hub_to_backend_rtmp(hub_dest: StreamDestination) -> Optional['RTMPDestination']:
        """
        Convert Hub StreamDestination to Backend RTMPDestination.
        
        Args:
            hub_dest: Hub's StreamDestination model
            
        Returns:
            Backend's RTMPDestination model, or None if backend unavailable
            
        Note:
            Key field name mapping:
            - Hub: stream_key → Backend: key
        """
        if not BACKEND_AVAILABLE or RTMPDestination is None:
            logger.error("Backend models not available")
            return None
            
        try:
            return RTMPDestination(
                name=hub_dest.name,
                url=hub_dest.url,
                key=hub_dest.stream_key,  # Hub: stream_key → Backend: key
                enabled=hub_dest.enabled,
                status=ModelAdapter._hub_to_backend_status(hub_dest.status),
            )
        except Exception as e:
            logger.error(f"Failed to convert Hub to Backend RTMP: {e}", exc_info=True)
            return None
    
    @staticmethod
    def backend_rtmp_to_hub(backend_dest: 'RTMPDestination') -> Optional[StreamDestination]:
        """
        Convert Backend RTMPDestination to Hub StreamDestination.
        
        Args:
            backend_dest: Backend's RTMPDestination model
            
        Returns:
            Hub's StreamDestination model, or None if conversion fails
            
        Note:
            Key field name mapping:
            - Backend: key → Hub: stream_key
        """
        if not BACKEND_AVAILABLE:
            logger.error("Backend models not available")
            return None
            
        try:
            # Infer platform type from URL
            platform_type = DestinationType.CUSTOM_RTMP
            if "youtube.com" in backend_dest.url.lower():
                platform_type = DestinationType.YOUTUBE
            elif "facebook.com" in backend_dest.url.lower():
                platform_type = DestinationType.FACEBOOK
            elif "twitter.com" in backend_dest.url.lower() or "x.com" in backend_dest.url.lower():
                platform_type = DestinationType.TWITTER
            elif "twitch.tv" in backend_dest.url.lower():
                platform_type = DestinationType.TWITCH
            
            return StreamDestination(
                id=backend_dest.name.lower().replace(" ", "-"),
                name=backend_dest.name,
                type=platform_type,
                url=backend_dest.url,
                stream_key=backend_dest.key,  # Backend: key → Hub: stream_key
                enabled=backend_dest.enabled,
                status=ModelAdapter._backend_to_hub_status(backend_dest.status),
            )
        except Exception as e:
            logger.error(f"Failed to convert Backend to Hub RTMP: {e}", exc_info=True)
            return None
    
    @staticmethod
    def hub_to_backend_srt(hub_dest: StreamDestination) -> Optional['SRTDestination']:
        """
        Convert Hub StreamDestination to Backend SRTDestination.
        
        Args:
            hub_dest: Hub's StreamDestination model
            
        Returns:
            Backend's SRTDestination model, or None if backend unavailable
        """
        if not BACKEND_AVAILABLE or SRTDestination is None:
            logger.error("Backend models not available")
            return None
            
        try:
            return SRTDestination(
                name=hub_dest.name,
                url=hub_dest.url,
                enabled=hub_dest.enabled,
                status=ModelAdapter._hub_to_backend_status(hub_dest.status),
                is_backup=True,  # SRT destinations are typically backup
            )
        except Exception as e:
            logger.error(f"Failed to convert Hub to Backend SRT: {e}", exc_info=True)
            return None
    
    @staticmethod
    def backend_health_to_hub(backend_dest: 'RTMPDestination') -> DestinationHealth:
        """
        Extract health information from Backend RTMPDestination.
        
        Args:
            backend_dest: Backend's RTMPDestination with embedded health metrics
            
        Returns:
            Hub's DestinationHealth model
            
        Note:
            Backend embeds health metrics directly in RTMPDestination.
            Hub separates health into its own model.
        """
        try:
            return DestinationHealth(
                timestamp=datetime.now(),
                is_connected=(backend_dest.status in [
                    BackendDestStatus.CONNECTED,
                    BackendDestStatus.STREAMING
                ]),
                is_streaming=(backend_dest.status == BackendDestStatus.STREAMING),
                bitrate_kbps=backend_dest.bitrate_kbps,
                fps=0.0,  # Not available in RTMPDestination
                dropped_frames=backend_dest.dropped_frames,
                total_frames_sent=backend_dest.total_frames,
                packet_loss_percent=(
                    backend_dest.drop_percentage 
                    if backend_dest.total_frames > 0 
                    else None
                ),
                rtt_ms=None,  # Not available in RTMPDestination
                jitter_ms=None,  # Not available in RTMPDestination
                viewer_count=None,  # Not available in RTMPDestination
                concurrent_viewers=None,  # Not available in RTMPDestination
                last_error=None,  # Not tracked in RTMPDestination
                error_count=0,
            )
        except Exception as e:
            logger.error(f"Failed to extract health: {e}", exc_info=True)
            # Return unhealthy state on error
            return DestinationHealth(
                timestamp=datetime.now(),
                is_connected=False,
                is_streaming=False,
                last_error=str(e),
                error_count=1,
            )
    
    @staticmethod
    def _hub_to_backend_status(hub_status: HubDestStatus) -> 'BackendDestStatus':
        """
        Convert Hub status enum to Backend status enum.
        
        Mapping:
        - Hub.IDLE → Backend.DISCONNECTED
        - Hub.CONNECTING → Backend.CONNECTING
        - Hub.LIVE → Backend.STREAMING
        - Hub.ERROR → Backend.FAILED
        - Hub.DISCONNECTED → Backend.DISCONNECTED
        """
        if not BACKEND_AVAILABLE or BackendDestStatus is None:
            return None
            
        mapping = {
            HubDestStatus.IDLE: BackendDestStatus.DISCONNECTED,
            HubDestStatus.CONNECTING: BackendDestStatus.CONNECTING,
            HubDestStatus.LIVE: BackendDestStatus.STREAMING,
            HubDestStatus.ERROR: BackendDestStatus.FAILED,
            HubDestStatus.DISCONNECTED: BackendDestStatus.DISCONNECTED,
        }
        return mapping.get(hub_status, BackendDestStatus.DISCONNECTED)
    
    @staticmethod
    def _backend_to_hub_status(backend_status: 'BackendDestStatus') -> HubDestStatus:
        """
        Convert Backend status enum to Hub status enum.
        
        Mapping:
        - Backend.DISCONNECTED → Hub.DISCONNECTED
        - Backend.CONNECTING → Hub.CONNECTING
        - Backend.CONNECTED → Hub.CONNECTING (map to connecting)
        - Backend.STREAMING → Hub.LIVE
        - Backend.FAILED → Hub.ERROR
        """
        if not BACKEND_AVAILABLE or BackendDestStatus is None:
            return HubDestStatus.IDLE
            
        mapping = {
            BackendDestStatus.DISCONNECTED: HubDestStatus.DISCONNECTED,
            BackendDestStatus.CONNECTING: HubDestStatus.CONNECTING,
            BackendDestStatus.CONNECTED: HubDestStatus.CONNECTING,  # Map CONNECTED to CONNECTING
            BackendDestStatus.STREAMING: HubDestStatus.LIVE,
            BackendDestStatus.FAILED: HubDestStatus.ERROR,
        }
        return mapping.get(backend_status, HubDestStatus.IDLE)
    
    @staticmethod
    def get_backend_path() -> str:
        """Get the path to the Backend directory"""
        return BACKEND_PATH


# Convenience functions for batch operations

def convert_hub_destinations_to_backend(
    hub_destinations: list[StreamDestination]
) -> list['RTMPDestination']:
    """
    Convert a list of Hub destinations to Backend destinations.
    
    Args:
        hub_destinations: List of Hub StreamDestination models
        
    Returns:
        List of Backend RTMPDestination models (skips failed conversions)
    """
    backend_destinations = []
    
    for hub_dest in hub_destinations:
        if hub_dest.type == DestinationType.CUSTOM_SRT:
            # Convert to SRT destination
            backend_dest = ModelAdapter.hub_to_backend_srt(hub_dest)
        else:
            # Convert to RTMP destination
            backend_dest = ModelAdapter.hub_to_backend_rtmp(hub_dest)
        
        if backend_dest is not None:
            backend_destinations.append(backend_dest)
        else:
            logger.warning(f"Failed to convert destination: {hub_dest.name}")
    
    return backend_destinations


def convert_backend_destinations_to_hub(
    backend_destinations: list
) -> list[StreamDestination]:
    """
    Convert a list of Backend destinations to Hub destinations.
    
    Args:
        backend_destinations: List of Backend RTMPDestination or SRTDestination models
        
    Returns:
        List of Hub StreamDestination models (skips failed conversions)
    """
    hub_destinations = []
    
    for backend_dest in backend_destinations:
        hub_dest = ModelAdapter.backend_rtmp_to_hub(backend_dest)
        
        if hub_dest is not None:
            hub_destinations.append(hub_dest)
        else:
            logger.warning(f"Failed to convert destination: {backend_dest.name}")
    
    return hub_destinations
