"""Update entities for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from unraid_api.exceptions import UnraidAPIError
from unraid_api.models import DockerContainer

from .const import (
    CONF_ENABLE_CONTAINER_UPDATES,
    DEFAULT_ENABLE_CONTAINER_UPDATES,
    DOMAIN,
)
from .coordinator import (
    UnraidSystemCoordinator,
)
from .entity import (
    UnraidBaseEntity,
    async_add_dynamic_resource_entities,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .coordinator import UnraidSystemData

_LOGGER = logging.getLogger(__name__)

# Limit concurrent update operations to avoid overloading the Unraid server.
PARALLEL_UPDATES = 1

# Fallback shown when the image reference carries no explicit tag (Docker
# treats a missing tag as ``latest``).
_DEFAULT_IMAGE_TAG: Final = "latest"

# Shown for ``latest_version`` when the Unraid API reports an update is
# available. The Unraid GraphQL API only exposes a boolean ``isUpdateAvailable``
# flag — it does not provide the target version number — so a descriptive
# marker is used instead of a real version string. It must differ from
# ``installed_version`` so Home Assistant surfaces the update.
_VERSION_UPDATE_AVAILABLE: Final = "Update available"


def _parse_image_tag(image: str | None) -> str | None:
    """
    Extract the tag from a Docker image reference.

    Handles registry hosts with ports (``host:5000/repo:tag``) and digest
    references (``repo@sha256:...``). Returns ``latest`` when no explicit tag
    is present, mirroring Docker's default behaviour. Returns ``None`` when no
    image reference is available.

    Examples:
        ``nginx:1.25.0`` -> ``1.25.0``
        ``ghcr.io/foo/bar:latest`` -> ``latest``
        ``registry:5000/app:2.1`` -> ``2.1``
        ``nginx`` -> ``latest``
        ``repo@sha256:abc...`` -> ``latest``

    """
    if not image:
        return None

    # Strip any digest suffix (``@sha256:...``) before locating the tag.
    reference = image.split("@", 1)[0]

    # Only the final path segment can contain a tag; earlier colons belong to a
    # registry host:port (e.g. ``registry:5000/repo``).
    last_segment = reference.rsplit("/", 1)[-1]
    if ":" in last_segment:
        return last_segment.rsplit(":", 1)[1] or _DEFAULT_IMAGE_TAG
    return _DEFAULT_IMAGE_TAG


class DockerContainerUpdateEntity(
    UnraidBaseEntity[UnraidSystemCoordinator], UpdateEntity
):
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
        # Strong reference to the coordinator data the cache was built from.
        # Comparing identity against a held object (rather than a stored id())
        # is safe: the address cannot be reused for new data while we hold it.
        self._cache_data: UnraidSystemData | None = None
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

        if data is self._cache_data:
            return self._cached_container

        container_map = {c.name.lstrip("/"): c for c in data.containers}
        self._cached_container = container_map.get(self._container_name)
        self._cache_data = data

        # Update stored ID if it changed (happens after container update/recreate)
        if self._cached_container is not None:
            self._container_id = self._cached_container.id

        return self._cached_container

    @property
    def installed_version(self) -> str | None:
        """
        Return the currently installed version (the Docker image tag).

        The Unraid API does not expose a dedicated version field, so the tag
        from the container's image reference is used (e.g. ``1.25.0`` or
        ``latest``). Returns ``None`` when the container is unavailable.
        """
        container = self._get_container()
        if container is None:
            return None
        return _parse_image_tag(container.image)

    @property
    def latest_version(self) -> str | None:
        """
        Return the latest available version.

        The Unraid GraphQL API only reports whether an update is available via
        a boolean flag — it does not provide the target version number. When an
        update is available a descriptive marker is returned so Home Assistant
        shows the update; otherwise ``installed_version`` is returned so no
        update is shown.
        """
        container = self._get_container()
        if container is None:
            return None

        if container.isUpdateAvailable:
            return _VERSION_UPDATE_AVAILABLE
        return _parse_image_tag(container.image)

    @property
    def release_url(self) -> str | None:
        """
        Return a URL with more information about the container's image.

        The Unraid API does not provide release notes, but the container
        template often includes a project, registry, or support URL that links
        to the upstream changelog or release notes. The first available URL is
        used.
        """
        container = self._get_container()
        if container is None:
            return None
        return (
            container.projectUrl
            or container.registryUrl
            or container.supportUrl
            or None
        )

    @property
    def release_summary(self) -> str | None:
        """
        Return a short summary shown in the update dialog.

        The Unraid API does not expose release notes, so a brief note is shown
        when an update is available, pointing the user to the release URL (when
        present) for upstream changes.
        """
        container = self._get_container()
        if container is None or not container.isUpdateAvailable:
            return None
        return (
            "A new image is available for this container. The Unraid API does "
            "not provide detailed release notes; use the link to view"
            "the project's changes."
        )

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

        # Refresh coordinator data to pick up the updated container state.
        # Force a Docker re-fetch so the new state is reflected immediately
        # rather than waiting for the throttled container poll.
        await self.coordinator.async_request_docker_refresh()


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up update entities."""
    _LOGGER.debug("Setting up Unraid update platform")

    # Allow users to opt out of per-container update entities. The options flow
    # reloads the entry on change, so toggling this re-runs platform setup.
    if not entry.options.get(
        CONF_ENABLE_CONTAINER_UPDATES, DEFAULT_ENABLE_CONTAINER_UPDATES
    ):
        _LOGGER.debug("Container update sensors disabled via options")
        async_add_entities([])
        return

    runtime_data = entry.runtime_data
    system_coordinator = runtime_data.system_coordinator
    server_info = runtime_data.server_info

    server_uuid = server_info.get("uuid", "unknown")
    server_name = server_info.get("name", entry.data.get("host", "Unraid"))

    if system_coordinator.data and system_coordinator.data.containers:
        _LOGGER.debug(
            "Creating update entities for %d container(s)",
            len(system_coordinator.data.containers),
        )
    else:
        _LOGGER.debug(
            "Docker service not running or no containers on %s",
            server_name,
        )

    # Containers created after setup get update entities on the next
    # coordinator refresh — no integration reload needed.
    entry.async_on_unload(
        async_add_dynamic_resource_entities(
            coordinator=system_coordinator,
            async_add_entities=async_add_entities,
            get_resources=lambda: (
                system_coordinator.data.containers if system_coordinator.data else []
            ),
            get_key=lambda container: container.name.lstrip("/"),
            create_entities=lambda container: [
                DockerContainerUpdateEntity(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    container,
                    server_info,
                )
            ],
        )
    )
