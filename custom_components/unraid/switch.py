"""Switch entities for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, PARALLEL_UPDATES, STATE_CONTAINER_RUNNING, VM_RUNNING_STATES
from .models import DockerContainer, VmDomain

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .api import UnraidAPIClient
    from .coordinator import UnraidSystemCoordinator, UnraidSystemData

_LOGGER = logging.getLogger(__name__)

# Export PARALLEL_UPDATES for Home Assistant
__all__ = ["PARALLEL_UPDATES", "async_setup_entry"]


class UnraidSwitchEntity(SwitchEntity):
    """Base class for Unraid switch entities."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        api_client: UnraidAPIClient,
        server_uuid: str,
        server_name: str,
        resource_id: str,
        name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize switch entity."""
        self.coordinator = coordinator
        self.api_client = api_client
        self._server_uuid = server_uuid
        self._server_name = server_name
        self._attr_unique_id = f"{server_uuid}_{resource_id}"
        self._attr_name = name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, server_uuid)},
            "name": server_name,
            "manufacturer": server_info.get("manufacturer") if server_info else None,
            "model": server_info.get("model") if server_info else None,
            "sw_version": server_info.get("sw_version") if server_info else None,
            "hw_version": server_info.get("hw_version") if server_info else None,
        }

    @property
    def available(self) -> bool:
        """Return whether entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher when added to Home Assistant."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self._async_write_ha_state)
        )


class DockerContainerSwitch(UnraidSwitchEntity):
    """Docker container control switch."""

    _attr_translation_key = "docker_container"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        api_client: UnraidAPIClient,
        server_uuid: str,
        server_name: str,
        container: DockerContainer,
    ) -> None:
        """Initialize docker container switch."""
        self._container_id = container.id
        self._container_name = container.name.lstrip("/")
        self._cached_container: DockerContainer | None = None
        self._cache_data_id: int | None = None
        super().__init__(
            coordinator=coordinator,
            api_client=api_client,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_switch_{container.id}",
            name=f"Container {self._container_name}",
        )

    def _get_container(self) -> DockerContainer | None:
        """Get current container from coordinator data with caching."""
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

        # Build lookup dict for O(1) access
        container_map = {c.id: c for c in data.containers}
        self._cached_container = container_map.get(self._container_id)
        self._cache_data_id = data_id
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
            raise HomeAssistantError(f"Failed to start container: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop container."""
        try:
            await self.api_client.stop_container(self._container_id)
            _LOGGER.debug("Stopped Docker container: %s", self._container_id)
        except Exception as err:
            _LOGGER.error("Failed to stop Docker container: %s", err)
            raise HomeAssistantError(f"Failed to stop container: {err}") from err


class VirtualMachineSwitch(UnraidSwitchEntity):
    """Virtual machine control switch."""

    _attr_translation_key = "virtual_machine"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        api_client: UnraidAPIClient,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
    ) -> None:
        """Initialize virtual machine switch."""
        self._vm_id = vm.id
        self._vm_name = vm.name
        self._cached_vm: VmDomain | None = None
        self._cache_data_id: int | None = None
        super().__init__(
            coordinator=coordinator,
            api_client=api_client,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"vm_switch_{vm.id}",
            name=f"VM {vm.name}",
        )

    def _get_vm(self) -> VmDomain | None:
        """Get current VM from coordinator data with caching."""
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

        # Build lookup dict for O(1) access
        vm_map = {v.id: v for v in data.vms}
        self._cached_vm = vm_map.get(self._vm_id)
        self._cache_data_id = data_id
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
            raise HomeAssistantError(f"Failed to start VM: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop VM."""
        try:
            await self.api_client.stop_vm(self._vm_id)
            _LOGGER.debug("Stopped VM: %s", self._vm_id)
        except Exception as err:
            _LOGGER.error("Failed to stop VM: %s", err)
            raise HomeAssistantError(f"Failed to stop VM: {err}") from err


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

    # Server info is now a flat dict with uuid, name, manufacturer, etc.
    server_uuid = server_info.get("uuid", "unknown")
    server_name = server_info.get("name", entry.data.get("host", "Unraid"))

    entities: list[UnraidSwitchEntity] = []

    # Add Docker container switches (only when Docker service is running)
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
        _LOGGER.info(
            "Docker service not running or no containers on %s",
            server_name,
        )

    # Add VM switches (only when VM/libvirt service is running)
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
        _LOGGER.info(
            "VM service not available or no VMs on %s, skipping VM switches",
            server_name,
        )

    _LOGGER.debug("Adding %d switch entities", len(entities))
    async_add_entities(entities)
