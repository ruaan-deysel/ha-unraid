"""Data update coordinators for Unraid integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from unraid_api import (
    ServerInfo,
    SystemMetrics,
    UnraidArray,
    UnraidClient,
)
from unraid_api.exceptions import (
    UnraidAPIError,
    UnraidAuthenticationError,
    UnraidConnectionError,
    UnraidTimeoutError,
)
from unraid_api.models import (
    ArrayCapacity,
    ArrayDisk,
    Cloud,
    Connect,
    DockerContainer,
    Network,
    NotificationOverview,
    ParityCheck,
    ParityHistoryEntry,
    Plugin,
    Registration,
    RemoteAccess,
    Service,
    Share,
    UPSDevice,
    Vars,
    VmDomain,
)

from .const import (
    DOMAIN,
    INFRA_POLL_INTERVAL,
    STORAGE_POLL_INTERVAL,
    SYSTEM_POLL_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)
MAX_SEEN_NOTIFICATION_IDS = 1000
NOTIFICATION_EVENT_TYPE_CREATED = "notification_created"


@dataclass
class UnraidSystemData:
    """Data class for system coordinator data using library models."""

    info: ServerInfo
    metrics: SystemMetrics
    containers: list[DockerContainer] = field(default_factory=list)
    vms: list[VmDomain] = field(default_factory=list)
    ups_devices: list[UPSDevice] = field(default_factory=list)
    notification_overview: NotificationOverview | None = None
    notifications_unread: int = 0


@dataclass(frozen=True)
class UnraidNotificationEventData:
    """Notification event payload emitted to EventEntity listeners."""

    event_type: str
    notification_id: str
    title: str
    subject: str
    description: str
    timestamp: str
    formatted_timestamp: str
    importance: str
    link: str
    notification_type: str


@dataclass
class UnraidStorageData:
    """Data class for storage coordinator data using library models."""

    array: UnraidArray
    shares: list[Share] = field(default_factory=list)
    parity_history: list[ParityHistoryEntry] = field(default_factory=list)

    # Convenience properties delegating to array
    @property
    def array_state(self) -> str | None:
        """Return array state."""
        return self.array.state

    @property
    def capacity(self) -> ArrayCapacity | None:
        """Return array capacity."""
        return self.array.capacity

    @property
    def parity_status(self) -> ParityCheck | None:
        """Return parity check status."""
        return self.array.parityCheckStatus

    @property
    def boot(self) -> ArrayDisk | None:
        """Return boot/flash device, falling back to bootDevices[0]."""
        if self.array.boot is not None:
            return self.array.boot
        if self.array.bootDevices:
            return self.array.bootDevices[0]
        return None

    @property
    def disks(self) -> list[ArrayDisk]:
        """Return data disks."""
        return self.array.disks

    @property
    def parities(self) -> list[ArrayDisk]:
        """Return parity disks."""
        return self.array.parities

    @property
    def caches(self) -> list[ArrayDisk]:
        """Return cache disks."""
        return self.array.caches


class UnraidSystemCoordinator(DataUpdateCoordinator[UnraidSystemData]):
    """Coordinator for Unraid system data (polls every 30 seconds)."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: UnraidClient,
        server_name: str,
        config_entry: ConfigEntry,
    ) -> None:
        """
        Initialize the system coordinator.

        Args:
            hass: Home Assistant instance
            api_client: Unraid API client (from unraid_api library)
            server_name: Server name for logging
            config_entry: The config entry for this coordinator

        """
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{server_name} System",
            update_interval=timedelta(seconds=SYSTEM_POLL_INTERVAL),
            config_entry=config_entry,
        )
        self.api_client = api_client
        self._server_name = server_name
        self._previously_unavailable = False
        self._event_listeners: dict[
            str, list[Callable[[UnraidNotificationEventData], None]]
        ] = {}
        self._seen_notification_store = Store[dict[str, list[str]]](
            hass,
            version=1,
            key=f"{DOMAIN}.{config_entry.entry_id}.notifications",
        )
        self._seen_notification_ids: set[str] = set()
        self._seen_ids_loaded = False

    def async_add_event_listener(
        self,
        callback: Callable[[UnraidNotificationEventData], None],
        target_event_id: str,
    ) -> Callable[[], None]:
        """Register an event callback for a specific event type."""
        listeners = self._event_listeners.setdefault(target_event_id, [])
        listeners.append(callback)

        def _remove_listener() -> None:
            if target_event_id not in self._event_listeners:
                return
            self._event_listeners[target_event_id] = [
                listener
                for listener in self._event_listeners[target_event_id]
                if listener != callback
            ]
            if not self._event_listeners[target_event_id]:
                self._event_listeners.pop(target_event_id, None)

        return _remove_listener

    def _async_notify_event_listeners(
        self, event_data: UnraidNotificationEventData
    ) -> None:
        """Notify listeners about a newly detected event."""
        for callback in self._event_listeners.get(event_data.event_type, []):
            callback(event_data)

    async def _async_load_seen_notification_ids(self) -> None:
        """Load persisted seen notification IDs once."""
        if self._seen_ids_loaded:
            return

        try:
            stored_data = await self._seen_notification_store.async_load()
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Failed to load seen notification IDs for %s: %s",
                self._server_name,
                err,
            )
            self._seen_ids_loaded = True
            return

        seen_ids = stored_data.get("seen_ids", []) if stored_data else []
        self._seen_notification_ids = set(seen_ids[:MAX_SEEN_NOTIFICATION_IDS])
        _LOGGER.debug(
            "Loaded %d seen notification IDs for %s",
            len(self._seen_notification_ids),
            self._server_name,
        )
        self._seen_ids_loaded = True

    async def _async_save_seen_notification_ids(self) -> None:
        """Persist trimmed seen notification IDs."""
        sorted_ids = sorted(self._seen_notification_ids)
        trimmed_ids = sorted_ids[-MAX_SEEN_NOTIFICATION_IDS:]
        self._seen_notification_ids = set(trimmed_ids)
        try:
            await self._seen_notification_store.async_save({"seen_ids": trimmed_ids})
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Failed to save seen notification IDs for %s: %s",
                self._server_name,
                err,
            )
            return

        _LOGGER.debug(
            "Saved %d seen notification IDs for %s",
            len(self._seen_notification_ids),
            self._server_name,
        )

    @staticmethod
    def _normalize_notification_response(response: Any) -> list[Any]:
        """Normalize notification responses into a list of notification records."""
        if response is None:
            return []

        if isinstance(response, dict):
            return list(response.get("list") or [])

        model_list = getattr(response, "list", None)
        if model_list is not None:
            return list(model_list or [])

        if isinstance(response, list):
            return response

        if isinstance(response, tuple):
            return list(response)

        _LOGGER.debug(
            "Ignoring unexpected notification response type: %s",
            type(response).__name__,
        )
        return []

    @staticmethod
    def _notification_response_shape(response: Any) -> str:
        """Return a compact response shape string for debug logging."""
        if isinstance(response, dict):
            list_value = response.get("list")
            list_count = len(list_value) if isinstance(list_value, list) else "n/a"
            return (
                f"dict(keys={sorted(response.keys())}, "
                f"list_type={type(list_value).__name__}, list_count={list_count})"
            )

        if isinstance(response, list):
            return f"list(len={len(response)})"

        return type(response).__name__

    async def _async_get_unread_notifications(self) -> list[Any]:
        """Fetch unread notifications via available API wrapper methods."""
        _LOGGER.debug("Polling unread notifications for %s", self._server_name)
        try:
            if hasattr(self.api_client, "typed_get_notifications"):
                response = await self.api_client.typed_get_notifications(
                    notification_type="UNREAD",
                    offset=0,
                    limit=200,
                )
                _LOGGER.debug(
                    "Unread notifications API path=typed_get_notifications shape=%s for %s",
                    self._notification_response_shape(response),
                    self._server_name,
                )
                notification_list = self._normalize_notification_response(response)
                _LOGGER.debug(
                    "Extracted %d unread notification records for %s via typed API",
                    len(notification_list),
                    self._server_name,
                )
                return notification_list

            if hasattr(self.api_client, "get_notifications"):
                response = await self.api_client.get_notifications(
                    notification_type="UNREAD",
                    offset=0,
                    limit=200,
                )
                _LOGGER.debug(
                    "Unread notifications API path=get_notifications shape=%s for %s",
                    self._notification_response_shape(response),
                    self._server_name,
                )
                notification_list = self._normalize_notification_response(response)
                _LOGGER.debug(
                    "Extracted %d unread notification records for %s via API",
                    len(notification_list),
                    self._server_name,
                )
                return notification_list
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.error(
                "Failed to poll unread notifications for %s: %s",
                self._server_name,
                err,
            )
            raise

        _LOGGER.debug(
            "Notification list API is not available on UnraidClient for %s",
            self._server_name,
        )
        return []

    @staticmethod
    def _notification_field(notification: Any, key: str) -> Any:
        """Return a notification field from model or dict payloads."""
        if isinstance(notification, dict):
            return notification.get(key)
        return getattr(notification, key, None)

    @staticmethod
    def _to_notification_event_data(
        notification: Any,
    ) -> UnraidNotificationEventData | None:
        """Convert unread notification payload to event data."""
        notification_id = UnraidSystemCoordinator._notification_field(
            notification, "id"
        )
        if not notification_id:
            return None

        timestamp = UnraidSystemCoordinator._notification_field(
            notification, "timestamp"
        )
        if not timestamp:
            return None

        formatted_timestamp = UnraidSystemCoordinator._notification_field(
            notification, "formattedTimestamp"
        )
        notification_type = UnraidSystemCoordinator._notification_field(
            notification, "type"
        )

        return UnraidNotificationEventData(
            event_type=NOTIFICATION_EVENT_TYPE_CREATED,
            notification_id=str(notification_id),
            title=str(
                UnraidSystemCoordinator._notification_field(notification, "title") or ""
            ),
            subject=str(
                UnraidSystemCoordinator._notification_field(notification, "subject")
                or ""
            ),
            description=str(
                UnraidSystemCoordinator._notification_field(notification, "description")
                or ""
            ),
            timestamp=str(timestamp or ""),
            formatted_timestamp=str(formatted_timestamp or ""),
            importance=str(
                UnraidSystemCoordinator._notification_field(notification, "importance")
                or ""
            ),
            link=str(
                UnraidSystemCoordinator._notification_field(notification, "link")
                or ""
            ),
            notification_type=str(notification_type or "UNREAD"),
        )

    async def _async_process_notification_events(self) -> None:
        """Detect new unread notifications and notify listeners."""
        await self._async_load_seen_notification_ids()

        notifications = await self._async_get_unread_notifications()
        unread_by_id: dict[str, Any] = {}
        for notification in notifications:
            notification_id = self._notification_field(notification, "id")
            notification_type = str(
                self._notification_field(notification, "type") or ""
            )
            if not notification_id:
                _LOGGER.warning(
                    "Skipping notification without ID on %s", self._server_name
                )
                continue

            if notification_type.upper() != "UNREAD":
                continue

            timestamp = self._notification_field(notification, "timestamp")
            if not timestamp:
                _LOGGER.warning(
                    "Skipping notification %s without timestamp on %s",
                    notification_id,
                    self._server_name,
                )
                continue
            unread_by_id[str(notification_id)] = notification

        unread_ids = set(unread_by_id)
        if not self._seen_notification_ids:
            self._seen_notification_ids = set(unread_ids)
            await self._async_save_seen_notification_ids()
            return

        unseen_ids = unread_ids - self._seen_notification_ids
        if not unseen_ids:
            return

        unseen_notifications = [
            unread_by_id[notification_id] for notification_id in unseen_ids
        ]
        unseen_notifications.sort(
            key=lambda notification: str(
                self._notification_field(notification, "timestamp") or ""
            )
        )

        emitted_any = False
        for notification in unseen_notifications:
            event_data = self._to_notification_event_data(notification)
            if event_data is None:
                notification_id = self._notification_field(notification, "id")
                _LOGGER.warning(
                    "Skipping invalid notification payload on %s: id=%s",
                    self._server_name,
                    notification_id,
                )
                continue

            try:
                self._async_notify_event_listeners(event_data)
            except Exception:
                _LOGGER.exception(
                    "Failed to emit notification event for %s on %s",
                    event_data.notification_id,
                    self._server_name,
                )
                continue

            _LOGGER.info(
                "Emitted Unraid notification event %s (%s) at %s",
                event_data.notification_id,
                event_data.title,
                event_data.timestamp,
            )
            self._seen_notification_ids.add(event_data.notification_id)
            emitted_any = True

        if emitted_any:
            await self._async_save_seen_notification_ids()

    async def _query_optional_docker(self) -> list[DockerContainer]:
        """Query Docker containers (fails gracefully if Docker not enabled)."""
        try:
            return await self.api_client.typed_get_containers()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Docker data not available: %s", err)
            return []

    async def _query_optional_vms(self) -> list[VmDomain]:
        """Query VMs (fails gracefully if VMs not enabled)."""
        try:
            return await self.api_client.typed_get_vms()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("VM data not available: %s", err)
            return []

    async def _query_optional_ups(self) -> list[UPSDevice]:
        """Query UPS devices (fails gracefully if no UPS configured)."""
        try:
            return await self.api_client.typed_get_ups_devices()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("UPS data not available: %s", err)
            return []

    # Action wrappers for entity control operations
    async def async_start_container(self, container_id: str) -> None:
        """Start a Docker container."""
        await self.api_client.start_container(container_id)

    async def async_stop_container(self, container_id: str) -> None:
        """Stop a Docker container."""
        await self.api_client.stop_container(container_id)

    async def async_restart_container(self, container_id: str) -> None:
        """Restart a Docker container."""
        await self.api_client.restart_container(container_id)

    async def async_update_container(self, container_id: str) -> None:
        """Update a Docker container to its latest image."""
        await self.api_client.update_container(container_id)

    async def async_start_vm(self, vm_id: str) -> None:
        """Start a virtual machine."""
        await self.api_client.start_vm(vm_id)

    async def async_stop_vm(self, vm_id: str) -> None:
        """Stop a virtual machine."""
        await self.api_client.stop_vm(vm_id)

    async def async_force_stop_vm(self, vm_id: str) -> None:
        """Force stop a virtual machine."""
        await self.api_client.force_stop_vm(vm_id)

    async def async_reboot_vm(self, vm_id: str) -> None:
        """Reboot a virtual machine."""
        await self.api_client.reboot_vm(vm_id)

    async def async_pause_vm(self, vm_id: str) -> None:
        """Pause a virtual machine."""
        await self.api_client.pause_vm(vm_id)

    async def async_resume_vm(self, vm_id: str) -> None:
        """Resume a virtual machine."""
        await self.api_client.resume_vm(vm_id)

    async def async_reset_vm(self, vm_id: str) -> None:
        """Reset a virtual machine."""
        await self.api_client.reset_vm(vm_id)

    async def async_archive_all_notifications(self) -> None:
        """Archive all notifications."""
        await self.api_client.archive_all_notifications()

    async def async_delete_all_notifications(self) -> None:
        """Delete all archived notifications."""
        await self.api_client.delete_all_notifications()

    async def _async_update_data(self) -> UnraidSystemData:
        """
        Fetch system data from Unraid server using library typed methods.

        Returns:
            UnraidSystemData containing server info, metrics, docker, vms, ups

        Raises:
            UpdateFailed: If update fails

        """
        _LOGGER.debug("Starting system data update")
        try:
            # Phase 1: Required calls — run concurrently; any failure raises immediately
            # NOTE: We use get_system_metrics_safe() instead of
            # get_system_metrics() to avoid querying metrics.temperature.sensors
            # which triggers smartctl disk reads and wakes sleeping disks.
            info, metrics, notifications = await asyncio.gather(
                self.api_client.get_server_info(),
                self.api_client.get_system_metrics_safe(),
                self.api_client.get_notification_overview(),
            )

            # Phase 2: Optional services — run concurrently; each fails gracefully
            containers, vms, ups_devices = await asyncio.gather(
                self._query_optional_docker(),
                self._query_optional_vms(),
                self._query_optional_ups(),
            )

            # Log recovery if previously unavailable
            if self._previously_unavailable:
                _LOGGER.info(
                    "Connection restored to Unraid server %s", self._server_name
                )
                self._previously_unavailable = False

            _LOGGER.debug("System data update completed successfully")

            try:
                await self._async_process_notification_events()
            except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
                _LOGGER.debug(
                    "Skipping notification event processing due to API issue: %s",
                    err,
                )
            except Exception:
                _LOGGER.exception(
                    "Unexpected notification event processing failure on %s",
                    self._server_name,
                )

            return UnraidSystemData(
                info=info,
                metrics=metrics,
                containers=containers,
                vms=vms,
                ups_devices=ups_devices,
                notification_overview=notifications,
                notifications_unread=notifications.unread.total
                if notifications.unread
                else 0,
            )

        except UnraidAuthenticationError as err:
            self._previously_unavailable = True
            msg = f"Authentication failed: {err}"
            _LOGGER.error("System data update failed: %s", msg)
            raise ConfigEntryAuthFailed(msg) from err
        # RuntimeError: catch aiohttp session-closed errors during HA shutdown
        except (UnraidConnectionError, UnraidTimeoutError, RuntimeError) as err:
            self._previously_unavailable = True
            msg = f"Connection error: {err}"
            _LOGGER.exception("System data update failed: %s", msg)
            raise UpdateFailed(msg) from err
        except UnraidAPIError as err:
            self._previously_unavailable = True
            msg = f"API error: {err}"
            _LOGGER.exception("System data update failed: %s", msg)
            raise UpdateFailed(msg) from err


