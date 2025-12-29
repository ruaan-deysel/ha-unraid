"""Config flow tests for the Unraid integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unraid.const import (
    CONF_STORAGE_INTERVAL,
    CONF_SYSTEM_INTERVAL,
    CONF_UPS_CAPACITY_VA,
    DEFAULT_STORAGE_POLL_INTERVAL,
    DEFAULT_SYSTEM_POLL_INTERVAL,
    DEFAULT_UPS_CAPACITY_VA,
    DOMAIN,
)


@pytest.fixture
def mock_setup_entry():
    """Mock setup_entry to avoid actual HA component setup."""
    with patch("custom_components.unraid.async_setup_entry", return_value=True):
        yield


def _mock_api_client(
    uuid: str = "test-server-uuid",
    hostname: str = "tower",
    unraid_version: str = "7.2.0",
    api_version: str = "4.29.2",
) -> AsyncMock:
    """Create a mock API client with standard responses."""
    mock_api = AsyncMock()
    mock_api.test_connection = AsyncMock(return_value=True)
    mock_api.get_version = AsyncMock(
        return_value={"unraid": unraid_version, "api": api_version}
    )
    mock_api.query = AsyncMock(
        return_value={
            "info": {
                "system": {"uuid": uuid},
                "os": {"hostname": hostname},
            }
        }
    )
    mock_api.close = AsyncMock()
    return mock_api


class TestConfigFlow:
    """Test Unraid config flow."""

    async def test_user_step_form_display(self, hass: HomeAssistant) -> None:
        """Test user step shows form with required fields."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert "host" in result["data_schema"].schema
        assert "api_key" in result["data_schema"].schema

    async def test_successful_connection(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test successful server connection creates config entry."""
        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            MockAPIClient.return_value = _mock_api_client()

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    "host": "unraid.local",
                    "api_key": "valid-api-key",
                },
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["title"] == "tower"  # Uses server hostname now
            assert result["data"]["host"] == "unraid.local"
            assert result["data"]["api_key"] == "valid-api-key"

    async def test_invalid_credentials_error(self, hass: HomeAssistant) -> None:
        """Test invalid API key shows authentication error."""
        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(
                side_effect=Exception("401: Unauthorized")
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    "host": "unraid.local",
                    "api_key": "invalid-key",
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"]["base"] == "invalid_auth"

    async def test_unreachable_server_error(self, hass: HomeAssistant) -> None:
        """Test unreachable server shows connection error."""
        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            import aiohttp

            mock_api = AsyncMock()
            # Use ClientError which is simpler to mock
            mock_api.test_connection = AsyncMock(
                side_effect=aiohttp.ClientError("Connection refused")
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    "host": "unraid.invalid",
                    "api_key": "valid-key",
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"]["base"] == "cannot_connect"

    async def test_unsupported_version_error(self, hass: HomeAssistant) -> None:
        """Test old Unraid version shows version error."""
        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(return_value=True)
            mock_api.get_version = AsyncMock(
                return_value={"unraid": "6.9.0", "api": "4.10.0"}
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    "host": "unraid.local",
                    "api_key": "valid-key",
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"]["base"] == "unsupported_version"

    async def test_duplicate_config_entry(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test duplicate server UUID is rejected."""
        # First entry
        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            MockAPIClient.return_value = _mock_api_client(uuid="same-server-uuid")

            result1 = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    "host": "unraid.local",
                    "api_key": "key1",
                },
            )

            assert result1["type"] == FlowResultType.CREATE_ENTRY

        # Second entry with same UUID (different host but same server)
        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            MockAPIClient.return_value = _mock_api_client(uuid="same-server-uuid")

            result2 = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    "host": "192.168.1.100",  # Different host
                    "api_key": "key2",
                },
            )

            assert result2["type"] == FlowResultType.ABORT
            assert result2["reason"] == "already_configured"

    async def test_hostname_validation(self, hass: HomeAssistant) -> None:
        """Test hostname/IP validation - empty hostname rejected."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                "host": "",
                "api_key": "valid-key",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert "host" in result["errors"]

    async def test_api_key_validation(self, hass: HomeAssistant) -> None:
        """Test API key validation - empty key rejected."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                "host": "unraid.local",
                "api_key": "",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert "api_key" in result["errors"]

    async def test_user_step_unknown_error(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test unexpected error during user step gets wrapped as cannot_connect."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "unraid.local", CONF_API_KEY: "valid-api-key"},
            )

        # RuntimeError gets wrapped as CannotConnectError by _handle_generic_error
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"

    async def test_hostname_max_length_validation(self, hass: HomeAssistant) -> None:
        """Test hostname exceeding max length shows error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Create hostname that exceeds MAX_HOSTNAME_LEN (254)
        long_hostname = "a" * 255

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: long_hostname, CONF_API_KEY: "valid-api-key"},
        )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"][CONF_HOST] == "invalid_hostname"

    async def test_http_error_403_shows_invalid_auth(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test HTTP 403 error is handled as invalid auth."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            import aiohttp

            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(
                side_effect=aiohttp.ClientResponseError(
                    request_info=None, history=(), status=403, message="Forbidden"
                )
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "unraid.local", CONF_API_KEY: "bad-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "invalid_auth"

    async def test_client_connector_error_shows_cannot_connect(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test ClientConnectorError is handled as cannot connect."""
        from unittest.mock import MagicMock

        from aiohttp import ClientConnectorError

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            conn_key = MagicMock()
            mock_api.test_connection = AsyncMock(
                side_effect=ClientConnectorError(
                    conn_key, OSError("Connection refused")
                )
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "unraid.local", CONF_API_KEY: "valid-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"

    async def test_ssl_error_shows_cannot_connect_with_hint(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test SSL errors are handled with helpful message."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(
                side_effect=Exception("SSL certificate verify failed")
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "unraid.local", CONF_API_KEY: "valid-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"

    async def test_unauthorized_in_error_message_shows_invalid_auth(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test 'unauthorized' in error message is detected as auth error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(
                side_effect=Exception("Request unauthorized")
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "unraid.local", CONF_API_KEY: "bad-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "invalid_auth"

    async def test_http_500_error_shows_cannot_connect(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test HTTP 500 error shows cannot connect."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            import aiohttp

            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(
                side_effect=aiohttp.ClientResponseError(
                    request_info=None,
                    history=(),
                    status=500,
                    message="Internal Server Error",
                )
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "unraid.local", CONF_API_KEY: "valid-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"


class TestReauthFlow:
    """Test Unraid reauth flow."""

    async def test_reauth_flow_shows_form(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test reauth flow shows form for new API key."""
        # Create initial config entry
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
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data={CONF_HOST: "unraid.local"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

    async def test_reauth_flow_success(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test successful reauth updates the config entry."""
        # Create initial config entry
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
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data={CONF_HOST: "unraid.local"},
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            MockAPIClient.return_value = _mock_api_client()

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_API_KEY: "new-api-key"},
            )

        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "reauth_successful"
        assert entry.data[CONF_API_KEY] == "new-api-key"

    async def test_reauth_flow_invalid_key(
        self, hass: HomeAssistant, mock_setup_entry: None
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
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data={CONF_HOST: "unraid.local"},
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(
                side_effect=Exception("401: Unauthorized")
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_API_KEY: "invalid-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "invalid_auth"

    async def test_reauth_flow_missing_entry(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test reauth flow raises UnknownEntry when entry doesn't exist."""
        from homeassistant.config_entries import UnknownEntry

        # When reauth is initiated with a nonexistent entry_id, Home Assistant
        # raises UnknownEntry during form display (when accessing _get_reauth_entry())
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
        self, hass: HomeAssistant, mock_setup_entry: None
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
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            import aiohttp

            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(
                side_effect=aiohttp.ClientError("Connection refused")
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_API_KEY: "new-api-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"

    async def test_reauth_flow_unsupported_version_error(
        self, hass: HomeAssistant, mock_setup_entry: None
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
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock()
            mock_api.get_version = AsyncMock(
                return_value={"api": "0.0.1", "unraid": "6.0.0"}  # Old version
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_API_KEY: "new-api-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "unsupported_version"

    async def test_reauth_flow_unknown_error(
        self, hass: HomeAssistant, mock_setup_entry: None
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
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_API_KEY: "new-api-key"},
            )

        # RuntimeError gets wrapped as CannotConnectError by _handle_generic_error
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"


class TestOptionsFlow:
    """Test Unraid options flow."""

    async def test_options_flow_shows_form(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test options flow shows form with current values."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="tower",
            data={CONF_HOST: "unraid.local", CONF_API_KEY: "key"},
            options={
                CONF_SYSTEM_INTERVAL: 60,
                CONF_STORAGE_INTERVAL: 600,
                CONF_UPS_CAPACITY_VA: 1000,
            },
            unique_id="test-uuid",
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_flow_saves_values(
        self, hass: HomeAssistant, mock_setup_entry: None
    ) -> None:
        """Test options flow saves new values."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="tower",
            data={CONF_HOST: "unraid.local", CONF_API_KEY: "key"},
            options={
                CONF_SYSTEM_INTERVAL: DEFAULT_SYSTEM_POLL_INTERVAL,
                CONF_STORAGE_INTERVAL: DEFAULT_STORAGE_POLL_INTERVAL,
                CONF_UPS_CAPACITY_VA: DEFAULT_UPS_CAPACITY_VA,
            },
            unique_id="test-uuid",
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_SYSTEM_INTERVAL: 45,
                CONF_STORAGE_INTERVAL: 120,
                CONF_UPS_CAPACITY_VA: 1500,
            },
        )

        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert entry.options[CONF_SYSTEM_INTERVAL] == 45
        assert entry.options[CONF_STORAGE_INTERVAL] == 120
        assert entry.options[CONF_UPS_CAPACITY_VA] == 1500


class TestReconfigureFlow:
    """Test Unraid reconfigure flow."""

    async def test_reconfigure_flow_shows_form(
        self, hass: HomeAssistant, mock_setup_entry: None
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

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

    async def test_reconfigure_flow_success(
        self, hass: HomeAssistant, mock_setup_entry: None
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
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            MockAPIClient.return_value = _mock_api_client()

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "192.168.1.100", CONF_API_KEY: "new-key"},
            )

        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "reconfigure_successful"
        assert entry.data[CONF_HOST] == "192.168.1.100"
        assert entry.data[CONF_API_KEY] == "new-key"

    async def test_reconfigure_flow_connection_error(
        self, hass: HomeAssistant, mock_setup_entry: None
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

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            import aiohttp

            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(
                side_effect=aiohttp.ClientError("Connection refused")
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "192.168.1.100", CONF_API_KEY: "new-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"

    async def test_reconfigure_flow_missing_entry(self, hass: HomeAssistant) -> None:
        """Test reconfigure flow aborts when entry is missing."""
        # Start reconfigure with invalid entry_id
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": "nonexistent-entry",
            },
        )

        # Should abort immediately
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reconfigure_failed"

    async def test_reconfigure_flow_validation_errors(
        self, hass: HomeAssistant, mock_setup_entry: None
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

        # Submit with empty host
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "", CONF_API_KEY: "new-key"},
        )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"][CONF_HOST] == "required"

    async def test_reconfigure_flow_invalid_auth_error(
        self, hass: HomeAssistant, mock_setup_entry: None
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

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            import aiohttp

            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(
                side_effect=aiohttp.ClientResponseError(
                    request_info=None, history=(), status=401, message="Unauthorized"
                )
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "192.168.1.100", CONF_API_KEY: "bad-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "invalid_auth"

    async def test_reconfigure_flow_unsupported_version_error(
        self, hass: HomeAssistant, mock_setup_entry: None
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

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock()
            mock_api.get_version = AsyncMock(
                return_value={"api": "0.0.1", "unraid": "6.0.0"}
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "192.168.1.100", CONF_API_KEY: "new-key"},
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "unsupported_version"

    async def test_reconfigure_flow_unknown_error(
        self, hass: HomeAssistant, mock_setup_entry: None
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

        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(side_effect=RuntimeError("Unexpected"))
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "192.168.1.100", CONF_API_KEY: "new-key"},
            )

        # RuntimeError gets wrapped as CannotConnectError by _handle_generic_error
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"
