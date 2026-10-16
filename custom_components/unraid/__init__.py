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
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
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
from yarl import URL

from .cleanup import async_cleanup_stale_entities
from .const import (
    CONF_IGNORE_SSL,
    DEFAULT_PORT,
    DOMAIN,
    REPAIR_AUTH_FAILED,
    is_placeholder_uuid,
)
from .coordinator import (
    UnraidInfraCoordinator,
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)
from .frontend import async_register_frontend
from .websocket import UnraidWebSocketManager

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

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
    try:
        parsed_url = URL(configuration_url or "")
        valid_configuration_url = parsed_url.scheme in {"http", "https"} and bool(
            parsed_url.host
        )
    except ValueError:
        valid_configuration_url = False

    if not valid_configuration_url:
        protocol = "https" if use_ssl else "http"
        configuration_url = f"{protocol}://{server_info.lan_ip or host}"

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


def _resolve_server_identity(
    api_uuid: str | None, entry_unique_id: str | None
) -> str | None:
    """
    Return the identity used as the ``{server_uuid}`` prefix at runtime.

    The config flow qualifies a placeholder SMBIOS UUID with the hostname
    (``{uuid}_{hostname}``) so two servers that share the same firmware UUID
    can both be configured.  Entities and the server device must use that
    same qualified identity, otherwise every server reuses the raw UUID and
    Home Assistant rejects the second server's entities as duplicates (#351).

    The hostname-qualified ``entry.unique_id`` is used only when the API UUID
    is a known placeholder *and* the stored unique ID was derived from it.
    Every other entry (real UUID, host fallback, legacy raw-placeholder
    unique ID, no unique ID) keeps the raw API value unchanged.
    """
    if not api_uuid or not entry_unique_id or not is_placeholder_uuid(api_uuid):
        return api_uuid
    if entry_unique_id.lower().startswith(f"{api_uuid.lower()}_"):
        return entry_unique_id
    return api_uuid


def _legacy_device_ids(
    hass: HomeAssistant, entry: UnraidConfigEntry, raw_uuid: str
) -> set[str]:
    """Return IDs of this entry's devices still keyed on the raw UUID."""
    dev_reg = dr.async_get(hass)
    return {
        device.id
        for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
        if (DOMAIN, raw_uuid) in device.identifiers
    }


def _migrate_entity_unique_ids(
    hass: HomeAssistant,
    entry: UnraidConfigEntry,
    raw_prefix: str,
    resolved_prefix: str,
    legacy_device_ids: set[str],
) -> None:
    """Rename this entry's entity unique IDs from the raw to the resolved prefix."""
    ent_reg = er.async_get(hass)
    for entity_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        unique_id = entity_entry.unique_id
        if not unique_id.startswith(raw_prefix):
            continue
        # The entity platform assigns unique_id and device together, so a
        # record attached to a device still keyed on the raw UUID was created
        # under the raw identity and needs migrating even when its resource ID
        # happens to start with the hostname (hostname "disk" vs
        # "disk_sda_temp"). Any other record already carrying the resolved
        # prefix was created, or migrated, under the resolved identity.
        if entity_entry.device_id not in legacy_device_ids and unique_id.startswith(
            resolved_prefix
        ):
            continue
        new_unique_id = f"{resolved_prefix}{unique_id[len(raw_prefix) :]}"
        existing = ent_reg.async_get_entity_id(
            entity_entry.domain, DOMAIN, new_unique_id
        )
        if existing is not None:
            _LOGGER.warning(
                "Cannot migrate %s to unique ID %s: %s already uses it. "
                "Remove the stale entity %s and reload the integration",
                entity_entry.entity_id,
                new_unique_id,
                existing,
                existing,
            )
            continue
        try:
            ent_reg.async_update_entity(
                entity_entry.entity_id, new_unique_id=new_unique_id
            )
        except ValueError as err:
            _LOGGER.warning(
                "Cannot migrate %s to unique ID %s: %s",
                entity_entry.entity_id,
                new_unique_id,
                err,
            )
            continue
        _LOGGER.debug(
            "Migrated %s unique ID %s -> %s",
            entity_entry.entity_id,
            unique_id,
            new_unique_id,
        )


