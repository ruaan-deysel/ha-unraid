---
description: Add a new entity to the Unraid server device
---

# Add Entity to Device

Add a new entity to the Unraid server device in this Home Assistant integration.

If not provided, ask for:

- Entity type (sensor, binary_sensor, switch, button)
- Entity name and purpose
- Data source (which coordinator: system, storage, or infra)

## Requirements

**Entity Implementation:**

- Create entity class in the appropriate platform file (`sensor.py`, `binary_sensor.py`, `switch.py`, `button.py`)
- Inherit from both the HA platform entity and `UnraidBaseEntity` (e.g., `SensorEntity, UnraidBaseEntity`)
- Set `_attr_translation_key` for translated names
- Access data from `self.coordinator.data` (typed as coordinator data class)

**Device Grouping:**

- All Unraid entities share a single device per server
- Device is identified by `(DOMAIN, server_uuid)` in `DeviceInfo.identifiers`
- `UnraidBaseEntity.__init__` handles DeviceInfo construction automatically
- Pass `server_uuid`, `server_name`, and `server_info` dict to base constructor

**Coordinator Data:**

- Entity must read from `self.coordinator.data` — never fetch data directly
- Handle `None` data gracefully (coordinator may not have data yet)
- Use typed data access: `data: UnraidSystemData | None = self.coordinator.data`
- For per-resource entities (disks, containers), implement a `_get_resource()` helper

**Translations & Icons:**

- Add entity name to `strings.json` under `entity.{platform}.{translation_key}.name`
- Add icon to `icons.json` under `entity.{platform}.{translation_key}.default`
- Use `_attr_translation_placeholders` for dynamic name parts (e.g., disk name)

**Registration:**

- Add entity instantiation in the platform's `async_setup_entry()` function
- Follow existing patterns for how entities are created and added

**Verification:**

- Run `./scripts/lint` to verify code quality
- Add test in `tests/test_{platform}.py`
- Verify entity unique_id follows `{server_uuid}_{resource_id}` format

**Related Files:**

- Entity base: `custom_components/unraid/entity.py`
- Constants: `custom_components/unraid/const.py`
- Coordinators: `custom_components/unraid/coordinator.py`
- Translations: `custom_components/unraid/strings.json`
- Icons: `custom_components/unraid/icons.json`
- Reference: `AGENTS.md`
