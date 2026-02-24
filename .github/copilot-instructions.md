# GitHub Copilot Instructions — ha-unraid

> Read **[`AGENTS.md`](/AGENTS.md)** for comprehensive project documentation.
> Path-specific `*.instructions.md` files in `.github/instructions/` auto-load per file type.
> Reusable task prompts are in `.github/prompts/`.

## Project Identity

- **Domain**: `unraid`
- **Class prefix**: `Unraid`
- **Code path**: `custom_components/unraid/`
- **Test path**: `tests/`
- **Python**: 3.13+ | **HA**: 2025.6.3+ | **Dep**: `unraid-api>=1.5.0`
- **Platforms**: `sensor`, `binary_sensor`, `switch`, `button`
- **iot_class**: `local_polling`

## Code Quality Baseline

- Ruff linter + formatter, line length 88, target `py313`
- `from __future__ import annotations` in every file
- Type hints on all public functions
- Constants in `const.py` with `Final` annotations
- Run `./scripts/lint` before committing

## Architecture Quick Reference

### Triple Coordinator Pattern

| Coordinator | Interval | Scope |
|-------------|----------|-------|
| `UnraidSystemCoordinator` | 30s | Metrics, Docker, VMs, UPS, notifications |
| `UnraidStorageCoordinator` | 5min | Array, disks, parity, shares |
| `UnraidInfraCoordinator` | 15min | Services, registration, cloud, plugins |

### Entity Hierarchy

```
CoordinatorEntity → UnraidBaseEntity → UnraidEntity (with EntityDescription)
```

Platform entities use MRO: `PlatformEntity, UnraidBaseEntity`

### Runtime Data

Access via `entry.runtime_data` (typed as `UnraidRuntimeData`). Never use `hass.data[DOMAIN]`.

## Workflow Rules

- Lint after every change: `./scripts/lint`
- Test: `pytest` or `./scripts/test`
- Entity names via `_attr_translation_key` + `strings.json`
- Icons via `icons.json` keyed by translation key
- Unique IDs: `{server_uuid}_{resource_id}`
- Handle `None` coordinator data gracefully

## Path-Specific Instruction Files

These files auto-load in Copilot based on `applyTo` patterns:

| Pattern | File | Scope |
|---------|------|-------|
| `**/*.py` | `python.instructions.md` | Python conventions |
| `**/entity.py`, `**/entities/*.py` | `entities.instructions.md` | Entity hierarchy, state, actions |
| `**/coordinator.py`, `**/coordinators/*.py` | `coordinator.instructions.md` | Triple coordinator, error handling |
| `config_flow.py` | `config_flow.instructions.md` | SSL, versions, options flow |
| `diagnostics.py` | `diagnostics.instructions.md` | Diagnostic data, security |
| `repairs.py` | `repairs.instructions.md` | Repair flows |
| `tests/**/*.py` | `tests.instructions.md` | Fixtures, mocking, scenarios |
| `strings.json`, `translations/` | `translations.instructions.md` | Translation structure |
| `icons.json` | `json.instructions.md` | Icon definitions |
| `manifest.json` | `manifest.instructions.md` | Integration metadata |
| `quality_scale.yaml` | `yaml.instructions.md` | Quality self-assessment |
| `**/*.md` | `markdown.instructions.md` | Documentation standards |
| `services.yaml` | `service_actions.instructions.md` | Service actions |

## Reusable Task Prompts

Available in `.github/prompts/` for common development tasks:

- **Add New Sensor** — Sensor entity creation guide
- **Add Entity Platform** — New platform setup
- **Add Config Option** — Options flow field addition
- **Add Action** — Custom service action creation
- **Debug Coordinator Issue** — Coordinator troubleshooting
- **Create Implementation Plan** — Feature planning template
- **Review Integration** — Quality audit checklist
- **Update Translations** — Translation management
