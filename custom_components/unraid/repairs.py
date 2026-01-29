"""Repairs for the Unraid integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, REPAIR_AUTH_FAILED

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class AuthFailedRepairFlow(RepairsFlow):
    """Handler for auth failed repair flow."""

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Handle the first step of the repair flow."""
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict | None = None) -> FlowResult:
        """Handle the confirm step - redirect to reauth flow."""
        if user_input is not None:
            # Find the config entry for this integration
            entries = self.hass.config_entries.async_entries(DOMAIN)
            if entries:
                # Start reauth flow for the first entry
                # (typically there's only one Unraid server)
                entry = entries[0]
                self.hass.async_create_task(
                    self.hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={
                            "source": "reauth",
                            "entry_id": entry.entry_id,
                        },
                        data=entry.data,
                    )
                )
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
        )


async def async_create_fix_flow(
    hass: HomeAssistant,  # noqa: ARG001
    issue_id: str,
    data: dict | None,  # noqa: ARG001
) -> RepairsFlow:
    """Create flow for fixing an issue."""
    if issue_id == REPAIR_AUTH_FAILED:
        return AuthFailedRepairFlow()

    # Unknown issue - this shouldn't happen
    raise ValueError(f"Unknown issue ID: {issue_id}")
