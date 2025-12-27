````markdown
# Implementation Plan: Unraid GraphQL Integration

**Branch**: `001-unraid-graphql-integration` | **Date**: 2025-12-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-unraid-graphql-integration/spec.md`

## Summary

Create a Home Assistant custom integration that connects to Unraid 7.2+ servers via the official GraphQL API. The integration provides real-time monitoring of system metrics, storage health, Docker containers, VMs, and UPS status with pydantic-based data validation. Uses dual-coordinator polling pattern (30s for system metrics, 5min for storage) with full Docker/VM control capabilities.

## Technical Context

**Language/Version**: Python 3.12+ (Home Assistant 2024.1+ requirement)  
**Primary Dependencies**: aiohttp (HA built-in), pydantic v2, homeassistant  
**Storage**: Home Assistant config entry storage (encrypted for API keys)  
**Testing**: pytest with pytest-homeassistant-custom-component  
**Target Platform**: Home Assistant (any platform - Linux, Docker, HAOS, etc.)
**Project Type**: Single project (HA custom integration structure)  
**Performance Goals**: <1s response for all entity updates, <500ms for control actions  
**Constraints**: Must comply with HA async patterns, no blocking I/O, memory-efficient for large container/VM counts  
**Scale/Scope**: Target 1-5 Unraid servers, 50+ Docker containers, 10+ VMs per server

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Home Assistant Quality Compliance | ✅ PASS | Uses HA patterns (config flow, coordinator, entity platforms) |
| II. Entity State and Data Model | ✅ PASS | Standard sensor/switch platforms with proper device classes |
| III. Config Flow Implementation | ✅ PASS | ConfigFlow + OptionsFlow designed per spec |
| IV. Discovery and Diagnostics | ✅ PASS | Diagnostics implemented; SSDP discovery deferred (not exposed by Unraid) |
| V. Release Compatibility | ✅ PASS | Targets HA 2024.1+; uses stable APIs only |

## Project Structure

### Documentation (this feature)

```text
specs/001-unraid-graphql-integration/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # API research and decisions
├── data-model.md        # Pydantic models and entity mappings
├── quickstart.md        # Development setup guide
├── contracts/           # GraphQL queries and mutations
│   ├── queries.graphql
│   └── mutations.graphql
└── checklists/
    └── requirements.md  # Requirement traceability
```

### Source Code (repository root)

```text
custom_components/
└── unraid/
    ├── __init__.py          # Integration setup, coordinators
    ├── manifest.json        # Integration manifest
    ├── config_flow.py       # Config and options flow
    ├── const.py             # Constants (DOMAIN, defaults)
    ├── coordinator.py       # DataUpdateCoordinators
    ├── api.py               # GraphQL client
    ├── models.py            # Pydantic models
    ├── diagnostics.py       # Diagnostics handler
    ├── sensor.py            # Sensor entities
    ├── switch.py            # Docker/VM switch entities
    ├── binary_sensor.py     # Problem sensors (disk health, etc.)
    ├── strings.json         # UI strings
    └── translations/
        └── en.json

tests/
├── conftest.py              # Test fixtures
├── test_config_flow.py      # Config flow tests
├── test_coordinator.py      # Coordinator tests
├── test_api.py              # API client tests
├── test_sensor.py           # Sensor entity tests
├── test_switch.py           # Switch entity tests
└── fixtures/                # Mock API responses
    ├── system_info.json
    ├── metrics.json
    ├── array.json
    ├── docker.json
    └── vms.json
```

**Structure Decision**: Standard Home Assistant custom integration structure with all code under `custom_components/unraid/`. Tests in separate `tests/` directory with fixtures for mock API responses.

## Phase 0: Research (Complete)

See [research.md](research.md) for full research findings.

### Key Decisions Made

1. **API Endpoint**: `https://{server}/graphql` with `x-api-key` header authentication
2. **Minimum Version**: Unraid 7.2.0 (first stable GraphQL API)
3. **Polling Strategy**: Dual coordinator (30s system, 5min storage)
4. **Unique IDs**: `{system_uuid}_{resource_id}` pattern using PrefixedID from API
5. **Mutation Approach**: Direct GraphQL mutations (not nested container.start)
6. **Error Handling**: HA exception hierarchy (ConfigEntryNotReady, UpdateFailed)

### API Coverage Verified

