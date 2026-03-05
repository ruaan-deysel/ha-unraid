---
agent: "agent"
tools:
  - "search/codebase"
  - "edit"
  - "search"
description: "Perform a comprehensive quality review of the Unraid integration"
---

# Review Integration

Your goal is to perform a comprehensive quality review of the Unraid integration against Home Assistant standards.
Treat the official Quality Scale rules as mandatory review criteria:
<https://developers.home-assistant.io/docs/core/integration-quality-scale/rules>

## Review Checklist

### Quality Scale Compliance

- [ ] Applicable rules from the official Quality Scale rules page have been reviewed
- [ ] All applicable rules are satisfied or clearly documented as not applicable

### Architecture

- [ ] Entities → Coordinator → API Client pattern followed (no layer skipping)
- [ ] Multi-coordinator system properly structured
- [ ] Data transforms handle all API response formats
- [ ] No direct API calls from entities

### Config Flow

- [ ] User setup works for both local and remote modes
- [ ] Reauth flow handles expired credentials
- [ ] Reconfigure flow allows changing settings
- [ ] Unique ID properly set and checked
- [ ] Validation errors shown to user clearly

### Entity Quality

- [ ] All entities use `EntityDescription` pattern
- [ ] `has_entity_name = True` set on all entities
- [ ] `translation_key` used (no hardcoded names)
- [ ] Proper `device_class` and `state_class` assigned
- [ ] Availability handled correctly (network vs Protect)
- [ ] `PARALLEL_UPDATES` set appropriately per platform

### Error Handling

- [ ] `ConfigEntryNotReady` for temporary setup failures
- [ ] `ConfigEntryAuthFailed` for authentication issues
- [ ] `UpdateFailed` for coordinator fetch failures
- [ ] `HomeAssistantError` for service call failures
- [ ] No bare `except Exception:` outside config flows

### Security

- [ ] Diagnostics use `async_redact_data()`
- [ ] No sensitive data in logs
- [ ] API keys not exposed in entity attributes
- [ ] SSL verification configurable

### Code Quality

- [ ] Full type hints on all public methods
- [ ] Module docstrings on all files
- [ ] Async patterns correctly applied
- [ ] No blocking calls on event loop
- [ ] Ruff and mypy pass cleanly

### Testing

- [ ] 90%+ coverage maintained
- [ ] Config flow tested (success + error paths)
- [ ] Coordinator tested (success + failure paths)
- [ ] Entity state and availability tested
- [ ] Service actions tested

### Translations

- [ ] All user-facing strings in `strings.json`
- [ ] Sentence case used consistently
- [ ] No hardcoded strings in Python code

## Output

Provide a summary with:
1. **Critical issues** — Must fix before release
2. **Improvements** — Should fix for quality
3. **Suggestions** — Nice to have
