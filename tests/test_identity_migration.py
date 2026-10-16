"""Tests for server identity resolution and registry migration (#351)."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unraid import (
    _async_migrate_registry_identity,
    _resolve_server_identity,
)
from custom_components.unraid.const import DEFAULT_PORT, DOMAIN, is_placeholder_uuid

from .conftest import create_mock_unraid_client, make_server_info, make_storage_data

PLACEHOLDER = "03000200-0400-0500-0006-000700080009"
MARS = f"{PLACEHOLDER}_mars"
SATURN = f"{PLACEHOLDER}_saturn"


def _make_entry(unique_id: str | None, host: str = "192.168.1.100") -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title=host,
        data={
            CONF_HOST: host,
            CONF_API_KEY: "test-api-key",
            CONF_PORT: DEFAULT_PORT,
            CONF_SSL: True,
        },
        unique_id=unique_id,
    )


# =============================================================================
# is_placeholder_uuid / _resolve_server_identity
# =============================================================================


@pytest.mark.parametrize(
    ("uuid", "expected"),
    [
        (PLACEHOLDER, True),
        (PLACEHOLDER.upper(), True),
        ("c3a7e1c0-1234-5678-9abc-def012345678", False),
        ("", False),
        (None, False),
    ],
)
def test_is_placeholder_uuid(uuid: str | None, expected: bool) -> None:
    """Placeholder detection is case-insensitive and safe for falsy input."""
    assert is_placeholder_uuid(uuid) is expected


@pytest.mark.parametrize(
    ("api_uuid", "entry_unique_id", "expected"),
    [
        # Real UUID: always the raw API value.
        ("real-uuid", "real-uuid", "real-uuid"),
        ("real-uuid", "real-uuid_tower", "real-uuid"),
        # Placeholder with hostname-qualified unique ID: composite identity.
        (PLACEHOLDER, MARS, MARS),
        # Casing differs between API and stored unique ID.
        (PLACEHOLDER.upper(), MARS, MARS),
        (PLACEHOLDER, f"{PLACEHOLDER.upper()}_mars", f"{PLACEHOLDER.upper()}_mars"),
        # Pre-#183 entry whose unique ID is the raw placeholder.
        (PLACEHOLDER, PLACEHOLDER, PLACEHOLDER),
        # Legacy entry without unique ID.
        (PLACEHOLDER, None, PLACEHOLDER),
        # Host-fallback entry (unique ID is the host, not UUID-derived).
        (PLACEHOLDER, "192.168.1.100", PLACEHOLDER),
        # Falsy API UUID is passed through untouched (no host fallback here).
        (None, MARS, None),
        ("", MARS, ""),
    ],
)
def test_resolve_server_identity(
    api_uuid: str | None, entry_unique_id: str | None, expected: str | None
) -> None:
    """Only placeholder servers with a derived unique ID use the composite."""
    assert _resolve_server_identity(api_uuid, entry_unique_id) == expected


# =============================================================================
# Registry migration
# =============================================================================


@pytest.fixture
def mars_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Config entry for a placeholder server with a composite unique ID."""
    entry = _make_entry(MARS, host="mars.local")
    entry.add_to_hass(hass)
    return entry


def _seed_registries(
    hass: HomeAssistant, entry: MockConfigEntry
) -> tuple[dr.DeviceEntry, er.RegistryEntry, er.RegistryEntry]:
    """Populate the registries as a pre-fix installation would have."""
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, PLACEHOLDER)},
        name="Mars",
    )
    cpu = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{PLACEHOLDER}_cpu_usage",
        config_entry=entry,
        device_id=device.id,
        suggested_object_id="mars_cpu_usage",
    )
    cpu = ent_reg.async_update_entity(
        cpu.entity_id, name="Custom CPU", new_entity_id="sensor.my_mars_cpu"
    )
    switch = ent_reg.async_get_or_create(
        "switch",
        DOMAIN,
        f"{PLACEHOLDER}_container_switch_plex",
        config_entry=entry,
        device_id=device.id,
    )
    return device, cpu, switch


async def test_migration_rekeys_entities_and_device(
    hass: HomeAssistant, mars_entry: MockConfigEntry
) -> None:
    """Unique IDs and the device identifier move to the composite identity."""
    device, cpu, switch = _seed_registries(hass, mars_entry)
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    _async_migrate_registry_identity(hass, mars_entry, PLACEHOLDER, MARS)

    migrated_cpu = ent_reg.async_get("sensor.my_mars_cpu")
    assert migrated_cpu is not None
    assert migrated_cpu.unique_id == f"{MARS}_cpu_usage"
    assert migrated_cpu.name == "Custom CPU"
    assert migrated_cpu.device_id == device.id
    assert migrated_cpu.id == cpu.id

    migrated_switch = ent_reg.async_get(switch.entity_id)
    assert migrated_switch is not None
    assert migrated_switch.unique_id == f"{MARS}_container_switch_plex"

    migrated_device = dev_reg.async_get(device.id)
    assert migrated_device is not None
    assert migrated_device.identifiers == {(DOMAIN, MARS)}
    assert (
        dev_reg.async_get_device_by_identifier(
            (DOMAIN, PLACEHOLDER), mars_entry.entry_id
        )
        is None
    )


