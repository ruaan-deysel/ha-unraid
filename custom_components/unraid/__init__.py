"""
The Unraid integration.

This integration connects Home Assistant to Unraid servers via the unraid-api library.
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
    CONF_SSL,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from unraid_api import ServerInfo, UnraidClient
from unraid_api.exceptions import (
    UnraidAPIError,
    UnraidAuthenticationError,
    UnraidConnectionError,
    UnraidSSLError,
    UnraidTimeoutError,
)

from .const import (
    CONF_IGNORE_SSL,
    DEFAULT_PORT,
    DOMAIN,
    REPAIR_AUTH_FAILED,
)
from .coordinator import (
    UnraidInfraCoordinator,
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)
from .websocket import UnraidWebSocketManager

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.UPDATE,
]


@dataclass
class UnraidRuntimeData:
    """Runtime data for Unraid integration (stored in entry.runtime_data)."""

    api_client: UnraidClient
    system_coordinator: UnraidSystemCoordinator
    storage_coordinator: UnraidStorageCoordinator
    infra_coordinator: UnraidInfraCoordinator
    websocket_manager: UnraidWebSocketManager
    server_info: dict


# Type alias for config entries with runtime data
type UnraidConfigEntry = ConfigEntry[UnraidRuntimeData]


def _build_server_info(server_info: ServerInfo, host: str, use_ssl: bool) -> dict:
    """Build server info dictionary from library's ServerInfo model."""
    # Use library's ServerInfo model directly
    # Model shows "Unraid {version}" for prominent display in Device Info
    unraid_version = server_info.sw_version or "Unknown"
    model = f"Unraid {unraid_version}"

    server_name = server_info.hostname or host

    # Determine configuration URL for device info
    configuration_url = server_info.local_url
    if not configuration_url and server_info.lan_ip:
        protocol = "https" if use_ssl else "http"
        configuration_url = f"{protocol}://{server_info.lan_ip}"

    return {
        "uuid": server_info.uuid,
        "name": server_name,
        "manufacturer": server_info.manufacturer,
        "model": model,
        "serial_number": server_info.serial_number,
        "sw_version": unraid_version,
        "hw_version": server_info.hw_version,
        "os_distro": server_info.os_distro,
        "os_release": server_info.os_release,
        "os_arch": server_info.os_arch,
        "api_version": server_info.api_version,
        "license_type": server_info.license_type,
        "lan_ip": server_info.lan_ip,
        "configuration_url": configuration_url,
        "cpu_brand": server_info.cpu_brand,
        "cpu_cores": server_info.cpu_cores,
        "cpu_threads": server_info.cpu_threads,
        # Hardware info for diagnostics
        "hw_manufacturer": server_info.hw_manufacturer,
        "hw_model": server_info.hw_model,
    }


def _normalize_ssl_config(
    hass: HomeAssistant,
    entry: UnraidConfigEntry,
    host: str,
    port: int,
) -> tuple[bool, bool, bool]:
    """Normalize SSL settings and update legacy entries if needed."""
    use_ssl = entry.data.get(CONF_SSL, True)
    ignore_ssl = entry.data.get(CONF_IGNORE_SSL, False)

    if CONF_IGNORE_SSL not in entry.data and use_ssl is False:
        use_ssl = True
        ignore_ssl = True
        _LOGGER.debug(
            "Applying legacy SSL compatibility normalization for %s:%s "
            "(ssl=False without ignore_ssl): normalized to ssl=True, ignore_ssl=True",
            host,
            port,
        )
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_SSL: use_ssl, CONF_IGNORE_SSL: ignore_ssl},
        )

    return use_ssl, ignore_ssl, not ignore_ssl


async def _async_connect_and_get_server_info(
    hass: HomeAssistant,
    api_client: UnraidClient,
    host: str,
    port: int,
) -> ServerInfo:
    """Validate connection and fetch server info with normalized errors."""
    try:
        await api_client.test_connection()
        info = await api_client.get_server_info()
        _LOGGER.debug("Initial connectivity test succeeded for %s:%s", host, port)
        ir.async_delete_issue(hass, DOMAIN, REPAIR_AUTH_FAILED)
        return info
    except UnraidAuthenticationError as err:
        await api_client.close()
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
        _LOGGER.warning(
            "Authentication failed for Unraid server %s:%s: %s",
            host,
            port,
            err,
        )
        msg = f"Authentication failed for Unraid server {host}"
        raise ConfigEntryAuthFailed(msg) from err
    except UnraidSSLError as err:
        await api_client.close()
        _LOGGER.warning(
            "TLS certificate validation failed for Unraid server %s:%s: %s. "
            "If this server uses a self-signed certificate, reconfigure "
            "the integration so certificate verification can be disabled "
            "and persisted.",
            host,
            port,
            err,
        )
        msg = f"SSL certificate error connecting to Unraid server {host}: {err}"
        raise ConfigEntryNotReady(msg) from err
    except (UnraidConnectionError, UnraidTimeoutError) as err:
        await api_client.close()
        _LOGGER.warning(
            "Connection failed for Unraid server %s:%s: %s",
            host,
            port,
            err,
        )
        msg = f"Failed to connect to Unraid server: {err}"
        raise ConfigEntryNotReady(msg) from err
    except UnraidAPIError as err:
        await api_client.close()
        _LOGGER.warning(
            "API error connecting to Unraid server %s:%s: %s",
            host,
            port,
            err,
        )
        msg = f"Unraid API error connecting to server {host}: {err}"
        raise ConfigEntryNotReady(msg) from err


