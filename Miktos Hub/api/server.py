"""
Main FastAPI Server

This is the central API server that provides HTTP REST endpoints
and WebSocket connections for controlling the Miktos Hub.

Features:
- REST API for all Hub operations
- WebSocket for real-time event streaming
- CORS support for web UIs
- Auto-generated OpenAPI documentation
- Health monitoring endpoints
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from core import DeviceRegistry, SessionManager, StreamRouter, EventBus
from services import (
    TranscriptionService,
    QualityService,
    EnhancementService,
    NetworkService,
    RecordingService,
    ExportService,
)
from modules import MultiCameraManager, MultiPlatformStreaming, OBSOrchestrator
from config import get_config

logger = logging.getLogger(__name__)


# ============================================================================
# GLOBAL STATE
# ============================================================================

class HubState:
    """Global Hub state container"""

    def __init__(self):
        # Core services
        self.device_registry: Optional[DeviceRegistry] = None
        self.session_manager: Optional[SessionManager] = None
        self.stream_router: Optional[StreamRouter] = None
        self.event_bus: Optional[EventBus] = None

        # Service wrappers
        self.transcription_service: Optional[TranscriptionService] = None
        self.quality_service: Optional[QualityService] = None
        self.enhancement_service: Optional[EnhancementService] = None
        self.network_service: Optional[NetworkService] = None
        self.recording_service: Optional[RecordingService] = None
        self.export_service: Optional[ExportService] = None

        # Feature modules
        self.camera_manager: Optional[MultiCameraManager] = None
        self.streaming_module: Optional[MultiPlatformStreaming] = None
        self.obs_orchestrator: Optional[OBSOrchestrator] = None

        # State
        self.initialized = False
        self.start_time = datetime.now()

    @property
    def streaming_manager(self):
        """Alias for streaming_module (backward compatibility)"""
        return self.streaming_module


# Global Hub state
hub_state = HubState()
# Alias for routes compatibility
app_state = hub_state


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown of all Hub components.
    """
    # STARTUP
    logger.info("=" * 60)
    logger.info("MIKTOS HUB API STARTING")
    logger.info("=" * 60)

    try:
        # Initialize core services
        logger.info("Initializing core services...")
        hub_state.device_registry = DeviceRegistry()
        hub_state.stream_router = StreamRouter()
        hub_state.event_bus = EventBus()
        hub_state.session_manager = SessionManager(
            hub_state.device_registry,
            hub_state.stream_router
        )

        # Initialize service wrappers
        logger.info("Initializing service wrappers...")
        hub_state.transcription_service = TranscriptionService()
        hub_state.quality_service = QualityService()
        hub_state.enhancement_service = EnhancementService()
        hub_state.network_service = NetworkService()
        hub_state.recording_service = RecordingService()
        hub_state.export_service = ExportService()

        # Initialize feature modules
        logger.info("Initializing feature modules...")
        hub_state.camera_manager = MultiCameraManager(
            hub_state.device_registry,
            hub_state.event_bus
        )
        hub_state.streaming_module = MultiPlatformStreaming(
            hub_state.session_manager,
            hub_state.event_bus
        )
        hub_state.obs_orchestrator = OBSOrchestrator(
            hub_state.device_registry,
            hub_state.stream_router,
            hub_state.event_bus
        )

        # Connect to OBS
        logger.info("Connecting to OBS...")
        try:
            await hub_state.obs_orchestrator.connect()
            logger.info("✓ Connected to OBS")
        except Exception as e:
            logger.warning(f"⚠ Could not connect to OBS: {e}")
            logger.warning("  Hub will continue without OBS integration")

        # Start camera discovery
        logger.info("Starting camera discovery...")
        await hub_state.camera_manager.start_discovery()
        logger.info("✓ Camera discovery active")

        hub_state.initialized = True

        logger.info("=" * 60)
        logger.info("MIKTOS HUB API READY")
        logger.info("=" * 60)
        logger.info("API Docs: http://localhost:8000/docs")
        logger.info("Health Check: http://localhost:8000/api/health")
        logger.info("=" * 60)

        yield

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    finally:
        # SHUTDOWN
        logger.info("=" * 60)
        logger.info("MIKTOS HUB API SHUTTING DOWN")
        logger.info("=" * 60)

        try:
            # Stop camera discovery
            if hub_state.camera_manager:
                logger.info("Stopping camera discovery...")
                await hub_state.camera_manager.shutdown()

            # Stop all active streams
            if hub_state.streaming_module:
                logger.info("Stopping active streams...")
                await hub_state.streaming_module.shutdown()

            # Disconnect from OBS
            if hub_state.obs_orchestrator:
                logger.info("Disconnecting from OBS...")
                await hub_state.obs_orchestrator.shutdown()

            logger.info("=" * 60)
            logger.info("MIKTOS HUB API STOPPED")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Shutdown error: {e}", exc_info=True)


# ============================================================================
# APP CREATION
# ============================================================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app
    """
    config = get_config()

    # Create app with lifespan
    app = FastAPI(
        title="Miktos Hub API",
        description="Professional live streaming orchestration platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.allowed_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all requests"""
        start_time = datetime.now()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Log
        logger.info(
            f"{request.method} {request.url.path} "
            f"- {response.status_code} - {duration_ms:.2f}ms"
        )

        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": str(exc),
                "timestamp": datetime.now().isoformat(),
            }
        )

    # Root endpoint
    @app.get("/")
    async def root():
        """API root - returns basic info"""
        return {
            "name": "Miktos Hub API",
            "version": "1.0.0",
            "status": "running" if hub_state.initialized else "starting",
            "uptime_seconds": (
                datetime.now() - hub_state.start_time
            ).total_seconds(),
            "docs": "/docs",
            "health": "/api/health",
        }

    # Import and include routers
    from api.routes import (
        sessions_router,
        cameras_router,
        scenes_router,
        streaming_router,
        health_router
    )
    from api import websocket

    # Include route modules under /api prefix
    app.include_router(sessions_router, prefix="/api")
    app.include_router(cameras_router, prefix="/api")
    app.include_router(scenes_router, prefix="/api")
    app.include_router(streaming_router, prefix="/api")
    app.include_router(health_router, prefix="/api")

    # Include WebSocket handler
    app.include_router(websocket.router)

    # Note: Periodic broadcasts will start when server runs via startup
    # event. websocket.start_periodic_broadcasts() shouldn't be called
    # here - needs event loop

    return app


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    config = get_config()

    # Run server
    uvicorn.run(
        "api.server:create_app",
        host=config.api.host or "0.0.0.0",
        port=config.api.port or 8000,
        reload=config.api.reload or False,
        factory=True,
    )
