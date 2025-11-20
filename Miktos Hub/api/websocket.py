"""
WebSocket Handlers
Real-time event streaming for control panel updates.
"""
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from datetime import datetime
import json
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        # Active connections by client ID
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Subscriptions by event type
        self.subscriptions: Dict[str, Set[str]] = {
            "camera_discovered": set(),
            "camera_connected": set(),
            "camera_disconnected": set(),
            "camera_health": set(),
            "session_created": set(),
            "session_started": set(),
            "session_stopped": set(),
            "streaming_started": set(),
            "streaming_stopped": set(),
            "streaming_health": set(),
            "scene_switched": set(),
            "destination_health": set(),
            "system_alert": set(),
            "*": set()  # Subscribe to all events
        }
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register new connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Unregister connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
            # Remove from all subscriptions
            for event_type in self.subscriptions:
                self.subscriptions[event_type].discard(client_id)
            
            logger.info(f"WebSocket client {client_id} disconnected. Total: {len(self.active_connections)}")
    
    def subscribe(self, client_id: str, event_types: list):
        """Subscribe client to event types"""
        for event_type in event_types:
            if event_type in self.subscriptions:
                self.subscriptions[event_type].add(client_id)
                logger.debug(f"Client {client_id} subscribed to {event_type}")
    
    def unsubscribe(self, client_id: str, event_types: list):
        """Unsubscribe client from event types"""
        for event_type in event_types:
            if event_type in self.subscriptions:
                self.subscriptions[event_type].discard(client_id)
                logger.debug(f"Client {client_id} unsubscribed from {event_type}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict, event_type: str):
        """Broadcast message to all subscribed clients"""
        # Get clients subscribed to this event type or all events
        recipients = self.subscriptions.get(event_type, set()) | self.subscriptions.get("*", set())
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        # Send to all recipients
        disconnected = []
        for client_id in recipients:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to {client_id}: {e}")
                    disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
        
        logger.debug(f"Broadcast {event_type} to {len(recipients)} clients")

# Global connection manager instance
manager = ConnectionManager()

# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

async def handle_subscribe(websocket: WebSocket, client_id: str, data: dict):
    """Handle subscription request"""
    event_types = data.get("event_types", [])
    manager.subscribe(client_id, event_types)
    
    await manager.send_personal_message({
        "type": "subscribed",
        "event_types": event_types,
        "message": f"Subscribed to {len(event_types)} event types"
    }, client_id)

async def handle_unsubscribe(websocket: WebSocket, client_id: str, data: dict):
    """Handle unsubscription request"""
    event_types = data.get("event_types", [])
    manager.unsubscribe(client_id, event_types)
    
    await manager.send_personal_message({
        "type": "unsubscribed",
        "event_types": event_types,
        "message": f"Unsubscribed from {len(event_types)} event types"
    }, client_id)

async def handle_ping(websocket: WebSocket, client_id: str, data: dict):
    """Handle ping request"""
    await manager.send_personal_message({
        "type": "pong",
        "timestamp": datetime.utcnow().isoformat()
    }, client_id)

# Message type handlers
MESSAGE_HANDLERS = {
    "subscribe": handle_subscribe,
    "unsubscribe": handle_unsubscribe,
    "ping": handle_ping
}

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """
    WebSocket endpoint for real-time updates
    
    Client can send:
    - {"type": "subscribe", "event_types": ["camera_discovered", "streaming_health"]}
    - {"type": "unsubscribe", "event_types": ["camera_discovered"]}
    - {"type": "ping"}
    
    Server sends:
    - Event messages: {"type": "event_type", "data": {...}, "timestamp": "..."}
    - Responses: {"type": "subscribed"/"pong"/etc, ...}
    """
    # Generate client ID if not provided
    if not client_id:
        client_id = f"client_{datetime.utcnow().timestamp()}"
    
    await manager.connect(websocket, client_id)
    
    # Send welcome message
    await manager.send_personal_message({
        "type": "connected",
        "client_id": client_id,
        "message": "Connected to Miktos Hub",
        "available_events": list(manager.subscriptions.keys())
    }, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type in MESSAGE_HANDLERS:
                await MESSAGE_HANDLERS[message_type](websocket, client_id, data)
            else:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "supported_types": list(MESSAGE_HANDLERS.keys())
                }, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)

# ============================================================================
# EVENT BROADCASTING FUNCTIONS
# ============================================================================
# These functions are called by other parts of the system to broadcast events

async def broadcast_camera_discovered(camera_id: str, camera_data: dict):
    """Broadcast camera discovered event"""
    await manager.broadcast({
        "type": "camera_discovered",
        "data": {
            "camera_id": camera_id,
            **camera_data
        }
    }, "camera_discovered")