def _migrate_device_identifiers(
    hass: HomeAssistant,
    entry: UnraidConfigEntry,
    raw_uuid: str,
    resolved_uuid: str,
) -> None:
    """Re-key this entry's server device from the raw UUID to the resolved one."""
    dev_reg = dr.async_get(hass)
    raw_identifier = (DOMAIN, raw_uuid)
    resolved_identifier = (DOMAIN, resolved_uuid)
    # Devices belong to exactly one config entry (HA 2026.8+), so a device that
    # servers previously shared has already been split per entry by core.
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        if raw_identifier not in device.identifiers:
            continue
        existing = dev_reg.async_get_device_by_identifier(
            resolved_identifier, entry.entry_id
        )
        if existing is not None and existing.id != device.id:
            _LOGGER.warning(
                "Cannot migrate device %s to identifier %s: device %s already "
                "uses it. Remove the stale device and reload the integration",
                device.id,
                resolved_uuid,
                existing.id,
            )
            continue
        dev_reg.async_update_device(
            device.id,
            new_identifiers=(device.identifiers - {raw_identifier})
            | {resolved_identifier},
        )
        _LOGGER.debug(
            "Migrated device %s identifier %s -> %s",
            device.id,
            raw_uuid,
            resolved_uuid,
        )


@callback
def _async_migrate_registry_identity(
    hass: HomeAssistant,
    entry: UnraidConfigEntry,
    raw_uuid: str | None,
    resolved_uuid: str | None,
) -> None:
    """
    Move registry records keyed on the raw placeholder UUID to the resolved identity.

    Runs before platforms are forwarded so existing entities keep their
    ``entity_id``, customisations and device.  The migration is idempotent:
    records that already carry the resolved prefix, records owned by another
    config entry and non-placeholder servers are never touched.  Conflicting
    targets are skipped with a warning rather than deleted.
    """
    if not raw_uuid or not resolved_uuid or raw_uuid == resolved_uuid:
        return
    _LOGGER.debug(
        "Server identity for entry %s resolved to %s (API UUID %s)",
        entry.entry_id,
        resolved_uuid,
        raw_uuid,
    )
    legacy_device_ids = _legacy_device_ids(hass, entry, raw_uuid)
    _migrate_entity_unique_ids(
        hass, entry, f"{raw_uuid}_", f"{resolved_uuid}_", legacy_device_ids
    )
    _migrate_device_identifiers(hass, entry, raw_uuid, resolved_uuid)


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
    server_info: ServerInfo,
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
        server_info=server_info,
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
    except ConfigEntryAuthFailed, ConfigEntryNotReady:
        await api_client.close()
        raise


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:  # noqa: ARG001
    """Set up the Unraid component and register dashboard frontend."""
    await async_register_frontend(hass)
    return True


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

    # Entities and the server device key off the config entry's identity, so
    # servers sharing a placeholder SMBIOS UUID stay distinct at runtime (#351).
    server_info["uuid"] = _resolve_server_identity(info.uuid, entry.unique_id)
    _async_migrate_registry_identity(hass, entry, info.uuid, server_info["uuid"])

    (
        system_coordinator,
        storage_coordinator,
        infra_coordinator,
    ) = _create_coordinators(
        hass,
        api_client,
        server_name,
        entry,
        info,
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
        storage_coordinator=storage_coordinator,
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

    # Register cleanup listeners on each coordinator so stale entities are
    # pruned automatically after every successful refresh cycle.  The cleanup
    # runs on both the system and storage coordinators so that a refresh of
    # either one triggers the check (important because containers live in the
    # system coordinator and disks/shares in the storage coordinator).
    server_uuid: str = entry.runtime_data.server_info["uuid"]

    def _run_cleanup(_: object = None) -> None:
        async_cleanup_stale_entities(
            hass,
            entry.entry_id,
            server_uuid,
            system_coordinator,
            storage_coordinator,
        )

    entry.async_on_unload(system_coordinator.async_add_listener(_run_cleanup))
    entry.async_on_unload(storage_coordinator.async_add_listener(_run_cleanup))

    # Run an initial cleanup pass now that platforms have been set up and the
    # entity registry contains whatever was persisted from the last run.
    _run_cleanup()

    _LOGGER.info(
        "Unraid integration setup complete for %s",
        server_name,
    )

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """
    Return whether a device can be removed from the UI.

    Returning ``True`` enables the *Delete* button in the device UI so that
    users can manually clean up orphaned devices.  The main Unraid server
    device (identified by its UUID) cannot be removed this way because it
    is the parent device for all integration entities and would be
    re-created on the next coordinator refresh.
    """
    server_uuid = entry.runtime_data.server_info.get("uuid", "unknown")
    return (DOMAIN, server_uuid) not in device_entry.identifiers


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
