"""Data update coordinators for Unraid integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
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
    DockerContainer,
    ParityCheck,
    Share,
    UPSDevice,
    VmDomain,
)

from .const import (
    STORAGE_POLL_INTERVAL,
    SYSTEM_POLL_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class UnraidSystemData:
    """Data class for system coordinator data using library models."""

    info: ServerInfo
    metrics: SystemMetrics
    containers: list[DockerContainer] = field(default_factory=list)
    vms: list[VmDomain] = field(default_factory=list)
    ups_devices: list[UPSDevice] = field(default_factory=list)
    notifications_unread: int = 0


@dataclass
class UnraidStorageData:
    """Data class for storage coordinator data using library models."""

    array: UnraidArray
    shares: list[Share] = field(default_factory=list)

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
        """Return boot/flash device."""
        return self.array.boot

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

    async def _query_optional_docker(self) -> list[DockerContainer]:
        """Query Docker containers (fails gracefully if Docker not enabled)."""
        try:
            return await self.api_client.typed_get_containers()
        except (UnraidAPIError, UnraidConnectionError) as err:
            _LOGGER.debug("Docker data not available: %s", err)
            return []

    async def _query_optional_vms(self) -> list[VmDomain]:
        """Query VMs (fails gracefully if VMs not enabled)."""
        try:
            return await self.api_client.typed_get_vms()
        except (UnraidAPIError, UnraidConnectionError) as err:
            _LOGGER.debug("VM data not available: %s", err)
            return []

    async def _query_optional_ups(self) -> list[UPSDevice]:
        """Query UPS devices (fails gracefully if no UPS configured)."""
        try:
            return await self.api_client.typed_get_ups_devices()
        except (UnraidAPIError, UnraidConnectionError) as err:
            _LOGGER.debug("UPS data not available: %s", err)
            return []

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
            # Query core system data (must succeed) using library typed methods
            info = await self.api_client.get_server_info()
            metrics = await self.api_client.get_system_metrics()
            notifications = await self.api_client.get_notification_overview()

            # Query optional services separately (fail gracefully if not enabled)
            containers = await self._query_optional_docker()
            vms = await self._query_optional_vms()
            ups_devices = await self._query_optional_ups()

            # Log recovery if previously unavailable
            if self._previously_unavailable:
                _LOGGER.info(
                    "Connection restored to Unraid server %s", self._server_name
                )
                self._previously_unavailable = False

            _LOGGER.debug("System data update completed successfully")

            return UnraidSystemData(
                info=info,
                metrics=metrics,
                containers=containers,
                vms=vms,
                ups_devices=ups_devices,
                notifications_unread=notifications.unread.total
                if notifications.unread
                else 0,
            )

        except UnraidAuthenticationError as err:
            self._previously_unavailable = True
            msg = f"Authentication failed: {err}"
            _LOGGER.error("System data update failed: %s", msg)
            raise ConfigEntryAuthFailed(msg) from err
        except (UnraidConnectionError, UnraidTimeoutError) as err:
            self._previously_unavailable = True
            msg = f"Connection error: {err}"
            _LOGGER.exception("System data update failed: %s", msg)
            raise UpdateFailed(msg) from err
        except UnraidAPIError as err:
            self._previously_unavailable = True
            msg = f"API error: {err}"
            _LOGGER.exception("System data update failed: %s", msg)
            raise UpdateFailed(msg) from err
        except Exception as err:
            self._previously_unavailable = True
            msg = f"Unexpected error: {err}"
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
        except (UnraidAPIError, UnraidConnectionError) as err:
            # Log at debug level - shares are optional/nice-to-have
            _LOGGER.debug(
                "Shares query failed (will continue without share data): %s", err
            )
            return []

    async def _async_update_data(self) -> UnraidStorageData:
        """
        Fetch storage data from Unraid server using library typed methods.

        Returns:
            UnraidStorageData containing array and shares data

        Raises:
            UpdateFailed: If update fails

        """
        try:
            # Get array data using typed library method
            # The library handles the GraphQL query internally
            array = await self.api_client.typed_get_array()

            # Query shares separately (gracefully handles failure)
            shares = await self._query_optional_shares()

            # Log recovery if previously unavailable
            if self._previously_unavailable:
                _LOGGER.info(
                    "Connection restored to Unraid server %s (storage)",
                    self._server_name,
                )
                self._previously_unavailable = False

            return UnraidStorageData(array=array, shares=shares)

        except UnraidAuthenticationError as err:
            self._previously_unavailable = True
            _LOGGER.error("Storage data update failed: Authentication failed: %s", err)
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except (UnraidConnectionError, UnraidTimeoutError) as err:
            self._previously_unavailable = True
            raise UpdateFailed(f"Connection error: {err}") from err
        except UnraidAPIError as err:
            self._previously_unavailable = True
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            self._previously_unavailable = True
            raise UpdateFailed(f"Unexpected error: {err}") from err
