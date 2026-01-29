# Tasks: Migrate to unraid-api Python Library

**Input**: Design documents from `/specs/001-unraid-api-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Test update tasks are included as part of User Story 6 (P3), as specified in the feature requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Custom component**: `custom_components/unraid/` for source
- **Tests**: `tests/` for test files
- Structure is a Home Assistant custom component (single directory)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add library dependency and prepare for migration

- [X] T001 Add unraid-api>=1.3.1 to requirements array in custom_components/unraid/manifest.json
- [X] T002 [P] Add library exception imports to custom_components/unraid/const.py for reuse across modules

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure changes that MUST be complete before user story implementation

**⚠️ CRITICAL**: These changes are the foundation - all entity files depend on coordinator working correctly

- [X] T003 Update UnraidSystemData dataclass in custom_components/unraid/coordinator.py to use library models (ServerInfo, SystemMetrics, DockerContainer, VmDomain, UPSDevice)
- [X] T004 Update UnraidStorageData dataclass in custom_components/unraid/coordinator.py to use library models (UnraidArray, Share) with convenience properties
- [X] T005 Update UnraidSystemCoordinator._async_update_data() in custom_components/unraid/coordinator.py to use typed library methods (get_server_info, get_system_metrics, typed_get_containers, typed_get_vms, typed_get_ups_devices, get_notification_overview)
- [X] T006 Update UnraidStorageCoordinator._async_update_data() in custom_components/unraid/coordinator.py to use typed library methods (typed_get_array, typed_get_shares)
- [X] T006b Verify SCAN_INTERVAL constants unchanged in custom_components/unraid/coordinator.py (30s system, 300s storage) per FR-012
- [X] T007 Update __init__.py async_setup_entry() in custom_components/unraid/__init__.py to create UnraidClient from library instead of UnraidAPIClient, inject HA session via async_get_clientsession()
- [X] T008 Update __init__.py _build_server_info() in custom_components/unraid/__init__.py to use library's ServerInfo model
- [X] T009 Remove GraphQL query string from async_setup_entry() in custom_components/unraid/__init__.py (the SystemInfo query)

**Checkpoint**: Foundation ready - coordinators fetch data using library methods, __init__.py uses library client

---

## Phase 3: User Story 1 - Transparent Migration (Priority: P1) 🎯 MVP

**Goal**: Existing users upgrade seamlessly with all entities maintaining their IDs and historical data

**Independent Test**: Upgrade existing ha-unraid installation, verify all entities report data with preserved unique_ids

### Implementation for User Story 1

- [X] T010 [P] [US1] Replace all local model imports with unraid_api.models in custom_components/unraid/sensor.py (remove "from .models import", add "from unraid_api.models import SystemMetrics, ArrayDisk, Share, UPSDevice, etc.")
- [X] T011 [P] [US1] Replace all local model imports with unraid_api.models in custom_components/unraid/binary_sensor.py (remove "from .models import", add "from unraid_api.models import ArrayDisk, ParityCheck")
- [X] T012 [P] [US1] Replace all local model imports with unraid_api.models in custom_components/unraid/switch.py (remove "from .models import", add "from unraid_api.models import DockerContainer, VmDomain")
- [X] T013 [P] [US1] Replace all local model imports with unraid_api.models in custom_components/unraid/button.py (remove "from .models import", add "from unraid_api.models import")
- [X] T014 [US1] Verify sensor entity attribute access in custom_components/unraid/sensor.py works with library model field names (camelCase like percentTotal, chargeLevel)
- [X] T015 [US1] Verify binary_sensor entity attribute access in custom_components/unraid/binary_sensor.py works with library model field names
- [X] T016 [US1] Verify switch entity attribute access in custom_components/unraid/switch.py works with library model field names (webUiUrl, iconUrl)
- [X] T017 [US1] Verify button entity works in custom_components/unraid/button.py with library client methods
- [X] T018 [US1] Confirm all entity unique_id patterns remain unchanged by reviewing each sensor/switch/button class

**Checkpoint**: All entities use library models, unique_ids preserved - upgrade should be transparent to users

---

## Phase 4: User Story 2 - Complete GraphQL Removal (Priority: P1)

**Goal**: Zero GraphQL strings remain in the codebase, all communication via library methods

**Independent Test**: grep -r "query\|mutation" custom_components/unraid/ returns zero results

### Implementation for User Story 2

- [X] T019 [US2] Replace any remaining raw query() calls in custom_components/unraid/coordinator.py with typed library methods
- [X] T020 [US2] Update start_container/stop_container calls in custom_components/unraid/switch.py to use library client methods
- [X] T021 [US2] Update start_vm/stop_vm calls in custom_components/unraid/switch.py to use library client methods
- [X] T022 [P] [US2] Update array start/stop button actions in custom_components/unraid/button.py to use library client methods (start_array, stop_array)
- [X] T023 [P] [US2] Update disk spin up/down button actions in custom_components/unraid/button.py to use library client methods (spin_up_disk, spin_down_disk)
- [X] T024 [P] [US2] Update parity check button actions in custom_components/unraid/button.py to use library client methods (start_parity_check, pause_parity_check, resume_parity_check, cancel_parity_check)
- [X] T024b [US2] Verify coordinator handles UnraidAPIError gracefully for optional queries (Docker, VMs, UPS) by reviewing try/except blocks in custom_components/unraid/coordinator.py per FR-011/SC-008
- [X] T025 [US2] Run grep -r "query\|mutation\|graphql" custom_components/unraid/ to verify no GraphQL strings remain

**Checkpoint**: All GraphQL removed - library methods used exclusively for all API communication

---

## Phase 5: User Story 3 - Remove Custom Files (Priority: P2)

**Goal**: api.py and models.py deleted, all imports reference unraid_api library

**Independent Test**: ls custom_components/unraid/api.py returns "No such file", same for models.py

### Implementation for User Story 3

> **Note**: Entity file imports (sensor.py, binary_sensor.py, switch.py, button.py) already updated in US1 (T010-T013). Coordinator imports updated in Foundational (T003-T006). This phase focuses on remaining imports and file deletion.

- [X] T026 [US3] Replace UnraidAPIClient import with UnraidClient from unraid_api in custom_components/unraid/__init__.py
- [X] T027 [US3] Replace .api imports with unraid_api in custom_components/unraid/config_flow.py
- [X] T028 [US3] Delete custom_components/unraid/api.py
- [X] T029 [US3] Delete custom_components/unraid/models.py
- [X] T030 [US3] Run ruff check custom_components/unraid/ to verify no broken imports

**Checkpoint**: api.py and models.py removed - codebase is cleaner with ~1000 fewer lines

---

## Phase 6: User Story 4 - Session Injection (Priority: P2)

**Goal**: UnraidClient properly uses Home Assistant's aiohttp session for connection pooling

**Independent Test**: Verify async_get_clientsession() is passed to UnraidClient constructor

### Implementation for User Story 4

- [X] T031 [US4] Verify UnraidClient initialization in custom_components/unraid/__init__.py passes session=async_get_clientsession(hass, verify_ssl=verify_ssl)
- [X] T032 [US4] Verify client.close() in async_unload_entry() in custom_components/unraid/__init__.py does not affect shared HA session
- [X] T033 [US4] Update config_flow.py test_connection in custom_components/unraid/config_flow.py to use UnraidClient with HA session

**Checkpoint**: Session injection working correctly for proper HA resource management

---

## Phase 7: User Story 5 - Exception Handling (Priority: P3)

**Goal**: Error handling uses library exception classes mapped to HA exceptions

**Independent Test**: Code review confirms UnraidAuthenticationError, UnraidConnectionError, UnraidAPIError used appropriately

### Implementation for User Story 5

- [X] T034 [P] [US5] Add library exception imports (UnraidAuthenticationError, UnraidConnectionError, UnraidTimeoutError, UnraidAPIError) to custom_components/unraid/__init__.py
- [X] T035 [US5] Update exception handling in async_setup_entry() in custom_components/unraid/__init__.py to catch UnraidAuthenticationError → ConfigEntryAuthFailed
- [X] T036 [US5] Update exception handling in async_setup_entry() in custom_components/unraid/__init__.py to catch UnraidConnectionError/UnraidTimeoutError → ConfigEntryNotReady
- [X] T037 [US5] Update exception handling in coordinator _async_update_data() methods in custom_components/unraid/coordinator.py to use library exceptions
- [X] T038 [US5] Update exception handling in config_flow test_connection in custom_components/unraid/config_flow.py to use library exceptions
- [X] T039 [US5] Update error handling in switch.py async_turn_on/off in custom_components/unraid/switch.py to catch UnraidAPIError

**Checkpoint**: All exception handling uses library exception types consistently

---

## Phase 8: User Story 6 - Update Test Suite (Priority: P3)

**Goal**: Test suite passes with new library-based implementation

**Independent Test**: pytest tests/ runs with 100% pass rate

### Implementation for User Story 6

- [X] T040 [US6] Delete tests/test_api.py (tests for deleted api.py)
- [X] T041 [US6] Delete or refactor tests/test_models.py (tests for deleted models.py)
- [X] T042 [US6] Update conftest.py fixtures in tests/conftest.py to mock UnraidClient instead of UnraidAPIClient
- [X] T043 [P] [US6] Update mocks in tests/test_config_flow.py to mock unraid_api.UnraidClient
- [X] T044 [P] [US6] Update mocks in tests/test_init.py to mock unraid_api.UnraidClient and library models
- [X] T045 [P] [US6] Update mocks in tests/test_coordinator.py to mock library typed methods (typed_get_array, typed_get_containers, etc.)
- [X] T046 [P] [US6] Update mocks in tests/test_coordinator_simple.py to mock library typed methods
- [X] T047 [P] [US6] Update mocks in tests/test_sensor.py to use library model fixtures
- [X] T048 [P] [US6] Update mocks in tests/test_binary_sensor.py to use library model fixtures
- [X] T049 [P] [US6] Update mocks in tests/test_switch.py to use library model fixtures
- [X] T050 [P] [US6] Update mocks in tests/test_button.py to use library model fixtures
- [X] T051 [P] [US6] Update mocks in tests/test_diagnostics.py to use library client
- [X] T052 [US6] Run pytest tests/ -v to verify all tests pass

**Checkpoint**: Test suite passes - code quality maintained through migration

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [X] T053 [P] Update diagnostics.py in custom_components/unraid/diagnostics.py to use library client info
- [X] T054 Run ruff check custom_components/unraid/ to verify code style compliance
- [X] T055 Run grep -r "from .api import\|from .models import" custom_components/unraid/ to confirm no local imports remain
- [X] T056 Run verification commands from quickstart.md to confirm success criteria met (including polling interval preservation: 30s system, 300s storage)
- [X] T057 Update version in manifest.json if needed for release

---

## Phase 10: HA Core Pattern Alignment (Post-Migration Enhancement)

**Purpose**: Align code structure with Home Assistant core integration patterns for easier future core submission

**Reference**: La Marzocco integration (https://github.com/home-assistant/core/tree/dev/homeassistant/components/lamarzocco)

- [X] T058 [P] Create entity.py with UnraidBaseEntity base class following La Marzocco CoordinatorEntity pattern
- [X] T059 [P] Create UnraidEntityDescription dataclass with available_fn and supported_fn
- [X] T060 Refactor sensor.py UnraidSensorEntity to inherit from UnraidBaseEntity
- [X] T061 Refactor binary_sensor.py UnraidBinarySensorEntity to inherit from UnraidBaseEntity
- [X] T062 Refactor switch.py UnraidSwitchEntity to inherit from UnraidBaseEntity
- [X] T063 Update button.py to use DeviceInfo type for consistent device registration
- [X] T064 Run lint and tests to verify refactoring (340 tests pass, 95% coverage)

**Checkpoint**: Entity hierarchy simplified with shared base class - reduces code duplication ~200 lines

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1-2 (Phase 3-4)**: Depend on Foundational phase completion - P1 priority, implement together
- **User Story 3-4 (Phase 5-6)**: Depend on US1-2 completion - P2 priority
- **User Story 5-6 (Phase 7-8)**: Can start after Foundational - P3 priority, internal quality
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) - Core entity migration
- **User Story 2 (P1)**: Depends on Foundational (Phase 2) - Can run parallel with US1
- **User Story 3 (P2)**: Depends on US1+US2 completion - File deletion requires all references updated
- **User Story 4 (P2)**: Depends on Foundational (Phase 2) - Can run parallel with US1-3
- **User Story 5 (P3)**: Depends on Foundational (Phase 2) - Can run parallel with others
- **User Story 6 (P3)**: Depends on US1-5 completion - Tests need final implementation

### Within Each User Story

- Models/imports before behavior changes
- Core implementation before integration
- Verification after implementation

### Parallel Opportunities

**Phase 1 (Setup)**:
- T001, T002 can run in parallel

**Phase 3 (US1) - Entity imports**:
- T010, T011, T012, T013 can all run in parallel (different entity files)

**Phase 4 (US2) - Button actions**:
- T022, T023, T024 can all run in parallel (different button types)

**Phase 7 (US5) - Exception handling**:
- T034 can run in parallel with others

**Phase 8 (US6) - Test updates**:
- T043, T044, T045, T046, T047, T048, T049, T050, T051 can all run in parallel (different test files)

---

## Parallel Example: User Story 6 (Test Updates)

```bash
# Launch all test file updates together (T043-T051):
Task: "T043 - Update mocks in tests/test_config_flow.py to mock unraid_api.UnraidClient"
Task: "T044 - Update mocks in tests/test_init.py to mock unraid_api.UnraidClient and library models"
Task: "T045 - Update mocks in tests/test_coordinator.py to mock library typed methods"
Task: "T047 - Update mocks in tests/test_sensor.py to use library model fixtures"
Task: "T048 - Update mocks in tests/test_binary_sensor.py to use library model fixtures"
Task: "T049 - Update mocks in tests/test_switch.py to use library model fixtures"
Task: "T050 - Update mocks in tests/test_button.py to use library model fixtures"
```

---

## Implementation Strategy

### MVP First (User Stories 1+2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (entity imports)
4. Complete Phase 4: User Story 2 (GraphQL removal)
5. **STOP and VALIDATE**: Integration loads, entities work, no GraphQL strings
6. Deploy/test with real Unraid server

### Incremental Delivery

1. Complete Setup + Foundational → Library integrated
2. Add User Stories 1+2 → MVP (entities work, no GraphQL) → Test
3. Add User Stories 3+4 → Clean codebase (files deleted, session injection) → Test
4. Add User Stories 5+6 → Quality complete (exceptions, tests) → Test
5. Each increment adds value without breaking previous functionality

### Recommended Execution Order

For a single developer working sequentially:

1. T001-T002 (Setup)
2. T003-T009, T006b (Foundational)
3. T010-T018 (US1 - Entity migration)
4. T019-T025, T024b (US2 - GraphQL removal)
5. T026-T030 (US3 - File deletion)
6. T031-T033 (US4 - Session injection)
7. T034-T039 (US5 - Exception handling)
8. T040-T052 (US6 - Test updates)
9. T053-T057 (Polish)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Entity unique_ids MUST remain unchanged (critical for backwards compatibility)
- Verify no GraphQL strings remain after US2 completion
- Test suite update (US6) can start early but must complete last
- Run ruff check after each major change to catch import errors
- Commit after each user story completion for easy rollback
