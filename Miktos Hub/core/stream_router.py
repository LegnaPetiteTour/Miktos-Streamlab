"""
Stream Router - Routes cameras to scenes to outputs

This service manages the flow of video/audio streams through the system.
It tracks which cameras feed into which scenes, and which scenes output to which destinations.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

from models.camera import CameraDevice
from models.scene import Scene
from models.destination import StreamDestination

logger = logging.getLogger(__name__)


class RouteState(Enum):
    """State of a stream route"""
    IDLE = "idle"
    ACTIVE = "active"
    ERROR = "error"


@dataclass
class Route:
    """Represents a stream route from camera → scene → outputs"""
    id: str
    source_camera_id: str
    target_scene_id: str
    target_output_ids: List[str]
    state: RouteState
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class RouteConfiguration:
    """Configuration for a stream route"""
    camera_id: str
    scene_id: str
    output_ids: List[str]
    priority: int = 0
    enabled: bool = True


class StreamRouter:
    """
    Manages routing of streams from cameras → scenes → outputs
    
    This is the central "switchboard" that connects all pieces.
    It ensures proper signal flow and handles conflicts/priorities.
    """
    
    def __init__(self):
        # Active routes indexed by route_id
        self._routes: Dict[str, Route] = {}
        
        # Quick lookups for finding routes
        self._camera_routes: Dict[str, Set[str]] = {}  # camera_id → set of route_ids
        self._scene_routes: Dict[str, Set[str]] = {}   # scene_id → set of route_ids
        self._output_routes: Dict[str, Set[str]] = {}  # output_id → set of route_ids
        
        logger.info("StreamRouter initialized")
    
    def attach_camera_to_scene(
        self,
        camera: CameraDevice,
        scene: Scene,
        config: Optional[Dict] = None
    ) -> Route:
        """
        Route a camera's stream into a scene
        
        Args:
            camera: Source camera device
            scene: Target scene
            config: Optional routing config (position, crop, etc.)
            
        Returns:
            Created route
        """
        route_id = f"route_{camera.id}_to_{scene.id}"
        
        # Check if route already exists
        if route_id in self._routes:
            logger.warning(f"Route {route_id} already exists, returning existing")
            return self._routes[route_id]
        
        # Create route
        route = Route(
            id=route_id,
            source_camera_id=camera.id,
            target_scene_id=scene.id,
            target_output_ids=[],  # Will be set when scene is routed to outputs
            state=RouteState.IDLE,
            metadata=config or {}
        )
        
        # Store route
        self._routes[route_id] = route
        
        # Update indexes
        if camera.id not in self._camera_routes:
            self._camera_routes[camera.id] = set()
        self._camera_routes[camera.id].add(route_id)
        
        if scene.id not in self._scene_routes:
            self._scene_routes[scene.id] = set()
        self._scene_routes[scene.id].add(route_id)
        
        logger.info(f"Created route: {camera.id} → {scene.id}")
        return route
    
    def detach_camera_from_scene(self, camera_id: str, scene_id: str) -> bool:
        """
        Remove a camera from a scene
        
        Args:
            camera_id: Camera to detach
            scene_id: Scene to detach from
            
        Returns:
            True if route was removed
        """
        route_id = f"route_{camera_id}_to_{scene_id}"
        
        if route_id not in self._routes:
            logger.warning(f"Route {route_id} not found")
            return False
        
        # Remove route
        route = self._routes.pop(route_id)
        
        # Update indexes
        if camera_id in self._camera_routes:
            self._camera_routes[camera_id].discard(route_id)
            if not self._camera_routes[camera_id]:
                del self._camera_routes[camera_id]
        
        if scene_id in self._scene_routes:
            self._scene_routes[scene_id].discard(route_id)
            if not self._scene_routes[scene_id]:
                del self._scene_routes[scene_id]
        
        # Remove from output indexes
        for output_id in route.target_output_ids:
            if output_id in self._output_routes:
                self._output_routes[output_id].discard(route_id)
        
        logger.info(f"Removed route: {camera_id} → {scene_id}")
        return True
    
    def route_scene_to_output(
        self,
        scene: Scene,
        destination: StreamDestination,
        config: Optional[Dict] = None
    ) -> List[Route]:
        """
        Route a scene to an output destination
        
        This updates all routes that feed into the scene to include the output.
        
        Args:
            scene: Scene to output
            destination: Target destination
            config: Optional output config
            
        Returns:
            List of affected routes
        """
        # Find all routes that target this scene
        scene_route_ids = self._scene_routes.get(scene.id, set())
        affected_routes = []
        
        for route_id in scene_route_ids:
            route = self._routes[route_id]
            
            # Add output to route if not already present
            if destination.id not in route.target_output_ids:
                route.target_output_ids.append(destination.id)
                
                # Update output index
                if destination.id not in self._output_routes:
                    self._output_routes[destination.id] = set()
                self._output_routes[destination.id].add(route_id)
                
                affected_routes.append(route)
        
        logger.info(f"Routed scene {scene.id} to output {destination.id}, affected {len(affected_routes)} routes")
        return affected_routes
    
    def unroute_scene_from_output(self, scene_id: str, destination_id: str) -> List[Route]:
        """
        Remove a scene from an output destination
        
        Args:
            scene_id: Scene to unroute
            destination_id: Destination to remove from
            
        Returns:
            List of affected routes
        """
        scene_route_ids = self._scene_routes.get(scene_id, set())
        affected_routes = []
        
        for route_id in scene_route_ids:
            route = self._routes[route_id]
            
            if destination_id in route.target_output_ids:
                route.target_output_ids.remove(destination_id)
                
                # Update output index
                if destination_id in self._output_routes:
                    self._output_routes[destination_id].discard(route_id)
                    if not self._output_routes[destination_id]:
                        del self._output_routes[destination_id]
                
                affected_routes.append(route)
        
        logger.info(f"Unrouted scene {scene_id} from output {destination_id}, affected {len(affected_routes)} routes")
        return affected_routes
    
    def get_routes_for_camera(self, camera_id: str) -> List[Route]:
        """Get all routes involving a camera"""
        route_ids = self._camera_routes.get(camera_id, set())
        return [self._routes[rid] for rid in route_ids if rid in self._routes]
    
    def get_routes_for_scene(self, scene_id: str) -> List[Route]:
        """Get all routes targeting a scene"""
        route_ids = self._scene_routes.get(scene_id, set())
        return [self._routes[rid] for rid in route_ids if rid in self._routes]
    
    def get_routes_for_output(self, output_id: str) -> List[Route]:
        """Get all routes going to an output"""
        route_ids = self._output_routes.get(output_id, set())
        return [self._routes[rid] for rid in route_ids if rid in self._routes]
    
    def get_active_routes(self) -> List[Route]:
        """Get all active routes"""
        return [
            route for route in self._routes.values()
            if route.state == RouteState.ACTIVE
        ]
    
    def activate_route(self, route_id: str) -> bool:
        """Mark a route as active"""
        if route_id not in self._routes:
            return False
        
        self._routes[route_id].state = RouteState.ACTIVE
        logger.info(f"Activated route: {route_id}")
        return True
    
    def deactivate_route(self, route_id: str) -> bool:
        """Mark a route as inactive"""
        if route_id not in self._routes:
            return False
        
        self._routes[route_id].state = RouteState.IDLE
        logger.info(f"Deactivated route: {route_id}")
        return True
    
    def clear_all_routes(self) -> int:
        """
        Remove all routes
        
        Returns:
            Number of routes cleared
        """
        count = len(self._routes)
        self._routes.clear()
        self._camera_routes.clear()
        self._scene_routes.clear()
        self._output_routes.clear()
        logger.info(f"Cleared {count} routes")
        return count
    
    def get_routing_graph(self) -> Dict:
        """
        Get a visual representation of the routing graph
        
        Returns:
            Dictionary showing cameras → scenes → outputs
        """
        graph = {
            "cameras": {},
            "scenes": {},
            "outputs": {}
        }
        
        # Build graph from routes
        for route in self._routes.values():
            # Camera → Scene connections
            if route.source_camera_id not in graph["cameras"]:
                graph["cameras"][route.source_camera_id] = []
            graph["cameras"][route.source_camera_id].append(route.target_scene_id)
            
            # Scene → Output connections
            if route.target_scene_id not in graph["scenes"]:
                graph["scenes"][route.target_scene_id] = []
            graph["scenes"][route.target_scene_id].extend(route.target_output_ids)
        
        # Outputs (destinations for each output)
        for output_id in self._output_routes.keys():
            graph["outputs"][output_id] = list(self._output_routes[output_id])
        
        return graph