async def test_migration_is_idempotent(
    hass: HomeAssistant, mars_entry: MockConfigEntry
) -> None:
    """A second run leaves already-migrated records untouched."""
    _seed_registries(hass, mars_entry)
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    _async_migrate_registry_identity(hass, mars_entry, PLACEHOLDER, MARS)
    first = {
        e.entity_id: (e.unique_id, e.device_id, e.modified_at)
        for e in er.async_entries_for_config_entry(ent_reg, mars_entry.entry_id)
    }
    first_devices = {
        d.id: (d.identifiers, d.modified_at)
        for d in dr.async_entries_for_config_entry(dev_reg, mars_entry.entry_id)
    }

    with (
        patch.object(ent_reg, "async_update_entity") as update_entity,
        patch.object(dev_reg, "async_update_device") as update_device,
    ):
        _async_migrate_registry_identity(hass, mars_entry, PLACEHOLDER, MARS)

    update_entity.assert_not_called()
    update_device.assert_not_called()
    assert {
        e.entity_id: (e.unique_id, e.device_id, e.modified_at)
        for e in er.async_entries_for_config_entry(ent_reg, mars_entry.entry_id)
    } == first
    assert {
        d.id: (d.identifiers, d.modified_at)
        for d in dr.async_entries_for_config_entry(dev_reg, mars_entry.entry_id)
    } == first_devices


async def test_migration_ignores_other_entries_and_other_prefixes(
    hass: HomeAssistant, mars_entry: MockConfigEntry
) -> None:
    """Records owned by another entry or with another prefix are not touched."""
    other = _make_entry("real-uuid", host="tower.local")
    other.add_to_hass(hass)
    ent_reg = er.async_get(hass)
    foreign = ent_reg.async_get_or_create(
        "sensor", DOMAIN, f"{PLACEHOLDER}_cpu_usage", config_entry=other
    )
    real = ent_reg.async_get_or_create(
        "sensor", DOMAIN, "real-uuid_cpu_usage", config_entry=mars_entry
    )
    composite = ent_reg.async_get_or_create(
        "sensor", DOMAIN, f"{MARS}_ram_usage", config_entry=mars_entry
    )

    _async_migrate_registry_identity(hass, mars_entry, PLACEHOLDER, MARS)

    assert ent_reg.async_get(foreign.entity_id).unique_id == f"{PLACEHOLDER}_cpu_usage"
    assert ent_reg.async_get(real.entity_id).unique_id == "real-uuid_cpu_usage"
    assert ent_reg.async_get(composite.entity_id).unique_id == f"{MARS}_ram_usage"


async def test_migration_handles_hostname_matching_resource_prefix(
    hass: HomeAssistant,
) -> None:
    """A hostname equal to a resource-ID token still migrates legacy records."""
    resolved = f"{PLACEHOLDER}_disk"
    entry = _make_entry(resolved, host="disk.local")
    entry.add_to_hass(hass)
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    legacy_device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, PLACEHOLDER)}
    )
    # Pre-fix record: raw prefix + "disk_sda_temp" looks like resolved prefix
    # + "sda_temp", but it hangs off the raw-keyed device.
    legacy = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{PLACEHOLDER}_disk_sda_temp",
        config_entry=entry,
        device_id=legacy_device.id,
    )
    # Record created under the resolved identity (workaround user) on a
    # device already keyed on the resolved identity: must not be touched.
    resolved_device = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, resolved)}
    )
    current = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{resolved}_cpu_usage",
        config_entry=entry,
        device_id=resolved_device.id,
    )
    # Record without a device falls back to the prefix rule.
    orphan_raw = ent_reg.async_get_or_create(
        "sensor", DOMAIN, f"{PLACEHOLDER}_ram_usage", config_entry=entry
    )

    _async_migrate_registry_identity(hass, entry, PLACEHOLDER, resolved)

    assert ent_reg.async_get(legacy.entity_id).unique_id == f"{resolved}_disk_sda_temp"
    assert ent_reg.async_get(current.entity_id).unique_id == f"{resolved}_cpu_usage"
    assert ent_reg.async_get(orphan_raw.entity_id).unique_id == f"{resolved}_ram_usage"
    # The resolved identifier is already taken by the workaround device, so
    # the legacy device is skipped (conflict) rather than merged or removed.
    assert dev_reg.async_get(legacy_device.id).identifiers == {(DOMAIN, PLACEHOLDER)}
    assert dev_reg.async_get(resolved_device.id).identifiers == {(DOMAIN, resolved)}


