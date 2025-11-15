"""
Tests for Health Metrics

Tests MetricSeries, StreamHealth, and HealthAggregator.
Part of Week 9-10 dashboard implementation.
"""

from datetime import datetime
from unittest.mock import Mock

from core.health_metrics import (
    HealthAggregator,
    MetricSample,
    MetricSeries,
    StreamHealth,
)


def test_metric_sample_creation():
    """Test MetricSample dataclass"""
    now = datetime.now()
    sample = MetricSample(timestamp=now, value=100.0)
    assert sample.value == 100.0
    assert sample.timestamp == now


def test_metric_series_creation():
    """Test MetricSeries creation"""
    series = MetricSeries(name="bitrate", unit="kbps")
    assert series.name == "bitrate"
    assert series.unit == "kbps"
    assert len(series.samples) == 0


def test_metric_series_add():
    """Test adding samples to MetricSeries"""
    series = MetricSeries(name="cpu", unit="%")

    for i in range(10):
        series.add(float(i))

    # Should keep all 10 samples (within 300 limit)
    assert len(series.samples) == 10
    # Should keep latest value
    assert series.samples[-1].value == 9.0


def test_metric_series_average():
    """Test average calculation"""
    series = MetricSeries(name="test", unit="unit")

    series.add(10.0)
    series.add(20.0)
    series.add(30.0)

    assert series.get_average() == 20.0


def test_metric_series_min_max():
    """Test min/max calculation"""
    series = MetricSeries(name="test", unit="unit")

    series.add(5.0)
    series.add(15.0)
    series.add(10.0)

    min_val, max_val = series.get_min_max()
    assert min_val == 5.0
    assert max_val == 15.0


def test_metric_series_trend_rising():
    """Test trend detection - rising"""
    series = MetricSeries(name="test", unit="unit")

    # Add rising trend - need at least 30 samples for trend detection
    for i in range(40):
        series.add(float(i * 10))

    trend = series.get_trend()
    assert trend == "rising"


def test_metric_series_trend_falling():
    """Test trend detection - falling"""
    series = MetricSeries(name="test", unit="unit")

    # Add falling trend - need at least 30 samples for trend detection
    # Generate values from 1000 down to 600 (avoiding negatives)
    for i in range(40):
        series.add(1000.0 - float(i * 10))

    trend = series.get_trend()
    assert trend == "falling"


def test_metric_series_trend_stable():
    """Test trend detection - stable"""
    series = MetricSeries(name="test", unit="unit")

    # Add stable values
    for _ in range(10):
        series.add(50.0)

    trend = series.get_trend()
    assert trend == "stable"


def test_stream_health_drop_percentage():
    """Test drop percentage calculation"""
    health = StreamHealth(
        dropped_frames=50,
        total_frames=1000,
    )

    assert health.drop_percentage == 5.0


def test_stream_health_zero_frames():
    """Test drop percentage with zero frames"""
    health = StreamHealth(
        dropped_frames=0,
        total_frames=0,
    )

    assert health.drop_percentage == 0.0


def test_health_aggregator_initialization():
    """Test HealthAggregator initialization"""
    mock_obs = Mock()
    mock_egress = Mock()

    aggregator = HealthAggregator(
        obs_controller=mock_obs,
        egress_manager=mock_egress,
        poll_interval=1.0,
    )

    assert aggregator.obs == mock_obs
    assert aggregator.egress == mock_egress
    assert aggregator.failover is None
    assert aggregator.poll_interval == 1.0
    assert not aggregator.running


def test_health_aggregator_metrics():
    """Test HealthAggregator creates metric series"""
    mock_obs = Mock()
    mock_egress = Mock()

    aggregator = HealthAggregator(
        obs_controller=mock_obs,
        egress_manager=mock_egress,
    )

    # Check that all expected metrics are created
    expected_metrics = [
        "bitrate_kbps",
        "fps",
        "cpu_usage",
        "gpu_usage",
        "memory_mb",
        "drop_percentage",
        "rtt_ms",
        "jitter_ms",
        "packet_loss_pct",
    ]

    for metric_name in expected_metrics:
        assert metric_name in aggregator.metrics
        assert isinstance(aggregator.metrics[metric_name], MetricSeries)


def test_get_health_summary():
    """Test health summary generation"""
    mock_obs = Mock()
    mock_egress = Mock()

    aggregator = HealthAggregator(
        obs_controller=mock_obs,
        egress_manager=mock_egress,
    )

    # Set current health
    aggregator.current_health = StreamHealth(
        streaming=True,
        uptime_seconds=120,
        bitrate_kbps=3000,
        fps=30.0,
        dropped_frames=10,
        total_frames=9000,
        cpu_usage=45.5,
    )

    summary = aggregator.get_health_summary()

    assert summary["status"] == "healthy"
    assert summary["streaming"] is True
    assert summary["uptime_seconds"] == 120
    assert summary["metrics"]["bitrate_kbps"] == 3000
    assert summary["metrics"]["fps"] == 30.0


def test_health_summary_warning_status():
    """Test health summary with warning status"""
    mock_obs = Mock()
    mock_egress = Mock()

    aggregator = HealthAggregator(
        obs_controller=mock_obs,
        egress_manager=mock_egress,
    )

    # Set health with high CPU
    aggregator.current_health = StreamHealth(
        streaming=True,
        cpu_usage=80.0,  # Above warning threshold (75)
        dropped_frames=50,
        total_frames=5000,  # 1% drop rate
    )

    summary = aggregator.get_health_summary()

    assert summary["status"] == "warning"
    assert len(summary["issues"]) > 0


def test_health_summary_critical_status():
    """Test health summary with critical status"""
    mock_obs = Mock()
    mock_egress = Mock()

    aggregator = HealthAggregator(
        obs_controller=mock_obs,
        egress_manager=mock_egress,
    )

    # Set health with critical drop rate
    aggregator.current_health = StreamHealth(
        streaming=True,
        dropped_frames=600,
        total_frames=10000,  # 6% drop rate (above 5% critical threshold)
    )

    summary = aggregator.get_health_summary()

    assert summary["status"] == "critical"
    assert "High drop rate" in summary["issues"][0]


def test_get_current_health():
    """Test getting current health"""
    mock_obs = Mock()
    mock_egress = Mock()

    aggregator = HealthAggregator(
        obs_controller=mock_obs,
        egress_manager=mock_egress,
    )

    # Initially None
    assert aggregator.get_current_health() is None

    # Set health
    health = StreamHealth(streaming=True)
    aggregator.current_health = health

    assert aggregator.get_current_health() == health


def test_get_metric_series():
    """Test getting individual metric series"""
    mock_obs = Mock()
    mock_egress = Mock()

    aggregator = HealthAggregator(
        obs_controller=mock_obs,
        egress_manager=mock_egress,
    )

    # Add some data
    aggregator.metrics["bitrate_kbps"].add(3000.0)

    series = aggregator.get_metric_series("bitrate_kbps")
    assert series is not None
    assert series.name == "Bitrate"
    assert len(series.samples) == 1


def test_get_all_metrics():
    """Test getting all metrics"""
    mock_obs = Mock()
    mock_egress = Mock()

    aggregator = HealthAggregator(
        obs_controller=mock_obs,
        egress_manager=mock_egress,
    )

    all_metrics = aggregator.get_all_metrics()

    assert isinstance(all_metrics, dict)
    assert len(all_metrics) > 0
    assert "bitrate_kbps" in all_metrics
    assert "fps" in all_metrics
