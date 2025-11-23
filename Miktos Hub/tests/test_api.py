"""
API Endpoint Tests

Tests all REST API endpoints and WebSocket functionality
"""
import pytest


# ============================================================================
# HEALTH ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
class TestHealthEndpoints:
    """Test suite for health monitoring endpoints"""

    @pytest.mark.asyncio
    async def test_ping_endpoint(self, test_client):
        """Test simple ping endpoint"""
        response = await test_client.get("/api/health/ping")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "pong"
        assert "timestamp" in data["data"]

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, test_client):
        """Test complete health check endpoint"""
        response = await test_client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        assert "overall_status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "cameras" in data
        assert isinstance(data["components"], list)

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, test_client):
        """Test system metrics endpoint"""
        response = await test_client.get("/api/health/metrics")

        assert response.status_code == 200
        data = response.json()

        assert "cpu_usage_percent" in data
        assert "memory_usage_percent" in data
        assert "disk_usage_percent" in data
        assert "active_sessions" in data
        assert "timestamp" in data


# ============================================================================
# SESSION ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
class TestSessionEndpoints:
    """Test suite for session management endpoints"""

    @pytest.mark.asyncio
    async def test_create_session(self, test_client):
        """Test creating a new session"""
        response = await test_client.post("/api/sessions/", json={
            "name": "Test Session",
            "description": "Test description"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Test Session"
        assert "session_id" in data
        assert data["state"] == "preparing"

    @pytest.mark.asyncio
    async def test_create_session_minimal(self, test_client):
        """Test creating session with only required fields"""
        response = await test_client.post("/api/sessions/", json={
            "name": "Minimal Session"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Session"

    @pytest.mark.asyncio
    async def test_create_session_validation_error(self, test_client):
        """Test creating session with invalid data"""
        response = await test_client.post("/api/sessions/", json={
            # Missing required 'name' field
            "description": "No name"
        })

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_list_sessions(self, test_client):
        """Test listing all sessions"""
        # Create a few sessions
        await test_client.post("/api/sessions/", json={"name": "Session 1"})
        await test_client.post("/api/sessions/", json={"name": "Session 2"})

        response = await test_client.get("/api/sessions/")

        assert response.status_code == 200
        data = response.json()

        assert "sessions" in data
        assert "total" in data
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_get_session(self, test_client):
        """Test getting a specific session"""
        # Create session
        create_response = await test_client.post("/api/sessions/", json={
            "name": "Get Test Session"
        })
        session_id = create_response.json()["session_id"]

        # Get session
        response = await test_client.get(f"/api/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["name"] == "Get Test Session"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, test_client):
        """Test getting a session that doesn't exist"""
        response = await test_client.get("/api/sessions/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_session(self, test_client):
        """Test starting a session"""
        # Create session
        create_response = await test_client.post("/api/sessions/", json={
            "name": "Start Test"
        })
        session_id = create_response.json()["session_id"]

        # Start session
        response = await test_client.post(f"/api/sessions/{session_id}/start")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_stop_session(self, test_client):
        """Test stopping a session"""
        # Create and start session
        create_response = await test_client.post("/api/sessions/", json={
            "name": "Stop Test"
        })
        session_id = create_response.json()["session_id"]
        await test_client.post(f"/api/sessions/{session_id}/start")

        # Stop session
        response = await test_client.post(f"/api/sessions/{session_id}/stop")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_delete_session(self, test_client):
        """Test deleting a session"""
        # Create session
        create_response = await test_client.post("/api/sessions/", json={
            "name": "Delete Test"
        })
        session_id = create_response.json()["session_id"]

        # Delete session
        response = await test_client.delete(f"/api/sessions/{session_id}")

        assert response.status_code == 200

        # Verify deleted
        get_response = await test_client.get(f"/api/sessions/{session_id}")
        assert get_response.status_code == 404


# ============================================================================
# CAMERA ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
class TestCameraEndpoints:
    """Test suite for camera management endpoints"""

    @pytest.mark.asyncio
    async def test_list_cameras(self, test_client):
        """Test listing all cameras"""
        response = await test_client.get("/api/cameras")

        assert response.status_code == 200
        data = response.json()

        assert "cameras" in data
        assert "total" in data
        assert isinstance(data["cameras"], list)

    @pytest.mark.asyncio
    async def test_list_discovered_cameras(self, test_client):
        """Test listing discovered cameras"""
        response = await test_client.get("/api/cameras/discovered")

        assert response.status_code == 200
        data = response.json()

        assert "cameras" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_manual_camera_pairing(self, test_client):
        """Test manually pairing a camera via QR code"""
        response = await test_client.post("/api/cameras/pair", json={
            "camera_id": "manual-camera-1",
            "pairing_code": "TEST-1234-ABCD"
        })

        # Will fail without actual discovery, but should validate request
        assert response.status_code in [200, 404, 503]


# ============================================================================
# SCENE ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
class TestSceneEndpoints:
    """Test suite for scene management endpoints"""

    @pytest.mark.asyncio
    async def test_list_scenes_empty(self, test_client):
        """Test listing scenes when none exist"""
        response = await test_client.get("/api/scenes", params={
            "session_id": "nonexistent-session"
        })

        # Should return 404 for nonexistent session
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_scene_validation(self, test_client):
        """Test scene creation validation"""
        response = await test_client.post("/api/scenes", json={
            # Missing required fields
            "name": "Test Scene"
        })

        assert response.status_code == 422  # Validation error


# ============================================================================
# STREAMING ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
class TestStreamingEndpoints:
    """Test suite for streaming control endpoints"""

    @pytest.mark.asyncio
    async def test_configure_destinations(self, test_client):
        """Test configuring streaming destinations"""
        # Create session first
        session_response = await test_client.post("/api/sessions", json={
            "name": "Streaming Test"
        })
        session_id = session_response.json()["id"]

        # Configure destinations
        response = await test_client.post("/api/streaming/destinations", json={
            "session_id": session_id,
            "destinations": [
                {
                    "platform": "youtube",
                    "stream_key": "test-key-123",
                    "label": "YouTube EN"
                }
            ]
        })

        # May fail without actual egress setup, but should validate
        assert response.status_code in [200, 404, 503]

    @pytest.mark.asyncio
    async def test_start_streaming_validation(self, test_client):
        """Test streaming start validation"""
        response = await test_client.post("/api/streaming/start", json={
            "session_id": "nonexistent-session"
        })

        # Should fail for nonexistent session
        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_get_streaming_health_nonexistent(self, test_client):
        """Test getting health for nonexistent session"""
        response = await test_client.get("/api/streaming/health", params={
            "session_id": "nonexistent"
        })

        assert response.status_code == 404


# ============================================================================
# ROOT ENDPOINT TEST
# ============================================================================

@pytest.mark.api
class TestRootEndpoint:
    """Test suite for root endpoint"""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, test_client):
        """Test API root endpoint"""
        response = await test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Miktos Hub API"
        assert "version" in data
        assert "status" in data
        assert "docs" in data
        assert "health" in data


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.api
class TestErrorHandling:
    """Test suite for API error handling"""

    @pytest.mark.asyncio
    async def test_404_on_invalid_endpoint(self, test_client):
        """Test 404 response for invalid endpoint"""
        response = await test_client.get("/api/invalid/endpoint")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_json_request(self, test_client):
        """Test handling of invalid JSON in request"""
        response = await test_client.post(
            "/api/sessions",
            content="invalid json{{{",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, test_client):
        """Test 405 response for wrong HTTP method"""
        response = await test_client.put("/api/health/ping")

        assert response.status_code == 405


# ============================================================================
# CORS TESTS
# ============================================================================

@pytest.mark.api
class TestCORS:
    """Test suite for CORS configuration"""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, test_client):
        """Test that CORS headers are present"""
        response = await test_client.options("/api/health")

        assert response.status_code == 200
        # Check for CORS headers
        headers_lower = [h.lower() for h in response.headers]
        assert "access-control-allow-origin" in headers_lower


# ============================================================================
# OPENAPI DOCUMENTATION TESTS
# ============================================================================

@pytest.mark.api
class TestOpenAPI:
    """Test suite for OpenAPI documentation"""

    @pytest.mark.asyncio
    async def test_openapi_json(self, test_client):
        """Test OpenAPI JSON schema is accessible"""
        response = await test_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    @pytest.mark.asyncio
    async def test_docs_ui_accessible(self, test_client):
        """Test that Swagger UI is accessible"""
        response = await test_client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
