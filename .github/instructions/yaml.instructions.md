---
applyTo: "custom_components/unraid/quality_scale.yaml"
---

# YAML Configuration Files Guidelines — ha-unraid

Refer to `AGENTS.md` for full project documentation.

## quality_scale.yaml

Self-assessment against the [HA Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/).

### Structure

```yaml
rules:
  rule-name:
    status: done | todo | exempt
    comment: Explanation (required for exempt/todo)
```

### Tiers

- **Bronze** (20 rules): config flow, unique IDs, `runtime-data`, `docs-*` basics
  including `docs-actions`, `docs-conditions` and `docs-triggers` (added mid-2026),
  `entity-event-setup`.
- **Silver** (10 rules): unloading, reauth, `log-when-unavailable`,
  `parallel-updates`, `entity-unavailable`, `integration-owner`, `test-coverage`.
- **Gold** (21 rules): devices, diagnostics, discovery, translations, repairs,
  `dynamic-devices`, `stale-devices`, remaining `docs-*` rules.
- **Platinum** (3 rules): `async-dependency`, `inject-websession`, `strict-typing`.

Current rule list: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/

### Rules

- Update status when implementing new quality scale requirements
- Always include a `comment` explaining `exempt` or `todo` status
- Current target: **Platinum** level
- Every rule must be listed (shorthand `rule: done` is fine; `exempt` needs a `comment`)
- `test-coverage` must stay **>=95%** per module; Codecov patch gate is 90%
- Review after adding new features to ensure all quality scale rules still apply
