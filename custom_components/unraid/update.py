"""Update entities for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from unraid_api.exceptions import UnraidAPIError
from unraid_api.models import DockerContainer

from .const import DOMAIN
from .entity import UnraidBaseEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .coordinator import UnraidSystemCoordinator, UnraidSystemData

_LOGGER = logging.getLogger(__name__)

# Limit concurrent update operations to avoid overloading the Unraid server.
PARALLEL_UPDATES = 1

# Sentinel version strings used when the API only provides a boolean
# `isUpdateAvailable` flag without actual version numbers.
_VERSION_CURRENT = "installed"
_VERSION_UPDATE_AVAILABLE = "update_available"


class DockerContainerUpdateEntity(UnraidBaseEntity, UpdateEntity):
    """Represents a Docker container update entity."""

    _attr_translation_key = "docker_container_update"
    _attr_supported_features = UpdateEntityFeature.INSTALL

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        container: DockerContainer,
        server_info: dict[str, Any] | None = None,
    ) -> None:
        """Initialize Docker container update entity."""
        self._container_name = container.name.lstrip("/")
        self._container_id = container.id
        self._cached_container: DockerContainer | None = None
        self._cache_data_id: int | None = None
        self._is_updating = False

        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_update_{self._container_name}",
            name=None,
            server_info=server_info,
        )

        self._attr_translation_placeholders = {"name": self._container_name}
        self._attr_title = self._container_name

    def _get_container(self) -> DockerContainer | None:
        """
        Get current container from coordinator data.

        Uses a per-data-refresh cache to avoid repeated list scans.
        Looks up by NAME (stable) since container IDs change after updates.
        """
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None

        data_id = id(data)
        if self._cache_data_id is not None and data_id == self._cache_data_id:
            return self._cached_container

        container_map = {c.name.lstrip("/"): c for c in data.containers}
        self._cached_container = container_map.get(self._container_name)
        self._cache_data_id = data_id

        # Update stored ID if it changed (happens after container update/recreate)
        if self._cached_container is not None:
            self._container_id = self._cached_container.id

        return self._cached_container

    @property
    def installed_version(self) -> str | None:
        """Return the current (installed) version."""
        container = self._get_container()
        if container is None:
            return None
        return _VERSION_CURRENT

    @property
    def latest_version(self) -> str | None:
        """
        Return the latest available version.

        When an update is available, returns a sentinel value different from
        ``installed_version`` so HA displays the update badge.  When up-to-date,
        returns the same sentinel as ``installed_version`` (no update shown).
        """
        container = self._get_container()
        if container is None:
            return None

        if container.isUpdateAvailable:
            return _VERSION_UPDATE_AVAILABLE
        return _VERSION_CURRENT

    @property
    def entity_picture(self) -> str | None:
        """Return the container icon URL as the entity picture."""
        container = self._get_container()
        if container is not None and container.iconUrl:
            return container.iconUrl
        return None

    @property
    def in_progress(self) -> bool:
        """Return True while an update operation is in progress."""
        return self._is_updating

    def _resolve_container_id(self) -> str:
        """Resolve the current container ID by name lookup."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is not None:
            for container in data.containers:
                if container.name.lstrip("/") == self._container_name:
                    return container.id
        return self._container_id

    async def async_install(
        self,
        version: str | None,
        backup: bool,
        **kwargs: Any,
    ) -> None:
        """Install the latest update for this container."""
        _LOGGER.info(
            "Updating Docker container '%s' on %s",
            self._container_name,
            self._server_name,
        )
        self._is_updating = True
        self.async_write_ha_state()

        try:
            container_id = self._resolve_container_id()
            await self.coordinator.async_update_container(container_id)
        except UnraidAPIError as err:
            _LOGGER.error(
                "Failed to update Docker container '%s': %s",
                self._container_name,
                err,
            )
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="container_update_failed",
                translation_placeholders={
                    "name": self._container_name,
                    "error": str(err),
                },
            ) from err
        finally:
            self._is_updating = False

        # Refresh coordinator data to pick up the updated container state
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up update entities."""
    _LOGGER.debug("Setting up Unraid update platform")

    runtime_data = entry.runtime_data
    system_coordinator = runtime_data.system_coordinator
    server_info = runtime_data.server_info

    server_uuid = server_info.get("uuid", "unknown")
    server_name = server_info.get("name", entry.data.get("host", "Unraid"))

    entities: list[UpdateEntity] = []

    if system_coordinator.data and system_coordinator.data.containers:
        _LOGGER.debug(
            "Creating update entities for %d container(s)",
            len(system_coordinator.data.containers),
        )
        for container in system_coordinator.data.containers:
            entities.append(
                DockerContainerUpdateEntity(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    container,
                    server_info,
                )
            )
    else:
        _LOGGER.debug(
            "Docker service not running or no containers on %s",
            server_name,
        )

    _LOGGER.debug("Adding %d update entities", len(entities))
    async_add_entities(entities)
