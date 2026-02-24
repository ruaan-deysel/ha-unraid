---
applyTo: "custom_components/unraid/quality_scale.yaml"
---

# YAML Configuration Files Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

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

- **Bronze**: Minimum requirements for all integrations
- **Silver**: Improved reliability and robustness
- **Gold**: Best user experience
- **Platinum**: Highest standards

### Rules

- Update status when implementing new quality scale requirements
- Always include a `comment` explaining `exempt` or `todo` status
- Current target: **Platinum** level
- Key outstanding item: `test-coverage` (63% → 95%)
- Review after adding new features to ensure all quality scale rules still apply
