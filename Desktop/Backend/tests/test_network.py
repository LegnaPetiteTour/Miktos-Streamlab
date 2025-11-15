"""
Tests for network monitoring
"""
import pytest
from core.network import NetworkMonitor, NetworkStatus, NetworkMetrics


class TestNetworkMetrics:
    """Test NetworkMetrics dataclass"""
    
    def test_metrics_creation(self):
        """Test creating network metrics"""
        metrics = NetworkMetrics(
            upload_speed=8.5,
            download_speed=50.0,
            latency=25.0,
            jitter=5.0,
            packet_loss=0.0,
            status=NetworkStatus.EXCELLENT,
            timestamp=1234567890.0
        )
        
        assert metrics.upload_speed == 8.5
        assert metrics.download_speed == 50.0
        assert metrics.latency == 25.0
        assert metrics.status == NetworkStatus.EXCELLENT
        
    def test_metrics_to_dict(self, mock_network_metrics):
        """Test converting metrics to dictionary"""
        data = mock_network_metrics.to_dict()
        
        assert isinstance(data, dict)
        assert 'upload_speed' in data
        assert 'download_speed' in data
        assert 'latency' in data
        assert 'status' in data
        assert data['status'] == 'excellent'


class TestNetworkMonitor:
    """Test NetworkMonitor class"""
    
    def test_initialization(self):
        """Test NetworkMonitor initialization"""
        monitor = NetworkMonitor(test_interval=120)
        
        assert monitor.test_interval == 120
        assert monitor._cached_metrics is None
        
    def test_status_assessment(self):
        """Test network status assessment"""
        monitor = NetworkMonitor()
        
        # Excellent
        status = monitor._assess_status(upload_speed=8.0, latency=25)
        assert status == NetworkStatus.EXCELLENT
        
        # Good
        status = monitor._assess_status(upload_speed=5.5, latency=45)
        assert status == NetworkStatus.GOOD
        
        # Marginal
        status = monitor._assess_status(upload_speed=3.5, latency=80)
        assert status == NetworkStatus.MARGINAL
        
        # Poor
        status = monitor._assess_status(upload_speed=2.0, latency=120)
        assert status == NetworkStatus.POOR
        
        # Critical
        status = monitor._assess_status(upload_speed=1.0, latency=200)
        assert status == NetworkStatus.CRITICAL
        
    def test_quick_metrics(self):
        """Test quick metrics retrieval"""
        monitor = NetworkMonitor()
        metrics = monitor.get_quick_metrics()
        
        assert isinstance(metrics, dict)
        assert 'bytes_sent' in metrics
        assert 'bytes_recv' in metrics
        
    def test_recommended_bitrate(self):
        """Test bitrate recommendations"""
        monitor = NetworkMonitor()
        
        # Mock different speeds
        class MockMetrics:
            def __init__(self, upload_speed):
                self.upload_speed = upload_speed
                
        # High speed -> high bitrate
        monitor._cached_metrics = MockMetrics(10.0)
        bitrate = monitor.get_recommended_bitrate()
        assert bitrate == 6000
        
        # Medium speed -> medium bitrate
        monitor._cached_metrics = MockMetrics(5.0)
        bitrate = monitor.get_recommended_bitrate()
        assert bitrate == 3000
        
        # Low speed -> low bitrate
        monitor._cached_metrics = MockMetrics(2.0)
        bitrate = monitor.get_recommended_bitrate()
        assert bitrate == 1500


class TestNetworkStatus:
    """Test NetworkStatus enum"""
    
    def test_status_values(self):
        """Test NetworkStatus enum values"""
        assert NetworkStatus.EXCELLENT.value == "excellent"
        assert NetworkStatus.GOOD.value == "good"
        assert NetworkStatus.MARGINAL.value == "marginal"
        assert NetworkStatus.POOR.value == "poor"
        assert NetworkStatus.CRITICAL.value == "critical"
