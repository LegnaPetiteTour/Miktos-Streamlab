"""
Device Registry Service

Tracks all cameras (phones, webcams, NDI, etc.) and provides unified access.
This is the single source of truth for camera devices in the Hub.
"""

from typing import Dict, List, Optional
import logging
from threading import RLock

from models.camera import CameraDevice, CameraHealth, CameraCapability

logger = logging.getLogger(__name__)


class DeviceRegistry:
    """
    Universal camera device registry.
    
    Thread-safe registry for all camera devices. Whether it's a phone,
    webcam, NDI source, or IP camera, they all register here.
    
    Example:
        ```python
        registry = DeviceRegistry()
        
        # Register a phone camera
        phone = CameraDevice(
            id="phone-001",
            label="Wide Shot (Phone 1)",
            transport=TransportType.SRT,
            url="srt://192.168.1.100:8888",
            capabilities=[
                CameraCapability.VIDEO,
                CameraCapability.AUDIO,
                CameraCapability.REMOTE_CONTROL,
            ]
        )
        registry.register(phone)
        
        # Later, get it back
        camera = registry.get("phone-001")
        ```
    """
    
    def __init__(self):
        self._devices: Dict[str, CameraDevice] = {}
        self._lock = RLock()  # Thread-safe access
        logger.info("Device Registry initialized")
    
    def register(self, device: CameraDevice) -> None:
        """
        Register a new camera device.
        
        Args:
            device: The camera device to register
            
        Raises:
            ValueError: If device with same ID already exists
        """
        with self._lock:
            if device.id in self._devices:
                logger.warning(f"Device {device.id} already registered, updating")
            
            device.is_registered = True
            self._devices[device.id] = device
            logger.info(f"Registered device: {device.id} ({device.label})")
    
    def unregister(self, device_id: str) -> None:
        """
        Unregister a camera device.
        
        Args:
            device_id: ID of the device to unregister
            
        Raises:
            KeyError: If device not found
        """
        with self._lock:
            if device_id not in self._devices:
                raise KeyError(f"Device {device_id} not found")
            
            device = self._devices[device_id]
            device.is_registered = False
            del self._devices[device_id]
            logger.info(f"Unregistered device: {device_id}")
    
    def get(self, device_id: str) -> Optional[CameraDevice]:
        """
        Get a specific camera by ID.
        
        Args:
            device_id: ID of the device to retrieve
            
        Returns:
            The camera device, or None if not found
        """
        with self._lock:
            return self._devices.get(device_id)
    
    def list_all(self) -> List[CameraDevice]:
        """
        List all registered cameras.
        
        Returns:
            List of all registered camera devices
        """
        with self._lock:
            return list(self._devices.values())
    
    def update_health(self, device_id: str, health: CameraHealth) -> None:
        """
        Update health metrics for a camera.
        
        Args:
            device_id: ID of the device
            health: New health metrics
            
        Raises:
            KeyError: If device not found
        """
        with self._lock:
            if device_id not in self._devices:
                raise KeyError(f"Device {device_id} not found")
            
            self._devices[device_id].health = health
            
            # Log warnings for unhealthy devices
            if not health.is_healthy():
                logger.warning(
                    f"Device {device_id} unhealthy: "
                    f"connected={health.is_connected}, "
                    f"fps={health.fps:.1f}, "
                    f"bitrate={health.bitrate_kbps:.0f}kbps"
                )
    
    def get_by_capability(self, capability: CameraCapability) -> List[CameraDevice]:
        """
        Get all cameras with a specific capability.
        
        Args:
            capability: The capability to filter by
            
        Returns:
            List of cameras with the specified capability
        """
        with self._lock:
            return [
                device for device in self._devices.values()
                if device.has_capability(capability)
            ]
    
    def get_healthy_devices(self) -> List[CameraDevice]:
        """
        Get all currently healthy cameras.
        
        Returns:
            List of healthy camera devices
        """
        with self._lock:
            return [
                device for device in self._devices.values()
                if device.is_healthy()
            ]
    
    def get_by_transport(self, transport_type: str) -> List[CameraDevice]:
        """
        Get all cameras using a specific transport type.
        
        Args:
            transport_type: The transport type (e.g., "srt", "ndi")
            
        Returns:
            List of cameras using the specified transport
        """
        with self._lock:
            return [
                device for device in self._devices.values()
                if device.transport.value == transport_type
            ]
    
    def update_metadata(self, device_id: str, metadata: Dict[str, any]) -> None:
        """
        Update device metadata.
        
        Args:
            device_id: ID of the device
            metadata: New metadata to merge
            
        Raises:
            KeyError: If device not found
        """
        with self._lock:
            if device_id not in self._devices:
                raise KeyError(f"Device {device_id} not found")
            
            self._devices[device_id].metadata.extra.update(metadata)
    
    def clear(self) -> None:
        """Clear all registered devices (for testing)"""
        with self._lock:
            self._devices.clear()
            logger.info("Device registry cleared")
    
    def __len__(self) -> int:
        """Get number of registered devices"""
        with self._lock:
            return len(self._devices)
    
    def __contains__(self, device_id: str) -> bool:
        """Check if device is registered"""
        with self._lock:
            return device_id in self._devices
