"""
Miktos StreamLab API Server

FastAPI server that exposes OBS controller functionality via REST and WebSocket
endpoints.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import OBS controller from parent directory
sys.path.append(str(Path(__file__).parent.parent))
from obs_controller import OBSController, OBSStatus  # noqa: E402

app = FastAPI(
    title="Miktos StreamLab API",
    description="REST API for OBS streaming control and monitoring",
    version="1.0.0",
)

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your UI domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global OBS controller instance
obs_controller: Optional[OBSController] = None


# WebSocket connection manager
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


# Helper function to check OBS connection
def is_obs_connected() -> bool:
    """Check if OBS controller is connected"""
    return obs_controller is not None and obs_controller.status == OBSStatus.CONNECTED


# ============================================================================
# Pydantic Models
# ============================================================================


# Pydantic models for request/response
class StreamConfig(BaseModel):
    """Configuration for starting a stream"""

    platform: str = "youtube"
    rtmp_url: Optional[str] = None
    stream_key: Optional[str] = None


class SceneSwitch(BaseModel):
    """Request to switch to a different scene"""

    scene_name: str


# ============================================================================
# Health & Status Endpoints
# ============================================================================


@app.get("/")
async def root() -> dict:
    """API root - health check"""
    return {
        "service": "Miktos StreamLab API",
        "version": "1.0.0",
        "status": "running",
        "obs_connected": is_obs_connected(),
    }


@app.get("/api/health")
async def get_health() -> dict:
    """Get system health metrics"""
    if not is_obs_connected():
        raise HTTPException(status_code=503, detail="OBS not connected")

    assert obs_controller is not None  # Type checker hint

    # Get real health data from OBS
    try:
        health_data = await obs_controller.get_health()

        return {
            "timestamp": datetime.now().isoformat(),
            "obs_connected": is_obs_connected(),
            "streaming": health_data.get("is_streaming", False),
            "recording": health_data.get("is_recording", False),
            "metrics": {
                "fps": health_data.get("fps", 0.0),
                "cpu_usage": health_data.get("cpu_usage", 0),
                "dropped_frames": health_data.get("dropped_frames", 0),
                "network_status": (
                    "good" if health_data.get("fps", 0) > 25 else "poor"
                ),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting health data: {str(e)}"
        )


# ============================================================================
# Scene Management Endpoints
# ============================================================================


@app.get("/api/scenes")
async def get_scenes() -> dict:
    """Get list of available scenes"""
    if not is_obs_connected():
        raise HTTPException(status_code=503, detail="OBS not connected")

    assert obs_controller is not None  # Type checker hint

    try:
        # Get real scene list from OBS
        scenes = await obs_controller.get_scenes()
        current_scene = await obs_controller.get_current_scene()

        scene_list = [
            {
                "name": scene.name,
                "active": scene.name == current_scene,
            }
            for scene in scenes
        ]

        return {"scenes": scene_list, "current_scene": current_scene or ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting scenes: {str(e)}")


@app.get("/api/scenes/current")
async def get_current_scene() -> dict:
    """Get the currently active scene"""
    if not is_obs_connected():
        raise HTTPException(status_code=503, detail="OBS not connected")

    assert obs_controller is not None  # Type checker hint

    try:
        current = await obs_controller.get_current_scene()
        return {"scene_name": current or "", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting current scene: {str(e)}"
        )


@app.post("/api/scenes/switch")
async def switch_scene(scene: SceneSwitch) -> dict:
    """Switch to a different scene"""
    if not is_obs_connected():
        raise HTTPException(status_code=503, detail="OBS not connected")

    assert obs_controller is not None  # Type checker hint

    try:
        success = await obs_controller.switch_scene(scene.scene_name)

        return {
            "success": success,
            "scene_name": scene.scene_name,
            "message": f"Switched to scene: {scene.scene_name}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error switching scene: {str(e)}")


@app.get("/api/streaming/status")
async def get_streaming_status() -> dict:
    """Get current streaming status"""
    if not is_obs_connected():
        raise HTTPException(status_code=503, detail="OBS not connected")

    assert obs_controller is not None  # Type checker hint

    try:
        health = await obs_controller.get_health()

        return {
            "streaming": health.get("is_streaming", False),
            "recording": health.get("is_recording", False),
            "uptime": 0,  # Could calculate from stream start time
            "destinations": [
                {
                    "name": "YouTube",
                    "status": ("live" if health.get("is_streaming") else "ready"),  # noqa: E501
                    "bitrate": f"{health.get('bitrate', 0)} Mbps",
                }
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting streaming status: {str(e)}"
        )


@app.post("/api/streaming/start")
async def start_streaming(config: Optional[StreamConfig] = None) -> dict:
    """Start streaming"""
    if not is_obs_connected():
        raise HTTPException(status_code=503, detail="OBS not connected")

    assert obs_controller is not None  # Type checker hint

    try:
        success = await obs_controller.start_streaming()

        if success:
            # Broadcast to WebSocket clients
            await manager.broadcast(
                {"type": "streaming_started", "timestamp": datetime.now().isoformat()}
            )

            return {
                "success": True,
                "message": "Streaming started",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start streaming")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting stream: {str(e)}")


@app.post("/api/streaming/stop")
async def stop_streaming() -> dict:
    """Stop streaming"""
    if not is_obs_connected():
        raise HTTPException(status_code=503, detail="OBS not connected")

    assert obs_controller is not None  # Type checker hint

    try:
        success = await obs_controller.stop_streaming()

        if success:
            # Broadcast to WebSocket clients
            await manager.broadcast(
                {"type": "streaming_stopped", "timestamp": datetime.now().isoformat()}
            )

            return {
                "success": True,
                "message": "Streaming stopped",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to stop streaming")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping stream: {str(e)}")


# ============================================================================
# WebSocket Endpoint for Real-time Updates
# ============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time health and status updates"""
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "message": "Connected to Miktos StreamLab",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep connection alive and send periodic updates
        while True:
            # Send health update every 2 seconds
            if is_obs_connected():
                assert obs_controller is not None  # Type checker hint
                try:
                    health = await obs_controller.get_health()
                    health_data = {
                        "type": "health_update",
                        "data": {
                            "fps": health.get("fps", 0.0),
                            "cpu": health.get("cpu_usage", 0),
                            "network": (
                                "good" if health.get("fps", 0) > 25 else "poor"
                            ),  # noqa: E501
                            "dropped_frames": health.get("dropped_frames", 0),
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                    await websocket.send_json(health_data)
                except Exception as e:
                    print(f"Error getting health data for WebSocket: {e}")
            else:
                # Send disconnected status
                await websocket.send_json(
                    {
                        "type": "health_update",
                        "data": {
                            "fps": 0,
                            "cpu": 0,
                            "network": "disconnected",
                            "dropped_frames": 0,
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# Startup & Shutdown Events
# ============================================================================


def set_obs_controller(controller: Optional[OBSController]) -> None:
    """Set the OBS controller instance for the API to use"""
    global obs_controller
    obs_controller = controller


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize OBS controller on startup"""
    global obs_controller

    # If obs_controller is already set by main_hybrid.py, use it
    if obs_controller is not None:
        print("🔗 Using shared OBS controller from main application")
        print("🚀 Miktos StreamLab API started")
        print("📡 Server running on http://localhost:8000")
        print("📚 API docs available at http://localhost:8000/docs")
        return

    # Otherwise, create our own connection (standalone mode)
    try:
        obs_controller = OBSController(
            host="localhost",
            port=4455,
            password="",  # Set your OBS WebSocket password here if needed
            auto_reconnect=True,
        )

        # Attempt to connect to OBS
        connected = await obs_controller.connect()
        if connected:
            print("✅ Connected to OBS Studio")
        else:
            print("⚠️  Could not connect to OBS Studio - API will return mock data")
            print("   Make sure OBS Studio is running with WebSocket server enabled")
            obs_controller = None
    except Exception as e:
        print(f"⚠️  Error initializing OBS connection: {e}")
        print("   API will return mock data until OBS is connected")
        obs_controller = None

    print("🚀 Miktos StreamLab API started")
    print("📡 Server running on http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown"""
    if obs_controller:
        try:
            await obs_controller.disconnect()
            print("✅ Disconnected from OBS Studio")
        except Exception as e:
            print(f"⚠️  Error disconnecting from OBS: {e}")

    print("👋 Miktos StreamLab API shutting down")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info",
    )
