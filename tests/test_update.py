"""Tests for Unraid update entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError
from unraid_api.exceptions import UnraidAPIError
from unraid_api.models import DockerContainer

from custom_components.unraid import UnraidRuntimeData
from custom_components.unraid.coordinator import UnraidSystemCoordinator
from custom_components.unraid.update import (
    _VERSION_CURRENT,
    _VERSION_UPDATE_AVAILABLE,
    DockerContainerUpdateEntity,
    async_setup_entry,
)
from tests.conftest import make_system_data

# =============================================================================
# DockerContainerUpdateEntity Tests
# =============================================================================


def _make_update_entity(
    container: DockerContainer,
    containers: list[DockerContainer] | None = None,
    coordinator_data_none: bool = False,
) -> DockerContainerUpdateEntity:
    """Create a DockerContainerUpdateEntity for testing."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    if coordinator_data_none:
        coordinator.data = None
    else:
        all_containers = containers or [container]
        coordinator.data = make_system_data(containers=all_containers)
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_update_container = AsyncMock()
    entity = DockerContainerUpdateEntity(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )
    # Mock async_write_ha_state since hass is not available in unit tests
    entity.async_write_ha_state = MagicMock()
    return entity


def test_update_entity_creation() -> None:
    """Test Docker container update entity creation."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        image="nginx:latest",
        isUpdateAvailable=False,
    )
    entity = _make_update_entity(container)

    assert entity.unique_id == "test-uuid_container_update_web"
    assert entity._attr_translation_key == "docker_container_update"
    assert entity._attr_translation_placeholders == {"name": "web"}
    assert entity.title == "web"
    assert entity.device_info is not None


def test_update_entity_name_strips_leading_slash() -> None:
    """Test that container names with leading slash are normalized."""
    container = DockerContainer(
        id="ct:1",
        name="/my-container",
        state="RUNNING",
    )
    entity = _make_update_entity(container)

    assert entity._container_name == "my-container"
    assert entity.unique_id == "test-uuid_container_update_my-container"


def test_installed_version_returns_sentinel() -> None:
    """Test installed_version returns sentinel constant."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    entity = _make_update_entity(container)

    assert entity.installed_version == _VERSION_CURRENT


def test_latest_version_when_no_update() -> None:
    """Test latest_version matches installed when no update available."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        isUpdateAvailable=False,
    )
    entity = _make_update_entity(container)

    assert entity.latest_version == _VERSION_CURRENT
    assert entity.latest_version == entity.installed_version


def test_latest_version_when_update_available() -> None:
    """Test latest_version differs from installed when update available."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        isUpdateAvailable=True,
    )
    entity = _make_update_entity(container)

    assert entity.latest_version == _VERSION_UPDATE_AVAILABLE
    assert entity.latest_version != entity.installed_version


def test_latest_version_when_update_none() -> None:
    """Test latest_version when isUpdateAvailable is None (unknown)."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        isUpdateAvailable=None,
    )
    entity = _make_update_entity(container)

    # None is falsy, so no update shown
    assert entity.latest_version == _VERSION_CURRENT


def test_entity_picture_from_icon_url() -> None:
    """Test entity_picture returns container icon URL."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        iconUrl="https://cdn.example.com/icons/nginx.png",
    )
    entity = _make_update_entity(container)

    assert entity.entity_picture == "https://cdn.example.com/icons/nginx.png"


def test_entity_picture_none_when_no_icon() -> None:
    """Test entity_picture returns None when container has no icon."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    entity = _make_update_entity(container)

    assert entity.entity_picture is None


def test_in_progress_initially_false() -> None:
    """Test in_progress is False by default."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    entity = _make_update_entity(container)

    assert entity.in_progress is False


def test_no_data_returns_none_versions() -> None:
    """Test version properties return None when coordinator has no data."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    entity = _make_update_entity(container, coordinator_data_none=True)

    assert entity.installed_version is None
    assert entity.latest_version is None
    assert entity.entity_picture is None


def test_container_not_found_returns_none() -> None:
    """Test version properties return None when container is not in data."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    other_container = DockerContainer(
        id="ct:2",
        name="/db",
        state="RUNNING",
    )
    entity = _make_update_entity(container, containers=[other_container])

    assert entity.installed_version is None
    assert entity.latest_version is None