From official schema v4.29.2:
- ✅ `info` - System information, CPU, memory specs, versions
- ✅ `metrics` - Real-time CPU/memory utilization
- ✅ `array` - Array state, capacity, disk health
- ✅ `disks` - Physical disk hardware info
- ✅ `docker.containers` - Container states and metadata
- ✅ `vms.domains` - VM states
- ✅ `upsDevices` - UPS status (corrected from `ups`)
- ✅ `notifications.overview` - Alert counts
- ✅ `shares` - User share info (optional)
- ✅ Docker mutations: `start`, `stop`, `pause`, `unpause`
- ✅ VM mutations: `start`, `stop`, `pause`, `resume`, `forceStop`, `reboot`

## Phase 1: Design (Complete)

See [data-model.md](data-model.md) for full data model and [contracts/](contracts/) for GraphQL contracts.

### Entity Summary

| Entity Type | Platform | Count | Source |
|-------------|----------|-------|--------|
| Server Device | device | 1 per server | `info.system.uuid` |
| CPU Usage | sensor | 1 | `metrics.cpu.percentTotal` |
| Memory Usage | sensor | 2 (used, percent) | `metrics.memory` |
| CPU Temperature | sensor | 1 | `info.cpu.packages.temp` |
| Array Status | sensor | 3+ (state, capacity, parity) | `array` |
| Disk Sensors | sensor | per disk | `array.disks/parities/caches` |
| Disk Health | binary_sensor | per disk | `disk.status` |
| Docker Containers | switch | per container | `docker.containers` |
| Container Updates | binary_sensor | per container | `isUpdateAvailable` |
| VMs | switch | per VM | `vms.domains` |
| UPS Status | sensor | per UPS | `upsDevices` |
| Notifications | sensor | 4 (total, info, warn, alert) | `notifications.overview` |

### Coordinator Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    UnraidSystemCoordinator                       │
│                    (30 second interval)                          │
├─────────────────────────────────────────────────────────────────┤
│  Queries: metrics, docker.containers, vms.domains,              │
│           upsDevices, notifications.overview                     │
│  Entities: CPU, Memory, Docker switches, VM switches, UPS, etc. │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   UnraidStorageCoordinator                       │
│                    (5 minute interval)                           │
├─────────────────────────────────────────────────────────────────┤
│  Queries: array, disks, shares                                   │
│  Entities: Array status, Disk sensors, Share sensors             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      UnraidAPIClient                             │
├─────────────────────────────────────────────────────────────────┤
│  - Async aiohttp session management                             │
│  - GraphQL query execution                                       │
│  - Mutation execution (Docker/VM control)                        │
│  - Error handling and retry logic                                │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 2: Implementation Tasks

*Note: Full task breakdown generated by `/speckit.tasks` command.*

### High-Level Task Groups

1. **Foundation** (Priority: P0)
   - Create manifest.json with requirements
   - Implement const.py with domain constants
   - Create base Pydantic models

2. **API Client** (Priority: P0)
   - Implement GraphQL client with aiohttp
   - Add query methods for all data types
   - Add mutation methods for Docker/VM control
   - Implement error handling

3. **Config Flow** (Priority: P0)
   - Implement ConfigFlow for initial setup
   - Add connection validation
   - Implement OptionsFlow for polling intervals

4. **Coordinators** (Priority: P0)
   - Implement SystemCoordinator
   - Implement StorageCoordinator
   - Add proper error handling and retry

5. **Entities** (Priority: P1)
   - Implement sensor platform
   - Implement switch platform (Docker/VM)
   - Implement binary_sensor platform
   - Add proper device classes and state classes

6. **Diagnostics** (Priority: P2)
   - Implement diagnostics.py
   - Add data redaction for sensitive info

7. **Testing** (Priority: P1)
   - Create test fixtures
   - Write config flow tests
   - Write coordinator tests
   - Write entity tests

8. **Documentation** (Priority: P2)
   - Update README with installation
   - Add HACS metadata

## Complexity Tracking

No constitution violations requiring justification.

## Next Steps

1. Run `/speckit.tasks` to generate detailed implementation tasks
2. Begin implementation following task priorities
3. Test against real Unraid 7.2 server
4. Prepare for HACS submission

## References

- [Unraid API Official Schema](https://github.com/unraid/api/blob/main/api/generated-schema.graphql)
- [Unraid API Documentation](https://docs.unraid.net/API/)
- [Home Assistant Integration Development](https://developers.home-assistant.io/docs/creating_integration_file_structure)
- [Home Assistant Quality Standards](https://developers.home-assistant.io/docs/integration_quality_scale_index)
````
