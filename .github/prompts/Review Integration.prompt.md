---
description: Review the Unraid integration against HA best practices and quality scale
---

# Review Integration

Perform a comprehensive review of the ha-unraid integration against Home Assistant best practices and the quality scale.

## Context

Read these files:
- `AGENTS.md` — Project documentation
- `custom_components/unraid/quality_scale.yaml` — Current self-assessment
- `custom_components/unraid/manifest.json` — Integration metadata

## Review Checklist

### Code Quality
- [ ] All files use `from __future__ import annotations`
- [ ] Type hints on all public functions
- [ ] `_LOGGER` follows naming convention
- [ ] No bare `except:` — all exceptions are specific
- [ ] Constants in `const.py` with `Final` annotation
- [ ] `./scripts/lint` passes clean (zero warnings)

### Entity Standards
- [ ] All entities use `_attr_has_entity_name = True`
- [ ] All entities use `_attr_translation_key`
- [ ] All entities have matching `icons.json` entries
- [ ] Unique IDs follow `{server_uuid}_{resource_id}` format
- [ ] Appropriate `entity_category` set (DIAGNOSTIC, CONFIG)
- [ ] Appropriate `device_class` used where applicable
- [ ] `entity_registry_enabled_default = False` for noisy entities

### Coordinator
- [ ] Auth errors → `ConfigEntryAuthFailed`
- [ ] Connection errors → `UpdateFailed`
- [ ] Optional services fail gracefully
- [ ] Recovery logging implemented
- [ ] `config_entry=` passed to super().__init__()

### Config Flow
- [ ] User step validates inputs
- [ ] Reauth flow implemented
- [ ] Reconfigure flow implemented
- [ ] Error IDs match `strings.json`
- [ ] Unique ID prevents duplicates

### Testing
- [ ] All platforms have test files
- [ ] Config flow paths tested (success, errors, reauth)
- [ ] Coordinator error scenarios tested
- [ ] Coverage meets target (95%)

### Quality Scale
- [ ] Bronze: All rules done/exempt
- [ ] Silver: All done (check test-coverage)
- [ ] Gold: All done/exempt
- [ ] Platinum: async-dependency, inject-websession, strict-typing
