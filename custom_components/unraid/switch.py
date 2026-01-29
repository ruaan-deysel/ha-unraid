"""Switch entities for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from unraid_api import UnraidClient
from unraid_api.models import ArrayDisk, DockerContainer, VmDomain

from .const import (
    DOMAIN,
    STATE_ARRAY_STARTED,
    STATE_CONTAINER_RUNNING,
    VM_RUNNING_STATES,
)
from .entity import UnraidBaseEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .coordinator import (
        UnraidStorageCoordinator,
        UnraidStorageData,
        UnraidSystemCoordinator,
        UnraidSystemData,
    )

_LOGGER = logging.getLogger(__name__)

# Switches make API calls, limit to one at a time to avoid overloading server
PARALLEL_UPDATES = 1

# Export PARALLEL_UPDATES for Home Assistant
__all__ = ["PARALLEL_UPDATES", "async_setup_entry"]


class UnraidSwitchEntity(UnraidBaseEntity, SwitchEntity):
    """Base class for Unraid switch entities."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        resource_id: str,
        name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize switch entity."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=resource_id,
            name=name,
            server_info=server_info,
        )
        # Store API client for mutations (start/stop containers, VMs)
        self.api_client = api_client


class DockerContainerSwitch(UnraidSwitchEntity):
    """Docker container control switch."""

    _attr_translation_key = "docker_container"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        container: DockerContainer,
    ) -> None:
        """Initialize docker container switch."""
        # Container IDs are ephemeral (change on container update/recreate)
        # Use container NAME for unique_id to maintain entity stability
        self._container_name = container.name.lstrip("/")
        # Store the current container ID for API calls (start/stop)
        # This will be updated when the container is recreated
        self._container_id = container.id
        self._cached_container: DockerContainer | None = None
        self._cache_data_id: int | None = None
        super().__init__(
            coordinator=coordinator,
            api_client=api_client,
            server_uuid=server_uuid,
            server_name=server_name,
            # Use container NAME for stable unique_id (not ID which changes)
            resource_id=f"container_switch_{self._container_name}",
            name=f"Container {self._container_name}",
        )

    def _get_container(self) -> DockerContainer | None:
        """
        Get current container from coordinator data with caching.

        Looks up container by NAME (stable) not ID (ephemeral).
        Also updates the stored container_id if it changed (e.g., after update).
        """
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None

        # Use cache if data object hasn't changed (same coordinator refresh)
        data_id = id(data)
        if (
            self._cache_data_id is not None
            and data_id == self._cache_data_id
            and self._cached_container is not None
        ):
            return self._cached_container

        # Build lookup dict by NAME for O(1) access (name is stable, ID is not)
        container_map = {c.name.lstrip("/"): c for c in data.containers}
        self._cached_container = container_map.get(self._container_name)
        self._cache_data_id = data_id

        # Update container ID if it changed (after container update/recreate)
        if self._cached_container is not None:
            self._container_id = self._cached_container.id

        return self._cached_container

    @property
    def is_on(self) -> bool:
        """Return True if container is running."""
        container = self._get_container()
        if container is None:
            return False
        return container.state == STATE_CONTAINER_RUNNING

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes, filtering out None values."""
        container = self._get_container()
        if container is None:
            return {}
        attrs: dict[str, Any] = {
            "status": container.state,
        }
        if container.image is not None:
            attrs["image"] = container.image
        if container.webUiUrl is not None:
            attrs["web_ui_url"] = container.webUiUrl
        if container.iconUrl is not None:
            attrs["icon_url"] = container.iconUrl
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start container."""
        try:
            await self.api_client.start_container(self._container_id)
            _LOGGER.debug("Started Docker container: %s", self._container_id)
        except Exception as err:
            _LOGGER.error("Failed to start Docker container: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="container_start_failed",
                translation_placeholders={
                    "name": self._container_name,
                    "error": str(err),
                },
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop container."""
        try:
            await self.api_client.stop_container(self._container_id)
            _LOGGER.debug("Stopped Docker container: %s", self._container_id)
        except Exception as err:
            _LOGGER.error("Failed to stop Docker container: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="container_stop_failed",
                translation_placeholders={
                    "name": self._container_name,
                    "error": str(err),
                },
            ) from err


class VirtualMachineSwitch(UnraidSwitchEntity):
    """Virtual machine control switch."""

    _attr_translation_key = "virtual_machine"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
    ) -> None:
        """Initialize virtual machine switch."""
        # VM names are stable across restarts; IDs may not be
        # Use VM NAME for unique_id to maintain entity stability
        self._vm_name = vm.name
        # Store the current VM ID for API calls (start/stop)
        self._vm_id = vm.id
        self._cached_vm: VmDomain | None = None
        self._cache_data_id: int | None = None
        super().__init__(
            coordinator=coordinator,
            api_client=api_client,
            server_uuid=server_uuid,
            server_name=server_name,
            # Use VM NAME for stable unique_id (not ID which may change)
            resource_id=f"vm_switch_{self._vm_name}",
            name=f"VM {vm.name}",
        )

    def _get_vm(self) -> VmDomain | None:
        """
        Get current VM from coordinator data with caching.

        Looks up VM by NAME (stable) not ID (may be ephemeral).
        Also updates the stored vm_id if it changed.
        """
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None

        # Use cache if data object hasn't changed (same coordinator refresh)
        data_id = id(data)
        if (
            self._cache_data_id is not None
            and data_id == self._cache_data_id
            and self._cached_vm is not None
        ):
            return self._cached_vm

        # Build lookup dict by NAME for O(1) access (name is stable)
        vm_map = {v.name: v for v in data.vms}
        self._cached_vm = vm_map.get(self._vm_name)
        self._cache_data_id = data_id

        # Update the VM ID if it changed
        if self._cached_vm is not None:
            self._vm_id = self._cached_vm.id

        return self._cached_vm

    @property
    def is_on(self) -> bool:
        """Return True if VM is running or idle."""
        vm = self._get_vm()
        if vm is None:
            return False
        return vm.state in VM_RUNNING_STATES

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes, filtering out None values."""
        vm = self._get_vm()
        if vm is None:
            return {}
        attrs: dict[str, Any] = {
            "state": vm.state,
        }
        if vm.memory is not None:
            attrs["memory"] = vm.memory
        if vm.vcpu is not None:
            attrs["vcpu"] = vm.vcpu
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start VM."""
        try:
            await self.api_client.start_vm(self._vm_id)
            _LOGGER.debug("Started VM: %s", self._vm_id)
        except Exception as err:
            _LOGGER.error("Failed to start VM: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="vm_start_failed",
                translation_placeholders={"name": self._vm_name, "error": str(err)},
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop VM."""
        try:
            await self.api_client.stop_vm(self._vm_id)
            _LOGGER.debug("Stopped VM: %s", self._vm_id)
        except Exception as err:
            _LOGGER.error("Failed to stop VM: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="vm_stop_failed",
                translation_placeholders={"name": self._vm_name, "error": str(err)},
            ) from err


# =============================================================================
# Array Control Switch
# =============================================================================


class ArraySwitch(UnraidBaseEntity, SwitchEntity):
    """
    Switch to control the Unraid array.

    ON = Array is started/running
    OFF = Array is stopped

    Disabled by default - users enable if they want array control via HA.
    """

    _attr_translation_key = "array"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize array switch."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="array_switch",
            name="Array",
            server_info=server_info,
        )
        self.api_client = api_client

    @property
    def is_on(self) -> bool | None:
        """Return True if array is started."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.array_state is None:
            return None
        return data.array_state.upper() == STATE_ARRAY_STARTED

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return array state details."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None:
            return {}
        return {
            "state": data.array_state,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the array."""
        _LOGGER.info("Starting Unraid array")
        try:
            await self.api_client.start_array()
            _LOGGER.debug("Array start command sent successfully")
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to start array: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="array_start_failed",
                translation_placeholders={"error": str(err)},
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the array."""
        _LOGGER.warning("Stopping Unraid array")
        try:
            await self.api_client.stop_array()
            _LOGGER.debug("Array stop command sent successfully")
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to stop array: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="array_stop_failed",
                translation_placeholders={"error": str(err)},
            ) from err


# =============================================================================
# Parity Check Control Switch
# =============================================================================


class ParityCheckSwitch(UnraidBaseEntity, SwitchEntity):
    """
    Switch to control parity check operations.

    ON = Parity check is running (starts a read-only check)
    OFF = No parity check running (stops any running check)

    Disabled by default - users enable if they want parity control via HA.
    """

    _attr_translation_key = "parity_check"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize parity check switch."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_check_switch",
            name="Parity Check",
            server_info=server_info,
        )
        self.api_client = api_client

    @property
    def is_on(self) -> bool | None:
        """Return True if parity check is running."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return None
        status = data.parity_status.status
        if status is None:
            return False
        # Running states include RUNNING and PAUSED
        running_states = {"RUNNING", "PAUSED"}
        return status.upper() in running_states

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return parity check details."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return {}
        parity = data.parity_status
        return {
            "status": parity.status.lower() if parity.status else None,
            "progress": parity.progress,
            "errors": parity.errors,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start a parity check (read-only mode)."""
        _LOGGER.info("Starting parity check")
        try:
            # Start check-only mode (correct=False)
            await self.api_client.start_parity_check(correct=False)
            _LOGGER.debug("Parity check start command sent successfully")
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to start parity check: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="parity_check_start_failed",
                translation_placeholders={"error": str(err)},
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop/cancel the parity check."""
        _LOGGER.warning("Stopping parity check")
        try:
            await self.api_client.cancel_parity_check()
            _LOGGER.debug("Parity check stop command sent successfully")
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to stop parity check: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="parity_check_stop_failed",
                translation_placeholders={"error": str(err)},
            ) from err


