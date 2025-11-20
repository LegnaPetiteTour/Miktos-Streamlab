"""
Miktos Hub Test Suite

This package contains comprehensive tests for all layers of the Miktos Hub.

Test Organization:
    - test_core.py: Core service tests (DeviceRegistry, SessionManager, etc.)
    - test_api.py: API endpoint tests
    - test_integration.py: Integration tests for complete workflows
    
Markers:
    - @pytest.mark.unit: Unit tests (fast, isolated)
    - @pytest.mark.integration: Integration tests (slower, component interaction)
    - @pytest.mark.api: API endpoint tests
    - @pytest.mark.slow: Tests that take >1 second
    - @pytest.mark.requires_obs: Tests requiring OBS connection
    - @pytest.mark.requires_hardware: Tests requiring real hardware

Running Tests:
    # All tests
    pytest
    
    # Specific test type
    pytest -m unit
    pytest -m integration
    pytest -m api
    
    # With coverage
    pytest --cov=. --cov-report=html
    
    # Using the runner script
    python run_tests.py unit
    python run_tests.py coverage
"""
