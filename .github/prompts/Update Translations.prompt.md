---
description: Update translation strings for the Unraid integration
---

# Update Translations

Add or modify translation strings in the ha-unraid integration.

## Context

Read these files:
- `custom_components/unraid/strings.json` — Source of truth for English text
- `custom_components/unraid/icons.json` — Icon definitions (often updated alongside)
- `custom_components/unraid/translations/en.json` — Generated from strings.json

## Translation Structure

```json
{
  "config": {
    "step": { "step_id": { "title": "", "description": "", "data": {}, "data_description": {} } },
    "error": { "error_id": "Error message" },
    "abort": { "abort_reason": "Abort message" }
  },
  "options": {
    "step": { "init": { "data": {}, "data_description": {} } }
  },
  "entity": {
    "platform": { "translation_key": { "name": "Entity Name" } }
  },
  "exceptions": {
    "exception_key": { "message": "Error: {placeholder}" }
  },
  "issues": {
    "issue_id": { "title": "Issue Title", "description": "Issue description" }
  }
}
```

## Steps

1. **Edit `strings.json`** — Add/modify the English translation keys
2. **Copy to `translations/en.json`** — Keep in sync (or regenerate)
3. **Update `icons.json`** if adding new entity translation keys
4. **Verify** the translation key matches `_attr_translation_key` on the entity class

## Rules

- `strings.json` is the source of truth — edit this, not `translations/en.json` directly
- Never modify non-English translation files (e.g., `translations/fr.json`)
- Use `{placeholder}` syntax for dynamic values in messages
- Keep text concise and user-friendly
- Entity names should be title case ("CPU Usage", not "cpu usage")
- Error messages should explain what went wrong and suggest a fix
