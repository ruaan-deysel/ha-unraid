"""Data update coordinators for Unraid integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import UnraidAPIClient
from .const import DEFAULT_STORAGE_POLL_INTERVAL, DEFAULT_SYSTEM_POLL_INTERVAL
from .models import (
    ArrayCapacity,
    ArrayDisk,
    DockerContainer,
    Metrics,
    ParityCheck,
    Share,
    SystemInfo,
    UPSDevice,
    VmDomain,
)

try:
    from pydantic import BaseModel, ValidationError
except ImportError:
    from typing import Any as BaseModel  # type: ignore[misc,assignment]

    ValidationError = ValueError  # type: ignore[misc,assignment]

_LOGGER = logging.getLogger(__name__)


@dataclass
class UnraidSystemData:
    """Data class for system coordinator data."""

    info: SystemInfo
    metrics: Metrics
    containers: list[DockerContainer] = field(default_factory=list)
    vms: list[VmDomain] = field(default_factory=list)
    ups_devices: list[UPSDevice] = field(default_factory=list)
    notifications_unread: int = 0


@dataclass
class UnraidStorageData:
    """Data class for storage coordinator data."""

    array_state: str | None = None
    capacity: ArrayCapacity | None = None
    parity_status: ParityCheck | None = None
    boot: ArrayDisk | None = None  # Flash/boot device
    disks: list[ArrayDisk] = field(default_factory=list)
    parities: list[ArrayDisk] = field(default_factory=list)
    caches: list[ArrayDisk] = field(default_factory=list)
    shares: list[Share] = field(default_factory=list)


class UnraidSystemCoordinator(DataUpdateCoordinator[UnraidSystemData]):
    """Coordinator for Unraid system data (30s polling)."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: UnraidAPIClient,
        server_name: str,
        update_interval: int = DEFAULT_SYSTEM_POLL_INTERVAL,
    ) -> None:
        """
        Initialize the system coordinator.

        Args:
            hass: Home Assistant instance
            api_client: Unraid API client
            server_name: Server name for logging
            update_interval: Polling interval in seconds (default 30s)

        """
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{server_name} System",
            update_interval=timedelta(seconds=update_interval),
        )
        self.api_client = api_client
        self._server_name = server_name
        self._previously_unavailable = False

    async def _async_update_data(self) -> UnraidSystemData:
        """
        Fetch system data from Unraid server.

        Returns:
            UnraidSystemData containing parsed info, metrics, docker, vms, ups

        Raises:
            UpdateFailed: If update fails

        """
        _LOGGER.debug("Starting system data update")
        try:
            # Build combined query for system data
            query = """
                query {
                    info {
                        time
                        system { uuid manufacturer model serial }
                        cpu { brand threads cores packages { temp totalPower } }
                        os { hostname uptime kernel }
                        versions { core { unraid api kernel } }
                    }
                    metrics {
                        cpu { percentTotal }
                        memory {
                            total used free available percentTotal
                            swapTotal swapUsed swapFree percentSwapTotal
                        }
                    }
                    docker {
                        containers {
                            id names state image
                            ports { privatePort publicPort type }
                        }
                    }
                    vms { domains { id name state } }
                    upsDevices {
                        id name status
                        battery { chargeLevel estimatedRuntime }
                        power { inputVoltage outputVoltage loadPercentage }
                    }
                    notifications {
                        overview { unread { total info warning alert } }
                    }
                }
            """

            raw_data = await self.api_client.query(query)

            # Log recovery if previously unavailable
            if self._previously_unavailable:
                _LOGGER.info(
                    "Connection restored to Unraid server %s", self._server_name
                )
                self._previously_unavailable = False

            _LOGGER.debug("System data update completed successfully")

            # Parse raw data into Pydantic models
            return self._parse_system_data(raw_data)

        except aiohttp.ClientResponseError as err:
            self._previously_unavailable = True
            if err.status in (401, 403):
                msg = f"Authentication failed: {err.message}"
                _LOGGER.exception("System data update failed: %s", msg)
                raise UpdateFailed(msg) from err
            msg = f"HTTP error {err.status}: {err.message}"
            _LOGGER.exception("System data update failed: %s", msg)
            raise UpdateFailed(msg) from err
        except aiohttp.ClientError as err:
            self._previously_unavailable = True
            msg = f"Connection error: {err}"
            _LOGGER.exception("System data update failed: %s", msg)
            raise UpdateFailed(msg) from err
        except TimeoutError as err:
            self._previously_unavailable = True
            msg = "Request timeout"
            _LOGGER.exception("System data update failed: %s", msg)
            raise UpdateFailed(msg) from err
        except Exception as err:
            self._previously_unavailable = True
            msg = f"Unexpected error: {err}"
            _LOGGER.exception("System data update failed: %s", msg)
            raise UpdateFailed(msg) from err

    def _parse_system_data(self, raw_data: dict[str, Any]) -> UnraidSystemData:
        """Parse raw API data into typed UnraidSystemData."""
        # Parse system info
        info = SystemInfo.model_validate(raw_data.get("info", {}))

        # Parse metrics
        metrics = Metrics.model_validate(raw_data.get("metrics", {}))

        # Parse Docker containers
        containers: list[DockerContainer] = []
        docker_data = raw_data.get("docker", {})
        for raw_container in docker_data.get("containers", []):
            # Handle 'names' field - API returns list, we store as 'name'
            container_data = dict(raw_container)
            names = container_data.get("names")
            if names and len(names) > 0:
                container_data["name"] = names[0].lstrip("/")
            try:
                containers.append(DockerContainer.model_validate(container_data))
            except (ValidationError, TypeError, KeyError) as e:
                _LOGGER.warning("Failed to parse container: %s - %s", container_data, e)

        # Parse VMs
        vms: list[VmDomain] = []
        vms_data = raw_data.get("vms", {})
        for vm_data in vms_data.get("domains", []):
            try:
                vms.append(VmDomain.model_validate(vm_data))
            except (ValidationError, TypeError, KeyError) as e:
                _LOGGER.warning("Failed to parse VM: %s - %s", vm_data, e)

        # Parse UPS devices
        ups_devices: list[UPSDevice] = []
        for ups_data in raw_data.get("upsDevices", []) or []:
            try:
                ups_devices.append(UPSDevice.model_validate(ups_data))
            except (ValidationError, TypeError, KeyError) as e:
                _LOGGER.warning("Failed to parse UPS device: %s - %s", ups_data, e)

        # Parse notifications
        notifications = raw_data.get("notifications", {})
        overview = notifications.get("overview", {})
        unread = overview.get("unread", {})
        notifications_unread = unread.get("total", 0) or 0

        return UnraidSystemData(
            info=info,
            metrics=metrics,
            containers=containers,
            vms=vms,
            ups_devices=ups_devices,
            notifications_unread=notifications_unread,
        )


