"""Tests for the UnraidWebSocketManager."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from unraid_api.exceptions import (
    UnraidAuthenticationError,
    UnraidConnectionError,
)
from unraid_api.models import DockerContainerStats

from custom_components.unraid.websocket import (
    ContainerStatsSnapshot,
    UnraidWebSocketManager,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_manager(
    *,
    api_client: AsyncMock | None = None,
    system_coordinator: MagicMock | None = None,
) -> UnraidWebSocketManager:
    """Create a WebSocket manager with mocked dependencies."""
    if api_client is None:
        api_client = AsyncMock()
    if system_coordinator is None:
        system_coordinator = MagicMock()
        system_coordinator.data = MagicMock()
    return UnraidWebSocketManager(
        api_client=api_client,
        system_coordinator=system_coordinator,
        server_name="TestServer",
    )


def _make_container_stats(
    container_id: str = "abc123",
    cpu_percent: float = 25.5,
    mem_usage: str = "512MiB / 16GiB",
    mem_percent: float = 3.1,
) -> DockerContainerStats:
    """Create a mock DockerContainerStats."""
    stats = MagicMock(spec=DockerContainerStats)
    stats.id = container_id
    stats.cpuPercent = cpu_percent
    stats.memUsage = mem_usage
    stats.memPercent = mem_percent
    stats.blockIO = "10MB / 5MB"
    stats.netIO = "1GB / 500MB"
    return stats


# =============================================================================
# ContainerStatsSnapshot Tests
# =============================================================================


class TestContainerStatsSnapshot:
    """Tests for ContainerStatsSnapshot dataclass."""

    def test_default_empty(self) -> None:
        """Test that a new snapshot starts with empty stats."""
        snapshot = ContainerStatsSnapshot()
        assert snapshot.stats == {}

    def test_stores_stats(self) -> None:
        """Test that stats can be stored and retrieved."""
        snapshot = ContainerStatsSnapshot()
        stats = _make_container_stats("container1")
        snapshot.stats["container1"] = stats
        assert snapshot.stats["container1"] is stats

    def test_multiple_containers(self) -> None:
        """Test storing stats for multiple containers."""
        snapshot = ContainerStatsSnapshot()
        stats1 = _make_container_stats("c1", cpu_percent=10.0)
        stats2 = _make_container_stats("c2", cpu_percent=20.0)
        snapshot.stats["c1"] = stats1
        snapshot.stats["c2"] = stats2
        assert len(snapshot.stats) == 2
        assert snapshot.stats["c1"].cpuPercent == 10.0
        assert snapshot.stats["c2"].cpuPercent == 20.0


# =============================================================================
# UnraidWebSocketManager — Lifecycle Tests
# =============================================================================


class TestWebSocketManagerLifecycle:
    """Tests for start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_creates_tasks(self) -> None:
        """Test that async_start creates background tasks."""
        manager = _make_manager()
        # Make subscriptions wait forever so tasks stay alive
        api = manager._api_client
        api.subscribe_container_stats = AsyncMock(side_effect=asyncio.CancelledError)
        api.subscribe_ups_updates = AsyncMock(side_effect=asyncio.CancelledError)
        api.subscribe_notification_added = AsyncMock(side_effect=asyncio.CancelledError)

        await manager.async_start()
        assert manager._running is True
        assert len(manager._tasks) == 3
        # Clean up
        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_start_idempotent(self) -> None:
        """Test that calling start twice doesn't duplicate tasks."""
        manager = _make_manager()
        api = manager._api_client
        api.subscribe_container_stats = AsyncMock(side_effect=asyncio.CancelledError)
        api.subscribe_ups_updates = AsyncMock(side_effect=asyncio.CancelledError)
        api.subscribe_notification_added = AsyncMock(side_effect=asyncio.CancelledError)

        await manager.async_start()
        await manager.async_start()  # Second call should be no-op
        assert len(manager._tasks) == 3
        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_tasks(self) -> None:
        """Test that async_stop cancels all tasks and clears state."""
        manager = _make_manager()
        api = manager._api_client
        api.subscribe_container_stats = AsyncMock(side_effect=asyncio.CancelledError)
        api.subscribe_ups_updates = AsyncMock(side_effect=asyncio.CancelledError)
        api.subscribe_notification_added = AsyncMock(side_effect=asyncio.CancelledError)

        await manager.async_start()
        # Add some container stats to verify they get cleared
        manager.container_stats.stats["test"] = _make_container_stats()
        await manager.async_stop()

        assert manager._running is False
        assert len(manager._tasks) == 0
        assert len(manager.container_stats.stats) == 0

    @pytest.mark.asyncio
    async def test_stop_idempotent(self) -> None:
        """Test that calling stop when not running is safe."""
        manager = _make_manager()
        await manager.async_stop()  # Should not raise
        assert manager._running is False


