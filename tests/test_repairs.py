"""Tests for the Unraid repairs module."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unraid.const import DOMAIN, REPAIR_AUTH_FAILED
from custom_components.unraid.repairs import (
    AuthFailedRepairFlow,
    async_create_fix_flow,
)


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={"host": "192.168.1.100", "api_key": "test-key"},
        unique_id="test-uuid",
    )


async def test_async_create_fix_flow_auth_failed(hass: HomeAssistant) -> None:
    """Test creating fix flow for auth failed issue."""
    flow = await async_create_fix_flow(hass, REPAIR_AUTH_FAILED, None)
    assert isinstance(flow, AuthFailedRepairFlow)


async def test_async_create_fix_flow_unknown_issue(hass: HomeAssistant) -> None:
    """Test creating fix flow for unknown issue raises error."""
    with pytest.raises(ValueError, match="Unknown issue ID"):
        await async_create_fix_flow(hass, "unknown_issue", None)


async def test_auth_failed_repair_flow_init(hass: HomeAssistant) -> None:
    """Test auth failed repair flow init step redirects to confirm."""
    flow = AuthFailedRepairFlow()
    flow.hass = hass

    result = await flow.async_step_init()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"


async def test_auth_failed_repair_flow_confirm_shows_form(hass: HomeAssistant) -> None:
    """Test auth failed repair flow confirm shows form when no input."""
    flow = AuthFailedRepairFlow()
    flow.hass = hass

    result = await flow.async_step_confirm()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"


async def test_auth_failed_repair_flow_confirm_starts_reauth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test auth failed repair flow starts reauth when user submits."""
    mock_config_entry.add_to_hass(hass)

    flow = AuthFailedRepairFlow()
    flow.hass = hass

    with patch.object(
        hass.config_entries.flow, "async_init", return_value={"flow_id": "test"}
    ) as mock_init:
        result = await flow.async_step_confirm(user_input={})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    # Verify reauth flow was initiated
    await hass.async_block_till_done()
    mock_init.assert_called_once()
    call_kwargs = mock_init.call_args
    assert call_kwargs[0][0] == DOMAIN
    assert call_kwargs[1]["context"]["source"] == "reauth"
    assert call_kwargs[1]["context"]["entry_id"] == mock_config_entry.entry_id


async def test_auth_failed_repair_flow_confirm_no_entries(
    hass: HomeAssistant,
) -> None:
    """Test auth failed repair flow handles no config entries gracefully."""
    flow = AuthFailedRepairFlow()
    flow.hass = hass

    result = await flow.async_step_confirm(user_input={})

    # Should still create entry even with no config entries
    assert result["type"] is FlowResultType.CREATE_ENTRY
