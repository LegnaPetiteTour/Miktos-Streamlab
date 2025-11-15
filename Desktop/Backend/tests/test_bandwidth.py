"""
Tests for bandwidth testing.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.preflight.bandwidth import BandwidthTester, BandwidthTestResult


class TestBandwidthTestResult:
    """Test BandwidthTestResult dataclass."""

    def test_result_creation(self):
        """Test creating bandwidth test result."""
        result = BandwidthTestResult(
            upload_mbps=15.5,
            download_mbps=50.2,
            ping_ms=25.3,
            jitter_ms=5.2,
            server_name="Test Server",
            server_location="USA",
            test_duration_seconds=12.5,
        )

        assert result.upload_mbps == 15.5
        assert result.download_mbps == 50.2
        assert result.ping_ms == 25.3
        assert result.jitter_ms == 5.2
        assert result.server_name == "Test Server"
        assert result.server_location == "USA"
        assert result.test_duration_seconds == 12.5


class TestBandwidthTester:
    """Test BandwidthTester."""

    def test_tester_creation(self):
        """Test creating bandwidth tester."""
        tester = BandwidthTester()
        assert tester is not None

    def test_thresholds(self):
        """Test that thresholds are set correctly."""
        tester = BandwidthTester()

        assert tester.MIN_UPLOAD_MBPS == 5.0
        assert tester.RECOMMENDED_UPLOAD_MBPS == 10.0
        assert tester.MAX_PING_MS == 100.0
        assert tester.MAX_JITTER_MS == 30.0

    @pytest.mark.asyncio
    async def test_check_bandwidth_no_speedtest(self):
        """Test bandwidth check when speedtest not available."""
        tester = BandwidthTester()

        with patch("speedtest.Speedtest", side_effect=ImportError("Not found")):
            result = await tester.check_bandwidth()

            assert result["status"] == "skipped"
            assert "not installed" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_bandwidth_sufficient(self):
        """Test bandwidth check with sufficient bandwidth."""
        tester = BandwidthTester()

        # Mock speedtest
        mock_st = MagicMock()
        mock_st.download.return_value = 50_000_000  # 50 Mbps
        mock_st.upload.return_value = 15_000_000  # 15 Mbps
        mock_st.results.dict.return_value = {
            "ping": 20.0,
            "server": {"name": "Test Server", "country": "USA"},
        }

        with patch("speedtest.Speedtest", return_value=mock_st):
            result = await tester.check_bandwidth()

            assert result["status"] == "passed"
            assert "sufficient" in result["message"].lower()
            assert result["details"]["upload_mbps"] == 15.0
            assert result["details"]["ping_ms"] == 20.0

    @pytest.mark.asyncio
    async def test_check_bandwidth_marginal(self):
        """Test bandwidth check with marginal bandwidth."""
        tester = BandwidthTester()

        # Mock speedtest - between MIN and RECOMMENDED
        mock_st = MagicMock()
        mock_st.download.return_value = 30_000_000  # 30 Mbps
        mock_st.upload.return_value = 7_000_000  # 7 Mbps
        mock_st.results.dict.return_value = {
            "ping": 30.0,
            "server": {"name": "Test Server", "country": "USA"},
        }

        with patch("speedtest.Speedtest", return_value=mock_st):
            result = await tester.check_bandwidth()

            assert result["status"] == "warning"
            assert "marginal" in result["message"].lower()
            assert result["details"]["upload_mbps"] == 7.0

    @pytest.mark.asyncio
    async def test_check_bandwidth_insufficient(self):
        """Test bandwidth check with insufficient bandwidth."""
        tester = BandwidthTester()

        # Mock speedtest - below MIN
        mock_st = MagicMock()
        mock_st.download.return_value = 10_000_000  # 10 Mbps
        mock_st.upload.return_value = 3_000_000  # 3 Mbps
        mock_st.results.dict.return_value = {
            "ping": 25.0,
            "server": {"name": "Test Server", "country": "USA"},
        }

        with patch("speedtest.Speedtest", return_value=mock_st):
            result = await tester.check_bandwidth()

            assert result["status"] == "failed"
            assert "too low" in result["message"].lower()
            assert result["details"]["upload_mbps"] == 3.0

    @pytest.mark.asyncio
    async def test_check_bandwidth_high_ping(self):
        """Test bandwidth check with high ping."""
        tester = BandwidthTester()

        # Mock speedtest - good bandwidth but high ping
        mock_st = MagicMock()
        mock_st.download.return_value = 50_000_000  # 50 Mbps
        mock_st.upload.return_value = 15_000_000  # 15 Mbps
        mock_st.results.dict.return_value = {
            "ping": 150.0,  # High ping
            "server": {"name": "Test Server", "country": "USA"},
        }

        with patch("speedtest.Speedtest", return_value=mock_st):
            result = await tester.check_bandwidth()

            assert result["status"] == "warning"
            assert "latency" in result["message"].lower()
            assert result["details"]["ping_ms"] == 150.0

    @pytest.mark.asyncio
    async def test_check_bandwidth_custom_bitrate(self):
        """Test bandwidth check with custom required bitrate."""
        tester = BandwidthTester()

        # Mock speedtest
        mock_st = MagicMock()
        mock_st.download.return_value = 50_000_000
        mock_st.upload.return_value = 15_000_000
        mock_st.results.dict.return_value = {
            "ping": 20.0,
            "server": {"name": "Test Server", "country": "USA"},
        }

        with patch("speedtest.Speedtest", return_value=mock_st):
            result = await tester.check_bandwidth(required_bitrate_kbps=5000)

            assert result["status"] == "passed"
            assert result["details"]["required_mbps"] == 5.0

    @pytest.mark.asyncio
    async def test_check_bandwidth_error(self):
        """Test bandwidth check when speedtest fails."""
        tester = BandwidthTester()

        # Mock speedtest to raise an error
        mock_st = MagicMock()
        mock_st.download.side_effect = Exception("Network error")

        with patch("speedtest.Speedtest", return_value=mock_st):
            result = await tester.check_bandwidth()

            # Generic errors now return "warning" (non-critical)
            assert result["status"] == "warning"
            assert "unavailable" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_bandwidth_http_403(self):
        """Test bandwidth check when HTTP 403 occurs (rate limiting)."""
        tester = BandwidthTester()

        # Mock speedtest to raise HTTP 403 error
        mock_st = MagicMock()
        mock_st.download.side_effect = Exception("HTTP Error 403: Forbidden")

        with patch("speedtest.Speedtest", return_value=mock_st):
            result = await tester.check_bandwidth()

            # HTTP errors are treated as skipped (rate limiting)
            assert result["status"] == "skipped"
            assert "rate limited" in result["message"].lower()
            assert "optional" in result["recommendation"].lower()

    @pytest.mark.asyncio
    async def test_test_bandwidth(self):
        """Test raw bandwidth testing."""
        tester = BandwidthTester()

        # Mock speedtest
        mock_st = MagicMock()
        mock_st.download.return_value = 50_000_000
        mock_st.upload.return_value = 15_000_000
        mock_st.results.dict.return_value = {
            "ping": 20.0,
            "server": {"name": "Test Server", "country": "USA"},
        }

        with patch("speedtest.Speedtest", return_value=mock_st):
            result = await tester.test_bandwidth()

            assert isinstance(result, BandwidthTestResult)
            assert result.upload_mbps == 15.0
            assert result.download_mbps == 50.0
            assert result.ping_ms == 20.0
            assert result.server_name == "Test Server"
            assert result.server_location == "USA"
            assert result.test_duration_seconds > 0
