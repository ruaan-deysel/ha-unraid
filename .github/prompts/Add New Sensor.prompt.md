---
description: Add a new sensor entity to the Unraid integration
---

# Add New Sensor

Add a new sensor entity to the ha-unraid integration.

## Context

Read these files before starting:
- `AGENTS.md` — Full project documentation
- `custom_components/unraid/sensor.py` — Existing sensor patterns
- `custom_components/unraid/entity.py` — Base entity classes
- `custom_components/unraid/coordinator.py` — Data classes and coordinator types
- `custom_components/unraid/strings.json` — Translation keys
- `custom_components/unraid/icons.json` — Icon definitions

## Requirements

1. **Identify the data source**: Which coordinator provides the data? (`UnraidSystemCoordinator`, `UnraidStorageCoordinator`, or `UnraidInfraCoordinator`)
2. **Choose the base class**: Use `UnraidSensorEntity(UnraidBaseEntity, SensorEntity)` for most sensors
3. **Set required attributes**:
   - `_attr_translation_key` — Unique key for translations
   - `_attr_device_class` — HA sensor device class if applicable
   - `_attr_native_unit_of_measurement` — Unit string
   - `_attr_state_class` — Usually `SensorStateClass.MEASUREMENT`
   - `_attr_entity_category` — `EntityCategory.DIAGNOSTIC` if diagnostic
   - `_attr_entity_registry_enabled_default` — `False` if disabled by default
4. **Implement `native_value` property** — Access data from `self.coordinator.data`
5. **Handle `None`** — Return `None` if coordinator data is unavailable

## Checklist

- [ ] Sensor class created in `sensor.py` following existing patterns
- [ ] Constructor calls `super().__init__()` with correct parameters
- [ ] Entity instantiated in `async_setup_entry()` function
- [ ] Translation key added to `strings.json` under `entity.sensor.{key}.name`
- [ ] Icon added to `icons.json` under `entity.sensor.{key}.default`
- [ ] Constant added to `const.py` if needed
- [ ] `./scripts/lint` passes
- [ ] Test added to `tests/test_sensor.py`
