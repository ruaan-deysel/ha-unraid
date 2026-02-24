---
applyTo: "custom_components/unraid/icons.json"
---

# JSON Data Files Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## icons.json

Defines Material Design Icons (mdi) for entities, keyed by translation key.

### Structure

```json
{
  "entity": {
    "sensor": {
      "cpu_usage": { "default": "mdi:cpu-64-bit" },
      "array_state": {
        "default": "mdi:harddisk",
        "state": {
          "started": "mdi:harddisk",
          "stopped": "mdi:harddisk-remove"
        }
      }
    },
    "binary_sensor": { ... },
    "switch": { ... },
    "button": { ... }
  }
}
```

### Rules

- Every entity with `_attr_translation_key` must have a matching entry in `icons.json`
- Use `mdi:` prefix for all icons (Material Design Icons)
- Use `"state"` sub-object for state-dependent icons
- Group by platform (`sensor`, `binary_sensor`, `switch`, `button`)
- Keep icons consistent within categories (e.g., all storage icons use `mdi:harddisk` variants)

### Adding a New Entity Icon

1. Add the translation key to `strings.json` first
2. Add matching icon entry to `icons.json` under the correct platform
3. Verify the icon exists at https://pictogrammers.com/library/mdi/
