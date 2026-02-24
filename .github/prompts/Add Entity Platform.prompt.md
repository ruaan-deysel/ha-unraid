---
description: Add a new entity platform to the Unraid integration
---

# Add Entity Platform

Add a new entity platform (e.g., `number`, `select`, `climate`) to the ha-unraid integration.

## Context

Read these files before starting:
- `AGENTS.md` — Full project documentation
- `custom_components/unraid/__init__.py` — Platform registration in `PLATFORMS` list
- `custom_components/unraid/entity.py` — Base entity classes
- `custom_components/unraid/sensor.py` — Reference implementation for platform setup

## Steps

1. **Add platform to `PLATFORMS`** in `__init__.py`:
   ```python
   PLATFORMS: list[Platform] = [
       Platform.SENSOR,
       Platform.BINARY_SENSOR,
       Platform.SWITCH,
       Platform.BUTTON,
       Platform.NEW_PLATFORM,  # Add here
   ]
   ```

2. **Create the platform file** (e.g., `custom_components/unraid/number.py`):
   - Import `AddEntitiesCallback` from `homeassistant.helpers.entity_platform`
   - Import `UnraidConfigEntry` from `.__init__`
   - Define `PARALLEL_UPDATES` (0 for read-only, 1 for write)
   - Implement `async_setup_entry(hass, entry, async_add_entities)`
   - Create entity classes extending `UnraidBaseEntity` and the platform entity

3. **Add translations** to `strings.json` under `entity.{platform}.{key}.name`

4. **Add icons** to `icons.json` under `entity.{platform}.{key}`

5. **Create tests** in `tests/test_{platform}.py`

## Important

- Ask the maintainer before adding new platforms — this is an architectural decision
- Follow the entity hierarchy: `PlatformEntity, UnraidBaseEntity`
- Use `_attr_translation_key` for names, never hardcode
- Set `_attr_entity_category` appropriately
