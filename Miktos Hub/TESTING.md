# Miktos Hub - Testing Guide

## 📋 Overview

Comprehensive test suite for Miktos Hub with 100+ tests covering all layers:
- **Unit Tests**: Individual component testing (fast, isolated)
- **Integration Tests**: Component interaction testing
- **API Tests**: HTTP endpoint testing
- **Performance Tests**: Load and stress testing

---

## 🚀 Quick Start

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html  # View coverage report
```

---

## 🎯 Test Categories

### Unit Tests (Fast)
Test individual components in isolation:

```bash
pytest -m unit
```

**What's tested**:
- DeviceRegistry operations
- SessionManager CRUD
- StreamRouter routing logic
- EventBus pub/sub system

**Run time**: ~2-5 seconds

---

### Integration Tests (Slower)
Test component interactions and workflows:

```bash
pytest -m integration
```

**What's tested**:
- Complete camera discovery → streaming workflow
- Multi-camera scene creation
- Event-driven component communication
- Error recovery scenarios
- Resource cleanup

**Run time**: ~10-30 seconds

---

### API Tests
Test all HTTP endpoints:

```bash
pytest -m api
```

**What's tested**:
- All REST endpoints (/sessions, /cameras, /scenes, /streaming, /health)
- Request validation
- Error handling
- CORS configuration
- OpenAPI documentation

**Run time**: ~5-10 seconds

---

## 🔧 Using the Test Runner

We provide a convenient test runner script:

```bash
# Run specific test types
python run_tests.py unit          # Unit tests only
python run_tests.py integration   # Integration tests only
python run_tests.py api           # API tests only
python run_tests.py fast          # Fast tests only (exclude slow)

# Coverage and reporting
python run_tests.py coverage      # Generate coverage report

# Debugging
python run_tests.py verbose       # Verbose output
python run_tests.py debug         # Run with debugger
python run_tests.py failed        # Re-run only failed tests

# Performance
python run_tests.py parallel      # Run in parallel (faster)
python run_tests.py quick         # Quick smoke test
```

---

## 📊 Test Markers

Tests are marked for easy filtering:

| Marker | Description | Usage |
|--------|-------------|-------|
| `unit` | Fast unit tests | `pytest -m unit` |
| `integration` | Integration tests | `pytest -m integration` |
| `api` | API endpoint tests | `pytest -m api` |
| `slow` | Slow tests (>1s) | `pytest -m slow` |
| `requires_obs` | Needs OBS connection | `pytest -m "not requires_obs"` |
| `requires_hardware` | Needs real hardware | `pytest -m "not requires_hardware"` |

---

## 🎯 Test Coverage Goals

### Current Coverage (Week 4 Start)

```
Core Services:    90%+ target
Services Layer:   80%+ target
Modules:          75%+ target
API Layer:        85%+ target
Overall:          80%+ target
```

### View Coverage Report

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

---

## 🔍 Running Specific Tests

### Run Single Test File

```bash
pytest tests/test_core.py
pytest tests/test_api.py
pytest tests/test_integration.py
```

### Run Single Test Class

```bash
pytest tests/test_core.py::TestDeviceRegistry
pytest tests/test_api.py::TestSessionEndpoints
```

### Run Single Test Function

```bash
pytest tests/test_core.py::TestDeviceRegistry::test_register_device
pytest tests/test_api.py::TestSessionEndpoints::test_create_session
```

### Run Tests Matching Pattern

```bash
pytest -k "device"           # All tests with 'device' in name
pytest -k "session and not delete"  # Session tests except delete
```

---

## 🐛 Debugging Tests

### Verbose Output

```bash
pytest -vv
```

### Show Print Statements

```bash
pytest -s
```

### Stop on First Failure

```bash
pytest -x
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Show Locals on Failure

```bash
pytest -l
```

---

## ⚡ Performance Testing

### Run Performance Tests

```bash
pytest -m slow
```

### Parallel Test Execution

```bash
# Install pytest-xdist first
pip install pytest-xdist

# Run in parallel
pytest -n auto
```