def test_container_id_updates_after_refresh() -> None:
    """Test container ID is updated when it changes (e.g., after update)."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    entity = _make_update_entity(container)

    assert entity._container_id == "ct:1"

    # Simulate a coordinator refresh where container ID changed
    new_container = DockerContainer(
        id="ct:99",
        name="/web",
        state="RUNNING",
    )
    entity.coordinator.data = make_system_data(containers=[new_container])

    # Access a property to trigger lookup
    _ = entity.installed_version
    assert entity._container_id == "ct:99"


def test_container_cache_invalidated_on_new_data() -> None:
    """Test the per-data-refresh cache works correctly."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        isUpdateAvailable=False,
    )
    entity = _make_update_entity(container)

    assert entity.latest_version == _VERSION_CURRENT

    # Replace coordinator data with update available
    updated = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        isUpdateAvailable=True,
    )
    entity.coordinator.data = make_system_data(containers=[updated])

    assert entity.latest_version == _VERSION_UPDATE_AVAILABLE


# =============================================================================
# async_install Tests
# =============================================================================


async def test_install_calls_update_container() -> None:
    """Test async_install calls coordinator update method."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        isUpdateAvailable=True,
    )
    entity = _make_update_entity(container)

    await entity.async_install(version=None, backup=False)

    entity.coordinator.async_update_container.assert_awaited_once_with("ct:1")
    entity.coordinator.async_request_refresh.assert_awaited_once()


async def test_install_resolves_current_container_id() -> None:
    """Test async_install resolves the latest container ID by name."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    entity = _make_update_entity(container)

    # Simulate container ID change
    new_container = DockerContainer(
        id="ct:42",
        name="/web",
        state="RUNNING",
    )
    entity.coordinator.data = make_system_data(containers=[new_container])

    await entity.async_install(version=None, backup=False)

    entity.coordinator.async_update_container.assert_awaited_once_with("ct:42")


async def test_install_raises_on_api_error() -> None:
    """Test async_install raises HomeAssistantError on API failure."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    entity = _make_update_entity(container)
    entity.coordinator.async_update_container = AsyncMock(
        side_effect=UnraidAPIError("Image pull failed")
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await entity.async_install(version=None, backup=False)

    assert "container_update_failed" in str(exc_info.value)


async def test_install_clears_in_progress_on_error() -> None:
    """Test in_progress is reset to False even when update fails."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    entity = _make_update_entity(container)
    entity.coordinator.async_update_container = AsyncMock(
        side_effect=UnraidAPIError("Failed")
    )

    with pytest.raises(HomeAssistantError):
        await entity.async_install(version=None, backup=False)

    assert entity.in_progress is False


async def test_install_clears_in_progress_on_success() -> None:
    """Test in_progress is reset to False after successful update."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    entity = _make_update_entity(container)

    await entity.async_install(version=None, backup=False)

    assert entity.in_progress is False


# =============================================================================
# async_setup_entry Tests
# =============================================================================


async def test_setup_entry_creates_entities_for_containers() -> None:
    """Test setup entry creates update entities for each container."""
    containers = [
        DockerContainer(id="ct:1", name="/web", state="RUNNING"),
        DockerContainer(id="ct:2", name="/db", state="RUNNING"),
        DockerContainer(id="ct:3", name="/redis", state="EXITED"),
    ]

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data(containers=containers)

    runtime_data = MagicMock(spec=UnraidRuntimeData)
    runtime_data.system_coordinator = system_coordinator
    runtime_data.server_info = {"uuid": "test-uuid", "name": "tower"}

    entry = MagicMock()
    entry.runtime_data = runtime_data
    entry.data = {"host": "192.168.1.100"}

    async_add_entities = MagicMock()
    await async_setup_entry(MagicMock(), entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 3

    names = {e._container_name for e in entities}
    assert names == {"web", "db", "redis"}


async def test_setup_entry_no_containers() -> None:
    """Test setup entry creates no entities when no containers exist."""
    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data(containers=[])

    runtime_data = MagicMock(spec=UnraidRuntimeData)
    runtime_data.system_coordinator = system_coordinator
    runtime_data.server_info = {"uuid": "test-uuid", "name": "tower"}

    entry = MagicMock()
    entry.runtime_data = runtime_data
    entry.data = {"host": "192.168.1.100"}

    async_add_entities = MagicMock()
    await async_setup_entry(MagicMock(), entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 0


async def test_setup_entry_no_data() -> None:
    """Test setup entry creates no entities when coordinator has no data."""
    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = None

    runtime_data = MagicMock(spec=UnraidRuntimeData)
    runtime_data.system_coordinator = system_coordinator
    runtime_data.server_info = {"uuid": "test-uuid", "name": "tower"}

    entry = MagicMock()
    entry.runtime_data = runtime_data
    entry.data = {"host": "192.168.1.100"}

    async_add_entities = MagicMock()
    await async_setup_entry(MagicMock(), entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 0
