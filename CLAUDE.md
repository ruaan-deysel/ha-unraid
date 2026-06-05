# Claude Code Instructions — ha-unraid

> Read **[`AGENTS.md`](AGENTS.md)** for comprehensive project documentation.
> This file is a thin wrapper for Claude Code / Claude AI agents.

## ⚠️ Critical Rule: Never Bypass `unraid-api`

All communication with the Unraid server **must** go through the
[`unraid-api`](https://github.com/ruaan-deysel/unraid-api) library
(`UnraidClient`). Never add direct GraphQL/HTTP/websocket/SSH I/O, and never
re-implement or work around the library to land a fix faster — this keeps the
integration compliant with Home Assistant best practice.

If a fix needs something `unraid-api` does not expose, **STOP**: do not work
around it here. Open an issue on **https://github.com/ruaan-deysel/unraid-api**
and direct the user there. Full policy in [`AGENTS.md`](AGENTS.md) → "Critical
Rule: Never Bypass `unraid-api`".

## Quick Reference

- **Domain**: `unraid` | **Prefix**: `Unraid` | **Python**: 3.13+ | **HA**: 2026.5.0+ | **Dep**: `unraid-api>=1.11.0`
- **Code**: `custom_components/unraid/` | **Tests**: `tests/`
- **Lint**: `./script/lint` | **Test**: `./script/test` | **Check**: `./script/check`

## Path-Specific Instructions

When editing specific file types, consult the relevant instruction file in `.github/instructions/`:

| File Pattern                                        | Instruction File                                                                                |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `**/*.py`                                           | [`python.instructions.md`](.github/instructions/python.instructions.md)                         |
| Entity platform files                               | [`entities.instructions.md`](.github/instructions/entities.instructions.md)                     |
| `coordinator.py`                                    | [`coordinator.instructions.md`](.github/instructions/coordinator.instructions.md)               |
| `__init__.py` / `config_flow.py` / `coordinator.py` | [`api.instructions.md`](.github/instructions/api.instructions.md)                               |
| `config_flow.py`                                    | [`config_flow.instructions.md`](.github/instructions/config_flow.instructions.md)               |
| `diagnostics.py`                                    | [`diagnostics.instructions.md`](.github/instructions/diagnostics.instructions.md)               |
| `repairs.py`                                        | [`repairs.instructions.md`](.github/instructions/repairs.instructions.md)                       |
| `tests/**/*.py`                                     | [`tests.instructions.md`](.github/instructions/tests.instructions.md)                           |
| `strings.json`, `translations/`                     | [`translations.instructions.md`](.github/instructions/translations.instructions.md)             |
| `icons.json`                                        | [`json.instructions.md`](.github/instructions/json.instructions.md)                             |
| `manifest.json`                                     | [`manifest.instructions.md`](.github/instructions/manifest.instructions.md)                     |
| `quality_scale.yaml`                                | [`yaml.instructions.md`](.github/instructions/yaml.instructions.md)                             |
| `**/configuration.yaml`                             | [`configuration_yaml.instructions.md`](.github/instructions/configuration_yaml.instructions.md) |
| `**/*.md`                                           | [`markdown.instructions.md`](.github/instructions/markdown.instructions.md)                     |
| `services.yaml` / `services.py`                     | [`service_actions.instructions.md`](.github/instructions/service_actions.instructions.md)       |
| `services.yaml`                                     | [`services_yaml.instructions.md`](.github/instructions/services_yaml.instructions.md)           |

## Task Prompts

Reusable prompts for common tasks in `.github/prompts/`:

- **Add New Sensor** — Step-by-step sensor entity creation
- **Add Entity Platform** — Adding a new platform (number, select, etc.)
- **Add Config Option** — Adding options flow fields
- **Add Action** — Adding custom service actions
- **Debug Coordinator Issue** — Troubleshooting coordinator problems
- **Create Implementation Plan** — Structured planning for new features
- **Review Integration** — Quality scale and best practices audit
- **Update Translations** — Translation string management
