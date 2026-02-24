---
description: Add a new service action to the Unraid integration
---

# Add Service Action

Add a new custom service action to the ha-unraid integration.

## Context

Read these files before starting:
- `AGENTS.md` — Full project documentation
- `custom_components/unraid/__init__.py` — Service registration location
- `custom_components/unraid/const.py` — Constants
- `custom_components/unraid/strings.json` — Translations

## Decision: Service vs Entity

Before adding a service action, consider whether an entity-based control (switch/button) would be more appropriate:

- **Use a button entity** if: It's a one-shot action (start, stop, restart)
- **Use a switch entity** if: It toggles a state (on/off)
- **Use a service action** if: It takes parameters, targets multiple entities, or doesn't map to a single entity

## Steps

1. **Create `services.yaml`** (if it doesn't exist):
   ```yaml
   my_action:
     name: My Action
     description: What this action does
     fields:
       parameter:
         name: Parameter
         description: What this parameter controls
         required: true
         selector:
           text:
   ```

2. **Register the service** in `async_setup_entry()`:
   ```python
   import voluptuous as vol
   from homeassistant.helpers import config_validation as cv

   MY_ACTION_SCHEMA = vol.Schema({
       vol.Required("parameter"): cv.string,
   })

   async def async_handle_my_action(call: ServiceCall) -> None:
       # Implementation — inputs already validated by the framework
       pass

   hass.services.async_register(DOMAIN, "my_action", async_handle_my_action, schema=MY_ACTION_SCHEMA)
   ```

3. **Unregister** in `async_unload_entry()`:
   ```python
   hass.services.async_remove(DOMAIN, "my_action")
   ```

4. **Add translations** in `strings.json` under `services.my_action`

5. **Update `quality_scale.yaml`** — `action-setup` and `action-exceptions` rules

## Rules

- Service handlers must raise exceptions on failure (HA Silver quality scale)
- Use `HomeAssistantError` with translations for user-facing errors
- Validate all inputs with `vol.Schema`
