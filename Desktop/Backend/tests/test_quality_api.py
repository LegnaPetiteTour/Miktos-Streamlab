"""
Tests for Quality API
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Mock imports to avoid OBS dependencies
import sys
sys.path.insert(0, '/Users/atorrella/Desktop/Miktos Streamlab/src')


@pytest.fixture
def mock_quality_components():
    """Create mock quality components"""
    analyzer = MagicMock()
    analyzer.analyze_frame.return_value = MagicMock(
        to_dict=lambda: {
            'overall_score': 85.0,
            'status': 'good',
            'scores': {
                'exposure': {'score': 90.0, 'status': 'good'},
                'focus': {'score': 85.0, 'status': 'good'},
                'color_balance': {'score': 80.0, 'status': 'good'},
                'noise': {'score': 85.0, 'status': 'good'},
                'sharpness': {'score': 85.0, 'status': 'good'}
            },
            'recommendations': []
        }
    )

    enhancement = AsyncMock()
    enhancement.auto_enhance = AsyncMock(
        return_value={
            'brightness': 0.1,
            'contrast': 0.15,
            'saturation': 0.1,
            'sharpness': 0.3
        }
    )

    preset_mgr = MagicMock()
    preset_mgr.get_preset.return_value = MagicMock(
        to_dict=lambda: {
            'name': 'professional',
            'description': 'Professional broadcast preset',
            'category': 'professional',
            'color_correction': {
                'brightness': 0.1,
                'contrast': 0.15,
                'saturation': 0.1,
                'gamma': 1.0
            },
            'sharpness': 0.3,
            'noise_reduction': True
        }
    )
    preset_mgr.list_presets.return_value = [
        MagicMock(
            to_dict=lambda: {
                'name': 'professional',
                'category': 'professional'
            }
        ),
        MagicMock(
            to_dict=lambda: {
                'name': 'gaming',
                'category': 'gaming'
            }
        )
    ]
    preset_mgr.get_preset_categories.return_value = [
        'professional',
        'gaming',
        'creative'
    ]
    preset_mgr.create_preset_from_current.return_value = MagicMock(
        to_dict=lambda: {
            'name': 'custom',
            'category': 'custom'
        }
    )
    preset_mgr.delete_preset.return_value = True

    nvidia = MagicMock()
    nvidia.available = True
    nvidia.apply_noise_removal.return_value = True
    nvidia.apply_background_blur.return_value = True
    nvidia.apply_auto_frame.return_value = True
    nvidia.apply_eye_contact.return_value = True
    nvidia.get_gpu_info.return_value = {
        'available': True,
        'gpu_name': 'NVIDIA RTX 3080'
    }

    filters = AsyncMock()
    filters.apply_color_correction = AsyncMock()
    filters.apply_sharpness = AsyncMock()
    filters.reset_filters = AsyncMock()

    return {
        'analyzer': analyzer,
        'enhancement': enhancement,
        'presets': preset_mgr,
        'nvidia': nvidia,
        'filters': filters
    }


@pytest.fixture
def test_app(mock_quality_components):
    """Create test FastAPI app"""
    from api.quality_api import QualityAPI  # type: ignore[import-not-found]

    app = FastAPI()

    quality_api = QualityAPI(
        quality_analyzer=mock_quality_components['analyzer'],
        enhancement_engine=mock_quality_components['enhancement'],
        preset_manager=mock_quality_components['presets'],
        nvidia_broadcast=mock_quality_components['nvidia'],
        filter_controller=mock_quality_components['filters']
    )

    app.include_router(quality_api.router)

    return app


def test_analyze_quality(test_app):
    """Test quality analysis endpoint"""
    client = TestClient(test_app)

    response = client.post(
        "/quality/analyze",
        json={"source_name": "Camera"}
    )

    assert response.status_code == 200
    data = response.json()
    assert 'overall_score' in data
    assert data['overall_score'] == 85.0
    assert data['status'] == 'good'


def test_auto_enhance(test_app):
    """Test auto-enhance endpoint"""
    client = TestClient(test_app)

    response = client.post(
        "/quality/auto-enhance",
        json={
            "source_name": "Camera",
            "preset": "professional"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'adjustments_applied' in data


def test_apply_preset(test_app):
    """Test apply preset endpoint"""
    client = TestClient(test_app)

    response = client.post(
        "/quality/apply-preset",
        json={
            "source_name": "Camera",
            "preset_name": "professional"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'preset' in data


def test_apply_preset_not_found(test_app, mock_quality_components):
    """Test apply preset with invalid name"""
    client = TestClient(test_app)

    # Make preset not found
    mock_quality_components['presets'].get_preset.return_value = None

    response = client.post(
        "/quality/apply-preset",
        json={
            "source_name": "Camera",
            "preset_name": "invalid"
        }
    )

    assert response.status_code == 404


def test_adjust_quality(test_app):
    """Test quality adjustment endpoint"""
    client = TestClient(test_app)

    # Test each adjustment type
    adjustments = [
        ('brightness', 0.2),
        ('contrast', 0.15),
        ('saturation', 0.1),
        ('sharpness', 0.3)
    ]

    for adj_type, value in adjustments:
        response = client.post(
            "/quality/adjust",
            json={
                "source_name": "Camera",
                "adjustment_type": adj_type,
                "value": value
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['adjustment_type'] == adj_type
        assert data['value'] == value


def test_adjust_quality_invalid_type(test_app):
    """Test quality adjustment with invalid type"""
    client = TestClient(test_app)

    response = client.post(
        "/quality/adjust",
        json={
            "source_name": "Camera",
            "adjustment_type": "invalid",
            "value": 0.5
        }
    )

    assert response.status_code == 400


def test_reset_adjustments(test_app):
    """Test reset adjustments endpoint"""
    client = TestClient(test_app)

    response = client.post(
        "/quality/reset",
        json={"source_name": "Camera"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True


def test_save_preset(test_app):
    """Test save preset endpoint"""
    client = TestClient(test_app)

    response = client.post(
        "/quality/save-preset",
        json={
            "name": "my_preset",
            "description": "My custom preset",
            "category": "custom",
            "source_name": "Camera"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'preset' in data


def test_list_presets(test_app):
    """Test list presets endpoint"""
    client = TestClient(test_app)

    response = client.get("/quality/presets")

    assert response.status_code == 200
    data = response.json()
    assert 'presets' in data
    assert 'categories' in data
    assert len(data['presets']) == 2


def test_list_presets_filtered(test_app):
    """Test list presets with category filter"""
    client = TestClient(test_app)

    response = client.get(
        "/quality/presets?category=professional"
    )

    assert response.status_code == 200


def test_get_preset(test_app):
    """Test get preset endpoint"""
    client = TestClient(test_app)

    response = client.get("/quality/presets/professional")

    assert response.status_code == 200
    data = response.json()
    assert data['name'] == 'professional'


def test_get_preset_not_found(test_app, mock_quality_components):
    """Test get preset with invalid name"""
    client = TestClient(test_app)

    # Make preset not found
    mock_quality_components['presets'].get_preset.return_value = None

    response = client.get("/quality/presets/invalid")

    assert response.status_code == 404


def test_delete_preset(test_app):
    """Test delete preset endpoint"""
    client = TestClient(test_app)

    response = client.delete("/quality/presets/custom")

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True


def test_delete_preset_failed(test_app, mock_quality_components):
    """Test delete preset failure"""
    client = TestClient(test_app)

    # Make delete fail
    mock_quality_components['presets'].delete_preset.return_value = False

    response = client.delete("/quality/presets/builtin")

    assert response.status_code == 400


def test_configure_nvidia(test_app):
    """Test NVIDIA configuration endpoint"""
    client = TestClient(test_app)

    # Test each effect
    effects = [
        ('noise_removal', 80),
        ('background_blur', 60),
        ('auto_frame', 1),
        ('eye_contact', 1)
    ]

    for effect, intensity in effects:
        response = client.post(
            "/quality/nvidia",
            json={
                "source_name": "Camera",
                "effect": effect,
                "intensity": intensity
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['effect'] == effect


def test_configure_nvidia_not_available(
    test_app,
    mock_quality_components
):
    """Test NVIDIA config when not available"""
    client = TestClient(test_app)

    # Make NVIDIA unavailable
    mock_quality_components['nvidia'].available = False

    response = client.post(
        "/quality/nvidia",
        json={
            "source_name": "Camera",
            "effect": "noise_removal",
            "intensity": 80
        }
    )

    assert response.status_code == 400


def test_configure_nvidia_invalid_effect(test_app):
    """Test NVIDIA config with invalid effect"""
    client = TestClient(test_app)

    response = client.post(
        "/quality/nvidia",
        json={
            "source_name": "Camera",
            "effect": "invalid",
            "intensity": 50
        }
    )

    assert response.status_code == 400


def test_nvidia_status(test_app):
    """Test NVIDIA status endpoint"""
    client = TestClient(test_app)

    response = client.get("/quality/nvidia/status")

    assert response.status_code == 200
    data = response.json()
    assert 'available' in data
    assert data['available'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
