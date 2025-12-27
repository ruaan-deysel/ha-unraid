"""Config flow tests for the Unraid integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.unraid.const import DOMAIN


@pytest.fixture
def mock_setup_entry():
    """Mock setup_entry to avoid actual HA component setup."""
    with patch("custom_components.unraid.async_setup_entry", return_value=True):
        yield


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
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(return_value=True)
            # API returns "api" and "unraid" keys, not "api_version"
            mock_api.get_version = AsyncMock(
                return_value={"unraid": "7.2.0", "api": "4.29.2"}
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    "host": "unraid.local",
                    "api_key": "valid-api-key",
                },
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["title"] == "unraid.local"
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
        """Test duplicate server host is rejected."""
        # First entry
        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(return_value=True)
            mock_api.get_version = AsyncMock(
                return_value={"unraid": "7.2.0", "api": "4.29.2"}
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result1 = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    "host": "unraid.local",
                    "api_key": "key1",
                },
            )

            assert result1["type"] == FlowResultType.CREATE_ENTRY

        # Second entry with same host
        with patch(
            "custom_components.unraid.config_flow.UnraidAPIClient"
        ) as MockAPIClient:
            mock_api = AsyncMock()
            mock_api.test_connection = AsyncMock(return_value=True)
            mock_api.get_version = AsyncMock(
                return_value={"unraid": "7.2.0", "api": "4.29.2"}
            )
            mock_api.close = AsyncMock()
            MockAPIClient.return_value = mock_api

            result2 = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data={
                    "host": "unraid.local",
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
