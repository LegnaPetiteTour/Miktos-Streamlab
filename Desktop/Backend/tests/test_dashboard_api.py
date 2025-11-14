"""
Tests for Dashboard API

Tests REST endpoints, WebSocket, and health aggregation.
Part of Week 9-10 dashboard implementation.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.api.dashboard_api import DashboardAPI
from src.core.health_metrics import HealthAggregator, StreamHealth


@pytest.fixture
def mock_obs_controller():
    """Mock OBS controller"""
    mock = Mock()
    mock.get_stats = Mock(
        return_value={
            "streaming": True,
            "recording": False,
            "fps": 30.0,
            "kbits_per_sec": 3000,
            "num_total_frames": 9000,
            "num_dropped_frames": 50,
            "cpu_usage": 45.5,
            "memory_usage": 512.0,
        }
    )
    return mock


@pytest.fixture
def mock_egress_manager():
    """Mock egress manager"""
    mock = Mock()
    mock.get_active_destinations = Mock(return_value=["rtmp://stream.example.com"])
    return mock


@pytest.fixture
def mock_failover():
    """Mock failover controller"""
    mock = Mock()
    mock.get_current_state = Mock(return_value={"state": "normal", "failover_active": False})
    return mock


@pytest.fixture
def health_aggregator(mock_obs_controller, mock_egress_manager, mock_failover):
    """Create HealthAggregator instance"""
    aggregator = HealthAggregator(
        obs_controller=mock_obs_controller,
        egress_manager=mock_egress_manager,
        failover_controller=mock_failover,
        poll_interval=1.0,
    )

    # Add some test data to metrics
    aggregator.metrics["bitrate"].add(3000.0)
    aggregator.metrics["fps"].add(30.0)
    aggregator.metrics["cpu_usage"].add(45.5)
    aggregator.metrics["drop_percentage"].add(0.5)

    # Set current health
    aggregator.current_health = StreamHealth(
        streaming=True,
        uptime_seconds=120,
        bitrate_kbps=3000,
        fps=30.0,
        dropped_frames=50,
        total_frames=10000,
        cpu_usage=45.5,
        memory_mb=512.0,
        rtt_ms=0.0,
        jitter_ms=0.0,
        packet_loss_pct=0.0,
        destinations=[{"url": "rtmp://stream.example.com", "status": "active"}],
        failover_state="normal",
        failover_active=False,
    )

    return aggregator


@pytest.fixture
def dashboard_api(health_aggregator):
    """Create DashboardAPI instance"""
    api = DashboardAPI(health_aggregator, host="127.0.0.1", port=8765)
    return api


@pytest.fixture
def client(dashboard_api):
    """Create test client"""
    return TestClient(dashboard_api.app)


def test_get_health_endpoint(client):
    """Test GET /health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "streaming" in data
    assert data["streaming"] is True


def test_get_metrics_endpoint(client):
    """Test GET /metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200

    data = response.json()
    assert "bitrate" in data
    assert "fps" in data
    assert "cpu_usage" in data
    assert "drop_percentage" in data

    # Check metric structure
    bitrate = data["bitrate"]
    assert "unit" in bitrate
    assert "current" in bitrate
    assert "average" in bitrate
    assert "min_max" in bitrate
    assert "trend" in bitrate
    assert bitrate["unit"] == "kbps"


def test_get_metric_by_name(client):
    """Test GET /metrics/{metric_name} endpoint"""
    response = client.get("/metrics/bitrate")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "bitrate"
    assert data["unit"] == "kbps"
    assert data["current"] == 3000.0


def test_get_metric_not_found(client):
    """Test GET /metrics/{metric_name} with invalid metric"""
    response = client.get("/metrics/invalid_metric")
    assert response.status_code == 404

    data = response.json()
    assert "error" in data


def test_html_export_endpoint(client):
    """Test GET /export/html endpoint"""
    response = client.get("/export/html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    html = response.text
    assert "<!DOCTYPE html>" in html
    assert "Miktos StreamLab" in html
    assert "Health Report" in html


@pytest.mark.asyncio
async def test_websocket_connection(dashboard_api):
    """Test WebSocket connection"""
    from fastapi.testclient import TestClient

    client = TestClient(dashboard_api.app)

    with client.websocket_connect("/ws") as websocket:
        # Should accept connection
        assert len(dashboard_api.websocket_clients) == 1

        # Send ping
        websocket.send_text("ping")

    # Should disconnect
    assert len(dashboard_api.websocket_clients) == 0


def test_dashboard_api_initialization():
    """Test DashboardAPI initialization"""
    mock_aggregator = Mock()
    api = DashboardAPI(mock_aggregator, host="0.0.0.0", port=9000)

    assert api.health_aggregator == mock_aggregator
    assert api.host == "0.0.0.0"
    assert api.port == 9000
    assert api.websocket_clients == []
    assert api.app is not None


def test_cors_middleware(dashboard_api):
    """Test CORS middleware is configured"""
    # Check that CORS middleware is in the middleware stack
    middleware_classes = [m.cls.__name__ for m in dashboard_api.app.user_middleware]
    assert "CORSMiddleware" in middleware_classes
