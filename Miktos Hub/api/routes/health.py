"""
Health Monitoring API Routes
System-wide health monitoring, metrics, and diagnostics.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from api.models import SuccessResponse

router = APIRouter(prefix="/health", tags=["health"])

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"

class ComponentHealth(BaseModel):
    """Health status of a system component"""
    name: str = Field(..., description="Component name")
    status: HealthStatus = Field(..., description="Health status")
    message: Optional[str] = Field(None, description="Status message")
    metrics: Dict[str, Any] = Field(default={}, description="Component metrics")
    last_check: datetime = Field(..., description="Last health check time")

class CameraHealthSummary(BaseModel):
    """Camera health summary"""
    camera_id: str
    label: str
    status: HealthStatus
    battery_percent: Optional[int]
    temperature_celsius: Optional[float]
    network_quality: Optional[str]
    bitrate_kbps: Optional[float]
    fps: Optional[float]
    last_seen: datetime

class SystemHealthResponse(BaseModel):
    """Complete system health status"""
    overall_status: HealthStatus
    timestamp: datetime
    components: List[ComponentHealth]
    cameras: List[CameraHealthSummary]
    active_sessions: int
    total_cameras: int
    healthy_cameras: int
    streaming_destinations: int
    healthy_destinations: int
    uptime_seconds: float

class MetricsResponse(BaseModel):
    """System metrics"""
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_rx_mbps: float
    network_tx_mbps: float
    active_sessions: int
    active_streams: int
    total_cameras: int
    timestamp: datetime

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_session_manager():
    """Get session manager instance"""
    from api.server import app_state
    if not app_state.session_manager:
        raise HTTPException(
            status_code=503,
            detail="Session manager not initialized"
        )
    return app_state.session_manager

def get_camera_manager():
    """Get camera manager instance"""
    from api.server import app_state
    if not app_state.camera_manager:
        raise HTTPException(
            status_code=503,
            detail="Camera manager not initialized"
        )
    return app_state.camera_manager

def get_streaming_module():
    """Get streaming module instance"""
    from api.server import app_state
    if not app_state.streaming_module:
        raise HTTPException(
            status_code=503,
            detail="Streaming module not initialized"
        )
    return app_state.streaming_module

def get_obs_orchestrator():
    """Get OBS orchestrator instance"""
    from api.server import app_state
    if not app_state.obs_orchestrator:
        raise HTTPException(
            status_code=503,
            detail="OBS orchestrator not initialized"
        )
    return app_state.obs_orchestrator

# ============================================================================
# HEALTH CHECK ROUTES
# ============================================================================

@router.get(
    "",
    response_model=SystemHealthResponse,
    summary="System health check",
    description="Get complete system health status"
)
async def get_system_health(
    session_mgr: object = Depends(get_session_manager),
    camera_mgr: object = Depends(get_camera_manager),
    streaming: object = Depends(get_streaming_module),
    obs: object = Depends(get_obs_orchestrator)
):
    """Get complete system health"""
    try:
        import psutil
        from datetime import datetime, timedelta
        
        # Collect component health
        components = []
        overall_status = HealthStatus.HEALTHY
        
        # Check OBS connection
        try:
            obs_connected = await obs.is_connected()
            obs_status = HealthStatus.HEALTHY if obs_connected else HealthStatus.FAILED
            components.append(ComponentHealth(
                name="OBS Engine",
                status=obs_status,
                message="Connected" if obs_connected else "Disconnected",
                last_check=datetime.utcnow()
            ))
            if obs_status == HealthStatus.FAILED:
                overall_status = HealthStatus.DEGRADED
        except Exception as e:
            components.append(ComponentHealth(
                name="OBS Engine",
                status=HealthStatus.FAILED,
                message=str(e),
                last_check=datetime.utcnow()
            ))
            overall_status = HealthStatus.DEGRADED
        
        # Check camera manager
        try:
            discovered_cameras = camera_mgr.get_discovered_cameras()
            camera_status = HealthStatus.HEALTHY
            components.append(ComponentHealth(
                name="Camera Manager",
                status=camera_status,
                message=f"{len(discovered_cameras)} cameras discovered",
                metrics={"camera_count": len(discovered_cameras)},
                last_check=datetime.utcnow()
            ))
        except Exception as e:
            components.append(ComponentHealth(
                name="Camera Manager",
                status=HealthStatus.FAILED,
                message=str(e),
                last_check=datetime.utcnow()
            ))
            overall_status = HealthStatus.DEGRADED
        
        # Collect camera health summaries
        camera_summaries = []
        healthy_cameras = 0
        
        for camera in camera_mgr.get_discovered_cameras():
            try:
                health = await camera_mgr.get_camera_health(camera.id)
                
                # Determine camera status
                cam_status = HealthStatus.HEALTHY
                if health.network_quality in ["poor", "critical"]:
                    cam_status = HealthStatus.DEGRADED
                if health.battery_percent and health.battery_percent < 20:
                    cam_status = HealthStatus.DEGRADED
                if health.temperature_celsius and health.temperature_celsius > 45:
                    cam_status = HealthStatus.DEGRADED
                
                if cam_status == HealthStatus.HEALTHY:
                    healthy_cameras += 1
                
                camera_summaries.append(CameraHealthSummary(
                    camera_id=camera.id,
                    label=camera.label,
                    status=cam_status,
                    battery_percent=health.battery_percent,
                    temperature_celsius=health.temperature_celsius,
                    network_quality=health.network_quality,
                    bitrate_kbps=health.bitrate_kbps,
                    fps=health.fps,
                    last_seen=health.last_seen
                ))
            except Exception:
                camera_summaries.append(CameraHealthSummary(
                    camera_id=camera.id,
                    label=camera.label,
                    status=HealthStatus.UNKNOWN,
                    battery_percent=None,
                    temperature_celsius=None,
                    network_quality=None,
                    bitrate_kbps=None,
                    fps=None,
                    last_seen=datetime.utcnow()
                ))
        
        # Check streaming health for active sessions
        active_sessions = session_mgr.list_sessions()
        streaming_destinations = 0
        healthy_destinations = 0
        
        for session in active_sessions:
            try:
                stream_health = await streaming.get_health(session.id)
                streaming_destinations += stream_health.total_destinations
                healthy_destinations += stream_health.healthy_destinations
                
                if stream_health.degraded_destinations > 0:
                    overall_status = HealthStatus.DEGRADED
            except Exception:
                pass
        
        # Calculate uptime
        uptime = psutil.boot_time()
        uptime_seconds = (datetime.utcnow().timestamp() - uptime)
        
        return SystemHealthResponse(
            overall_status=overall_status,
            timestamp=datetime.utcnow(),
            components=components,
            cameras=camera_summaries,
            active_sessions=len(active_sessions),
            total_cameras=len(camera_summaries),
            healthy_cameras=healthy_cameras,
            streaming_destinations=streaming_destinations,
            healthy_destinations=healthy_destinations,
            uptime_seconds=uptime_seconds
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system health: {str(e)}"
        )

@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="System metrics",
    description="Get real-time system resource metrics"
)
async def get_system_metrics(
    session_mgr: object = Depends(get_session_manager),
    camera_mgr: object = Depends(get_camera_manager),
    streaming: object = Depends(get_streaming_module)
):
    """Get system resource metrics"""
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_total_mb = memory.total / (1024 * 1024)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_total_gb = disk.total / (1024 * 1024 * 1024)
        
        # Network I/O
        net_io = psutil.net_io_counters()
        # Convert to Mbps (approximate, based on 1-second interval)
        network_rx_mbps = net_io.bytes_recv / (1024 * 1024)
        network_tx_mbps = net_io.bytes_sent / (1024 * 1024)
        
        # Application metrics
        active_sessions = len(session_mgr.list_sessions())
        active_streams = 0
        total_cameras = len(camera_mgr.get_discovered_cameras())
        
        for session in session_mgr.list_sessions():
            try:
                health = await streaming.get_health(session.id)
                if health.is_streaming:
                    active_streams += 1
            except Exception:
                pass
        
        return MetricsResponse(
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_total_mb=memory_total_mb,
            disk_usage_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            network_rx_mbps=network_rx_mbps,
            network_tx_mbps=network_tx_mbps,
            active_sessions=active_sessions,
            active_streams=active_streams,
            total_cameras=total_cameras,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system metrics: {str(e)}"
        )

@router.get(
    "/ping",
    response_model=SuccessResponse,
    summary="Ping check",
    description="Simple ping to check if API is responsive"
)
async def ping():
    """Simple health ping"""
    return SuccessResponse(
        message="pong",
        data={"timestamp": datetime.utcnow().isoformat()}
    )

# ============================================================================
# DIAGNOSTICS
# ============================================================================

@router.get(
    "/diagnostics",
    response_model=Dict[str, Any],
    summary="Run diagnostics",
    description="Run comprehensive system diagnostics"
)
async def run_diagnostics(
    include_cameras: bool = True,
    include_network: bool = True,
    include_obs: bool = True,
    camera_mgr: object = Depends(get_camera_manager),
    obs: object = Depends(get_obs_orchestrator)
):
    """Run system diagnostics"""
    try:
        import psutil
        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "platform": psutil.Process().name(),
                "cpu_count": psutil.cpu_count(),
                "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "memory_total_gb": psutil.virtual_memory().total / (1024 * 1024 * 1024),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
        }
        
        if include_cameras:
            cameras = camera_mgr.get_discovered_cameras()
            diagnostics["cameras"] = {
                "total": len(cameras),
                "details": [
                    {
                        "id": cam.id,
                        "label": cam.label,
                        "transport": cam.transport.value,
                        "url": cam.url
                    }
                    for cam in cameras
                ]
            }
        
        if include_obs:
            try:
                obs_connected = await obs.is_connected()
                diagnostics["obs"] = {
                    "connected": obs_connected,
                    "version": await obs.get_version() if obs_connected else None
                }
            except Exception as e:
                diagnostics["obs"] = {
                    "connected": False,
                    "error": str(e)
                }
        
        if include_network:
            net_connections = psutil.net_connections(kind='inet')
            diagnostics["network"] = {
                "active_connections": len(net_connections),
                "interfaces": list(psutil.net_if_addrs().keys())
            }
        
        return diagnostics
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run diagnostics: {str(e)}"
        )
