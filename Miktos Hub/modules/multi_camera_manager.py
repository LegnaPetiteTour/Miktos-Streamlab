"""
Multi-Camera Manager Module

Handles phone camera discovery, registration, and health monitoring.
This is the module that connects your Android phone cameras to the Hub.

Features:
- Auto-discovery via mDNS/Bonjour
- Manual pairing via QR code
- Real-time health monitoring (battery, thermal, network)
- Remote control coordination
- Automatic reconnection handling
"""

import logging
import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import socket

from core import DeviceRegistry, EventBus
from services import NetworkService
from models import CameraDevice, CameraHealth, TransportType
from config import get_config

logger = logging.getLogger(__name__)


class DiscoveryMethod(Enum):
    """How a camera was discovered"""
    MDNS = "mdns"  # Auto-discovered via mDNS
    MANUAL = "manual"  # Manually paired via QR code
    RECONNECT = "reconnect"  # Previously known camera reconnected


@dataclass
class PairingRequest:
    """A manual pairing request"""
    pairing_code: str
    device_info: Dict[str, any]
    timestamp: datetime
    expires_at: datetime


@dataclass
class DiscoveryEvent:
    """Camera discovery event"""
    camera: CameraDevice
    method: DiscoveryMethod
    timestamp: datetime


class MultiCameraManager:
    """
    Multi-camera discovery and management.

    Handles automatic discovery of phone cameras on the network,
    manual pairing via QR codes, health monitoring, and remote control.

    Example:
        ```python
        manager = MultiCameraManager(device_registry)

        # Start discovery
        await manager.start_discovery()

        # Wait for cameras
        await asyncio.sleep(10)

        # Get discovered cameras
        cameras = manager.get_discovered_cameras()
        print(f"Found {len(cameras)} cameras")

        # Monitor health
        for camera in cameras:
            health = await manager.get_camera_health(camera.id)
            print(f"{camera.label}: {health.overall_status}")

        # Stop discovery
        await manager.stop_discovery()
        ```
    """

    def __init__(
        self,
        device_registry: DeviceRegistry,
        event_bus: Optional[EventBus] = None,
    ):
        self._registry = device_registry
        self._event_bus = event_bus or EventBus()

        config = get_config()

        # Network service for health monitoring
        self._network_service = NetworkService()

        # Discovery state
        self._discovery_active = False
        self._discovery_task: Optional[asyncio.Task] = None

        # Discovered cameras (not yet registered)
        self._discovered: Dict[str, CameraDevice] = {}

        # Pairing requests (for manual pairing)
        self._pairing_requests: Dict[str, PairingRequest] = {}

        # Health monitoring
        self._health_monitoring_tasks: Dict[str, asyncio.Task] = {}

        # Discovery settings
        self._mdns_service_name = (
            config.camera.mdns_service_name or "_miktos._tcp.local."
        )
        self._discovery_interval = getattr(
            config.camera, 'discovery_interval_seconds', 5.0
        )
        self._health_check_interval = (
            config.camera.health_check_interval_seconds or 10.0
        )

        # Callbacks for discovery events
        self._discovery_callbacks: List[Callable[[DiscoveryEvent], None]] = []

        logger.info("Multi-camera manager initialized")

    async def start_discovery(self) -> None:
        """
        Start automatic camera discovery.

        Begins mDNS/Bonjour service discovery to find cameras on the network.
        Cameras broadcast themselves as '_miktos._tcp.local.' services.
        """
        if self._discovery_active:
            logger.warning("Discovery already active")
            return

        logger.info("Starting camera discovery")
        self._discovery_active = True

        # Start discovery task
        self._discovery_task = asyncio.create_task(self._discovery_loop())

        # Emit event
        await self._event_bus.publish("camera_discovery_started", {
            "timestamp": datetime.now().isoformat(),
        })

    async def stop_discovery(self) -> None:
        """Stop automatic camera discovery."""
        if not self._discovery_active:
            return

        logger.info("Stopping camera discovery")
        self._discovery_active = False

        # Cancel discovery task
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
            self._discovery_task = None

        # Emit event
        await self._event_bus.publish("camera_discovery_stopped", {
            "timestamp": datetime.now().isoformat(),
        })

    async def _discovery_loop(self) -> None:
        """
        Main discovery loop.

        Periodically scans the network for mDNS services.
        """
        logger.info(
            f"Discovery loop started (service: "
            f"{self._mdns_service_name})"
        )

        while self._discovery_active:
            try:
                # Discover cameras via mDNS
                discovered = await self._discover_mdns()

                # Process newly discovered cameras
                for camera in discovered:
                    if camera.id not in self._discovered:
                        logger.info(
                            f"New camera discovered: "
                            f"{camera.label} ({camera.id})"
                        )

                        # Add to discovered list
                        self._discovered[camera.id] = camera

                        # Emit discovery event
                        event = DiscoveryEvent(
                            camera=camera,
                            method=DiscoveryMethod.MDNS,
                            timestamp=datetime.now(),
                        )

                        await self._notify_discovery(event)

                        # Auto-register if configured
                        config = get_config()
                        if config.camera.auto_register_discovered:
                            await self.register_camera(camera.id)

                # Wait before next scan
                await asyncio.sleep(self._discovery_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Discovery error: {e}", exc_info=True)
                await asyncio.sleep(self._discovery_interval)

        logger.info("Discovery loop stopped")

    async def _discover_mdns(self) -> List[CameraDevice]:
        """
        Discover cameras via mDNS/Bonjour.

        Returns:
            List of discovered cameras
        """
        discovered = []

        try:
            # This is a simplified implementation
            # In production, you'd use a proper mDNS library like zeroconf

            # For now, we'll scan for devices responding on the expected port
            # Real implementation would use:
            # from zeroconf import ServiceBrowser, Zeroconf

            # Placeholder: Scan local network for Miktos services
            # In reality, mDNS would handle this automatically

            config = get_config()
            camera_port = config.camera.default_port or 8554

            # Get local IP to determine network
            local_ip = self._get_local_ip()
            if not local_ip:
                return discovered

            # Extract network prefix (e.g., "192.168.1.")
            network_prefix = '.'.join(local_ip.split('.')[:3]) + '.'

            # Scan first 10 IPs (in production, use proper mDNS)
            scan_tasks = []
            for i in range(1, 11):
                ip = f"{network_prefix}{i}"
                if ip != local_ip:  # Skip ourselves
                    scan_tasks.append(self._check_camera_at(ip, camera_port))

            # Wait for all scans
            results = await asyncio.gather(*scan_tasks, return_exceptions=True)

            # Collect discovered cameras
            for result in results:
                if isinstance(result, CameraDevice):
                    discovered.append(result)

        except Exception as e:
            logger.error(f"mDNS discovery failed: {e}")

        return discovered

    async def _check_camera_at(
            self,
            ip: str,
            port: int) -> Optional[CameraDevice]:
        """
        Check if a Miktos camera is at the given IP:port.

        Args:
            ip: IP address to check
            port: Port to check

        Returns:
            CameraDevice if found, None otherwise
        """
        try:
            # Try to connect and get device info
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=1.0
            )

            # Send device info request
            writer.write(b"MIKTOS_DEVICE_INFO\n")
            await writer.drain()

            # Read response
            response = await asyncio.wait_for(
                reader.readline(),
                timeout=1.0
            )

            writer.close()
            await writer.wait_closed()

            # Parse device info
            device_info = json.loads(response.decode())

            # Create camera device
            camera = CameraDevice(
                id=device_info.get("id", f"camera_{ip.replace('.', '_')}"),
                label=device_info.get("label", f"Camera at {ip}"),
                transport=TransportType.SRT,
                connection_url=(
                    f"srt://{ip}:{device_info.get('srt_port', 8554)}"
                ),
                capabilities=(
                    device_info.get("capabilities", ["video", "audio"])
                ),
                metadata={
                    "ip": ip,
                    "port": port,
                    "device_info": device_info,
                    "discovered_at": (
                        datetime.now().isoformat()
                    ),
                }
            )

            return camera

        except (
            asyncio.TimeoutError,
            ConnectionRefusedError,
            json.JSONDecodeError
        ):
            # Not a Miktos camera or not responding
            return None
        except Exception as e:
            logger.debug(f"Error checking {ip}:{port}: {e}")
            return None

    def _get_local_ip(self) -> Optional[str]:
        """Get local IP address of this machine."""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            logger.error(f"Failed to get local IP: {e}")
            return None

    async def generate_pairing_code(
        self,
        device_info: Dict[str, Any],
        ttl_seconds: int = 300,
    ) -> str:
        """
        Generate a pairing code for manual camera pairing.

        Args:
            device_info: Information about the device requesting pairing
            ttl_seconds: How long the code is valid (default 5 minutes)

        Returns:
            Pairing code (to be displayed as QR code)
        """
        import uuid
        import hashlib

        # Generate unique pairing code
        code = hashlib.sha256(
            f"{uuid.uuid4()}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8].upper()

        # Create pairing request
        request = PairingRequest(
            pairing_code=code,
            device_info=device_info,
            timestamp=datetime.now(),
            expires_at=(
                datetime.now().replace(
                    second=datetime.now().second + ttl_seconds
                )
            ),
        )

        self._pairing_requests[code] = request

        logger.info(
            f"Generated pairing code: {code} (expires in {ttl_seconds}s)")

        # Schedule cleanup
        asyncio.create_task(self._cleanup_pairing_code(code, ttl_seconds))

        return code

    async def _cleanup_pairing_code(self, code: str, delay: int) -> None:
        """Remove expired pairing code."""
        await asyncio.sleep(delay)
        if code in self._pairing_requests:
            logger.info(f"Pairing code expired: {code}")
            del self._pairing_requests[code]

    async def pair_camera_manual(
        self,
        pairing_code: str,
        camera: CameraDevice,
    ) -> bool:
        """
        Complete manual pairing using a pairing code.

        Args:
            pairing_code: Code generated by generate_pairing_code()
            camera: Camera device to pair

        Returns:
            True if paired successfully
        """
        # Verify pairing code exists and is valid
        if pairing_code not in self._pairing_requests:
            logger.error(
                f"Invalid or expired pairing code: {pairing_code}"
            )
            return False

        request = self._pairing_requests[pairing_code]

        # Check if expired
        if datetime.now() > request.expires_at:
            logger.error(f"Pairing code expired: {pairing_code}")
            del self._pairing_requests[pairing_code]
            return False

        logger.info(
            f"Pairing camera manually: {
                camera.label} (code: {pairing_code})")

        # Add to discovered
        self._discovered[camera.id] = camera

        # Remove pairing request
        del self._pairing_requests[pairing_code]

        # Emit discovery event
        event = DiscoveryEvent(
            camera=camera,
            method=DiscoveryMethod.MANUAL,
            timestamp=datetime.now(),
        )

        await self._notify_discovery(event)

        # Auto-register
        config = get_config()
        if config.camera.auto_register_discovered:
            await self.register_camera(camera.id)

        return True

    async def register_camera(self, camera_id: str) -> bool:
        """
        Register a discovered camera with the device registry.

        Args:
            camera_id: ID of camera to register

        Returns:
            True if registered successfully
        """
        if camera_id not in self._discovered:
            logger.error(f"Camera not discovered: {camera_id}")
            return False

        camera = self._discovered[camera_id]

        try:
            # Register with device registry
            self._registry.register(camera)

            logger.info(f"Camera registered: {camera.label} ({camera.id})")

            # Start health monitoring
            await self._start_health_monitoring(camera.id)

            # Emit event
            await self._event_bus.publish("camera_registered", {
                "camera_id": camera.id,
                "camera_label": camera.label,
                "timestamp": datetime.now().isoformat(),
            })

            return True

        except Exception as e:
            logger.error(f"Failed to register camera: {e}", exc_info=True)
            return False

    async def unregister_camera(self, camera_id: str) -> bool:
        """
        Unregister a camera from the device registry.

        Args:
            camera_id: ID of camera to unregister

        Returns:
            True if unregistered successfully
        """
        try:
            # Stop health monitoring
            await self._stop_health_monitoring(camera_id)

            # Unregister from device registry
            self._registry.unregister(camera_id)

            # Remove from discovered
            if camera_id in self._discovered:
                del self._discovered[camera_id]

            logger.info(f"Camera unregistered: {camera_id}")

            # Emit event
            await self._event_bus.publish("camera_unregistered", {
                "camera_id": camera_id,
                "timestamp": datetime.now().isoformat(),
            })

            return True

        except Exception as e:
            logger.error(f"Failed to unregister camera: {e}", exc_info=True)
            return False

    async def _start_health_monitoring(self, camera_id: str) -> None:
        """Start monitoring health for a camera."""
        if camera_id in self._health_monitoring_tasks:
            logger.warning(f"Already monitoring camera: {camera_id}")
            return

        logger.info(f"Starting health monitoring for camera: {camera_id}")

        task = asyncio.create_task(self._health_monitoring_loop(camera_id))
        self._health_monitoring_tasks[camera_id] = task

    async def _stop_health_monitoring(self, camera_id: str) -> None:
        """Stop monitoring health for a camera."""
        if camera_id not in self._health_monitoring_tasks:
            return

        logger.info(f"Stopping health monitoring for camera: {camera_id}")

        task = self._health_monitoring_tasks[camera_id]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        del self._health_monitoring_tasks[camera_id]

    async def _health_monitoring_loop(self, camera_id: str) -> None:
        """
        Monitor camera health continuously.

        Checks network, battery, thermal status periodically.
        """
        logger.debug(
            f"Health monitoring loop started for camera: {camera_id}"
        )

        while True:
            try:
                # Get camera
                camera = self._registry.get(camera_id)
                if not camera:
                    logger.warning(f"Camera no longer registered: {camera_id}")
                    break

                # Check network health
                try:
                    network_metrics = (
                        await self._network_service.get_metrics(camera_id)
                    )

                    # Update camera health from network metrics
                    camera.health.network_quality = (
                        network_metrics.quality.value
                    )
                    camera.health.is_connected = (
                        network_metrics.is_connected
                    )

                except Exception as e:
                    logger.error(
                        f"Network check failed for {camera_id}: {e}"
                    )
                    camera.health.is_connected = False

                # Get battery/thermal from camera metadata
                # (phone app reports this)
                camera.health.battery_percent = (
                    camera.metadata.get("battery_percent", 0)
                )
                camera.health.temperature_celsius = camera.metadata.get(
                    "temperature_celsius", 0)

                # Update overall status
                camera.health.update_overall_status()

                # Emit health update event
                await self._event_bus.publish("camera_health_updated", {
                    "camera_id": camera.id,
                    "health": camera.health.to_dict(),
                    "timestamp": datetime.now().isoformat(),
                })

                # Check for critical issues
                if camera.health.overall_status == "critical":
                    logger.warning(
                        f"Camera {camera.id} in critical state: "
                        f"{camera.health}"
                    )

                    await self._event_bus.publish(
                        "camera_health_critical",
                        {
                            "camera_id": camera.id,
                            "health": camera.health.to_dict(),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                # Wait before next check
                await asyncio.sleep(
                    self._health_check_interval
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Health monitoring error for {camera_id}: {e}",
                    exc_info=True)
                await asyncio.sleep(self._health_check_interval)

        logger.debug(f"Health monitoring loop stopped for camera: {camera_id}")

    async def get_camera_health(
            self, camera_id: str) -> Optional[CameraHealth]:
        """
        Get current health status for a camera.

        Args:
            camera_id: Camera to check

        Returns:
            Camera health or None if not found
        """
        camera = self._registry.get(camera_id)
        if not camera:
            return None

        return camera.health

    def get_discovered_cameras(self) -> List[CameraDevice]:
        """Get all discovered cameras (registered or not)."""
        return list(self._discovered.values())

    def get_registered_cameras(self) -> List[CameraDevice]:
        """Get all registered cameras."""
        return self._registry.list_all()

    def is_camera_registered(self, camera_id: str) -> bool:
        """Check if camera is registered."""
        return self._registry.get(camera_id) is not None

    def add_discovery_callback(
            self, callback: Callable[[DiscoveryEvent], None]) -> None:
        """
        Add a callback to be notified when cameras are discovered.

        Args:
            callback: Function to call with DiscoveryEvent
        """
        self._discovery_callbacks.append(callback)

    async def _notify_discovery(self, event: DiscoveryEvent) -> None:
        """Notify all discovery callbacks of a new camera."""
        # Emit via event bus
        await self._event_bus.publish("camera_discovered", {
            "camera_id": event.camera.id,
            "camera_label": event.camera.label,
            "method": event.method.value,
            "timestamp": event.timestamp.isoformat(),
        })

        # Call callbacks
        for callback in self._discovery_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Discovery callback error: {e}")

    async def shutdown(self) -> None:
        """Shutdown the manager and clean up resources."""
        logger.info("Shutting down multi-camera manager")

        # Stop discovery
        await self.stop_discovery()

        # Stop all health monitoring
        tasks = list(self._health_monitoring_tasks.keys())
        for camera_id in tasks:
            await self._stop_health_monitoring(camera_id)

        logger.info("Multi-camera manager shutdown complete")
