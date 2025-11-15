"""
Tests for audio monitoring.
"""

import pytest

from core.preflight.audio import AudioCheckResult, AudioLevelSample, AudioMonitor


class TestAudioDataClasses:
    """Test audio data classes."""

    def test_audio_level_sample_creation(self):
        """Test creating audio level sample."""
        sample = AudioLevelSample(
            source_name="Microphone",
            level_db=-18.5,
            peak_db=-6.2,
            timestamp=1234567890.0,
        )

        assert sample.source_name == "Microphone"
        assert sample.level_db == -18.5
        assert sample.peak_db == -6.2
        assert sample.timestamp == 1234567890.0

    def test_audio_check_result_creation(self):
        """Test creating audio check result."""
        result = AudioCheckResult(
            source_name="Microphone",
            average_level_db=-20.5,
            peak_level_db=-8.2,
            clipping_detected=False,
            sample_rate=48000,
            channels=2,
            samples_count=100,
        )

        assert result.source_name == "Microphone"
        assert result.average_level_db == -20.5
        assert result.peak_level_db == -8.2
        assert not result.clipping_detected
        assert result.sample_rate == 48000
        assert result.channels == 2
        assert result.samples_count == 100


class TestAudioMonitor:
    """Test AudioMonitor."""

    def test_monitor_creation(self):
        """Test creating audio monitor."""
        monitor = AudioMonitor()
        assert monitor is not None
        assert monitor.obs_controller is None

    def test_monitor_with_controller(self):
        """Test creating monitor with OBS controller."""
        mock_controller = object()
        monitor = AudioMonitor(mock_controller)
        assert monitor.obs_controller is mock_controller

    def test_thresholds(self):
        """Test that audio thresholds are set correctly."""
        monitor = AudioMonitor()

        assert monitor.MIN_LEVEL_DB == -60.0
        assert monitor.RECOMMENDED_LEVEL_DB == -20.0
        assert monitor.CLIPPING_THRESHOLD_DB == -3.0
        assert monitor.MAX_LEVEL_DB == 0.0
        assert 48000 in monitor.RECOMMENDED_SAMPLE_RATES
        assert 44100 in monitor.RECOMMENDED_SAMPLE_RATES

    @pytest.mark.asyncio
    async def test_check_audio_sources_no_controller(self):
        """Test checking audio sources without controller."""
        monitor = AudioMonitor()
        result = await monitor.check_audio_sources()

        assert result["status"] == "skipped"
        assert "not available" in result["message"]

    @pytest.mark.asyncio
    async def test_check_audio_sources_with_controller(self):
        """Test checking audio sources with controller."""
        mock_controller = object()
        monitor = AudioMonitor(mock_controller)
        result = await monitor.check_audio_sources()

        assert result["status"] == "passed"
        assert result["details"]["source_count"] == 2

    @pytest.mark.asyncio
    async def test_check_audio_levels_no_controller(self):
        """Test checking audio levels without controller."""
        monitor = AudioMonitor()
        result = await monitor.check_audio_levels()

        assert result["status"] == "skipped"
        assert "not available" in result["message"]

    @pytest.mark.asyncio
    async def test_check_audio_levels_with_controller(self):
        """Test checking audio levels with controller."""
        mock_controller = object()
        monitor = AudioMonitor(mock_controller)
        result = await monitor.check_audio_levels()

        assert result["status"] == "passed"
        assert "average_db" in result["details"]
        assert "peak_db" in result["details"]

    @pytest.mark.asyncio
    async def test_check_sample_rate_no_controller(self):
        """Test checking sample rate without controller."""
        monitor = AudioMonitor()
        result = await monitor.check_sample_rate()

        assert result["status"] == "skipped"
        assert "not available" in result["message"]

    @pytest.mark.asyncio
    async def test_check_sample_rate_with_controller(self):
        """Test checking sample rate with controller."""
        mock_controller = object()
        monitor = AudioMonitor(mock_controller)
        result = await monitor.check_sample_rate()

        assert result["status"] == "passed"
        assert result["details"]["sample_rate"] == 48000

    @pytest.mark.asyncio
    async def test_check_all_no_controller(self):
        """Test checking all audio without controller."""
        monitor = AudioMonitor()
        results = await monitor.check_all()

        assert "sources" in results
        assert "levels" in results
        assert "sample_rate" in results
        assert results["sources"]["status"] == "skipped"
        assert results["levels"]["status"] == "skipped"
        assert results["sample_rate"]["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_check_all_with_controller(self):
        """Test checking all audio with controller."""
        mock_controller = object()
        monitor = AudioMonitor(mock_controller)
        results = await monitor.check_all()

        assert "sources" in results
        assert "levels" in results
        assert "sample_rate" in results
        assert all(
            r["status"] in ["passed", "warning", "failed"]
            for r in results.values()
        )

    @pytest.mark.asyncio
    async def test_placeholder_audio_sources(self):
        """Test placeholder audio sources."""
        mock_controller = object()
        monitor = AudioMonitor(mock_controller)
        sources = await monitor._get_audio_sources_placeholder()

        assert isinstance(sources, list)
        assert len(sources) > 0

    @pytest.mark.asyncio
    async def test_placeholder_monitor_levels(self):
        """Test placeholder audio level monitoring."""
        mock_controller = object()
        monitor = AudioMonitor(mock_controller)
        result = await monitor._monitor_levels_placeholder()

        assert isinstance(result, AudioCheckResult)
        assert result.source_name
        assert result.sample_rate > 0

    @pytest.mark.asyncio
    async def test_placeholder_sample_rate(self):
        """Test placeholder sample rate."""
        mock_controller = object()
        monitor = AudioMonitor(mock_controller)
        sample_rate = await monitor._get_sample_rate_placeholder()

        assert isinstance(sample_rate, int)
        assert sample_rate in monitor.RECOMMENDED_SAMPLE_RATES
