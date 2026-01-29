"""Base entity classes for Unraid integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import (
        UnraidStorageCoordinator,
        UnraidStorageData,
        UnraidSystemCoordinator,
        UnraidSystemData,
    )


@dataclass(frozen=True, kw_only=True)
class UnraidEntityDescription(EntityDescription):
    """
    Describes an Unraid entity.

    Extends EntityDescription with availability and support checks.
    """

    available_fn: Callable[[UnraidSystemData | UnraidStorageData], bool] = (
        lambda _: True
    )
    """Function that returns whether entity is available based on coordinator data."""

    supported_fn: Callable[[UnraidSystemData | UnraidStorageData], bool] = (
        lambda _: True
    )
    """Function that returns whether entity is supported (used in async_setup_entry)."""


class UnraidBaseEntity(
    CoordinatorEntity["UnraidSystemCoordinator | UnraidStorageCoordinator"]
):
    """
    Base entity for all Unraid entities.

    This base class provides:
    - Common DeviceInfo generation
    - Unique ID construction
    - Availability based on coordinator update success
    - Entity naming with _attr_has_entity_name = True

    Subclasses should call super().__init__() with all required parameters
    and implement their specific state/value properties.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator | UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        resource_id: str,
        name: str,
        server_info: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the Unraid base entity.

        Args:
            coordinator: The data update coordinator
            server_uuid: Unique identifier for the Unraid server
            server_name: Friendly name of the server
            resource_id: Resource-specific identifier for unique_id construction
            name: Display name for the entity
            server_info: Optional dict containing device info fields:
                - manufacturer: Device manufacturer
                - model: Device model
                - serial_number: Device serial number
                - sw_version: Software version
                - hw_version: Hardware version
                - configuration_url: URL to device configuration

        """
        super().__init__(coordinator)

        self._server_uuid = server_uuid
        self._server_name = server_name

        # Construct stable unique_id: {server_uuid}_{resource_id}
        self._attr_unique_id = f"{server_uuid}_{resource_id}"
        self._attr_name = name

        # Build DeviceInfo using HA's DeviceInfo class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, server_uuid)},
            name=server_name,
            manufacturer=server_info.get("manufacturer") if server_info else None,
            model=server_info.get("model") if server_info else None,
            serial_number=server_info.get("serial_number") if server_info else None,
            sw_version=server_info.get("sw_version") if server_info else None,
            hw_version=server_info.get("hw_version") if server_info else None,
            configuration_url=(
                server_info.get("configuration_url") if server_info else None
            ),
        )

    @property
    def available(self) -> bool:
        """Return whether entity is available based on coordinator update success."""
        return self.coordinator.last_update_success


class UnraidEntity(UnraidBaseEntity):
    """
    Unraid entity with entity description support.

    Use this class when you want to use EntityDescription dataclasses
    for entity configuration. The entity_description is accessible
    for availability and support checks.
    """

    entity_description: UnraidEntityDescription

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator | UnraidStorageCoordinator,
        entity_description: UnraidEntityDescription,
        server_uuid: str,
        server_name: str,
        server_info: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize entity with description.

        Args:
            coordinator: The data update coordinator
            entity_description: Entity description with configuration
            server_uuid: Unique identifier for the Unraid server
            server_name: Friendly name of the server
            server_info: Optional dict containing device info fields

        """
        # Get name from description, falling back to key
        entity_name = entity_description.key
        if entity_description.name is not None:
            entity_name = str(entity_description.name)

        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=entity_description.key,
            name=entity_name,
            server_info=server_info,
        )
        self.entity_description = entity_description

    @property
    def available(self) -> bool:
        """Return availability based on coordinator and entity description."""
        if not self.coordinator.last_update_success:
            return False
        if self.coordinator.data is None:
            return False
        return self.entity_description.available_fn(self.coordinator.data)
