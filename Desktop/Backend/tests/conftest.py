"""
Test fixtures for Miktos StreamLab tests
"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'obs': {
            'host': 'localhost',
            'port': 4455,
            'password': 'test_password'
        },
        'stream': {
            'youtube_en_key': 'test_en_key',
            'youtube_fr_key': 'test_fr_key',
            'bitrate': 4500,
            'resolution': '1920x1080',
            'fps': 30,
            'audio_bitrate': 128
        },
        'ai': {
            'whisper_model': 'base',
            'enable_live_captions': True,
            'caption_language': 'auto'
        }
    }


@pytest.fixture
def mock_network_metrics():
    """Mock network metrics"""
    from core.network import NetworkMetrics, NetworkStatus
    return NetworkMetrics(
        upload_speed=8.5,
        download_speed=50.0,
        latency=25.0,
        jitter=5.0,
        packet_loss=0.0,
        status=NetworkStatus.EXCELLENT,
        timestamp=1234567890.0
    )


@pytest.fixture
def sample_transcript_segments():
    """Sample transcript segments for testing"""
    from core.transcription import TranscriptSegment
    return [
        TranscriptSegment(
            start=0.0,
            end=3.5,
            text="Hello, this is a test.",
            language="en"
        ),
        TranscriptSegment(
            start=3.5,
            end=7.0,
            text="Bonjour, ceci est un test.",
            language="fr"
        ),
        TranscriptSegment(
            start=7.0,
            end=10.0,
            text="This is bilingual content.",
            language="en"
        )
    ]
