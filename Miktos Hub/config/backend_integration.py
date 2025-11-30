"""
Backend Integration Configuration

This module manages the integration between Miktos Hub and the
existing Backend. It handles path setup and provides utilities
for importing Backend modules.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Backend path configuration
BACKEND_PATH = Path(
    '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
)


def setup_backend_path() -> bool:
    """
    Add Backend to Python path if it exists.
    
    Returns:
        bool: True if Backend path was added successfully, False otherwise
    """
    if not BACKEND_PATH.exists():
        logger.warning(
            f"Backend path not found: {BACKEND_PATH}\n"
            "Backend services will operate in limited mode"
        )
        return False
    
    backend_str = str(BACKEND_PATH)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)
        logger.info(f"Added Backend to Python path: {backend_str}")
    
    return True


def get_backend_path() -> Optional[Path]:
    """
    Get the Backend directory path if it exists.
    
    Returns:
        Optional[Path]: Backend path if it exists, None otherwise
    """
    if BACKEND_PATH.exists():
        return BACKEND_PATH
    return None


def is_backend_available() -> bool:
    """
    Check if Backend is available for import.
    
    Returns:
        bool: True if Backend can be imported, False otherwise
    """
    if not BACKEND_PATH.exists():
        return False
    
    try:
        # Try to import a core Backend module
        setup_backend_path()
        import core.config  # noqa: F401
        return True
    except ImportError as e:
        logger.debug(f"Backend import failed: {e}")
        return False


# Module availability flags - updated at runtime
MODULES_AVAILABLE = {
    'transcription': False,
    'quality_analyzer': False,
    'enhancement': False,
    'network': False,
    'recording': False,
    'egress': False,
    'youtube': False,
    'facebook': False,
    'twitter': False,
}


def check_module_availability():
    """
    Check which Backend modules are available and update flags.
    """
    if not setup_backend_path():
        return
    
    # Check transcription
    try:
        import core.transcription  # noqa: F401
        MODULES_AVAILABLE['transcription'] = True
        logger.debug("✓ Transcription module available")
    except ImportError:
        logger.debug("✗ Transcription module not available")
    
    # Check quality analyzer
    try:
        import core.quality_analyzer  # noqa: F401
        MODULES_AVAILABLE['quality_analyzer'] = True
        logger.debug("✓ Quality analyzer module available")
    except ImportError:
        logger.debug("✗ Quality analyzer module not available")
    
    # Check enhancement
    try:
        import core.enhancement_engine  # noqa: F401
        MODULES_AVAILABLE['enhancement'] = True
        logger.debug("✓ Enhancement module available")
    except ImportError:
        logger.debug("✗ Enhancement module not available")
    
    # Check network
    try:
        import core.network  # noqa: F401
        MODULES_AVAILABLE['network'] = True
        logger.debug("✓ Network module available")
    except ImportError:
        logger.debug("✗ Network module not available")
    
    # Check recording
    try:
        import core.iso_recording  # noqa: F401
        MODULES_AVAILABLE['recording'] = True
        logger.debug("✓ Recording module available")
    except ImportError:
        logger.debug("✗ Recording module not available")
    
    # Check egress (streaming engine)
    try:
        import core.egress_v2  # noqa: F401
        MODULES_AVAILABLE['egress'] = True
        logger.debug("✓ Egress module available")
    except ImportError:
        logger.debug("✗ Egress module not available")
    
    # Check YouTube
    try:
        import core.youtube_dual_stream  # noqa: F401
        MODULES_AVAILABLE['youtube'] = True
        logger.debug("✓ YouTube module available")
    except ImportError:
        logger.debug("✗ YouTube module not available")
    
    # Check Facebook
    try:
        import core.facebook_live  # noqa: F401
        MODULES_AVAILABLE['facebook'] = True
        logger.debug("✓ Facebook module available")
    except ImportError:
        logger.debug("✗ Facebook module not available")
    
    # Check Twitter/X
    try:
        import core.twitter_live  # noqa: F401
        MODULES_AVAILABLE['twitter'] = True
        logger.debug("✓ Twitter module available")
    except ImportError:
        logger.debug("✗ Twitter module not available")


def get_module_status() -> dict:
    """
    Get the current status of Backend module availability.
    
    Returns:
        dict: Module availability status
    """
    return MODULES_AVAILABLE.copy()


def log_integration_status():
    """
    Log the current Backend integration status.
    """
    if not is_backend_available():
        logger.warning("Backend integration: NOT AVAILABLE")
        logger.warning("Hub will operate in limited mode")
        return
    
    check_module_availability()
    
    available_count = sum(1 for v in MODULES_AVAILABLE.values() if v)
    total_count = len(MODULES_AVAILABLE)
    
    logger.info(f"Backend integration: CONNECTED")
    logger.info(
        f"Modules available: {available_count}/{total_count}"
    )
    
    if available_count < total_count:
        unavailable = [
            k for k, v in MODULES_AVAILABLE.items() if not v
        ]
        logger.info(f"Unavailable modules: {', '.join(unavailable)}")


# Initialize on import
check_module_availability()
