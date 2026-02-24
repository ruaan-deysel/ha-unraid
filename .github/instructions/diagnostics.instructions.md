---
applyTo: "custom_components/unraid/diagnostics.py"
---

# Diagnostics Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Purpose

The `diagnostics.py` file provides debug data export via HA's diagnostics framework.
Users access it at: Settings > Devices & Services > Unraid > (...) > Download diagnostics.

## Required Function

```python
async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: UnraidConfigEntry,
) -> dict[str, Any]:
```

## Security Rules

- **Never expose**: API keys, passwords, tokens, or full IP addresses
- **Safe to include**: UUID, hostname, manufacturer, model, sw_version, api_version, license_type
- **Redact**: Any field that could identify the user's network (use `async_redact_data` if needed)
- Access runtime data via `entry.runtime_data` (typed as `UnraidRuntimeData`)

## Data to Include

- Config entry metadata (entry_id, title, version)
- Server info (sanitized subset)
- Coordinator health (last_update_success, timestamps)
- Optionally: entity counts, platform states, error summaries

## Pattern

```python
runtime_data = entry.runtime_data
server_info = runtime_data.server_info if runtime_data else {}

return {
    "entry_id": entry.entry_id,
    "entry_title": entry.title,
    "entry_version": entry.version,
    "server_info": {
        "uuid": server_info.get("uuid") if server_info else None,
        "hostname": server_info.get("name") if server_info else None,
        # ... safe fields only
    },
    "system_coordinator": {
        "last_update_success": (
            runtime_data.system_coordinator.last_update_success
            if runtime_data and runtime_data.system_coordinator
            else None
        ),
    },
}
```