class UnraidStorageCoordinator(DataUpdateCoordinator[UnraidStorageData]):
    """Coordinator for Unraid storage data (polls every 5 minutes)."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: UnraidClient,
        server_name: str,
        config_entry: ConfigEntry,
    ) -> None:
        """
        Initialize the storage coordinator.

        Args:
            hass: Home Assistant instance
            api_client: Unraid API client (from unraid_api library)
            server_name: Server name for logging
            config_entry: The config entry for this coordinator

        """
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{server_name} Storage",
            update_interval=timedelta(seconds=STORAGE_POLL_INTERVAL),
            config_entry=config_entry,
        )
        self.api_client = api_client
        self._server_name = server_name
        self._previously_unavailable = False

    async def _query_optional_shares(self) -> list[Share]:
        """
        Query shares separately to handle servers with problematic shares.

        Some Unraid servers have shares where the GraphQL API returns null for
        the 'id' field, causing the entire shares query to fail. By querying
        shares separately, we can gracefully handle this and still return
        array/disk data even if shares fail.
        """
        try:
            return await self.api_client.typed_get_shares()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            # Log at debug level - shares are optional/nice-to-have
            _LOGGER.debug(
                "Shares query failed (will continue without share data): %s", err
            )
            return []

    async def _query_optional_parity_history(self) -> list[ParityHistoryEntry]:
        """Query parity history (fails gracefully)."""
        try:
            return await self.api_client.get_parity_history()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Parity history not available: %s", err)
            return []

    # Action wrappers for entity control operations
    async def async_start_array(self) -> None:
        """Start the Unraid array."""
        await self.api_client.start_array()

    async def async_stop_array(self) -> None:
        """Stop the Unraid array."""
        await self.api_client.stop_array()

    async def async_start_parity_check(self, *, correct: bool) -> None:
        """Start a parity check."""
        await self.api_client.start_parity_check(correct=correct)

    async def async_cancel_parity_check(self) -> None:
        """Cancel a running parity check."""
        await self.api_client.cancel_parity_check()

    async def async_pause_parity_check(self) -> None:
        """Pause a running parity check."""
        await self.api_client.pause_parity_check()

    async def async_resume_parity_check(self) -> None:
        """Resume a paused parity check."""
        await self.api_client.resume_parity_check()

    async def async_spin_up_disk(self, disk_id: str) -> None:
        """Spin up a disk."""
        await self.api_client.spin_up_disk(disk_id)

    async def async_spin_down_disk(self, disk_id: str) -> None:
        """Spin down a disk."""
        await self.api_client.spin_down_disk(disk_id)

    async def _async_update_data(self) -> UnraidStorageData:
        """
        Fetch storage data from Unraid server using library typed methods.

        Returns:
            UnraidStorageData containing array and shares data

        Raises:
            UpdateFailed: If update fails

        """
        try:
            # Phase 1: Required array data
            array = await self.api_client.typed_get_array()

            # Phase 2: Optional queries — run concurrently; each fails gracefully
            shares, parity_history = await asyncio.gather(
                self._query_optional_shares(),
                self._query_optional_parity_history(),
            )

            # Log recovery if previously unavailable
            if self._previously_unavailable:
                _LOGGER.info(
                    "Connection restored to Unraid server %s (storage)",
                    self._server_name,
                )
                self._previously_unavailable = False

            return UnraidStorageData(
                array=array, shares=shares, parity_history=parity_history
            )

        except UnraidAuthenticationError as err:
            self._previously_unavailable = True
            _LOGGER.error("Storage data update failed: Authentication failed: %s", err)
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        # RuntimeError: catch aiohttp session-closed errors during HA shutdown
        except (UnraidConnectionError, UnraidTimeoutError, RuntimeError) as err:
            self._previously_unavailable = True
            raise UpdateFailed(f"Connection error: {err}") from err
        except UnraidAPIError as err:
            self._previously_unavailable = True
            raise UpdateFailed(f"API error: {err}") from err


@dataclass
class UnraidInfraData:
    """Data class for infrastructure coordinator data (slow-changing)."""

    services: list[Service] = field(default_factory=list)
    registration: Registration | None = None
    cloud: Cloud | None = None
    connect: Connect | None = None
    remote_access: RemoteAccess | None = None
    vars: Vars | None = None
    plugins: list[Plugin] = field(default_factory=list)
    network: Network | None = None


class UnraidInfraCoordinator(DataUpdateCoordinator[UnraidInfraData]):
    """
    Coordinator for Unraid infrastructure data (polls every 15 minutes).

    Handles slow-changing data: services, registration, cloud/connect status,
    system variables, and plugins.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: UnraidClient,
        server_name: str,
        config_entry: ConfigEntry,
    ) -> None:
        """
        Initialize the infrastructure coordinator.

        Args:
            hass: Home Assistant instance
            api_client: Unraid API client (from unraid_api library)
            server_name: Server name for logging
            config_entry: The config entry for this coordinator

        """
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{server_name} Infrastructure",
            update_interval=timedelta(seconds=INFRA_POLL_INTERVAL),
            config_entry=config_entry,
        )
        self.api_client = api_client
        self._server_name = server_name
        self._previously_unavailable = False

    async def _query_optional_services(self) -> list[Service]:
        """Query services (fails gracefully)."""
        try:
            return await self.api_client.typed_get_services()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Services data not available: %s", err)
            return []

    async def _query_optional_registration(self) -> Registration | None:
        """Query registration info (fails gracefully)."""
        try:
            return await self.api_client.typed_get_registration()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Registration data not available: %s", err)
            return None

    async def _query_optional_cloud(self) -> Cloud | None:
        """Query cloud status (fails gracefully)."""
        try:
            return await self.api_client.typed_get_cloud()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Cloud data not available: %s", err)
            return None

    async def _query_optional_connect(self) -> Connect | None:
        """Query connect status (fails gracefully)."""
        try:
            return await self.api_client.typed_get_connect()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Connect data not available: %s", err)
            return None

    async def _query_optional_remote_access(self) -> RemoteAccess | None:
        """Query remote access config (fails gracefully)."""
        try:
            return await self.api_client.typed_get_remote_access()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Remote access data not available: %s", err)
            return None

    async def _query_optional_vars(self) -> Vars | None:
        """Query system variables (fails gracefully)."""
        try:
            return await self.api_client.typed_get_vars()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Vars data not available: %s", err)
            return None

    async def _query_optional_plugins(self) -> list[Plugin]:
        """Query plugins (fails gracefully)."""
        try:
            return await self.api_client.typed_get_plugins()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Plugins data not available: %s", err)
            return []

    async def _query_optional_network(self) -> Network | None:
        """Query network info (fails gracefully)."""
        try:
            return await self.api_client.typed_get_network()
        except UnraidAuthenticationError:
            raise
        except (UnraidAPIError, UnraidConnectionError, UnraidTimeoutError) as err:
            _LOGGER.debug("Network data not available: %s", err)
            return None

    async def _async_update_data(self) -> UnraidInfraData:
        """
        Fetch infrastructure data from Unraid server.

        Returns:
            UnraidInfraData containing services, registration, cloud, etc.

        Raises:
            UpdateFailed: If update fails

        """
        _LOGGER.debug("Starting infrastructure data update")
        try:
            # All sub-queries are optional — run all concurrently
            (
                services,
                registration,
                cloud,
                connect,
                remote_access,
                vars_data,
                plugins,
                network,
            ) = await asyncio.gather(
                self._query_optional_services(),
                self._query_optional_registration(),
                self._query_optional_cloud(),
                self._query_optional_connect(),
                self._query_optional_remote_access(),
                self._query_optional_vars(),
                self._query_optional_plugins(),
                self._query_optional_network(),
            )

            # Log recovery if previously unavailable
            if self._previously_unavailable:
                _LOGGER.info(
                    "Connection restored to Unraid server %s (infrastructure)",
                    self._server_name,
                )
                self._previously_unavailable = False

            _LOGGER.debug(
                "Infrastructure data update completed: %d services, %d plugins",
                len(services),
                len(plugins),
            )

            return UnraidInfraData(
                services=services,
                registration=registration,
                cloud=cloud,
                connect=connect,
                remote_access=remote_access,
                vars=vars_data,
                plugins=plugins,
                network=network,
            )

        except UnraidAuthenticationError as err:
            self._previously_unavailable = True
            msg = f"Authentication failed: {err}"
            _LOGGER.error("Infrastructure data update failed: %s", msg)
            raise ConfigEntryAuthFailed(msg) from err
        # RuntimeError: catch aiohttp session-closed errors during HA shutdown
        except (UnraidConnectionError, UnraidTimeoutError, RuntimeError) as err:
            self._previously_unavailable = True
            raise UpdateFailed(f"Connection error: {err}") from err
        except UnraidAPIError as err:
            self._previously_unavailable = True
            raise UpdateFailed(f"API error: {err}") from err
