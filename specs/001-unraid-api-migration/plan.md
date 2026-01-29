# Implementation Plan: Migrate to unraid-api Python Library

**Branch**: `001-unraid-api-migration` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-unraid-api-migration/spec.md`

## Summary

Migrate the ha-unraid Home Assistant integration from a custom GraphQL-based API client to the official `unraid-api` Python library (v1.3.1). This removes ~1,000 lines of custom code (api.py + models.py) and aligns with Home Assistant best practices of using dedicated Python libraries for device communication. The migration must preserve all existing entity unique_ids for backwards compatibility.

## Technical Context

**Language/Version**: Python 3.12+ (Home Assistant 2025.6+ requirement)
**Primary Dependencies**: homeassistant, unraid-api>=1.3.1, aiohttp (for session injection), pydantic v2
**Storage**: N/A (no local storage, data fetched from Unraid server via API)
**Testing**: pytest with homeassistant test framework, pytest-asyncio, pytest-homeassistant-custom-component
**Target Platform**: Home Assistant (any platform: Linux, macOS, Docker, HAOS)
**Project Type**: Home Assistant custom component (single directory structure)
**Performance Goals**: Maintain current polling intervals (30s system, 300s storage), no additional latency from library usage
**Constraints**: Must preserve entity unique_ids, must handle all 3 SSL modes (No, Yes, Strict), must gracefully handle optional features
**Scale/Scope**: Single integration, ~15 source files, ~25 entities per server

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Home Assistant Quality Compliance

| Requirement | Status | Notes |
|-------------|--------|-------|
| Pass HA integration quality checklist | PASS | Migration maintains existing quality |
| Follow HA coding style | PASS | No style changes required |
| Use HA recommended libraries | PASS | **Migration aligns with this** - using unraid-api library |
| No deprecated HA APIs | PASS | No deprecated APIs used |
| Error handling per HA guidelines | PASS | Using library exceptions mapped to HA exceptions |
| Use UNRAID-API python library | **PASS** | **Core objective of this migration** |
| No conflicting dependencies | PASS | unraid-api compatible with HA requirements |
| Test against stable HA releases | PASS | Test suite will be updated |

### Principle II: Entity State and Data Model Adherence

| Requirement | Status | Notes |
|-------------|--------|-------|
| Appropriate entity platforms | PASS | No changes to platforms |
| State machine patterns | PASS | No changes to state handling |
| snake_case attributes | PASS | Library models use camelCase, will maintain adapter pattern |
| State restoration | PASS | Unchanged |
| Stable unique IDs | **CRITICAL** | Must verify library models provide same ID values |
| Appropriate device/state classes | PASS | Unchanged |

### Principle III: Config Flow Implementation

| Requirement | Status | Notes |
|-------------|--------|-------|
| ConfigFlow implemented | PASS | Existing, update to use library client |
| Clear descriptions | PASS | Unchanged |
| Input validation | PASS | Will use library's test_connection() |
| Options flow | PASS | Unchanged |
| Graceful error handling | PASS | Library provides typed exceptions |

### Principle IV: Discovery and Diagnostics Support

| Requirement | Status | Notes |
|-------------|--------|-------|
| Discovery support | N/A | Unraid doesn't support SSDP/Zeroconf discovery |
| Diagnostics implementation | PASS | Will update to use library client info |
| Debug logging | PASS | Maintain current log levels |
| Repair flows | PASS | Existing auth repair unchanged |

### Principle V: Release Compatibility

| Requirement | Status | Notes |
|-------------|--------|-------|
| Min HA version declared | PASS | manifest.json maintained |
| Breaking changes documented | **REQUIRED** | Must note library dependency in changelog |
| Deprecated API updates | PASS | No deprecated APIs used |
| Beta testing | PASS | Normal testing process |
| Backwards compatibility | **CRITICAL** | Entity unique_ids must be preserved |

**Gate Result**: PASS - All requirements met or have clear mitigation plan. Critical items (unique ID preservation) addressed in design.

## Project Structure

### Documentation (this feature)

```text
specs/001-unraid-api-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no new APIs)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
custom_components/unraid/
├── __init__.py          # Entry point, UnraidClient initialization
├── api.py               # TO BE DELETED - replaced by unraid_api library
├── binary_sensor.py     # Update imports to use unraid_api.models
├── button.py            # Update imports and API calls
├── config_flow.py       # Update to use UnraidClient from library
├── const.py             # May need new constants for library
├── coordinator.py       # MAJOR CHANGES - replace GraphQL with typed methods
├── diagnostics.py       # Update to use library client
├── icons.json           # No changes
├── manifest.json        # Add unraid-api>=1.3.1 to requirements
├── models.py            # TO BE DELETED - replaced by unraid_api.models
├── py.typed             # No changes
├── quality_scale.yaml   # No changes
├── sensor.py            # Update imports to use unraid_api.models
├── strings.json         # No changes
└── switch.py            # Update imports and API calls

tests/
├── __init__.py
├── conftest.py          # Update fixtures to mock UnraidClient
├── test_api.py          # TO BE DELETED
├── test_binary_sensor.py # Update mocks
├── test_button.py       # Update mocks
├── test_config_flow.py  # Update to mock library client
├── test_coordinator.py  # Update mocks for typed methods
├── test_coordinator_simple.py # Update mocks
├── test_diagnostics.py  # Update mocks
├── test_init.py         # Update mocks
├── test_models.py       # TO BE DELETED or refactored
├── test_sensor.py       # Update mocks
└── test_switch.py       # Update mocks
```

**Structure Decision**: Home Assistant custom component - single directory under `custom_components/unraid/`. This is the standard HA pattern and will not change.

## Complexity Tracking

> No violations requiring justification. Migration simplifies codebase by removing ~1,000 lines of custom code.

| Aspect | Before | After | Change |
|--------|--------|-------|--------|
| Source files | 16 | 14 | -2 (api.py, models.py removed) |
| Lines of code | ~3,500 | ~2,500 | ~-1,000 (estimate) |
| External dependencies | 0 (runtime) | 1 (unraid-api) | +1 |
| GraphQL strings | ~20 | 0 | All removed |
| Custom Pydantic models | ~25 | 0 | All from library |
