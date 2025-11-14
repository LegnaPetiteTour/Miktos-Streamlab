"""
Dashboard API for Stream Health Monitoring

Provides REST endpoints and WebSocket for real-time health metrics.
Part of Week 9-10 Dashboard implementation.
"""

import asyncio
import json
from typing import Any, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.health_metrics import HealthAggregator
from src.core.logger import get_logger

logger = get_logger(__name__)


class DashboardAPI:
    """
    FastAPI server for dashboard metrics.

    Provides REST endpoints and WebSocket for real-time updates.
    """

    def __init__(
        self,
        health_aggregator: HealthAggregator,
        host: str = "0.0.0.0",
        port: int = 8765,
    ) -> None:
        """
        Initialize dashboard API.

        Args:
            health_aggregator: HealthAggregator instance
            host: Host to bind to
            port: Port to listen on
        """
        self.health_aggregator = health_aggregator
        self.host = host
        self.port = port

        # Active WebSocket connections
        self.websocket_clients: List[WebSocket] = []

        # Create FastAPI app
        self.app = FastAPI(
            title="Miktos StreamLab Dashboard",
            description="Real-time stream health monitoring",
            version="1.0.0",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify allowed origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Register routes
        self._register_routes()

        # WebSocket broadcast task
        self.broadcast_task: Optional[asyncio.Task[Any]] = None

    def _register_routes(self) -> None:
        """Register API endpoints"""

        @self.app.get("/health")
        async def get_health() -> JSONResponse:
            """Get current health snapshot"""
            try:
                health = self.health_aggregator.get_health_summary()
                return JSONResponse(content=health)
            except Exception as e:
                logger.error(f"Error getting health: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})

        @self.app.get("/metrics")
        async def get_metrics() -> JSONResponse:
            """Get all time series metrics"""
            try:
                metrics = {}
                for name, series in self.health_aggregator.metrics.items():
                    current_val = series.samples[-1].value if series.samples else None
                    metrics[name] = {
                        "unit": series.unit,
                        "current": current_val,
                        "average": series.get_average(),
                        "min_max": series.get_min_max(),
                        "trend": series.get_trend(),
                        "samples": series.get_samples_for_chart(),
                    }
                return JSONResponse(content=metrics)
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})

        @self.app.get("/metrics/{metric_name}")
        async def get_metric(metric_name: str) -> JSONResponse:
            """Get specific metric time series"""
            try:
                if metric_name not in self.health_aggregator.metrics:
                    return JSONResponse(
                        status_code=404,
                        content={"error": f"Metric '{metric_name}' not found"},
                    )

                series = self.health_aggregator.metrics[metric_name]
                current_val = series.samples[-1].value if series.samples else None
                return JSONResponse(
                    content={
                        "name": metric_name,
                        "unit": series.unit,
                        "current": current_val,
                        "average": series.get_average(),
                        "min_max": series.get_min_max(),
                        "trend": series.get_trend(),
                        "samples": series.get_samples_for_chart(),
                    }
                )
            except Exception as e:
                logger.error(f"Error getting metric {metric_name}: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})

        @self.app.get("/export/html")
        async def export_html_report() -> Any:
            """Generate HTML report with current health and metrics"""
            try:
                from fastapi.responses import HTMLResponse

                html = self._generate_html_report()
                return HTMLResponse(content=html)
            except Exception as e:
                logger.error(f"Error generating HTML report: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.websocket_clients.append(websocket)
            client_count = len(self.websocket_clients)
            logger.info(f"WebSocket client connected (total: {client_count})")

            try:
                # Keep connection alive and handle incoming messages
                while True:
                    # Wait for messages (ping/pong for keepalive)
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.websocket_clients.remove(websocket)
                client_count = len(self.websocket_clients)
                logger.info(f"WebSocket client disconnected (total: {client_count})")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.websocket_clients:
                    self.websocket_clients.remove(websocket)

    async def start(self) -> None:
        """Start the dashboard API server"""
        logger.info(f"Starting dashboard API on {self.host}:{self.port}")

        # Start WebSocket broadcast
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())

        # Start uvicorn server
        import uvicorn

        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def stop(self) -> None:
        """Stop the dashboard API server"""
        logger.info("Stopping dashboard API")

        # Stop broadcast task
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass

        # Close all WebSocket connections
        for websocket in self.websocket_clients:
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        self.websocket_clients.clear()

    async def _broadcast_loop(self) -> None:
        """Broadcast health updates to all WebSocket clients"""
        logger.info("Starting WebSocket broadcast loop")

        try:
            while True:
                if self.websocket_clients:
                    try:
                        # Get current health
                        health = self.health_aggregator.get_health_summary()

                        # Convert to JSON (health is already a dict)
                        message = json.dumps(health)

                        # Broadcast to all clients
                        disconnected = []
                        for websocket in self.websocket_clients:
                            try:
                                await websocket.send_text(message)
                            except Exception as e:
                                logger.error(f"Error sending to WebSocket: {e}")
                                disconnected.append(websocket)

                        # Remove disconnected clients
                        for websocket in disconnected:
                            if websocket in self.websocket_clients:
                                self.websocket_clients.remove(websocket)

                    except Exception as e:
                        logger.error(f"Error in broadcast loop: {e}")

                # Broadcast every second
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.info("WebSocket broadcast loop cancelled")
        except Exception as e:
            logger.error(f"Fatal error in broadcast loop: {e}")

    def _generate_html_report(self) -> str:
        """Generate HTML report with current health and metrics"""
        from datetime import datetime

        health = self.health_aggregator.get_health_summary()
        metrics = self.health_aggregator.get_all_metrics()

        # Build HTML report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = health.get("status", "unknown")
        streaming = health.get("streaming", False)

        # Status color
        status_colors = {
            "healthy": "#4caf50",
            "warning": "#ff9800",
            "critical": "#f44336",
            "unknown": "#9e9e9e",
        }
        status_color = status_colors.get(status, "#9e9e9e")

        # fmt: off
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Miktos StreamLab - Health Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;  # noqa: E501
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .report-header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            color: white;
            font-weight: 500;
            margin-top: 15px;
            background: {status_color};
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-name {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: 600;
            color: #333;
        }}
        .metric-unit {{
            font-size: 16px;
            color: #999;
            margin-left: 5px;
        }}
        .metric-stats {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #666;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #999;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1>🎥 Miktos StreamLab - Health Report</h1>
        <div class="timestamp">Generated: {timestamp}</div>
        <div class="status-badge">{status.upper()}</div>
        <div class="status-badge" style="background: {'#4caf50' if streaming else '#9e9e9e'}">  # noqa: E501
            {'STREAMING' if streaming else 'STOPPED'}
        </div>
    </div>

    <div class="metrics-grid">
"""

        # Add metric cards
        for name, series in metrics.items():
            current = series.samples[-1].value if series.samples else 0
            avg = series.get_average()
            min_val, max_val = series.get_min_max()
            trend = series.get_trend()

            # Trend emoji
            if trend == "rising":
                trend_emoji = "📈"
            elif trend == "falling":
                trend_emoji = "📉"
            else:
                trend_emoji = "➡️"

            html += f"""
        <div class="metric-card">
            <div class="metric-name">{name.replace('_', ' ')}</div>
            <div class="metric-value">
                {current:.1f}
                <span class="metric-unit">{series.unit}</span>
            </div>
            <div class="metric-stats">
                <div class="stat-row">
                    <span>Average:</span>
                    <span>{avg:.1f} {series.unit}</span>
                </div>
                <div class="stat-row">
                    <span>Range:</span>
                    <span>{min_val:.1f} - {max_val:.1f} {series.unit}</span>
                </div>
                <div class="stat-row">
                    <span>Trend:</span>
                    <span>{trend_emoji} {trend}</span>
                </div>
            </div>
        </div>
"""

        html += """
    </div>

    <div class="footer">
        <p>Miktos StreamLab Dashboard - Week 9-10 Implementation</p>
        <p>streaming Streaming Platform</p>
    </div>
</body>
</html>
"""
        # fmt: on
        return html


async def run_dashboard_api(
    health_aggregator: HealthAggregator,
    host: str = "0.0.0.0",
    port: int = 8765,
) -> None:
    """
    Run the dashboard API server.

    Args:
        health_aggregator: HealthAggregator instance
        host: Host to bind to
        port: Port to listen on
    """
    api = DashboardAPI(health_aggregator, host, port)
    await api.start()