---

## 📝 Test Structure

```
tests/
├── __init__.py              # Package init
├── conftest.py              # Shared fixtures & config
├── test_core.py             # Core services tests
├── test_api.py              # API endpoint tests
├── test_integration.py      # Integration tests
└── test_modules.py          # (Future) Module tests
```

---

## 🎨 Writing New Tests

### Example Unit Test

```python
import pytest
from core import DeviceRegistry
from models import CameraDevice, TransportType

@pytest.mark.unit
def test_my_feature(device_registry, mock_camera):
    """Test description"""
    # Arrange
    device_registry.register(mock_camera)
    
    # Act
    result = device_registry.get(mock_camera.id)
    
    # Assert
    assert result.id == mock_camera.id
```

### Example Integration Test

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow(session_manager, device_registry):
    """Test complete workflow"""
    # Setup
    session = session_manager.create_session(
        session_id="test",
        name="Test"
    )
    
    # Execute workflow
    # ... test steps ...
    
    # Verify
    assert session.state == SessionState.READY
```

### Example API Test

```python
import pytest

@pytest.mark.api
@pytest.mark.asyncio
async def test_endpoint(test_client):
    """Test API endpoint"""
    response = await test_client.post("/api/sessions", json={
        "name": "Test Session"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Session"
```

---

## 🔧 Test Configuration

### pytest.ini

Main configuration file with:
- Test discovery patterns
- Coverage settings
- Markers
- Timeouts
- Logging

### conftest.py

Shared fixtures:
- `device_registry`: Fresh DeviceRegistry
- `session_manager`: Configured SessionManager
- `mock_camera`: Mock camera device
- `mock_cameras`: Multiple mock cameras
- `test_client`: HTTP test client
- Many more...

---

## 📊 Coverage Reports

### Generate HTML Report

```bash
pytest --cov=. --cov-report=html
```

### Generate Terminal Report

```bash
pytest --cov=. --cov-report=term-missing
```

### Generate XML Report (for CI)

```bash
pytest --cov=. --cov-report=xml
```

---

## 🚨 Troubleshooting

### Tests Hanging

```bash
# Add timeout
pytest --timeout=30
```

### Import Errors

```bash
# Ensure project root in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"
pytest
```

### AsyncIO Warnings

Tests use `pytest-asyncio` plugin automatically configured.

### OBS Connection Tests

Skip tests requiring OBS:

```bash
pytest -m "not requires_obs"
```

---

## ✅ Pre-Commit Testing

Before committing code, run:

```bash
# Quick smoke test
python run_tests.py quick

# Full test suite
python run_tests.py coverage
```

---

## 🎯 Test Maintenance

### Keep Tests Fast
- Unit tests should be <0.1s each
- Use mocks for external dependencies
- Mark slow tests with `@pytest.mark.slow`

### Keep Tests Isolated
- Tests should not depend on each other
- Use fixtures for setup/teardown
- Clean up resources in fixtures

### Keep Tests Readable
- Clear test names describing what's tested
- Arrange-Act-Assert structure
- Good docstrings

---

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

---

## 🎉 Test Results Example

```bash
$ pytest -v

tests/test_core.py::TestDeviceRegistry::test_register_device PASSED     [  5%]
tests/test_core.py::TestDeviceRegistry::test_remove_device PASSED       [ 10%]
tests/test_api.py::TestSessionEndpoints::test_create_session PASSED     [ 15%]
tests/test_api.py::TestSessionEndpoints::test_list_sessions PASSED      [ 20%]
tests/test_integration.py::TestCameraToStreamWorkflow PASSED            [ 25%]
...

================================ 100 passed in 15.23s ===============================

Coverage:
    Core:     92%
    Services: 85%
    Modules:  78%
    API:      88%
    Overall:  86%
```

---

**Last Updated**: November 20, 2024
**Test Count**: 100+ tests
**Average Coverage**: 80%+
**Run Time**: ~30 seconds (all tests)