class UnraidStorageCoordinator(DataUpdateCoordinator[UnraidStorageData]):
    """Coordinator for Unraid storage data (5min polling)."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: UnraidAPIClient,
        server_name: str,
        update_interval: int = DEFAULT_STORAGE_POLL_INTERVAL,
    ) -> None:
        """
        Initialize the storage coordinator.

        Args:
            hass: Home Assistant instance
            api_client: Unraid API client
            server_name: Server name for logging
            update_interval: Polling interval in seconds (default 300s)

        """
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{server_name} Storage",
            update_interval=timedelta(seconds=update_interval),
        )
        self.api_client = api_client
        self._server_name = server_name
        self._previously_unavailable = False

    async def _async_update_data(self) -> UnraidStorageData:
        """
        Fetch storage data from Unraid server.

        Returns:
            UnraidStorageData containing parsed array, disks data

        Raises:
            UpdateFailed: If update fails

        """
        try:
            # Build combined query for storage data
            # Note: isSpinning is included to track disk standby state
            # This field is returned by the API without waking the disk
            #
            # IMPORTANT: We do NOT query the physical 'disks' endpoint for
            # temperature or smartStatus because those queries WAKE UP
            # sleeping disks. The array.disks already provides temp data
            # for spinning disks (returns null/0 for standby disks).
            # SMART status is a "nice to have" but not worth waking disks.
            query = """
                query {
                    array {
                        state
                        capacity { kilobytes { total used free } }
                        parityCheckStatus { status progress errors }
                        boot {
                            id name device size status type
                            fsSize fsUsed fsFree fsType
                        }
                        disks {
                            id idx name device size status temp type
                            fsSize fsUsed fsFree fsType isSpinning
                        }
                        parities { id idx name device size status temp type isSpinning }
                        caches {
                            id idx name device size status temp type
                            fsSize fsUsed fsFree fsType isSpinning
                        }
                    }
                    shares { id name size used free }
                }
            """

            raw_data = await self.api_client.query(query)

            # Log recovery if previously unavailable
            if self._previously_unavailable:
                _LOGGER.info(
                    "Connection restored to Unraid server %s (storage)",
                    self._server_name,
                )
                self._previously_unavailable = False

            return self._parse_storage_data(raw_data)

        except aiohttp.ClientResponseError as err:
            self._previously_unavailable = True
            if err.status in (401, 403):
                raise UpdateFailed(f"Authentication failed: {err.message}") from err
            raise UpdateFailed(f"HTTP error {err.status}: {err.message}") from err
        except aiohttp.ClientError as err:
            self._previously_unavailable = True
            raise UpdateFailed(f"Connection error: {err}") from err
        except TimeoutError as err:
            self._previously_unavailable = True
            raise UpdateFailed("Request timeout") from err
        except Exception as err:
            self._previously_unavailable = True
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _parse_model[T: BaseModel](
        self, data: dict[str, Any] | None, model_class: type[T], name: str
    ) -> T | None:
        """Parse a single model from data, returning None on failure."""
        if not data:
            return None
        try:
            return model_class.model_validate(data)
        except (ValidationError, TypeError, KeyError) as e:
            _LOGGER.warning("Failed to parse %s: %s - %s", name, data, e)
            return None

    def _parse_model_list[T: BaseModel](
        self, data_list: list[dict[str, Any]], model_class: type[T], name: str
    ) -> list[T]:
        """Parse a list of models from data, skipping failures."""
        results: list[T] = []
        for item in data_list:
            try:
                results.append(model_class.model_validate(item))
            except (ValidationError, TypeError, KeyError) as e:
                _LOGGER.warning("Failed to parse %s: %s - %s", name, item, e)
        return results

    def _parse_disks_with_type(
        self,
        data_list: list[dict[str, Any]],
        default_type: str,
        name: str,
    ) -> list[ArrayDisk]:
        """Parse disk list, setting default type BEFORE validation to avoid mutation."""
        results: list[ArrayDisk] = []
        for item in data_list:
            try:
                # Set type before validation if not already present
                disk_data = {**item, "type": item.get("type") or default_type}
                results.append(ArrayDisk.model_validate(disk_data))
            except (ValidationError, TypeError, KeyError) as e:
                _LOGGER.warning("Failed to parse %s: %s - %s", name, item, e)
        return results

    def _parse_storage_data(self, raw_data: dict[str, Any]) -> UnraidStorageData:
        """Parse raw API data into typed UnraidStorageData."""
        array_data = raw_data.get("array", {})

        # Parse disks with default type set BEFORE validation (not after)
        disks = self._parse_disks_with_type(array_data.get("disks", []), "DATA", "disk")
        parities = self._parse_disks_with_type(
            array_data.get("parities", []), "PARITY", "parity disk"
        )
        caches = self._parse_disks_with_type(
            array_data.get("caches", []), "CACHE", "cache disk"
        )

        # Parse boot device with type set before validation
        boot_data = array_data.get("boot")
        boot = None
        if boot_data:
            boot_with_type = {**boot_data, "type": boot_data.get("type") or "FLASH"}
            boot = self._parse_model(boot_with_type, ArrayDisk, "boot device")

        return UnraidStorageData(
            array_state=array_data.get("state"),
            capacity=self._parse_model(
                array_data.get("capacity"), ArrayCapacity, "capacity"
            ),
            parity_status=self._parse_model(
                array_data.get("parityCheckStatus"), ParityCheck, "parity status"
            ),
            boot=boot,
            disks=disks,
            parities=parities,
            caches=caches,
            shares=self._parse_model_list(raw_data.get("shares", []), Share, "share"),
        )
