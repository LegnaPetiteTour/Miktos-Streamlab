"""
API Routes Package
Exports all route routers for FastAPI application.
"""
from .sessions import router as sessions_router
from .cameras import router as cameras_router
from .scenes import router as scenes_router
from .streaming import router as streaming_router
from .health import router as health_router

__all__ = [
    "sessions_router",
    "cameras_router",
    "scenes_router",
    "streaming_router",
    "health_router"
]