# =============================================================================
# UnraidWebSocketManager — Container Stats Subscription Tests
# =============================================================================


class TestContainerStatsSubscription:
    """Tests for container stats WebSocket subscription."""

    @pytest.mark.asyncio
    async def test_container_stats_stored(self) -> None:
        """Test that container stats are stored in the snapshot."""
        stats1 = _make_container_stats("c1", cpu_percent=15.0)
        stats2 = _make_container_stats("c2", cpu_percent=30.0)

        async def mock_subscribe() -> Any:
            yield stats1
            yield stats2

        system_coordinator = MagicMock()
        system_coordinator.data = MagicMock()
        api_client = AsyncMock()
        api_client.subscribe_container_stats = mock_subscribe

        manager = _make_manager(
            api_client=api_client,
            system_coordinator=system_coordinator,
        )
        manager._running = True
        await manager._handle_container_stats()

        assert "c1" in manager.container_stats.stats
        assert "c2" in manager.container_stats.stats
        assert manager.container_stats.stats["c1"].cpuPercent == 15.0

    @pytest.mark.asyncio
    async def test_container_stats_no_coordinator_push(self) -> None:
        """Test that container stats are stored without pushing to coordinator."""
        stats = _make_container_stats("c1")

        async def mock_subscribe() -> Any:
            yield stats

        system_coordinator = MagicMock()
        system_coordinator.data = MagicMock()
        api_client = AsyncMock()
        api_client.subscribe_container_stats = mock_subscribe

        manager = _make_manager(
            api_client=api_client,
            system_coordinator=system_coordinator,
        )
        manager._running = True
        await manager._handle_container_stats()

        assert "c1" in manager.container_stats.stats
        system_coordinator.async_set_updated_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_container_stats_skips_none_id(self) -> None:
        """Test that stats with None id are skipped."""
        stats = _make_container_stats()
        stats.id = None

        async def mock_subscribe() -> Any:
            yield stats

        api_client = AsyncMock()
        api_client.subscribe_container_stats = mock_subscribe

        manager = _make_manager(api_client=api_client)
        manager._running = True
        await manager._handle_container_stats()

        assert len(manager.container_stats.stats) == 0

    @pytest.mark.asyncio
    async def test_container_stats_stored_when_coordinator_data_none(self) -> None:
        """Test that stats are stored even when coordinator data is None."""
        stats = _make_container_stats("c1")

        async def mock_subscribe() -> Any:
            yield stats

        system_coordinator = MagicMock()
        system_coordinator.data = None
        api_client = AsyncMock()
        api_client.subscribe_container_stats = mock_subscribe

        manager = _make_manager(
            api_client=api_client,
            system_coordinator=system_coordinator,
        )
        manager._running = True
        await manager._handle_container_stats()

        assert "c1" in manager.container_stats.stats


# =============================================================================
# UnraidWebSocketManager — UPS Updates Subscription Tests
# =============================================================================


