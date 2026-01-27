"""Tests for Unraid integration setup and teardown."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unraid_api.exceptions import UnraidAuthenticationError, UnraidConnectionError

from custom_components.unraid import (
    PLATFORMS,
    UnraidRuntimeData,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.unraid.const import DOMAIN

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_API_KEY: "test-api-key",
            CONF_PORT: 443,
            CONF_VERIFY_SSL: True,
        },
        options={},
        unique_id="test-uuid-123",
    )


@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.data = {}
    return coordinator


# =============================================================================
# Setup Entry Tests
# =============================================================================


async def test_setup_entry_successful(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_unraid_client: MagicMock,
    mock_coordinator: MagicMock,
) -> None:
    """Test successful integration setup."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.unraid.UnraidSystemCoordinator",
            return_value=mock_coordinator,
        ),
        patch(
            "custom_components.unraid.UnraidStorageCoordinator",
            return_value=mock_coordinator,
        ),
        patch("custom_components.unraid.async_get_clientsession") as mock_session,
        patch.object(
            hass.config_entries, "async_forward_entry_setups", return_value=None
        ),
    ):
        mock_session.return_value = MagicMock()
        result = await async_setup_entry(hass, mock_config_entry)

    assert result is True
    assert mock_config_entry.runtime_data is not None
    assert isinstance(mock_config_entry.runtime_data, UnraidRuntimeData)
    assert mock_config_entry.runtime_data.server_info["uuid"] == "test-uuid-123"
    assert mock_config_entry.runtime_data.server_info["name"] == "tower"


async def test_setup_entry_auth_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_unraid_client: MagicMock,
) -> None:
    """Test setup fails with authentication error."""
    mock_config_entry.add_to_hass(hass)
    mock_unraid_client.test_connection.side_effect = UnraidAuthenticationError(
        "Invalid API key"
    )

    with patch("custom_components.unraid.async_get_clientsession") as mock_session:
        mock_session.return_value = MagicMock()
        with pytest.raises(ConfigEntryAuthFailed):
            await async_setup_entry(hass, mock_config_entry)

    mock_unraid_client.close.assert_called_once()


async def test_setup_entry_connection_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_unraid_client: MagicMock,
) -> None:
    """Test setup fails with connection error."""
    mock_config_entry.add_to_hass(hass)
    mock_unraid_client.test_connection.side_effect = UnraidConnectionError(
        "Connection refused"
    )

    with patch("custom_components.unraid.async_get_clientsession") as mock_session:
        mock_session.return_value = MagicMock()
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, mock_config_entry)


async def test_setup_entry_captures_hardware_info(
    hass: HomeAssistant,
    mock_unraid_client_factory: type,
    mock_coordinator: MagicMock,
) -> None:
    """Test setup captures hardware info from library's ServerInfo model."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_API_KEY: "test-api-key",
        },
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    # Configure mock with specific hardware info
    from tests.conftest import create_mock_unraid_client, make_server_info

    client = create_mock_unraid_client(
        server_info=make_server_info(
            uuid="test-uuid",
            manufacturer="Supermicro",
            hw_manufacturer="Supermicro",
            hw_model="X11SSH-F",
        )
    )
    mock_unraid_client_factory.return_value = client

    with (
        patch(
            "custom_components.unraid.UnraidSystemCoordinator",
            return_value=mock_coordinator,
        ),
        patch(
            "custom_components.unraid.UnraidStorageCoordinator",
            return_value=mock_coordinator,
        ),
        patch("custom_components.unraid.async_get_clientsession") as mock_session,
        patch.object(
            hass.config_entries, "async_forward_entry_setups", return_value=None
        ),
    ):
        mock_session.return_value = MagicMock()
        await async_setup_entry(hass, entry)

    assert entry.runtime_data.server_info["manufacturer"] == "Supermicro"
    assert entry.runtime_data.server_info["model"] == "Unraid 7.2.0"
    assert entry.runtime_data.server_info["hw_manufacturer"] == "Supermicro"
    assert entry.runtime_data.server_info["hw_model"] == "X11SSH-F"


async def test_setup_entry_creates_coordinators(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_unraid_client: MagicMock,
    mock_coordinator: MagicMock,
) -> None:
    """Test setup creates coordinators."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch("custom_components.unraid.UnraidSystemCoordinator") as mock_system_coord,
        patch(
            "custom_components.unraid.UnraidStorageCoordinator"
        ) as mock_storage_coord,
        patch("custom_components.unraid.async_get_clientsession") as mock_session,
        patch.object(
            hass.config_entries, "async_forward_entry_setups", return_value=None
        ),
    ):
        mock_system_coord.return_value = mock_coordinator
        mock_storage_coord.return_value = mock_coordinator
        mock_session.return_value = MagicMock()
        await async_setup_entry(hass, mock_config_entry)

    mock_system_coord.assert_called_once()
    mock_storage_coord.assert_called_once()


# =============================================================================
# Unload Entry Tests
# =============================================================================


async def test_unload_entry_successful(hass: HomeAssistant) -> None:
    """Test successful integration unload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_API_KEY: "test-api-key",
        },
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    mock_api = AsyncMock()
    mock_api.close = AsyncMock()
    entry.runtime_data = UnraidRuntimeData(
        api_client=mock_api,
        system_coordinator=MagicMock(),
        storage_coordinator=MagicMock(),
        server_info={"uuid": "test-uuid", "name": "tower"},
    )

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        return_value=True,
    ):
        result = await async_unload_entry(hass, entry)

    assert result is True
    mock_api.close.assert_called_once()


async def test_unload_entry_platform_failure(hass: HomeAssistant) -> None:
    """Test unload when platform unload fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_API_KEY: "test-api-key",
        },
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    mock_api = AsyncMock()
    mock_api.close = AsyncMock()
    entry.runtime_data = UnraidRuntimeData(
        api_client=mock_api,
        system_coordinator=MagicMock(),
        storage_coordinator=MagicMock(),
        server_info={},
    )

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        return_value=False,
    ):
        result = await async_unload_entry(hass, entry)

    assert result is False
    mock_api.close.assert_not_called()


# =============================================================================
# Platform Constants Tests
# =============================================================================


def test_platforms_list() -> None:
    """Test that all expected platforms are defined."""
    from homeassistant.const import Platform

    assert Platform.SENSOR in PLATFORMS
    assert Platform.BINARY_SENSOR in PLATFORMS
    assert Platform.SWITCH in PLATFORMS
    assert Platform.BUTTON in PLATFORMS
    assert len(PLATFORMS) == 4
