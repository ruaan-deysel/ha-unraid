---
applyTo: "custom_components/unraid/strings.json,custom_components/unraid/translations/**/*.json"
---

# Translation Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Source of Truth

`strings.json` is the **single source of truth** for English text. `translations/en.json` is generated from it.

## Structure

```json
{
  "config": {
    "step": {
      "user": {
        "title": "...",
        "description": "...",
        "data": { "host": "Host", "api_key": "API Key", ... }
      }
    },
    "error": { "cannot_connect": "...", "invalid_auth": "..." },
    "abort": { "already_configured": "..." }
  },
  "options": { ... },
  "entity": {
    "sensor": {
      "cpu_usage": { "name": "CPU Usage" },
      "ram_usage": { "name": "RAM Usage" }
    },
    "binary_sensor": { ... },
    "switch": { ... },
    "button": { ... }
  },
  "exceptions": { ... }
}
```

## Rules

- Business logic first, translations later — get entity working before adding translation keys
- Entity names come from `entity.{platform}.{translation_key}.name`
- Exception messages from `exceptions.{key}.message` with `{placeholder}` support
- Never manually edit non-English translation files — they are managed by translators
- Keep translation values concise and user-friendly
- Use placeholders `{name}`, `{error}`, `{host}` for dynamic content
