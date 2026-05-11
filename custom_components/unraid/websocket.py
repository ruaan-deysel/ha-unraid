"""WebSocket subscription manager for real-time Unraid data updates."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from unraid_api.exceptions import (
    UnraidAPIError,
    UnraidAuthenticationError,
    UnraidConnectionError,
    UnraidTimeoutError,
)
from unraid_api.models import DockerContainerStats

from .const import (
    WS_INITIAL_RETRY_DELAY,
    WS_MAX_RETRY_DELAY,
    WS_REFRESH_DEBOUNCE_SECONDS,
    WS_RETRY_BACKOFF_FACTOR,
)

if TYPE_CHECKING:
    from unraid_api import UnraidClient

    from .coordinator import UnraidSystemCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class ContainerStatsSnapshot:
    """Snapshot of real-time container stats from WebSocket subscription."""

    stats: dict[str, DockerContainerStats] = field(default_factory=dict)


class UnraidWebSocketManager:
    """
    Manage WebSocket subscriptions for real-time data updates.

    Runs background tasks for each subscription type, pushing updates
    to the relevant coordinators. Automatically reconnects with
    exponential backoff on disconnects.
    """

    def __init__(
        self,
        api_client: UnraidClient,
        system_coordinator: UnraidSystemCoordinator,
        server_name: str,
    ) -> None:
        """Initialize the WebSocket manager."""
        self._api_client = api_client
        self._system_coordinator = system_coordinator
        self._server_name = server_name
        self._tasks: list[asyncio.Task[None]] = []
        self._running = False
        self.container_stats: ContainerStatsSnapshot = ContainerStatsSnapshot()
        # Debounce timestamps for WebSocket-triggered coordinator refreshes
        # (leading-edge: first event refreshes immediately, subsequent events
        # within the cooldown window are suppressed)
        self._last_ups_refresh: float = 0.0
        self._last_notification_refresh: float = 0.0

    async def async_start(self) -> None:
        """Start all WebSocket subscriptions as background tasks."""
        if self._running:
            return
        self._running = True
        _LOGGER.info("Starting WebSocket subscriptions for %s", self._server_name)

        self._tasks = [
            asyncio.create_task(
                self._run_subscription("container_stats", self._handle_container_stats),
                name=f"unraid_ws_container_stats_{self._server_name}",
            ),
            asyncio.create_task(
                self._run_subscription("ups_updates", self._handle_ups_updates),
                name=f"unraid_ws_ups_updates_{self._server_name}",
            ),
            asyncio.create_task(
                self._run_subscription(
                    "notification_added",
                    self._handle_notification_added,
                ),
                name=f"unraid_ws_notification_added_{self._server_name}",
            ),
        ]

    async def async_stop(self) -> None:
        """Stop all WebSocket subscriptions and cancel background tasks."""
        if not self._running:
            return
        self._running = False
        _LOGGER.info("Stopping WebSocket subscriptions for %s", self._server_name)

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self.container_stats = ContainerStatsSnapshot()

    async def _run_subscription(
        self,
        name: str,
        handler: Any,
    ) -> None:
        """Run a subscription with automatic reconnection and backoff."""
        retry_delay = WS_INITIAL_RETRY_DELAY

        while self._running:
            try:
                _LOGGER.debug(
                    "Connecting %s WebSocket subscription for %s",
                    name,
                    self._server_name,
                )
                await handler()
                # If handler returns normally (generator exhausted), reconnect
                retry_delay = WS_INITIAL_RETRY_DELAY

            except UnraidAuthenticationError:
                _LOGGER.error(
                    "WebSocket auth failed for %s (%s)",
                    name,
                    self._server_name,
                )
                return

            except (UnraidConnectionError, UnraidTimeoutError, UnraidAPIError) as err:
                if not self._running:
                    return
                _LOGGER.debug(
                    "WebSocket %s disconnected for %s: %s — retrying in %ss",
                    name,
                    self._server_name,
                    err,
                    retry_delay,
                )

            except asyncio.CancelledError:
                return

            except Exception:
                if not self._running:
                    return
                _LOGGER.exception(
                    "Unexpected error in %s WebSocket for %s",
                    name,
                    self._server_name,
                )

            if not self._running:
                return

            # Wait before reconnecting (with backoff)
            try:
                await asyncio.sleep(retry_delay)
            except asyncio.CancelledError:
                return
            retry_delay = min(retry_delay * WS_RETRY_BACKOFF_FACTOR, WS_MAX_RETRY_DELAY)

    def _should_trigger_refresh(self, last_refresh_time: float) -> bool:
        """Return True if enough time has elapsed since the last refresh."""
        return time.monotonic() - last_refresh_time >= WS_REFRESH_DEBOUNCE_SECONDS

    async def _handle_container_stats(self) -> None:
        """Process container stats subscription and update coordinator."""
        async for stats in self._api_client.subscribe_container_stats():
            if not self._running:
                break
            if stats.id is None:
                continue
            self.container_stats.stats[stats.id] = stats

    async def _handle_ups_updates(self) -> None:
        """Process UPS state subscription and trigger system refresh."""
        async for update in self._api_client.subscribe_ups_updates():
            if not self._running:
                break
            _LOGGER.debug(
                "UPS update received for %s: %s",
                self._server_name,
                update,
            )
            if self._should_trigger_refresh(self._last_ups_refresh):
                self._last_ups_refresh = time.monotonic()
                await self._system_coordinator.async_request_refresh()
            else:
                _LOGGER.debug(
                    "UPS update for %s suppressed (debounce cooldown active)",
                    self._server_name,
                )

    async def _handle_notification_added(self) -> None:
        """Process notification subscription and trigger system refresh."""
        async for notification in self._api_client.subscribe_notification_added():
            if not self._running:
                break
            _LOGGER.debug(
                "Notification received for %s: %s — %s",
                self._server_name,
                notification.importance,
                notification.title,
            )
            if self._should_trigger_refresh(self._last_notification_refresh):
                self._last_notification_refresh = time.monotonic()
                await self._system_coordinator.async_request_refresh()
            else:
                _LOGGER.debug(
                    "Notification refresh for %s suppressed (debounce cooldown active)",
                    self._server_name,
                )