async def broadcast_camera_connected(camera_id: str):
    """Broadcast camera connected event"""
    await manager.broadcast({
        "type": "camera_connected",
        "data": {"camera_id": camera_id}
    }, "camera_connected")

async def broadcast_camera_disconnected(camera_id: str, reason: Optional[str] = None):
    """Broadcast camera disconnected event"""
    await manager.broadcast({
        "type": "camera_disconnected",
        "data": {
            "camera_id": camera_id,
            "reason": reason
        }
    }, "camera_disconnected")

async def broadcast_camera_health(camera_id: str, health_data: dict):
    """Broadcast camera health update"""
    await manager.broadcast({
        "type": "camera_health",
        "data": {
            "camera_id": camera_id,
            **health_data
        }
    }, "camera_health")

async def broadcast_session_created(session_id: str, session_data: dict):
    """Broadcast session created event"""
    await manager.broadcast({
        "type": "session_created",
        "data": {
            "session_id": session_id,
            **session_data
        }
    }, "session_created")

async def broadcast_session_started(session_id: str):
    """Broadcast session started event"""
    await manager.broadcast({
        "type": "session_started",
        "data": {"session_id": session_id}
    }, "session_started")

async def broadcast_session_stopped(session_id: str):
    """Broadcast session stopped event"""
    await manager.broadcast({
        "type": "session_stopped",
        "data": {"session_id": session_id}
    }, "session_stopped")

async def broadcast_streaming_started(session_id: str, destinations: list):
    """Broadcast streaming started event"""
    await manager.broadcast({
        "type": "streaming_started",
        "data": {
            "session_id": session_id,
            "destination_count": len(destinations)
        }
    }, "streaming_started")

async def broadcast_streaming_stopped(session_id: str):
    """Broadcast streaming stopped event"""
    await manager.broadcast({
        "type": "streaming_stopped",
        "data": {"session_id": session_id}
    }, "streaming_stopped")

async def broadcast_streaming_health(session_id: str, health_data: dict):
    """Broadcast streaming health update"""
    await manager.broadcast({
        "type": "streaming_health",
        "data": {
            "session_id": session_id,
            **health_data
        }
    }, "streaming_health")

async def broadcast_scene_switched(session_id: str, scene_id: str, scene_name: str):
    """Broadcast scene switched event"""
    await manager.broadcast({
        "type": "scene_switched",
        "data": {
            "session_id": session_id,
            "scene_id": scene_id,
            "scene_name": scene_name
        }
    }, "scene_switched")

async def broadcast_destination_health(destination_id: str, health_data: dict):
    """Broadcast destination health update"""
    await manager.broadcast({
        "type": "destination_health",
        "data": {
            "destination_id": destination_id,
            **health_data
        }
    }, "destination_health")

async def broadcast_system_alert(level: str, message: str, details: Optional[dict] = None):
    """Broadcast system alert"""
    await manager.broadcast({
        "type": "system_alert",
        "data": {
            "level": level,  # "info", "warning", "error", "critical"
            "message": message,
            "details": details or {}
        }
    }, "system_alert")

# ============================================================================
# PERIODIC HEALTH BROADCAST
# ============================================================================

async def periodic_health_broadcast():
    """Periodically broadcast health updates"""
    while True:
        try:
            # Import here to avoid circular dependencies
            from api.server import app_state
            
            if app_state.session_manager and app_state.streaming_module:
                # Broadcast health for all active sessions
                for session in app_state.session_manager.list_sessions():
                    try:
                        health = await app_state.streaming_module.get_health(session.id)
                        
                        await broadcast_streaming_health(
                            session.id,
                            {
                                "overall_status": health.overall_status.value,
                                "healthy_destinations": health.healthy_destinations,
                                "total_destinations": health.total_destinations,
                                "avg_bitrate_kbps": health.avg_bitrate_kbps,
                                "avg_fps": health.avg_fps
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to broadcast health for session {session.id}: {e}")
            
            # Broadcast camera health
            if app_state.camera_manager:
                for camera in app_state.camera_manager.get_discovered_cameras():
                    try:
                        health = await app_state.camera_manager.get_camera_health(camera.id)
                        
                        await broadcast_camera_health(
                            camera.id,
                            {
                                "battery_percent": health.battery_percent,
                                "temperature_celsius": health.temperature_celsius,
                                "network_quality": health.network_quality,
                                "bitrate_kbps": health.bitrate_kbps,
                                "fps": health.fps
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to broadcast health for camera {camera.id}: {e}")
        
        except Exception as e:
            logger.error(f"Error in periodic health broadcast: {e}")
        
        # Wait 10 seconds before next broadcast
        await asyncio.sleep(10)

# Function to start periodic broadcast (called from main.py)
def start_periodic_broadcasts():
    """Start background task for periodic broadcasts"""
    asyncio.create_task(periodic_health_broadcast())
