---
applyTo: "**/configuration.yaml"
---

# configuration.yaml Guidelines — ha-unraid

Refer to `AGENTS.md` for full project documentation.

## Integration Setup Model

Unraid is **UI-configured only** (`config_flow: true`).

- Do not add a `unraid:` YAML integration block.
- Use YAML only for HA-wide features (logger, automations, scripts, templates).

## Preferred YAML Patterns

- Use modern action syntax (`action:`), not deprecated `service:` in examples.
- Keep examples minimal and production-safe.
- Use two-space indentation.

## Debug Logging Snippet

```yaml
logger:
  default: info
  logs:
    custom_components.unraid: debug
    unraid_api: debug
```

## Polling Reminder

Polling intervals are fixed by integration design. For ad-hoc refreshes, use
`homeassistant.update_entity` in automations instead of adding YAML polling
options.