# =============================================================================
# Disk Spin Control Switch
# =============================================================================


class DiskSpinSwitch(UnraidBaseEntity, SwitchEntity):
    """
    Switch to control disk spin state.

    ON = Disk is spinning (active)
    OFF = Disk is spun down (standby)

    Disabled by default - users enable for disks they want to control.
    """

    _attr_translation_key = "disk_spin"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        disk: ArrayDisk,
        server_info: dict | None = None,
    ) -> None:
        """Initialize disk spin switch."""
        self._disk_id = disk.id
        self._disk_name = disk.name or disk.id
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"disk_spin_{disk.id}",
            name=f"Disk {self._disk_name} Spin",
            server_info=server_info,
        )
        self.api_client = api_client

    def _get_disk(self) -> ArrayDisk | None:
        """Get current disk from coordinator data."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None:
            return None
        all_disks = data.disks + data.parities + data.caches
        for disk in all_disks:
            if disk.id == self._disk_id:
                return disk
        return None

    @property
    def is_on(self) -> bool | None:
        """Return True if disk is spinning."""
        disk = self._get_disk()
        if disk is None:
            return None
        return disk.isSpinning

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return disk details."""
        disk = self._get_disk()
        if disk is None:
            return {}
        attrs: dict[str, Any] = {
            "device": disk.device,
            "type": disk.type,
            "status": disk.status,
        }
        if disk.temp is not None:
            attrs["temperature"] = disk.temp
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Spin up the disk."""
        _LOGGER.info("Spinning up disk %s", self._disk_name)
        try:
            await self.api_client.spin_up_disk(self._disk_id)
            _LOGGER.debug("Disk spin up command sent successfully")
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to spin up disk %s: %s", self._disk_name, err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="disk_spin_up_failed",
                translation_placeholders={"name": self._disk_name, "error": str(err)},
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Spin down the disk."""
        _LOGGER.info("Spinning down disk %s", self._disk_name)
        try:
            await self.api_client.spin_down_disk(self._disk_id)
            _LOGGER.debug("Disk spin down command sent successfully")
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to spin down disk %s: %s", self._disk_name, err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="disk_spin_down_failed",
                translation_placeholders={"name": self._disk_name, "error": str(err)},
            ) from err


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
    async_add_entities: Any,
) -> None:
    """Set up switch entities."""
    _LOGGER.debug("Setting up Unraid switch platform")

    # Get coordinators and API client from runtime_data (HA 2024.4+ pattern)
    runtime_data = entry.runtime_data
    system_coordinator = runtime_data.system_coordinator
    api_client = runtime_data.api_client
    server_info = runtime_data.server_info
    storage_coordinator = runtime_data.storage_coordinator

    # Server info is now a flat dict with uuid, name, manufacturer, etc.
    server_uuid = server_info.get("uuid", "unknown")
    server_name = server_info.get("name", entry.data.get("host", "Unraid"))

    entities: list[SwitchEntity] = []

    # ==========================================================================
    # Control Switches (disabled by default - users enable as needed)
    # ==========================================================================

    # Array control switch (replaces start/stop buttons)
    entities.append(
        ArraySwitch(
            storage_coordinator, api_client, server_uuid, server_name, server_info
        )
    )

    # Parity check control switch (replaces start/stop buttons)
    entities.append(
        ParityCheckSwitch(
            storage_coordinator, api_client, server_uuid, server_name, server_info
        )
    )

    # Disk spin switches (replaces spin up/down buttons, one per disk)
    if storage_coordinator.data:
        all_disks = (
            storage_coordinator.data.disks
            + storage_coordinator.data.parities
            + storage_coordinator.data.caches
        )
        for disk in all_disks:
            entities.append(
                DiskSpinSwitch(
                    storage_coordinator,
                    api_client,
                    server_uuid,
                    server_name,
                    disk,
                    server_info,
                )
            )

    # ==========================================================================
    # Docker Container Switches (always enabled)
    # ==========================================================================
    if system_coordinator.data and system_coordinator.data.containers:
        _LOGGER.debug(
            "Docker service running with %d container(s), creating switches",
            len(system_coordinator.data.containers),
        )
        for container in system_coordinator.data.containers:
            entities.append(
                DockerContainerSwitch(
                    system_coordinator, api_client, server_uuid, server_name, container
                )
            )
    else:
        _LOGGER.debug(
            "Docker service not running or no containers on %s",
            server_name,
        )

    # ==========================================================================
    # VM Switches (always enabled)
    # ==========================================================================
    if system_coordinator.data and system_coordinator.data.vms:
        _LOGGER.debug(
            "VM service running with %d VM(s), creating switches",
            len(system_coordinator.data.vms),
        )
        for vm in system_coordinator.data.vms:
            entities.append(
                VirtualMachineSwitch(
                    system_coordinator, api_client, server_uuid, server_name, vm
                )
            )
    else:
        _LOGGER.debug(
            "VM service not available or no VMs on %s, skipping VM switches",
            server_name,
        )

    _LOGGER.debug("Adding %d switch entities", len(entities))
    async_add_entities(entities)
