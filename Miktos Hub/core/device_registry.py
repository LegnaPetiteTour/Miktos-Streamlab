"""
Device Registry Service

Tracks all cameras (phones, webcams, NDI, etc.) and provides unified access.
This is the single source of truth for camera devices in the Hub.
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging
from threading import RLock

from models.camera import CameraDevice, CameraHealth, CameraCapability

if TYPE_CHECKING:
    from db import Database

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

    def __init__(
        self,
        enable_persistence: bool = True,
        database: Optional['Database'] = None
    ):
        self._devices: Dict[str, CameraDevice] = {}
        self._lock = RLock()  # Thread-safe access
        self._enable_persistence = enable_persistence
        self._db = database  # Allow test database injection
        self._camera_repo = None
        logger.info(
            f"Device Registry initialized "
            f"(persistence: {enable_persistence})"
        )

        # Auto-recover cameras from database if persistence enabled
        if self._enable_persistence:
            self.restore_from_database()

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
                logger.warning(
                    f"Device {device.id} already registered, updating"
                )

            device.is_registered = True
            self._devices[device.id] = device
            logger.info(f"Registered device: {device.id} ({device.label})")

            # Persist to database
            self._persist_camera(device)

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

            # Remove from database
            self._delete_camera_from_db(device_id)

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

    def get_by_capability(
        self, capability: CameraCapability
    ) -> List[CameraDevice]:
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

    def update_metadata(
        self, device_id: str, metadata: Dict[str, Any]
    ) -> None:
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

    # ========================================================================
    # PERSISTENCE METHODS
    # ========================================================================

    def _get_db(self):
        """Get database connection (lazy initialization)"""
        if not self._enable_persistence:
            return None

        if self._db is None:
            try:
                from db import get_database
                self._db = get_database()
                logger.info(
                    "Database connection established for DeviceRegistry"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize database: {e}. "
                    "Running without persistence."
                )
                self._enable_persistence = False
                return None

        return self._db

    def _get_camera_repo(self):
        """Get camera repository"""
        db = self._get_db()
        if db is None:
            return None

        if self._camera_repo is None:
            from db.repositories import CameraRepository
            self._camera_repo = CameraRepository

        return self._camera_repo

    def restore_from_database(self) -> int:
        """
        Restore cameras from database on startup.

        Returns:
            Number of cameras restored
        """
        db = self._get_db()
        if db is None:
            logger.info(
                "Persistence disabled, skipping camera restoration"
            )
            return 0

        try:
            from db.repositories import CameraRepository
            from models.camera import (
                TransportType,
                CameraMetadata,
            )

            with db.session() as db_session:
                repo = CameraRepository(db_session)
                active_cameras = repo.list_active()

                restored_count = 0
                for db_camera in active_cameras:
                    # Convert database model to core camera device
                    caps_data: Dict[str, Any] = (
                        db_camera.capabilities or {}  # type: ignore
                    )

                    # Parse transport type
                    transport_str = caps_data.get(
                        "transport", "rtmp"
                    )
                    try:
                        transport = TransportType(transport_str)
                    except ValueError:
                        logger.warning(
                            f"Unknown transport type: {transport_str}, "
                            "using RTMP"
                        )
                        transport = TransportType.RTMP

                    # Parse capabilities
                    cap_list = caps_data.get("capabilities", [])
                    capabilities = []
                    for cap_str in cap_list:  # type: ignore[attr-defined]
                        try:
                            capabilities.append(
                                CameraCapability(cap_str)
                            )
                        except ValueError:
                            logger.warning(
                                f"Unknown capability: {cap_str}"
                            )

                    # Create camera device
                    camera = CameraDevice(
                        id=db_camera.id,  # type: ignore[arg-type]
                        label=(  # type: ignore[arg-type]
                            str(db_camera.name or "Unknown Camera")
                        ),
                        transport=transport,
                        url=str(  # type: ignore[arg-type]
                            db_camera.stream_url or ""
                        ),
                        capabilities=capabilities,
                        is_registered=(  # type: ignore[arg-type]
                            bool(db_camera.is_active)
                        ),
                        metadata=CameraMetadata(
                            extra={
                                "discovery_method": (
                                    db_camera.discovery_method
                                ),
                                "host": db_camera.host,
                                "port": db_camera.port,
                            }
                        )
                    )

                    # Add to registry
                    with self._lock:
                        self._devices[camera.id] = camera
                    restored_count += 1

                    logger.info(
                        f"Restored camera: {camera.id} - {camera.label}"
                    )

                logger.info(
                    f"Restored {restored_count} camera(s) from database"
                )
                return restored_count

        except Exception as e:
            logger.error(
                f"Failed to restore cameras: {e}",
                exc_info=True
            )
            return 0

    def _persist_camera(self, camera: CameraDevice) -> None:
        """Persist or update camera in database"""
        db = self._get_db()
        if db is None:
            return

        try:
            from db.repositories import CameraRepository

            with db.session() as db_session:
                repo = CameraRepository(db_session)

                # Check if camera exists
                existing = repo.get(camera.id)

                if existing:
                    # Update existing
                    repo.update(camera)
                else:
                    # Create new
                    repo.create(camera)

        except Exception as e:
            logger.error(
                f"Failed to persist camera {camera.id}: {e}",
                exc_info=True
            )

    def _delete_camera_from_db(self, camera_id: str) -> None:
        """Delete camera from database"""
        db = self._get_db()
        if db is None:
            return

        try:
            from db.repositories import CameraRepository

            with db.session() as db_session:
                repo = CameraRepository(db_session)
                repo.delete(camera_id)

        except Exception as e:
            logger.error(
                f"Failed to delete camera {camera_id} from database: {e}",
                exc_info=True
            )
