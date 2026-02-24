---
applyTo: "custom_components/unraid/services.yaml"
---

# services.yaml Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) and [`service_actions.instructions.md`](service_actions.instructions.md).

## Status

The integration currently has no `services.yaml` — all controls use entity platforms (switches, buttons). This file would only be created if custom service actions are added.

## Format

```yaml
service_name:
  name: Human readable name
  description: Description of the service action
  target:
    entity:
      integration: unraid
  fields:
    field_name:
      name: Field name
      description: Field description
      required: true
      example: "example value"
      selector:
        text:
```

## Rules

- Every service field needs a `selector` for the UI
- Add corresponding translations in `strings.json` under `services.{service_name}`
- Target should specify `integration: unraid` for entity-targeted services
- Keep service names in snake_case matching the domain convention
