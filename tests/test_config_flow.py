"""Config flow tests for the Unraid integration."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import ClientConnectorError
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unraid_api.models import ServerInfo, UPSDevice

from custom_components.unraid.config_flow import (
    CONF_HTTP_PORT,
    CONF_HTTPS_PORT,
    CannotConnectError,
)
from custom_components.unraid.const import (
    CONF_UPS_CAPACITY_VA,
    CONF_UPS_NOMINAL_POWER,
    DEFAULT_UPS_CAPACITY_VA,
    DEFAULT_UPS_NOMINAL_POWER,
    DOMAIN,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_setup_entry():
    """Mock setup_entry to avoid actual HA component setup."""
    with patch("custom_components.unraid.async_setup_entry", return_value=True):
        yield


@pytest.fixture
def mock_api_client() -> MagicMock:
    """Create a mock API client with standard responses."""
    mock_api = MagicMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_version = AsyncMock(return_value={"unraid": "7.2.0", "api": "4.29.2"})
    mock_api.get_server_info = AsyncMock(
        return_value=ServerInfo(
            uuid="test-server-uuid",
            hostname="tower",
            sw_version="7.2.0",
            api_version="4.29.2",
        )
    )
    mock_api.close = AsyncMock()
    return mock_api


# =============================================================================
# User Flow Tests
# =============================================================================


async def test_user_step_form_display(hass: HomeAssistant) -> None:
    """Test user step shows form with required fields."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "host" in result["data_schema"].schema
    assert "api_key" in result["data_schema"].schema


async def test_user_step_form_includes_port_field(hass: HomeAssistant) -> None:
    """Test user step shows form with HTTP and HTTPS port fields."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "http_port" in result["data_schema"].schema
    assert "https_port" in result["data_schema"].schema


async def test_successful_connection(
    hass: HomeAssistant, mock_setup_entry: None, mock_api_client: MagicMock
) -> None:
    """Test successful server connection creates config entry."""
    with patch(
        "custom_components.unraid.config_flow.UnraidClient",
        return_value=mock_api_client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"host": "unraid.local", "api_key": "valid-api-key"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "tower"
    assert result["data"]["host"] == "unraid.local"
    assert result["data"]["api_key"] == "valid-api-key"


async def test_successful_connection_with_custom_port(
    hass: HomeAssistant, mock_setup_entry: None, mock_api_client: MagicMock
) -> None:
    """Test successful connection with custom ports creates config entry."""
    with patch(
        "custom_components.unraid.config_flow.UnraidClient",
        return_value=mock_api_client,
    ) as mock_client_class:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                "host": "unraid.local",
                "http_port": 8080,
                "https_port": 8443,
                "api_key": "valid-api-key",
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["http_port"] == 8080
    assert result["data"]["https_port"] == 8443
    mock_client_class.assert_called_with(
        host="unraid.local",
        api_key="valid-api-key",
        http_port=8080,
        https_port=8443,
        verify_ssl=True,
    )


async def test_connection_uses_default_port_when_not_specified(
    hass: HomeAssistant, mock_setup_entry: None, mock_api_client: MagicMock
) -> None:
    """Test that default ports 80/443 are used when not specified."""
    with patch(
        "custom_components.unraid.config_flow.UnraidClient",
        return_value=mock_api_client,
    ) as mock_client_class:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"host": "unraid.local", "api_key": "valid-api-key"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    mock_client_class.assert_called_with(
        host="unraid.local",
        api_key="valid-api-key",
        http_port=80,
        https_port=443,
        verify_ssl=True,
    )


async def test_invalid_credentials_error(hass: HomeAssistant) -> None:
    """Test invalid API key shows authentication error."""
    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(side_effect=Exception("401: Unauthorized"))
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"host": "unraid.local", "api_key": "invalid-key"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"][CONF_API_KEY] == "invalid_auth"


async def test_unreachable_server_error(hass: HomeAssistant) -> None:
    """Test unreachable server shows connection error."""
    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(
        side_effect=aiohttp.ClientError("Connection refused")
    )
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"host": "unraid.invalid", "api_key": "valid-key"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"][CONF_HOST] == "cannot_connect"
    assert result["errors"][CONF_HTTPS_PORT] == "check_port"


async def test_unsupported_version_error(hass: HomeAssistant) -> None:
    """Test old Unraid version shows version error."""
    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_version = AsyncMock(return_value={"unraid": "6.9.0", "api": "4.10.0"})
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"host": "unraid.local", "api_key": "valid-key"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "unsupported_version"


async def test_duplicate_config_entry(
    hass: HomeAssistant, mock_setup_entry: None, mock_api_client: MagicMock
) -> None:
    """Test duplicate server UUID is rejected."""
    mock_api_client.get_server_info.return_value = ServerInfo(
        uuid="same-server-uuid",
        hostname="tower",
        sw_version="7.2.0",
        api_version="4.29.2",
    )

    with patch(
        "custom_components.unraid.config_flow.UnraidClient",
        return_value=mock_api_client,
    ):
        result1 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"host": "unraid.local", "api_key": "key1"},
        )
        assert result1["type"] is FlowResultType.CREATE_ENTRY

        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"host": "192.168.1.100", "api_key": "key2"},
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_hostname_validation(hass: HomeAssistant) -> None:
    """Test hostname/IP validation - empty hostname rejected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"host": "", "api_key": "valid-key"},
    )

    assert result["type"] is FlowResultType.FORM
    assert "host" in result["errors"]


