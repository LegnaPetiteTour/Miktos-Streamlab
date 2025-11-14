"""
Tests for failover slate integration

Tests the integration between EgressManager and SlateManager
to ensure slates are displayed during failover scenarios.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.core.egress import (
    EgressManager,
    EgressConfig,
    FailoverConfig
)


@pytest.fixture
def mock_obs_controller():
    """Create a mock OBS controller"""
    obs = MagicMock()
    obs.ws = MagicMock()
    obs.is_connected = MagicMock(return_value=True)
    obs.connect = AsyncMock(return_value=True)
    obs.disconnect = AsyncMock()
    return obs


@pytest.fixture
def failover_config():
    """Create failover configuration with slate enabled"""
    return FailoverConfig(
        enabled=True,
        trigger_duration_sec=5.0,
        show_slate=True,
        slate_text="We are experiencing technical difficulties"
    )


@pytest.fixture
def primary_destination():
    """Create primary RTMP destination config"""
    return {
        "type": "rtmp",
        "name": "primary",
        "url": "rtmp://primary.example.com/live",
        "key": "key123",  # Note: key not stream_key
        "bitrate_mbps": 6.0
    }


@pytest.fixture
def backup_destination():
    """Create backup RTMP destination config"""
    return {
        "type": "rtmp",
        "name": "backup",
        "url": "rtmp://backup.example.com/live",
        "key": "key456",  # Note: key not stream_key
        "bitrate_mbps": 4.0
    }


class TestFailoverSlateIntegration:
    """Test slate display during failover scenarios"""

    @pytest.mark.asyncio
    async def test_slate_manager_initialization(
        self,
        primary_destination,
        backup_destination,
        failover_config,
        mock_obs_controller
    ):
        """Test that SlateManager is initialized with OBS controller"""
        config = EgressConfig(
            primary_destination=primary_destination,
            backup_destination=backup_destination,
            failover=failover_config
        )

        with patch('src.core.egress.SlateManager') as MockSlateManager:
            manager = EgressManager(
                config,
                obs_controller=mock_obs_controller
            )

            # Verify SlateManager was instantiated with OBS controller
            MockSlateManager.assert_called_once_with(mock_obs_controller)
            assert manager.slate_manager is not None

    @pytest.mark.asyncio
    async def test_slate_manager_not_initialized_without_obs(
        self,
        primary_destination,
        backup_destination,
        failover_config
    ):
        """Test that SlateManager is not initialized without OBS"""
        config = EgressConfig(
            primary_destination=primary_destination,
            backup_destination=backup_destination,
            failover=failover_config
        )

        manager = EgressManager(config, obs_controller=None)
        assert manager.slate_manager is None

    @pytest.mark.asyncio
    async def test_show_slate_during_failover(
        self,
        primary_destination,
        backup_destination,
        failover_config,
        mock_obs_controller
    ):
        """Test that slate is shown when failover is initiated"""
        config = EgressConfig(
            primary_destination=primary_destination,
            backup_destination=backup_destination,
            failover=failover_config
        )

        with patch('src.core.egress.SlateManager') as MockSlateManager:
            mock_slate = MagicMock()
            mock_slate.show_slate = AsyncMock()
            mock_slate.show_preset_message = AsyncMock()
            MockSlateManager.return_value = mock_slate

            manager = EgressManager(
                config,
                obs_controller=mock_obs_controller
            )

            # Mock the backup starting successfully
            manager.backup.start_streaming = AsyncMock(  # pyright: ignore
                return_value=True
            )
            manager.backup.status = MagicMock()  # pyright: ignore

            # Trigger failover
            await manager._initiate_failover()

            # Verify slate was shown with custom message
            mock_slate.show_slate.assert_called_once()
            call_kwargs = mock_slate.show_slate.call_args[1]
            assert call_kwargs['auto_hide'] is False
            assert "technical difficulties" in call_kwargs['message'].lower()

    @pytest.mark.asyncio
    async def test_hide_slate_during_recovery(
        self,
        primary_destination,
        backup_destination,
        failover_config,
        mock_obs_controller
    ):
        """Test that slate is hidden when recovery completes"""
        config = EgressConfig(
            primary_destination=primary_destination,
            backup_destination=backup_destination,
            failover=failover_config
        )

        with patch('src.core.egress.SlateManager') as MockSlateManager:
            mock_slate = MagicMock()
            mock_slate.hide_slate = AsyncMock()
            MockSlateManager.return_value = mock_slate

            manager = EgressManager(
                config,
                obs_controller=mock_obs_controller
            )

            # Setup manager state for recovery
            manager.failover_active = True
            manager.active_destination = manager.backup

            # Mock primary reconnecting successfully
            manager.primary.status = MagicMock()  # pyright: ignore
            manager.primary.connect = AsyncMock(  # pyright: ignore
                return_value=True
            )
            manager.primary.start_streaming = AsyncMock(  # pyright: ignore
                return_value=True
            )
            manager.backup.stop_streaming = AsyncMock()  # pyright: ignore

            # Complete recovery
            await manager._complete_failover_recovery()

            # Verify slate was hidden
            mock_slate.hide_slate.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_slate_when_disabled(
        self,
        primary_destination,
        backup_destination,
        mock_obs_controller
    ):
        """Test that slate is not shown when disabled in config"""
        failover_config = FailoverConfig(
            enabled=True,
            trigger_duration_sec=5.0,
            show_slate=False  # Disabled
        )

        config = EgressConfig(
            primary_destination=primary_destination,
            backup_destination=backup_destination,
            failover=failover_config
        )

        with patch('src.core.egress.SlateManager') as MockSlateManager:
            mock_slate = MagicMock()
            mock_slate.show_slate = AsyncMock()
            MockSlateManager.return_value = mock_slate

            manager = EgressManager(
                config,
                obs_controller=mock_obs_controller
            )

            # Mock the backup starting successfully
            manager.backup.start_streaming = AsyncMock(  # pyright: ignore
                return_value=True
            )
            manager.backup.status = MagicMock()  # pyright: ignore

            # Trigger failover
            await manager._initiate_failover()

            # Verify slate was NOT shown
            mock_slate.show_slate.assert_not_called()

    @pytest.mark.asyncio
    async def test_slate_error_handling(
        self,
        primary_destination,
        backup_destination,
        failover_config,
        mock_obs_controller
    ):
        """Test that failover continues even if slate display fails"""
        config = EgressConfig(
            primary_destination=primary_destination,
            backup_destination=backup_destination,
            failover=failover_config
        )

        with patch('src.core.egress.SlateManager') as MockSlateManager:
            mock_slate = MagicMock()
            # Slate fails to show
            mock_slate.show_slate = AsyncMock(
                side_effect=Exception("Slate error")
            )
            MockSlateManager.return_value = mock_slate

            manager = EgressManager(
                config,
                obs_controller=mock_obs_controller
            )

            # Mock the backup starting successfully
            manager.backup.start_streaming = AsyncMock(  # pyright: ignore
                return_value=True
            )
            manager.backup.status = MagicMock()  # pyright: ignore

            # Trigger failover - should not crash
            await manager._initiate_failover()

            # Verify failover completed despite slate error
            assert manager.failover_active is True
            assert manager.active_destination == manager.backup