def _create_coordinators(
    hass: HomeAssistant,
    api_client: UnraidClient,
    server_name: str,
    entry: UnraidConfigEntry,
) -> tuple[
    UnraidSystemCoordinator,
    UnraidStorageCoordinator,
    UnraidInfraCoordinator,
]:
    """Create integration coordinators."""
    system_coordinator = UnraidSystemCoordinator(
        hass=hass,
        api_client=api_client,
        server_name=server_name,
        config_entry=entry,
    )
    storage_coordinator = UnraidStorageCoordinator(
        hass=hass,
        api_client=api_client,
        server_name=server_name,
        config_entry=entry,
    )
    infra_coordinator = UnraidInfraCoordinator(
        hass=hass,
        api_client=api_client,
        server_name=server_name,
        config_entry=entry,
    )
    return system_coordinator, storage_coordinator, infra_coordinator


async def _async_refresh_coordinators(
    api_client: UnraidClient,
    system_coordinator: UnraidSystemCoordinator,
    storage_coordinator: UnraidStorageCoordinator,
    infra_coordinator: UnraidInfraCoordinator,
) -> None:
    """Run initial refresh for all coordinators."""
    try:
        await system_coordinator.async_config_entry_first_refresh()
        await storage_coordinator.async_config_entry_first_refresh()
        await infra_coordinator.async_config_entry_first_refresh()
    except (ConfigEntryAuthFailed, ConfigEntryNotReady):
        await api_client.close()
        raise


async def async_setup_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Set up Unraid from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    api_key = entry.data[CONF_API_KEY]
    use_ssl, ignore_ssl, verify_ssl = _normalize_ssl_config(hass, entry, host, port)
    _LOGGER.debug(
        "Starting runtime setup for %s:%s (ssl=%s, ignore_ssl=%s)",
        host,
        port,
        use_ssl,
        ignore_ssl,
    )

    # Get HA's aiohttp session for proper connection pooling
    session = async_get_clientsession(hass, verify_ssl=verify_ssl)

    # Create API client with injected session (using unraid_api library >=1.5.0).
    # The library handles SSL detection automatically via HTTP probe.
    api_client = UnraidClient(
        host=host,
        http_port=port,
        api_key=api_key,
        verify_ssl=verify_ssl,
        session=session,
    )
    info = await _async_connect_and_get_server_info(hass, api_client, host, port)

    # Build server info using helper function
    server_info = _build_server_info(info, host, use_ssl)
    server_name = server_info["name"]

    (
        system_coordinator,
        storage_coordinator,
        infra_coordinator,
    ) = _create_coordinators(
        hass,
        api_client,
        server_name,
        entry,
    )

    # Fetch initial data
    await _async_refresh_coordinators(
        api_client,
        system_coordinator,
        storage_coordinator,
        infra_coordinator,
    )

    # Store runtime data in config entry (HA 2024.4+ pattern)
    websocket_manager = UnraidWebSocketManager(
        api_client=api_client,
        system_coordinator=system_coordinator,
        server_name=server_name,
    )

    entry.runtime_data = UnraidRuntimeData(
        api_client=api_client,
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        infra_coordinator=infra_coordinator,
        websocket_manager=websocket_manager,
        server_info=server_info,
    )

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start WebSocket subscriptions after platforms are set up
    await websocket_manager.async_start()

    async def _async_stop_websocket_on_hass_stop(_event: object) -> None:
        """Stop websocket tasks when Home Assistant is stopping."""
        await websocket_manager.async_stop()

    # Ensure websocket tasks are cleaned up even if entry unload is not invoked.
    entry.async_on_unload(
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP,
            _async_stop_websocket_on_hass_stop,
        )
    )

    _LOGGER.info(
        "Unraid integration setup complete for %s",
        server_name,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Stop WebSocket subscriptions
        await entry.runtime_data.websocket_manager.async_stop()
        # Close API client
        await entry.runtime_data.api_client.close()
        _LOGGER.info("Unraid integration unloaded for entry %s", entry.title)

    return unload_ok