class TestUpsUpdatesSubscription:
    """Tests for UPS updates WebSocket subscription."""

    @pytest.mark.asyncio
    async def test_ups_update_triggers_refresh(self) -> None:
        """Test that UPS updates trigger system coordinator refresh."""
        update = MagicMock()

        async def mock_subscribe() -> Any:
            yield update

        system_coordinator = AsyncMock()
        system_coordinator.data = MagicMock()
        api_client = AsyncMock()
        api_client.subscribe_ups_updates = mock_subscribe

        manager = _make_manager(
            api_client=api_client,
            system_coordinator=system_coordinator,
        )
        manager._running = True
        await manager._handle_ups_updates()

        system_coordinator.async_request_refresh.assert_called_once()


# =============================================================================
# UnraidWebSocketManager — Debounce Tests
# =============================================================================


class TestRefreshDebounce:
    """Tests for WebSocket-triggered coordinator refresh debouncing."""

    @pytest.mark.asyncio
    async def test_ups_first_event_triggers_refresh(self) -> None:
        """First UPS WS event always triggers a system refresh."""
        update = MagicMock()

        async def mock_subscribe() -> Any:
            yield update

        system_coordinator = AsyncMock()
        api_client = AsyncMock()
        api_client.subscribe_ups_updates = mock_subscribe

        manager = _make_manager(
            api_client=api_client,
            system_coordinator=system_coordinator,
        )
        manager._running = True

        with patch(
            "custom_components.unraid.websocket.time.monotonic", return_value=100.0
        ):
            await manager._handle_ups_updates()

        system_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_ups_rapid_events_debounced(self) -> None:
        """UPS WS events within cooldown window are suppressed."""
        update1 = MagicMock()
        update2 = MagicMock()

        async def mock_subscribe() -> Any:
            yield update1
            yield update2

        system_coordinator = AsyncMock()
        api_client = AsyncMock()
        api_client.subscribe_ups_updates = mock_subscribe

        manager = _make_manager(
            api_client=api_client,
            system_coordinator=system_coordinator,
        )
        manager._running = True

        # First call at t=100 triggers; second at t=107 → still in cooldown.
        with patch(
            "custom_components.unraid.websocket.time.monotonic",
            side_effect=[100.0, 100.0, 107.0],
        ):
            await manager._handle_ups_updates()

        system_coordinator.async_request_refresh.assert_called_once()


# =============================================================================
# UnraidWebSocketManager — Reconnection Tests
# =============================================================================


class TestReconnection:
    """Tests for WebSocket reconnection behavior."""

    @pytest.mark.asyncio
    async def test_auth_error_stops_subscription(self) -> None:
        """Test that authentication errors stop the subscription permanently."""
        call_count = 0

        async def failing_handler() -> None:
            nonlocal call_count
            call_count += 1
            raise UnraidAuthenticationError("Auth failed")

        manager = _make_manager()
        manager._running = True

        await manager._run_subscription("test", failing_handler)

        # Should only be called once (no retry on auth error)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_connection_error_retries(self) -> None:
        """Test that connection errors cause reconnection with backoff."""
        call_count = 0

        async def failing_handler() -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                # Stop after 3 attempts
                manager._running = False
                return
            raise UnraidConnectionError("Connection lost")

        manager = _make_manager()
        manager._running = True

        with patch("custom_components.unraid.websocket.asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None  # Don't actually sleep
            await manager._run_subscription("test", failing_handler)

        # Should have retried after first two failures
        assert call_count == 3
        # Should have slept between retries with backoff
        assert mock_sleep.call_count >= 2

    @pytest.mark.asyncio
    async def test_cancelled_error_stops_cleanly(self) -> None:
        """Test that CancelledError stops without retry."""
        call_count = 0

        async def cancelled_handler() -> None:
            nonlocal call_count
            call_count += 1
            raise asyncio.CancelledError

        manager = _make_manager()
        manager._running = True

        await manager._run_subscription("test", cancelled_handler)

        assert call_count == 1
