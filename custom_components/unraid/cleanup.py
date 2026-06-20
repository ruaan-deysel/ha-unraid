"""
Stale entity and device cleanup for the Unraid integration.

After every successful coordinator refresh, this module diffs the entity
registry against the current set of live resources and removes any entities
whose backing resource no longer exists on the Unraid server.

Design principles
-----------------
* **Safe-only pruning** — only entities whose ``unique_id`` matches a known
  dynamic resource pattern are ever removed.  Static entities (e.g.
  ``cpu_usage``, ``array_state``) are never touched.
* **Transient-failure guard** — cleanup is skipped when a coordinator's last
  update failed, preventing entity loss due to a momentary API or network
  error.
* **Device cleanup** — after entity removal, any HA device that has lost all
  its entities is also removed from the device registry.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Final

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .coordinator import UnraidStorageData, UnraidSystemData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import (
        UnraidStorageCoordinator,
        UnraidSystemCoordinator,
    )

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dynamic-resource prefix detection
# ---------------------------------------------------------------------------

# Resource-id prefixes that are EXCLUSIVELY used for dynamic (per-resource)
# entities — i.e. every entity with one of these prefixes is bound to a live
# resource that may be removed.
#
# "container_switch_" and "container_restart_" are specific enough to avoid
# colliding with the static "container_updates_count" resource id.
# "disk_" covers all disk entities (disk_id_temp, disk_health_id, disk_spin_id).
# "share_" covers all share usage sensors.
# "ups_" covers all UPS sensor/binary_sensor entities.
# "temp_" covers per-hardware-temperature-sensor entities (not "temperature_average").
_DYNAMIC_RESOURCE_ID_PREFIXES: Final[tuple[str, ...]] = (
    "container_switch_",  # per-container switch
    "container_restart_",  # per-container restart button
    "container_update_",  # per-container update entity (update platform)
    "vm_switch_",  # per-VM switch
    "vm_force_stop_",  # per-VM force-stop button
    "vm_reboot_",  # per-VM reboot button
    "vm_pause_",  # per-VM pause button
    "vm_resume_",  # per-VM resume button
    "vm_reset_",  # per-VM reset button
    "disk_",  # all disk entities (all disk types and metrics)
    "share_",  # per-share usage sensor
    "ups_",  # all UPS sensor / binary_sensor entities
    "temp_",  # per-hardware-temperature-sensor entity
)

# Static resource ids that start with "container_" (and must not be cleaned up)
_STATIC_CONTAINER_RESOURCE_IDS: Final[frozenset[str]] = frozenset(
    {"container_updates_count"}
)

# Static resource ids that start with "network_" (and must not be cleaned up)
_STATIC_NETWORK_RESOURCE_IDS: Final[frozenset[str]] = frozenset({"network_access"})

# Network-interface sensors use resource_id = "network_{name}_{rx|tx}".
# This pattern distinguishes them from the static "network_access" sensor.
_NETWORK_INTERFACE_RESOURCE_ID_RE: Final = re.compile(
    r"^network_(?P<name>.+?)_(?:rx|tx)$"
)


def _is_dynamic_resource_id(resource_id: str) -> bool:
    """
    Return True if *resource_id* belongs to a dynamic (per-resource) entity.

    The check is intentionally conservative: only patterns whose prefixes
    are exclusively used for dynamic resources are matched, so no static
    entity can ever be accidentally pruned.
    """
    # Standard dynamic prefixes (single startswith check via tuple)
    if resource_id.startswith(_DYNAMIC_RESOURCE_ID_PREFIXES):
        return True

    # Per-container stats/update sensors: container_{name}_{cpu|memory|...}
    # Only those NOT in the static allow-list count as dynamic.
    if (
        resource_id.startswith("container_")
        and resource_id not in _STATIC_CONTAINER_RESOURCE_IDS
    ):
        return True

    # Network-interface throughput sensors: network_{interface}_{rx|tx}
    # Only those NOT in the static allow-list count as dynamic.
    return (
        resource_id.startswith("network_")
        and resource_id not in _STATIC_NETWORK_RESOURCE_IDS
        and bool(_NETWORK_INTERFACE_RESOURCE_ID_RE.match(resource_id))
    )


# ---------------------------------------------------------------------------
# Expected unique-id computation
# ---------------------------------------------------------------------------


def build_expected_dynamic_unique_ids(
    server_uuid: str,
    sys_data: UnraidSystemData,
    stor_data: UnraidStorageData,
) -> frozenset[str]:
    """
    Return every unique_id that *should* exist for dynamic resources.

    Args:
        server_uuid: The Unraid server UUID used as the unique_id prefix.
        sys_data:    Latest snapshot from the system coordinator.
        stor_data:   Latest snapshot from the storage coordinator.

    Returns:
        Frozenset of ``"{server_uuid}_{resource_id}"`` strings for all dynamic
        resources that are currently alive.

    """
    expected: set[str] = set()
    pfx = f"{server_uuid}_"

    # --- Docker containers ---
    for container in sys_data.containers or []:
        name = container.name.lstrip("/")
        expected.update(
            {
                f"{pfx}container_switch_{name}",
                f"{pfx}container_restart_{name}",
                f"{pfx}container_{name}_cpu",
                f"{pfx}container_{name}_memory",
                f"{pfx}container_{name}_memory_pct",
                # binary_sensor update entity
                f"{pfx}container_{name}_update",
                # update platform entity (different resource_id pattern)
                f"{pfx}container_update_{name}",
            }
        )

    # --- Virtual machines ---
    for vm in sys_data.vms or []:
        expected.update(
            {
                f"{pfx}vm_switch_{vm.name}",
                f"{pfx}vm_force_stop_{vm.name}",
                f"{pfx}vm_reboot_{vm.name}",
                f"{pfx}vm_pause_{vm.name}",
                f"{pfx}vm_resume_{vm.name}",
                f"{pfx}vm_reset_{vm.name}",
            }
        )

    # --- UPS devices ---
    for ups in sys_data.ups_devices or []:
        for suffix in (
            "battery",
            "load",
            "runtime",
            "power",
            "energy",
            "input_voltage",
            "output_voltage",
            "battery_health",
            "status",
            "connected",
        ):
            expected.add(f"{pfx}ups_{ups.id}_{suffix}")

    # --- Hardware temperature sensors ---
    # Use a conditional iterable to avoid a separate if branch (PLR0912).
    for sensor in (
        sys_data.metrics.temperature.sensors
        if (sys_data.metrics and sys_data.metrics.temperature is not None)
        else []
    ):
        expected.add(f"{pfx}temp_{sensor.id}")

    # --- Network interfaces ---
    for iface in sys_data.network_metrics or []:
        if iface.name is not None:
            expected.update(
                {
                    f"{pfx}network_{iface.name}_rx",
                    f"{pfx}network_{iface.name}_tx",
                }
            )

    # --- Array disks (data, parity, cache, and boot/flash) ---
    all_disks = list(stor_data.disks or [])
    all_disks.extend(stor_data.parities or [])
    all_disks.extend(stor_data.caches or [])
    if stor_data.boot is not None:
        all_disks.append(stor_data.boot)

    for disk in all_disks:
        if disk.id is None:
            continue
        expected.update(
            {
                f"{pfx}disk_{disk.id}_temp",
                f"{pfx}disk_{disk.id}_errors",
                f"{pfx}disk_{disk.id}_usage",
                f"{pfx}disk_health_{disk.id}",
                f"{pfx}disk_spin_{disk.id}",
            }
        )

    # --- Shares ---
    for share in stor_data.shares or []:
        if share.id is None:
            continue
        expected.add(f"{pfx}share_{share.id}_usage")

    return frozenset(expected)


# ---------------------------------------------------------------------------
# Core cleanup logic
# ---------------------------------------------------------------------------


def async_cleanup_stale_entities(
    hass: HomeAssistant,
    entry_id: str,
    server_uuid: str,
    system_coordinator: UnraidSystemCoordinator,
    storage_coordinator: UnraidStorageCoordinator,
) -> None:
    """
    Remove orphaned entities and empty devices for a config entry.

    Should be called after every successful coordinator refresh. The function
    is synchronous (``async_`` prefix follows HA convention for callbacks that
    run inside the event loop but do not need to be awaited).

    Args:
        hass:                 Home Assistant instance.
        entry_id:             Config entry ID to inspect.
        server_uuid:          Unraid server UUID (unique_id prefix).
        system_coordinator:   System data coordinator.
        storage_coordinator:  Storage data coordinator.

    """
    # Guard: skip if either coordinator's last update failed (transient errors
    # must never cause entity loss).
    if not system_coordinator.last_update_success:
        _LOGGER.debug(
            "Cleanup skipped for entry %s: system coordinator last update failed",
            entry_id,
        )
        return
    if not storage_coordinator.last_update_success:
        _LOGGER.debug(
            "Cleanup skipped for entry %s: storage coordinator last update failed",
            entry_id,
        )
        return

    sys_data = system_coordinator.data
    stor_data = storage_coordinator.data

    if not isinstance(sys_data, UnraidSystemData):
        _LOGGER.debug(
            "Cleanup skipped for entry %s: system coordinator data not ready",
            entry_id,
        )
        return
    if not isinstance(stor_data, UnraidStorageData):
        _LOGGER.debug(
            "Cleanup skipped for entry %s: storage coordinator data not ready",
            entry_id,
        )
        return

    # Build the complete set of unique_ids that should exist right now.
    expected = build_expected_dynamic_unique_ids(server_uuid, sys_data, stor_data)

    # Collect registered entities for this config entry.
    ent_reg = er.async_get(hass)
    registered = er.async_entries_for_config_entry(ent_reg, entry_id)

    server_uuid_prefix = f"{server_uuid}_"
    orphans: list[er.RegistryEntry] = []

    for entity_entry in registered:
        uid = entity_entry.unique_id
        if not uid.startswith(server_uuid_prefix):
            # Entity belongs to a different server (multi-instance setups).
            continue

        resource_id = uid[len(server_uuid_prefix) :]

        if not _is_dynamic_resource_id(resource_id):
            # Static entity — never prune.
            continue

        if uid not in expected:
            orphans.append(entity_entry)

    if not orphans:
        return

    _LOGGER.info(
        "Removing %d stale %s for entry %s",
        len(orphans),
        "entity" if len(orphans) == 1 else "entities",
        entry_id,
    )
    for entity_entry in orphans:
        _LOGGER.debug(
            "Removing stale entity %s (unique_id=%s)",
            entity_entry.entity_id,
            entity_entry.unique_id,
        )
        ent_reg.async_remove(entity_entry.entity_id)

    # Remove any devices that are now empty after entity removal.
    _async_remove_orphaned_devices(hass, entry_id)


def _async_remove_orphaned_devices(hass: HomeAssistant, entry_id: str) -> None:
    """Remove devices that have no entities remaining for *entry_id*."""
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    devices_for_entry = dr.async_entries_for_config_entry(dev_reg, entry_id)
    for device_entry in devices_for_entry:
        remaining = er.async_entries_for_device(
            ent_reg, device_entry.id, include_disabled_entities=True
        )
        if not remaining:
            _LOGGER.debug(
                "Removing empty device %s (%s)",
                device_entry.name,
                device_entry.id,
            )
            dev_reg.async_remove_device(device_entry.id)
