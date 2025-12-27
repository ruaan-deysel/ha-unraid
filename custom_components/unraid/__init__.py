"""
The Unraid integration.

This integration connects Home Assistant to Unraid servers via GraphQL API.
Provides monitoring and control for system metrics, storage, Docker, and VMs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import issue_registry as ir

from .api import UnraidAPIClient
from .const import (
    CONF_STORAGE_INTERVAL,
    CONF_SYSTEM_INTERVAL,
    DEFAULT_STORAGE_POLL_INTERVAL,
    DEFAULT_SYSTEM_POLL_INTERVAL,
    DOMAIN,
    REPAIR_AUTH_FAILED,
)
from .coordinator import UnraidStorageCoordinator, UnraidSystemCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]


@dataclass
class UnraidRuntimeData:
    """Runtime data for Unraid integration (stored in entry.runtime_data)."""

    api_client: UnraidAPIClient
    system_coordinator: UnraidSystemCoordinator
    storage_coordinator: UnraidStorageCoordinator
    server_info: dict


# Type alias for config entries with runtime data
type UnraidConfigEntry = ConfigEntry[UnraidRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Set up Unraid from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 443)
    api_key = entry.data[CONF_API_KEY]
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, True)

    # Get polling intervals from options (or use defaults)
    system_interval = entry.options.get(
        CONF_SYSTEM_INTERVAL, DEFAULT_SYSTEM_POLL_INTERVAL
    )
    storage_interval = entry.options.get(
        CONF_STORAGE_INTERVAL, DEFAULT_STORAGE_POLL_INTERVAL
    )

    # Create API client
    api_client = UnraidAPIClient(
        host=host,
        port=port,
        api_key=api_key,
        verify_ssl=verify_ssl,
    )

    # Test connection and get server info
    try:
        await api_client.test_connection()
        info = await api_client.query(
            """
            query SystemInfo {
                info {
                    system { uuid manufacturer model }
                    baseboard { manufacturer model }
                    os { hostname distro release kernel arch }
                    versions { core { unraid api } }
                }
                registration { type state }
            }
            """
        )
        # Clear any previous auth repair issues on successful connection
        ir.async_delete_issue(hass, DOMAIN, REPAIR_AUTH_FAILED)
    except Exception as err:
        await api_client.close()
        error_str = str(err).lower()
        # Check for authentication errors
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
            # Create repair issue for auth failure
            ir.async_create_issue(
                hass,
                DOMAIN,
                REPAIR_AUTH_FAILED,
                is_fixable=True,
                is_persistent=True,
                severity=ir.IssueSeverity.ERROR,
                translation_key="auth_failed",
                translation_placeholders={"host": host},
            )
            msg = f"Authentication failed for Unraid server {host}"
            raise ConfigEntryAuthFailed(msg) from err
        msg = f"Failed to connect to Unraid server: {err}"
        raise ConfigEntryNotReady(msg) from err

    # Extract server info for device registration
    info_data = info.get("info", {})
    system_data = info_data.get("system", {})
    baseboard_data = info_data.get("baseboard", {})
    os_data = info_data.get("os", {})
    versions_data = info_data.get("versions", {}).get("core", {})
    registration_data = info.get("registration", {})

    # Use baseboard manufacturer/model if system is empty
    manufacturer = (
        system_data.get("manufacturer")
        or baseboard_data.get("manufacturer")
        or "Lime Technology"
    )
    model = system_data.get("model") or baseboard_data.get("model") or "Unraid Server"

    server_name = os_data.get("hostname") or host
    server_uuid = system_data.get("uuid")

    # Build comprehensive server info for device registration
    server_info = {
        "uuid": server_uuid,
        "name": server_name,
        "manufacturer": manufacturer,
        "model": model,
        "sw_version": versions_data.get("unraid"),
        "hw_version": os_data.get("kernel"),
        "os_distro": os_data.get("distro"),
        "os_release": os_data.get("release"),
        "os_arch": os_data.get("arch"),
        "api_version": versions_data.get("api"),
        "license_type": registration_data.get("type"),
    }

    # Create coordinators
    system_coordinator = UnraidSystemCoordinator(
        hass=hass,
        api_client=api_client,
        server_name=server_name,
        update_interval=system_interval,
    )

    storage_coordinator = UnraidStorageCoordinator(
        hass=hass,
        api_client=api_client,
        server_name=server_name,
        update_interval=storage_interval,
    )

    # Fetch initial data
    await system_coordinator.async_config_entry_first_refresh()
    await storage_coordinator.async_config_entry_first_refresh()

    # Store runtime data in config entry (HA 2024.4+ pattern)
    entry.runtime_data = UnraidRuntimeData(
        api_client=api_client,
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info=server_info,
    )

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(_async_options_update_listener))

    _LOGGER.info(
        "Unraid integration setup complete for %s (system: %ds, storage: %ds)",
        server_name,
        system_interval,
        storage_interval,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Close API client
        await entry.runtime_data.api_client.close()
        _LOGGER.info("Unraid integration unloaded for entry %s", entry.title)

    return unload_ok


async def _async_options_update_listener(
    hass: HomeAssistant, entry: UnraidConfigEntry
) -> None:
    """Handle options update - triggers full entry reload."""
    _LOGGER.info(
        "Options changed for %s, reloading integration",
        entry.title,
    )
    # Reload the entry to apply new options
    await hass.config_entries.async_reload(entry.entry_id)