async def test_migration_skips_entity_conflict_with_warning(
    hass: HomeAssistant,
    mars_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A record whose target unique ID already exists is skipped, not deleted."""
    ent_reg = er.async_get(hass)
    legacy = ent_reg.async_get_or_create(
        "sensor", DOMAIN, f"{PLACEHOLDER}_cpu_usage", config_entry=mars_entry
    )
    workaround = ent_reg.async_get_or_create(
        "sensor", DOMAIN, f"{MARS}_cpu_usage", config_entry=mars_entry
    )

    with caplog.at_level(logging.WARNING):
        _async_migrate_registry_identity(hass, mars_entry, PLACEHOLDER, MARS)

    assert ent_reg.async_get(legacy.entity_id).unique_id == f"{PLACEHOLDER}_cpu_usage"
    assert ent_reg.async_get(workaround.entity_id).unique_id == f"{MARS}_cpu_usage"
    assert "Cannot migrate" in caplog.text
    assert legacy.entity_id in caplog.text
    assert workaround.entity_id in caplog.text


async def test_migration_handles_registry_value_error(
    hass: HomeAssistant,
    mars_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A ValueError from the registry is logged and does not abort setup."""
    ent_reg = er.async_get(hass)
    legacy = ent_reg.async_get_or_create(
        "sensor", DOMAIN, f"{PLACEHOLDER}_cpu_usage", config_entry=mars_entry
    )

    with (
        patch.object(ent_reg, "async_update_entity", side_effect=ValueError("boom")),
        caplog.at_level(logging.WARNING),
    ):
        _async_migrate_registry_identity(hass, mars_entry, PLACEHOLDER, MARS)

    assert ent_reg.async_get(legacy.entity_id).unique_id == f"{PLACEHOLDER}_cpu_usage"
    assert "boom" in caplog.text


async def test_migration_skips_device_conflict_with_warning(
    hass: HomeAssistant,
    mars_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A different device already keyed on the composite identity is left alone."""
    dev_reg = dr.async_get(hass)
    legacy = dev_reg.async_get_or_create(
        config_entry_id=mars_entry.entry_id, identifiers={(DOMAIN, PLACEHOLDER)}
    )
    workaround = dev_reg.async_get_or_create(
        config_entry_id=mars_entry.entry_id, identifiers={(DOMAIN, MARS)}
    )

    with caplog.at_level(logging.WARNING):
        _async_migrate_registry_identity(hass, mars_entry, PLACEHOLDER, MARS)

    assert dev_reg.async_get(legacy.id).identifiers == {(DOMAIN, PLACEHOLDER)}
    assert dev_reg.async_get(workaround.id).identifiers == {(DOMAIN, MARS)}
    assert "Cannot migrate device" in caplog.text


async def test_migration_rekeys_device_already_carrying_resolved_identifier(
    hass: HomeAssistant,
    mars_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A device holding both identifiers is re-keyed without a conflict warning."""
    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=mars_entry.entry_id,
        identifiers={(DOMAIN, PLACEHOLDER), (DOMAIN, MARS), ("other", "x")},
    )

    with caplog.at_level(logging.WARNING):
        _async_migrate_registry_identity(hass, mars_entry, PLACEHOLDER, MARS)

    assert dev_reg.async_get(device.id).identifiers == {(DOMAIN, MARS), ("other", "x")}
    assert "Cannot migrate device" not in caplog.text


async def test_migration_rekeys_each_servers_own_device(
    hass: HomeAssistant, mars_entry: MockConfigEntry
) -> None:
    """Two entries that each own a raw-keyed device both get re-keyed."""
    saturn_entry = _make_entry(SATURN, host="saturn.local")
    saturn_entry.add_to_hass(hass)
    dev_reg = dr.async_get(hass)
    mars_device = dev_reg.async_get_or_create(
        config_entry_id=mars_entry.entry_id, identifiers={(DOMAIN, PLACEHOLDER)}
    )
    saturn_device = dev_reg.async_get_or_create(
        config_entry_id=saturn_entry.entry_id, identifiers={(DOMAIN, PLACEHOLDER)}
    )
    assert mars_device.id != saturn_device.id

    _async_migrate_registry_identity(hass, mars_entry, PLACEHOLDER, MARS)
    _async_migrate_registry_identity(hass, saturn_entry, PLACEHOLDER, SATURN)

    assert dev_reg.async_get(mars_device.id).identifiers == {(DOMAIN, MARS)}
    assert dev_reg.async_get(saturn_device.id).identifiers == {(DOMAIN, SATURN)}
    assert (
        dev_reg.async_get_device_by_identifier(
            (DOMAIN, PLACEHOLDER), mars_entry.entry_id
        )
        is None
    )


@pytest.mark.parametrize(
    ("raw", "resolved"),
    [
        ("real-uuid", "real-uuid"),
        (None, MARS),
        (PLACEHOLDER, None),
    ],
)
async def test_migration_noop_when_identity_unchanged(
    hass: HomeAssistant,
    mars_entry: MockConfigEntry,
    raw: str | None,
    resolved: str | None,
) -> None:
    """No registry access happens when there is nothing to migrate."""
    with (
        patch("custom_components.unraid.er.async_get") as ent_get,
        patch("custom_components.unraid.dr.async_get") as dev_get,
    ):
        _async_migrate_registry_identity(hass, mars_entry, raw, resolved)

    ent_get.assert_not_called()
    dev_get.assert_not_called()


# =============================================================================
# End-to-end: two servers sharing a placeholder UUID
# =============================================================================


def _coordinator_client(hostname: str) -> MagicMock:
    """Mock client with every method the three coordinators await."""
    client = create_mock_unraid_client(
        server_info=make_server_info(uuid=PLACEHOLDER, hostname=hostname)
    )
    client.typed_get_containers_safe = AsyncMock(return_value=[])
    client.get_network_metrics = AsyncMock(return_value=[])
    client.typed_get_vms = AsyncMock(return_value=[])
    client.typed_get_ups_devices = AsyncMock(return_value=[])
    client.typed_get_array = AsyncMock(return_value=make_storage_data().array)
    client.typed_get_shares = AsyncMock(return_value=[])
    client.get_parity_history = AsyncMock(return_value=[])
    client.typed_get_notifications = AsyncMock(return_value=[])
    return client


async def test_two_placeholder_servers_coexist(
    hass: HomeAssistant,
    mock_unraid_client_factory: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Both servers get a full, distinct set of entities and their own device."""
    mars_entry = _make_entry(MARS, host="mars.local")
    saturn_entry = _make_entry(SATURN, host="saturn.local")
    mars_entry.add_to_hass(hass)
    saturn_entry.add_to_hass(hass)

    clients = {
        "mars.local": _coordinator_client("mars"),
        "saturn.local": _coordinator_client("saturn"),
    }
    mock_unraid_client_factory.side_effect = lambda **kwargs: clients[kwargs["host"]]

    websocket_manager = MagicMock()
    websocket_manager.async_start = AsyncMock()
    websocket_manager.async_stop = AsyncMock()

    with (
        patch("custom_components.unraid.async_register_frontend"),
        patch(
            "custom_components.unraid.UnraidWebSocketManager",
            return_value=websocket_manager,
        ),
        caplog.at_level(logging.ERROR),
    ):
        # Setting up the first entry loads the integration, which sets up
        # every entry for the domain.
        assert await hass.config_entries.async_setup(mars_entry.entry_id)
        await hass.async_block_till_done()

    assert mars_entry.state is ConfigEntryState.LOADED
    assert saturn_entry.state is ConfigEntryState.LOADED

    assert mars_entry.runtime_data.server_info["uuid"] == MARS
    assert saturn_entry.runtime_data.server_info["uuid"] == SATURN
    assert "does not generate unique IDs" not in caplog.text

    ent_reg = er.async_get(hass)
    mars_entities = er.async_entries_for_config_entry(ent_reg, mars_entry.entry_id)
    saturn_entities = er.async_entries_for_config_entry(ent_reg, saturn_entry.entry_id)
    assert mars_entities
    assert all(e.unique_id.startswith(f"{MARS}_") for e in mars_entities)
    assert all(e.unique_id.startswith(f"{SATURN}_") for e in saturn_entities)
    assert {e.unique_id[len(MARS) :] for e in mars_entities} == {
        e.unique_id[len(SATURN) :] for e in saturn_entities
    }
    all_unique_ids = [e.unique_id for e in mars_entities + saturn_entities]
    assert len(all_unique_ids) == len(set(all_unique_ids))

    dev_reg = dr.async_get(hass)
    mars_device = dev_reg.async_get_device_by_identifier(
        (DOMAIN, MARS), mars_entry.entry_id
    )
    saturn_device = dev_reg.async_get_device_by_identifier(
        (DOMAIN, SATURN), saturn_entry.entry_id
    )
    assert mars_device is not None
    assert saturn_device is not None
    assert mars_device.id != saturn_device.id
    for entry in (mars_entry, saturn_entry):
        assert (
            dev_reg.async_get_device_by_identifier(
                (DOMAIN, PLACEHOLDER), entry.entry_id
            )
            is None
        )
