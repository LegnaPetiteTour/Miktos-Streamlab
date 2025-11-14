#!/bin/bash
# Run OBS Controller Tests
# ========================
# Execute this script to run the OBS controller test suite

echo "🧪 Running OBS Controller Tests..."
echo "=================================="
echo ""

# Activate virtual environment
source venv/bin/activate

# Run tests with verbose output
python -m pytest tests/test_obs_controller.py -v --tb=short

# Show test coverage for OBS controller
echo ""
echo "📊 Test Coverage for OBS Controller:"
echo "===================================="
python -m pytest tests/test_obs_controller.py --cov=src.obs_controller --cov-report=term-missing

echo ""
echo "✅ Test run complete!"
