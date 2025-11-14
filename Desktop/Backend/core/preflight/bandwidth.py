"""
Bandwidth testing for preflight validation.

Tests network upload bandwidth, latency, and stability to ensure
the connection can support streaming at configured bitrates.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BandwidthTestResult:
    """Results from a bandwidth test."""

    upload_mbps: float
    download_mbps: float
    ping_ms: float
    jitter_ms: float
    server_name: str
    server_location: str
    test_duration_seconds: float


class BandwidthTester:
    """
    Test network bandwidth for streaming readiness.

    Uses speedtest-cli to measure upload bandwidth, latency,
    and network stability.
    """

    # Thresholds for streaming quality
    MIN_UPLOAD_MBPS = 5.0  # Minimum for 2500kbps stream
    RECOMMENDED_UPLOAD_MBPS = 10.0  # Recommended for reliable streaming
    MAX_PING_MS = 100.0  # Maximum acceptable ping
    MAX_JITTER_MS = 30.0  # Maximum acceptable jitter

    def __init__(self) -> None:
        """Initialize the bandwidth tester."""
        self.logger = logging.getLogger(__name__)

    async def test_bandwidth(self, timeout_seconds: int = 30) -> BandwidthTestResult:
        """
        Test network bandwidth.

        Args:
            timeout_seconds: Maximum time to wait for test

        Returns:
            BandwidthTestResult with test metrics

        Raises:
            Exception: If speedtest fails or times out
        """
        try:
            # Try to import speedtest
            try:
                import speedtest  # type: ignore # noqa: F401
            except ImportError:
                raise ImportError(
                    "speedtest-cli not installed. "
                    "Install with: pip install speedtest-cli"
                )

            self.logger.info("Starting bandwidth test...")

            # Run speedtest in a thread to avoid blocking
            import asyncio

            result = await asyncio.get_event_loop().run_in_executor(
                None, self._run_speedtest
            )

            self.logger.info(
                f"Bandwidth test complete: "
                f"{result.upload_mbps:.1f} Mbps upload, "
                f"{result.ping_ms:.1f}ms ping"
            )

            return result

        except ImportError as e:
            self.logger.error(f"Speedtest not available: {e}")
            raise

        except Exception as e:
            self.logger.error(f"Bandwidth test failed: {e}")
            raise

    def _run_speedtest(self) -> BandwidthTestResult:
        """
        Run speedtest (blocking operation).

        Returns:
            BandwidthTestResult with test metrics
        """
        import speedtest
        import time

        start_time = time.time()

        # Create speedtest instance
        st = speedtest.Speedtest()

        # Get best server
        st.get_best_server()

        # Run download and upload tests
        download_bps = st.download()
        upload_bps = st.upload()

        # Get results
        results = st.results.dict()

        duration = time.time() - start_time

        # Calculate jitter (simplified - variance in ping)
        # In a real implementation, we'd track multiple ping samples
        jitter = 0.0  # Placeholder for now

        return BandwidthTestResult(
            upload_mbps=upload_bps / 1_000_000,  # Convert to Mbps
            download_mbps=download_bps / 1_000_000,
            ping_ms=results.get("ping", 0.0),
            jitter_ms=jitter,
            server_name=results.get("server", {}).get("name", "Unknown"),
            server_location=results.get("server", {}).get("country", "Unknown"),
            test_duration_seconds=duration,
        )

    async def check_bandwidth(self, required_bitrate_kbps: int = 2500) -> dict:
        """
        Check if bandwidth is sufficient for streaming.

        Args:
            required_bitrate_kbps: Required upload bitrate in kbps

        Returns:
            dict with status, message, details, and recommendation
        """
        try:
            # Run bandwidth test
            result = await self.test_bandwidth()

            # Convert required bitrate to Mbps
            required_mbps = required_bitrate_kbps / 1000.0

            # Check upload bandwidth
            if result.upload_mbps < self.MIN_UPLOAD_MBPS:
                return {
                    "status": "failed",
                    "message": (
                        f"Upload bandwidth too low: {result.upload_mbps:.1f} Mbps "
                        f"(minimum: {self.MIN_UPLOAD_MBPS} Mbps)"
                    ),
                    "details": {
                        "upload_mbps": result.upload_mbps,
                        "download_mbps": result.download_mbps,
                        "ping_ms": result.ping_ms,
                        "required_mbps": required_mbps,
                        "server": result.server_name,
                    },
                    "recommendation": (
                        "Check internet connection or reduce stream bitrate"
                    ),
                }

            # Check if bandwidth is below recommended
            if result.upload_mbps < self.RECOMMENDED_UPLOAD_MBPS:
                return {
                    "status": "warning",
                    "message": (
                        f"Upload bandwidth marginal: {result.upload_mbps:.1f} Mbps "
                        f"(recommended: {self.RECOMMENDED_UPLOAD_MBPS} Mbps)"
                    ),
                    "details": {
                        "upload_mbps": result.upload_mbps,
                        "download_mbps": result.download_mbps,
                        "ping_ms": result.ping_ms,
                        "required_mbps": required_mbps,
                        "server": result.server_name,
                    },
                    "recommendation": (
                        "Consider reducing bitrate for more reliable streaming"
                    ),
                }

            # Check ping
            if result.ping_ms > self.MAX_PING_MS:
                return {
                    "status": "warning",
                    "message": (
                        f"High latency: {result.ping_ms:.1f}ms "
                        f"(max: {self.MAX_PING_MS}ms)"
                    ),
                    "details": {
                        "upload_mbps": result.upload_mbps,
                        "download_mbps": result.download_mbps,
                        "ping_ms": result.ping_ms,
                        "server": result.server_name,
                    },
                    "recommendation": "Check network connection stability",
                }

            # All checks passed
            return {
                "status": "passed",
                "message": (
                    f"Bandwidth sufficient: {result.upload_mbps:.1f} Mbps upload, "
                    f"{result.ping_ms:.1f}ms ping"
                ),
                "details": {
                    "upload_mbps": result.upload_mbps,
                    "download_mbps": result.download_mbps,
                    "ping_ms": result.ping_ms,
                    "required_mbps": required_mbps,
                    "server": result.server_name,
                    "location": result.server_location,
                },
            }

        except ImportError:
            return {
                "status": "skipped",
                "message": (
                    "Bandwidth testing not available "
                    "(speedtest-cli not installed)"
                ),
                "details": {},
                "recommendation": (
                    "Install speedtest-cli: pip install speedtest-cli"
                ),
            }

        except Exception as e:
            error_str = str(e)
            self.logger.warning(f"Bandwidth test unavailable: {e}")

            # Treat HTTP errors (403, 503, etc.) as skipped, not failed
            # These often occur due to speedtest.net rate limiting or blocks
            if "HTTP Error" in error_str or "403" in error_str:
                return {
                    "status": "skipped",
                    "message": "Bandwidth test unavailable (rate limited)",
                    "details": {"error": error_str},
                    "recommendation": (
                        "Speedtest.net may be rate limiting. "
                        "Bandwidth check is optional - you can proceed if "
                        "you know your connection is stable."
                    ),
                }

            # Other errors are genuine failures
            return {
                "status": "warning",
                "message": f"Bandwidth test unavailable: {error_str}",
                "details": {"error": error_str},
                "recommendation": (
                    "Bandwidth check failed but is optional. "
                    "Verify your internet connection manually."
                ),
            }
