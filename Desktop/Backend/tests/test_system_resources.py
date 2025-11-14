"""
Tests for system resource monitoring.
"""

import pytest

from src.core.preflight.system_resources import (
    SystemResourceChecker,
    SystemResources,
)


class TestSystemResources:
    """Test SystemResources dataclass."""

    def test_system_resources_creation(self):
        """Test creating SystemResources instance."""
        resources = SystemResources(
            cpu_percent=25.5,
            memory_total_gb=16.0,
            memory_available_gb=8.0,
            memory_percent=50.0,
            disk_total_gb=500.0,
            disk_free_gb=250.0,
            disk_percent=50.0,
            platform="Darwin",
            cpu_count=8,
        )

        assert resources.cpu_percent == 25.5
        assert resources.memory_total_gb == 16.0
        assert resources.memory_available_gb == 8.0
        assert resources.memory_percent == 50.0
        assert resources.disk_total_gb == 500.0
        assert resources.disk_free_gb == 250.0
        assert resources.disk_percent == 50.0
        assert resources.platform == "Darwin"
        assert resources.cpu_count == 8


class TestSystemResourceChecker:
    """Test SystemResourceChecker."""

    def test_checker_creation(self):
        """Test creating SystemResourceChecker."""
        checker = SystemResourceChecker()
        assert checker is not None

    def test_get_system_resources(self):
        """Test getting system resources."""
        checker = SystemResourceChecker()
        resources = checker.get_system_resources()

        assert isinstance(resources, SystemResources)
        assert resources.cpu_count >= 0
        assert resources.disk_total_gb >= 0
        assert resources.disk_free_gb >= 0
        assert resources.disk_percent >= 0

    def test_check_cpu_low_usage(self):
        """Test CPU check with low usage."""
        checker = SystemResourceChecker()
        resources = SystemResources(
            cpu_percent=30.0,
            memory_total_gb=16.0,
            memory_available_gb=8.0,
            memory_percent=50.0,
            disk_total_gb=500.0,
            disk_free_gb=250.0,
            disk_percent=50.0,
            platform="Darwin",
            cpu_count=8,
        )

        result = checker.check_cpu(resources)
        assert result["status"] == "passed"
        assert "30.0%" in result["message"]

    def test_check_cpu_high_usage(self):
        """Test CPU check with high usage."""
        checker = SystemResourceChecker()
        resources = SystemResources(
            cpu_percent=85.0,
            memory_total_gb=16.0,
            memory_available_gb=8.0,
            memory_percent=50.0,
            disk_total_gb=500.0,
            disk_free_gb=250.0,
            disk_percent=50.0,
            platform="Darwin",
            cpu_count=8,
        )

        result = checker.check_cpu(resources)
        assert result["status"] == "warning"
        assert "85.0%" in result["message"]

    def test_check_cpu_no_psutil(self):
        """Test CPU check without psutil."""
        checker = SystemResourceChecker()
        resources = SystemResources(
            cpu_percent=0.0,
            memory_total_gb=0.0,
            memory_available_gb=0.0,
            memory_percent=0.0,
            disk_total_gb=500.0,
            disk_free_gb=250.0,
            disk_percent=50.0,
            platform="Darwin",
            cpu_count=8,
        )

        result = checker.check_cpu(resources)
        assert result["status"] == "warning"
        assert "psutil" in result["message"].lower()

    def test_check_memory_sufficient(self):
        """Test memory check with sufficient memory."""
        checker = SystemResourceChecker()
        resources = SystemResources(
            cpu_percent=30.0,
            memory_total_gb=16.0,
            memory_available_gb=8.0,
            memory_percent=50.0,
            disk_total_gb=500.0,
            disk_free_gb=250.0,
            disk_percent=50.0,
            platform="Darwin",
            cpu_count=8,
        )

        result = checker.check_memory(resources)
        assert result["status"] == "passed"
        assert "8.0GB" in result["message"]

    def test_check_memory_low(self):
        """Test memory check with low memory."""
        checker = SystemResourceChecker()
        resources = SystemResources(
            cpu_percent=30.0,
            memory_total_gb=16.0,
            memory_available_gb=1.5,
            memory_percent=90.6,
            disk_total_gb=500.0,
            disk_free_gb=250.0,
            disk_percent=50.0,
            platform="Darwin",
            cpu_count=8,
        )

        result = checker.check_memory(resources)
        assert result["status"] == "failed"
        assert "1.5GB" in result["message"]

    def test_check_memory_high_usage(self):
        """Test memory check with high memory usage."""
        checker = SystemResourceChecker()
        resources = SystemResources(
            cpu_percent=30.0,
            memory_total_gb=16.0,
            memory_available_gb=2.5,
            memory_percent=88.0,
            disk_total_gb=500.0,
            disk_free_gb=250.0,
            disk_percent=50.0,
            platform="Darwin",
            cpu_count=8,
        )

        result = checker.check_memory(resources)
        assert result["status"] == "warning"
        assert "88.0%" in result["message"]

    def test_check_disk_sufficient(self):
        """Test disk check with sufficient space."""
        checker = SystemResourceChecker()
        resources = SystemResources(
            cpu_percent=30.0,
            memory_total_gb=16.0,
            memory_available_gb=8.0,
            memory_percent=50.0,
            disk_total_gb=500.0,
            disk_free_gb=250.0,
            disk_percent=50.0,
            platform="Darwin",
            cpu_count=8,
        )

        result = checker.check_disk_space(resources)
        assert result["status"] == "passed"
        assert "250.0GB" in result["message"]

    def test_check_disk_low(self):
        """Test disk check with low disk space."""
        checker = SystemResourceChecker()
        resources = SystemResources(
            cpu_percent=30.0,
            memory_total_gb=16.0,
            memory_available_gb=8.0,
            memory_percent=50.0,
            disk_total_gb=500.0,
            disk_free_gb=3.0,
            disk_percent=99.4,
            platform="Darwin",
            cpu_count=8,
        )

        result = checker.check_disk_space(resources)
        assert result["status"] == "warning"
        assert "3.0GB" in result["message"]

    def test_check_disk_nearly_full(self):
        """Test disk check with nearly full disk."""
        checker = SystemResourceChecker()
        resources = SystemResources(
            cpu_percent=30.0,
            memory_total_gb=16.0,
            memory_available_gb=8.0,
            memory_percent=50.0,
            disk_total_gb=500.0,
            disk_free_gb=10.0,
            disk_percent=98.0,
            platform="Darwin",
            cpu_count=8,
        )

        result = checker.check_disk_space(resources)
        assert result["status"] == "warning"
        assert "98.0%" in result["message"]

    def test_check_all(self):
        """Test checking all resources at once."""
        checker = SystemResourceChecker()
        results = checker.check_all()

        assert "resources" in results
        assert "cpu" in results
        assert "memory" in results
        assert "disk" in results

        assert isinstance(results["resources"], SystemResources)
        assert "status" in results["cpu"]
        assert "status" in results["memory"]
        assert "status" in results["disk"]

    def test_custom_thresholds(self):
        """Test that custom thresholds are respected."""
        checker = SystemResourceChecker()
        
        # Verify the thresholds are set correctly
        assert checker.MIN_MEMORY_GB == 2.0
        assert checker.MIN_DISK_GB == 5.0
        assert checker.MAX_CPU_PERCENT == 80.0
        assert checker.MAX_MEMORY_PERCENT == 85.0
        assert checker.MAX_DISK_PERCENT == 90.0
