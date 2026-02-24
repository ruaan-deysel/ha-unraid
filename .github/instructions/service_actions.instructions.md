---
applyTo: "custom_components/unraid/services.yaml,custom_components/unraid/services.py"
---

# Service Actions Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Current Status

The integration does **not** currently register custom service actions. All controls are implemented via entity platforms (switches, buttons).

## If Adding Service Actions

Follow the HA pattern:

1. Define services in `services.yaml` with fields and translations
2. Register handlers in `__init__.py` via `async_setup_entry`
3. Use `hass.services.async_register(DOMAIN, service_name, handler, schema)`
4. Validate inputs with `vol.Schema`

### services.yaml Structure

```yaml
service_name:
  name: Human Readable Name
  description: What this service does
  fields:
    field_name:
      name: Field Name
      description: What this field does
      required: true
      selector:
        text:
```

### Handler Pattern

```python
async def async_handle_service(call: ServiceCall) -> None:
    """Handle a service call."""
    entry_id = call.data.get("entry_id")
    entry = hass.config_entries.async_get_entry(entry_id)
    runtime_data = entry.runtime_data
    # ... perform action via runtime_data.api_client
```

### Rules

- Service actions must raise exceptions on failure (Silver quality scale)
- Use translated error messages
- Register in `async_setup_entry`, unregister in `async_unload_entry`
- Prefer entity-based controls over service actions when possible
