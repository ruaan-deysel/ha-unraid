"""Diagnostics support for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.redact import async_redact_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    # Use runtime_data (HA 2024.4+ pattern)
    runtime_data = entry.runtime_data
    server_info = runtime_data.server_info
    system_coordinator = runtime_data.system_coordinator
    storage_coordinator = runtime_data.storage_coordinator
    infra_coordinator = runtime_data.infra_coordinator

    # Gather entity counts from coordinator data for troubleshooting
    system_data = system_coordinator.data
    storage_data = storage_coordinator.data
    infra_data = infra_coordinator.data

    entity_counts: dict[str, int | bool] = {}
    if system_data:
        entity_counts["containers"] = len(system_data.containers)
        entity_counts["vms"] = len(system_data.vms)
        entity_counts["ups_devices"] = len(system_data.ups_devices)
    if storage_data:
        entity_counts["disks"] = len(storage_data.disks)
        entity_counts["parities"] = len(storage_data.parities)
        entity_counts["caches"] = len(storage_data.caches)
        entity_counts["shares"] = len(storage_data.shares)
        entity_counts["has_boot"] = storage_data.boot is not None
    if infra_data:
        entity_counts["plugins"] = (
            len(infra_data.installed_plugins)
            if infra_data.installed_plugins
            else 0
        )

    # Build diagnostics with redaction of sensitive identifiers
    diag_data = {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "version": entry.version,
        "server_info": {
            "uuid": server_info.get("uuid"),
            "hostname": server_info.get("name"),
            "manufacturer": server_info.get("manufacturer"),
            "model": server_info.get("model"),
            "sw_version": server_info.get("sw_version"),
            "api_version": server_info.get("api_version"),
            "license_type": server_info.get("license_type"),
        },
        "entity_counts": entity_counts,
        "system_coordinator": {
            "last_update_success": system_coordinator.last_update_success,
            "last_update_time": str(system_coordinator.last_update_success_time),
        },
        "storage_coordinator": {
            "last_update_success": storage_coordinator.last_update_success,
            "last_update_time": str(storage_coordinator.last_update_success_time),
        },
        "infra_coordinator": {
            "last_update_success": infra_coordinator.last_update_success,
            "last_update_time": str(infra_coordinator.last_update_success_time),
        },
    }

    # Redact potentially sensitive identifiers (UUID, hostname)
    # These are network identifiers that could identify the user's setup
    return async_redact_data(diag_data, {"uuid", "hostname"})