async def test_api_key_validation(hass: HomeAssistant) -> None:
    """Test API key validation - empty key rejected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"host": "unraid.local", "api_key": ""},
    )

    assert result["type"] is FlowResultType.FORM
    assert "api_key" in result["errors"]


async def test_hostname_max_length_validation(hass: HomeAssistant) -> None:
    """Test hostname exceeding max length shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    long_hostname = "a" * 255
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: long_hostname, CONF_API_KEY: "valid-api-key"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_HOST] == "invalid_hostname"


async def test_user_step_unknown_error(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test unexpected error during user step gets wrapped as cannot_connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(side_effect=RuntimeError("Unexpected"))
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "unraid.local", CONF_API_KEY: "valid-api-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_HOST] == "cannot_connect"


async def test_http_error_403_shows_invalid_auth(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test HTTP 403 error is handled as invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(
        side_effect=aiohttp.ClientResponseError(
            request_info=None, history=(), status=403, message="Forbidden"
        )
    )
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "unraid.local", CONF_API_KEY: "bad-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_API_KEY] == "invalid_auth"


async def test_client_connector_error_shows_cannot_connect(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test ClientConnectorError is handled as cannot connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_api = AsyncMock()
    conn_key = MagicMock()
    mock_api.test_connection = AsyncMock(
        side_effect=ClientConnectorError(conn_key, OSError("Connection refused"))
    )
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "unraid.local", CONF_API_KEY: "valid-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_HOST] == "cannot_connect"


async def test_ssl_error_retries_with_verify_disabled(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test SSL errors trigger retry with verify_ssl=False (self-signed certs)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    call_count = 0

    def create_client(**kwargs: object) -> MagicMock:
        nonlocal call_count
        call_count += 1
        mock_api = MagicMock()
        mock_api.close = AsyncMock()

        if kwargs.get("verify_ssl", True) is True:
            mock_api.test_connection = AsyncMock(
                side_effect=CannotConnectError("SSL certificate verify failed")
            )
        else:
            mock_api.test_connection = AsyncMock(return_value=True)
            mock_api.get_version = AsyncMock(
                return_value={"unraid": "7.2.0", "api": "4.29.2"}
            )
            mock_api.get_server_info = AsyncMock(
                return_value=ServerInfo(
                    uuid="test-uuid",
                    hostname="tower",
                    sw_version="7.2.0",
                    api_version="4.29.2",
                )
            )
        return mock_api

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", side_effect=create_client
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "unraid.local", CONF_API_KEY: "valid-key"},
        )

    assert call_count == 2
    assert result2["type"] is FlowResultType.CREATE_ENTRY


async def test_ssl_error_shows_cannot_connect_with_hint(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test SSL errors are handled with helpful message."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(
        side_effect=Exception("SSL certificate verify failed")
    )
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "unraid.local", CONF_API_KEY: "valid-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_HOST] == "cannot_connect"


async def test_unauthorized_in_error_message_shows_invalid_auth(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test 'unauthorized' in error message is detected as auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(side_effect=Exception("Request unauthorized"))
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "unraid.local", CONF_API_KEY: "bad-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_API_KEY] == "invalid_auth"


async def test_http_500_error_shows_cannot_connect(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test HTTP 500 error shows cannot connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(
        side_effect=aiohttp.ClientResponseError(
            request_info=None, history=(), status=500, message="Internal Server Error"
        )
    )
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "unraid.local", CONF_API_KEY: "valid-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_HOST] == "cannot_connect"


# =============================================================================
# Reauth Flow Tests
# =============================================================================


async def test_reauth_flow_shows_form(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reauth flow shows form for new API key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
        data={CONF_HOST: "unraid.local"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"


async def test_reauth_flow_success(
    hass: HomeAssistant, mock_setup_entry: None, mock_api_client: MagicMock
) -> None:
    """Test successful reauth updates the config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
        data={CONF_HOST: "unraid.local"},
    )

    with patch(
        "custom_components.unraid.config_flow.UnraidClient",
        return_value=mock_api_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "new-api-key"},
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert entry.data[CONF_API_KEY] == "new-api-key"


async def test_reauth_flow_invalid_key(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reauth with invalid API key shows error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
        data={CONF_HOST: "unraid.local"},
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(side_effect=Exception("401: Unauthorized"))
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "invalid-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "invalid_auth"


async def test_reauth_flow_missing_entry(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reauth flow raises UnknownEntry when entry doesn't exist."""
    from homeassistant.config_entries import UnknownEntry

    with pytest.raises(UnknownEntry):
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": "nonexistent-entry-id",
            },
            data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        )


async def test_reauth_flow_cannot_connect_error(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reauth flow shows connection error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
        data=entry.data,
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(
        side_effect=aiohttp.ClientError("Connection refused")
    )
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "new-api-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "cannot_connect"


async def test_reauth_flow_unsupported_version_error(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reauth flow shows unsupported version error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
        data=entry.data,
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock()
    mock_api.get_version = AsyncMock(return_value={"api": "0.0.1", "unraid": "6.0.0"})
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "new-api-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "unsupported_version"


async def test_reauth_flow_unknown_error(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reauth flow wraps unexpected exceptions as cannot_connect."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
        data=entry.data,
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(side_effect=RuntimeError("Unexpected"))
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "new-api-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "cannot_connect"


# =============================================================================
# Options Flow Tests
# =============================================================================


async def test_options_flow_empty_form_without_ups(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test options flow shows empty form when no UPS detected."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema_keys = list(result["data_schema"].schema.keys())
    schema_key_names = [str(k) for k in schema_keys]
    assert CONF_UPS_CAPACITY_VA not in schema_key_names
    assert CONF_UPS_NOMINAL_POWER not in schema_key_names


async def test_options_flow_shows_ups_options_when_ups_detected(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test options flow shows UPS options when UPS is detected."""

    @dataclass
    class MockSystemData:
        ups_devices: list

    @dataclass
    class MockRuntimeData:
        system_coordinator: MagicMock

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "key"},
        options={CONF_UPS_CAPACITY_VA: 1000, CONF_UPS_NOMINAL_POWER: 800},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    mock_coordinator = MagicMock()
    mock_coordinator.data = MockSystemData(
        ups_devices=[UPSDevice(id="ups:1", name="APC")]
    )
    entry.runtime_data = MockRuntimeData(system_coordinator=mock_coordinator)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema_keys = list(result["data_schema"].schema.keys())
    schema_key_names = [str(k) for k in schema_keys]
    assert CONF_UPS_CAPACITY_VA in schema_key_names
    assert CONF_UPS_NOMINAL_POWER in schema_key_names


async def test_options_flow_completes_without_ups(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test options flow completes with empty data when no UPS is present."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY


async def test_options_flow_saves_ups_values(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test options flow saves UPS values when UPS is present."""

    @dataclass
    class MockSystemData:
        ups_devices: list

    @dataclass
    class MockRuntimeData:
        system_coordinator: MagicMock

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "key"},
        options={
            CONF_UPS_CAPACITY_VA: DEFAULT_UPS_CAPACITY_VA,
            CONF_UPS_NOMINAL_POWER: DEFAULT_UPS_NOMINAL_POWER,
        },
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    mock_coordinator = MagicMock()
    mock_coordinator.data = MockSystemData(
        ups_devices=[UPSDevice(id="ups:1", name="APC")]
    )
    entry.runtime_data = MockRuntimeData(system_coordinator=mock_coordinator)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_UPS_CAPACITY_VA: 1500, CONF_UPS_NOMINAL_POWER: 1200},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_UPS_CAPACITY_VA] == 1500
    assert entry.options[CONF_UPS_NOMINAL_POWER] == 1200


# =============================================================================
# Reconfigure Flow Tests
# =============================================================================


async def test_reconfigure_flow_shows_form(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reconfigure flow shows form with current values."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"


async def test_reconfigure_flow_success(
    hass: HomeAssistant, mock_setup_entry: None, mock_api_client: MagicMock
) -> None:
    """Test successful reconfigure updates the config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    with patch(
        "custom_components.unraid.config_flow.UnraidClient",
        return_value=mock_api_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.1.100", CONF_API_KEY: "new-key"},
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "192.168.1.100"
    assert entry.data[CONF_API_KEY] == "new-key"


async def test_reconfigure_flow_connection_error(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reconfigure with connection error shows error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(
        side_effect=aiohttp.ClientError("Connection refused")
    )
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.1.100", CONF_API_KEY: "new-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "cannot_connect"


async def test_reconfigure_flow_missing_entry(hass: HomeAssistant) -> None:
    """Test reconfigure flow aborts when entry is missing."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": "nonexistent-entry",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_failed"


async def test_reconfigure_flow_validation_errors(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reconfigure flow shows validation errors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "", CONF_API_KEY: "new-key"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_HOST] == "required"


async def test_reconfigure_flow_invalid_auth_error(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reconfigure flow shows invalid auth error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(
        side_effect=aiohttp.ClientResponseError(
            request_info=None, history=(), status=401, message="Unauthorized"
        )
    )
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.1.100", CONF_API_KEY: "bad-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "invalid_auth"


async def test_reconfigure_flow_unsupported_version_error(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reconfigure flow shows unsupported version error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock()
    mock_api.get_version = AsyncMock(return_value={"api": "0.0.1", "unraid": "6.0.0"})
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.1.100", CONF_API_KEY: "new-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "unsupported_version"


async def test_reconfigure_flow_unknown_error(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reconfigure flow wraps unexpected exceptions as cannot_connect."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(side_effect=RuntimeError("Unexpected"))
    mock_api.close = AsyncMock()

    with patch(
        "custom_components.unraid.config_flow.UnraidClient", return_value=mock_api
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.1.100", CONF_API_KEY: "new-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "cannot_connect"


async def test_reconfigure_flow_shows_port_field(
    hass: HomeAssistant, mock_setup_entry: None
) -> None:
    """Test reconfigure flow shows form with HTTP and HTTPS port fields."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={
            CONF_HOST: "unraid.local",
            CONF_HTTP_PORT: 8080,
            CONF_HTTPS_PORT: 8443,
            CONF_API_KEY: "old-key",
        },
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert "http_port" in result["data_schema"].schema
    assert "https_port" in result["data_schema"].schema


async def test_reconfigure_flow_updates_port(
    hass: HomeAssistant, mock_setup_entry: None, mock_api_client: MagicMock
) -> None:
    """Test reconfigure flow can update the ports."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={
            CONF_HOST: "unraid.local",
            CONF_HTTP_PORT: 80,
            CONF_HTTPS_PORT: 443,
            CONF_API_KEY: "old-key",
        },
        options={},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    with patch(
        "custom_components.unraid.config_flow.UnraidClient",
        return_value=mock_api_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "unraid.local",
                CONF_HTTP_PORT: 8080,
                CONF_HTTPS_PORT: 8443,
                CONF_API_KEY: "new-key",
            },
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HTTP_PORT] == 8080
    assert entry.data[CONF_HTTPS_PORT] == 8443
