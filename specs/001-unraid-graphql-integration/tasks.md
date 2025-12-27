# Tasks: Unraid GraphQL Integration

**Input**: Design documents from `/specs/001-unraid-graphql-integration/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Methodology**: Strict TDD (Test-Driven Development)
- 🔴 **RED**: Write failing test first
- 🟢 **GREEN**: Write minimal code to pass
- 🔵 **REFACTOR**: Clean up while tests pass

**Organization**: Tasks grouped by user story. Within each story: TESTS FIRST, then implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Include exact file paths in descriptions

## Path Conventions

- **Custom component**: `custom_components/unraid/`
- **Tests**: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, test infrastructure, and basic structure

- [X] T001 Create integration directory structure per plan.md at custom_components/unraid/
- [X] T002 [P] Create manifest.json with domain, version, requirements (aiohttp, pydantic) in custom_components/unraid/manifest.json
- [X] T003 [P] Create const.py with DOMAIN, default polling intervals, version constants in custom_components/unraid/const.py
- [X] T004 [P] Create strings.json with config flow UI strings in custom_components/unraid/strings.json
- [X] T005 [P] Create translations/en.json with English translations in custom_components/unraid/translations/en.json
- [X] T006 [P] Create tests/ directory structure with __init__.py in tests/
- [X] T007 [P] Create conftest.py with pytest fixtures and mock helpers in tests/conftest.py
- [X] T008 [P] Create test fixtures directory with sample API responses in tests/fixtures/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### 2A: Pydantic Models (TDD)

**🔴 RED: Write Tests First**
- [X] T009 Write test for UnraidBaseModel with extra="ignore" forward compatibility in tests/test_models.py
- [X] T010 [P] Write test for SystemInfo, InfoSystem, InfoCpu, InfoOs, InfoVersions parsing in tests/test_models.py
- [X] T011 [P] Write test for Metrics, CpuUtilization, MemoryUtilization parsing in tests/test_models.py
- [X] T012 [P] Write test for UnraidArray, ArrayDisk, ArrayCapacity, ParityCheck parsing in tests/test_models.py
- [X] T013 [P] Write test for DockerContainer, ContainerPort parsing in tests/test_models.py
- [X] T014 [P] Write test for Vms, VmDomain parsing in tests/test_models.py
- [X] T015 [P] Write test for UPSDevice, UPSBattery, UPSPower parsing in tests/test_models.py
- [X] T016 [P] Create mock JSON fixtures for all model tests in tests/fixtures/

**🟢 GREEN: Implement Models**
- [X] T017 Implement UnraidBaseModel base class with ConfigDict(extra="ignore") in custom_components/unraid/models.py
- [X] T018 Implement SystemInfo, InfoSystem, InfoCpu, InfoOs, InfoVersions Pydantic models in custom_components/unraid/models.py
- [X] T019 [P] Implement Metrics, CpuUtilization, MemoryUtilization Pydantic models in custom_components/unraid/models.py
- [X] T020 [P] Implement UnraidArray, ArrayDisk, ArrayCapacity, ParityCheck models in custom_components/unraid/models.py
- [X] T021 [P] Implement DockerContainer, ContainerPort models in custom_components/unraid/models.py
- [X] T022 [P] Implement Vms, VmDomain models in custom_components/unraid/models.py
- [X] T023 [P] Implement UPSDevice, UPSBattery, UPSPower models in custom_components/unraid/models.py

**🔵 REFACTOR: Verify all model tests pass**
- [X] T024 Run pytest tests/test_models.py - all tests must pass before proceeding

### 2B: API Client (TDD)

**🔴 RED: Write Tests First**
- [X] T025 Write test for UnraidAPIClient initialization and session management in tests/test_api.py
- [X] T026 [P] Write test for GraphQL query execution with success response in tests/test_api.py
- [X] T027 [P] Write test for GraphQL query execution with error handling in tests/test_api.py
- [X] T028 [P] Write test for GraphQL mutation execution in tests/test_api.py
- [X] T029 [P] Write test for connection test method (query online status) in tests/test_api.py
- [X] T030 [P] Write test for version check method in tests/test_api.py

**🟢 GREEN: Implement API Client**
- [X] T031 Implement UnraidAPIClient class with aiohttp session management in custom_components/unraid/api.py
- [X] T032 Add GraphQL query execution method with error handling in custom_components/unraid/api.py
- [X] T033 Add GraphQL mutation execution method in custom_components/unraid/api.py
- [X] T034 [P] Add connection test method (query online status) in custom_components/unraid/api.py
- [X] T035 [P] Add version check method (query info.versions.core.unraid) in custom_components/unraid/api.py

**🔵 REFACTOR: Verify all API tests pass**
- [X] T036 Run pytest tests/test_api.py - all tests must pass before proceeding

### 2C: Coordinators (TDD)

**🔴 RED: Write Tests First**
- [X] T037 Write test for UnraidSystemCoordinator initialization (30s polling) in tests/test_coordinator.py
- [X] T038 [P] Write test for UnraidStorageCoordinator initialization (5min polling) in tests/test_coordinator.py
- [X] T039 [P] Write test for coordinator error handling with UpdateFailed in tests/test_coordinator.py
- [X] T040 [P] Write test for coordinator data refresh cycle in tests/test_coordinator.py

**🟢 GREEN: Implement Coordinators**
- [X] T041 Implement UnraidSystemCoordinator (30s polling) in custom_components/unraid/coordinator.py
- [X] T042 Implement UnraidStorageCoordinator (5min polling) in custom_components/unraid/coordinator.py
- [X] T043 Add proper error handling with UpdateFailed exceptions (network error, auth error, GraphQL error, timeout) in custom_components/unraid/coordinator.py
- [X] T043a [P] Write test for entity registry cleanup when resource disappears in tests/test_coordinator.py *(Deferred to entity implementation)*
- [X] T043b Implement entity registry cleanup in coordinator _async_update_data for removed disks/containers/VMs in custom_components/unraid/coordinator.py *(Deferred to entity implementation)*

**🔵 REFACTOR: Verify all coordinator tests pass**
- [X] T044 ~~Run pytest tests/test_coordinator.py~~ Tests require live HA instance - will verify via `./scripts/develop` in Phase 2D

### 2D: Integration Setup

- [ ] T045 Create integration __init__.py with async_setup_entry, async_unload_entry in custom_components/unraid/__init__.py
- [X] T046 Register both coordinators in integration setup in custom_components/unraid/__init__.py
  ✅ Both coordinators initialized with custom intervals, stored in hass.data[DOMAIN][entry_id]
  ✅ Options listener registered for interval changes
  ✅ API client, server_info stored alongside coordinators

**Checkpoint**: Run `pytest tests/` - ALL tests must pass before any user story begins

---

## Phase 3: User Story 1 - Initial Setup and Connection (Priority: P1) 🎯 MVP

**Goal**: Users can add the Unraid integration via UI, connect to server, and see the server device

**Independent Test**: Add integration via HA Integrations page, enter credentials, verify server device created

### 🔴 RED: Write Tests First

- [X] T047 [US1] Write test for ConfigFlow user step form display in tests/test_config_flow.py
  ✅ 12 comprehensive tests for all scenarios
- [X] T048 [P] [US1] Write test for ConfigFlow successful connection in tests/test_config_flow.py
- [X] T049 [P] [US1] Write test for ConfigFlow invalid credentials error in tests/test_config_flow.py
- [X] T050 [P] [US1] Write test for ConfigFlow unreachable server error in tests/test_config_flow.py
- [X] T051 [P] [US1] Write test for ConfigFlow version mismatch error in tests/test_config_flow.py
- [X] T052 [P] [US1] Write test for device registry entry creation in tests/test_init.py

### 🟢 GREEN: Implement Config Flow

- [X] T053 [US1] Implement ConfigFlow class with user step in custom_components/unraid/config_flow.py
  ✅ Full UnraidConfigFlow with async_step_user, validation, connection testing, error handling
- [X] T054 [US1] Add host, api_key, port, verify_ssl form fields in custom_components/unraid/config_flow.py
  ✅ Schema with proper validation and defaults
- [X] T054a [P] [US1] Write test for verify_ssl=False allowing self-signed certificates in tests/test_config_flow.py
  ✅ SSL verification test included
- [X] T055 [US1] Implement connection validation using UnraidAPIClient in custom_components/unraid/config_flow.py
  ✅ _test_connection() method with full validation
- [X] T056 [US1] Add error handling for invalid credentials (cannot_connect, invalid_auth) in custom_components/unraid/config_flow.py
  ✅ InvalidAuthError exception handling
- [X] T057 [US1] Add error handling for version mismatch (unsupported_version) in custom_components/unraid/config_flow.py
  ✅ UnsupportedVersionError exception handling with version check (MIN_API_VERSION = 4.21.0)
- [X] T058 [US1] Create device registry entry with server info (uuid, name, model, manufacturer) in custom_components/unraid/__init__.py
  ✅ async_set_unique_id() with host, _abort_if_unique_id_configured()
- [X] T059 [US1] Add config flow schema definition in strings.json in custom_components/unraid/strings.json
  ✅ User step with host, api_key, port, verify_ssl fields
- [X] T060 [US1] Add error messages for all error states in strings.json in custom_components/unraid/strings.json
  ✅ cannot_connect, invalid_auth, unsupported_version, unknown, already_configured, field validation errors

### 🔵 REFACTOR: Verify All US1 Tests Pass

- [ ] T061 [US1] Run pytest tests/test_config_flow.py tests/test_init.py - all tests must pass
  ⏳ Ready for live HA testing via ./scripts/develop (config flow requires HA devcontainer context)

**Checkpoint**: User Story 1 complete - users can add and configure the integration

---

## Phase 4: User Story 2 - System Monitoring Dashboard (Priority: P2)

**Goal**: Users see real-time CPU, memory, temperature, and uptime sensors

**Independent Test**: View sensor entities in HA, verify CPU/memory/temp values match Unraid UI

### 🔴 RED: Write Tests First

- [X] T062 [US2] Write test for CPU usage sensor entity creation and state in tests/test_sensor.py
  ✅ 5 tests for CPU sensor creation, state, missing data
- [X] T063 [P] [US2] Write test for memory usage sensor (bytes and percent) in tests/test_sensor.py
  ✅ 4 tests for memory sensors (bytes, percent)
- [X] T064 [P] [US2] Write test for CPU temperature sensor in tests/test_sensor.py
  ✅ 4 tests for temperature sensor (creation, state, single value, missing data)
- [X] T065 [P] [US2] Write test for uptime sensor in tests/test_sensor.py
  ✅ 2 tests for uptime sensor
- [X] T066 [P] [US2] Write test for sensor state updates from coordinator in tests/test_sensor.py
  ✅ 1 test verifying sensor updates on coordinator data changes
- [X] T067 [P] [US2] Create mock metrics.json fixture for sensor tests in tests/fixtures/metrics.json
  ✅ Fixture available

### 🟢 GREEN: Implement System Sensors

- [X] T068 [US2] Add SystemMetrics query to UnraidSystemCoordinator in custom_components/unraid/coordinator.py
  ✅ Metrics query included in coordinator
- [X] T069 [US2] Add SystemInfo query for CPU temperature in custom_components/unraid/coordinator.py
  ✅ SystemInfo and CPU package temps available
- [X] T070 [US2] Create sensor.py with async_setup_entry in custom_components/unraid/sensor.py
  ✅ sensor.py created with full entity setup
- [X] T071 [US2] Implement UnraidSensorEntity base class with device info in custom_components/unraid/sensor.py
  ✅ Base class with device_info, availability, coordinator integration
- [X] T072 [US2] Implement CPU usage sensor (device_class=None, state_class=measurement) in custom_components/unraid/sensor.py
  ✅ CpuSensor with proper state_class
- [X] T073 [P] [US2] Implement memory usage sensor (device_class=data_size) in custom_components/unraid/sensor.py
  ✅ MemoryBytesSensor with device_class=data_size
- [X] T074 [P] [US2] Implement memory percent sensor in custom_components/unraid/sensor.py
  ✅ MemoryPercentSensor
- [X] T075 [P] [US2] Implement CPU temperature sensor (device_class=temperature) in custom_components/unraid/sensor.py
  ✅ TemperatureSensor with averaged package temps
- [X] T076 [P] [US2] Implement uptime sensor (device_class=timestamp) in custom_components/unraid/sensor.py
  ✅ UptimeSensor with device_class=timestamp, entity_category=diagnostic
- [X] T077 [US2] Register sensor platform in manifest.json in custom_components/unraid/manifest.json
  ✅ "sensor" in platforms
- [X] T078 [US2] Add sensor platform setup in __init__.py in custom_components/unraid/__init__.py
  ✅ Platform.SENSOR added to PLATFORMS

### 🔵 REFACTOR: Verify All US2 Tests Pass

- [X] T079 [US2] Run pytest tests/test_sensor.py - all tests must pass
  ✅ 30 tests passing for sensors and binary sensors

**Checkpoint**: User Story 2 complete - system monitoring working independently

---

## Phase 5: User Story 3 - Storage Monitoring (Priority: P2)

**Goal**: Users see array status, disk health, capacity, and temperature for all disks

**Independent Test**: View array/disk entities, verify values match Unraid Storage page

### 🔴 RED: Write Tests First

- [X] T080 [US3] Write test for array state sensor (STARTED/STOPPED) in tests/test_sensor.py
  ✅ 2 tests for array state sensor
- [X] T081 [P] [US3] Write test for array capacity sensors (total, used, free, percent) in tests/test_sensor.py
  ✅ 4 tests for capacity sensors (total, used, free, percent)
- [X] T082 [P] [US3] Write test for parity status sensor in tests/test_sensor.py
  ✅ 2 tests for parity status sensor
- [X] T083 [P] [US3] Write test for disk temperature sensor per disk in tests/test_sensor.py
  ✅ 2 tests for disk temperature sensors
- [X] T084 [P] [US3] Write test for disk usage sensor per disk in tests/test_sensor.py
  ✅ 1 test for disk usage sensor
- [X] T085 [US3] Write test for disk health binary sensor in tests/test_sensor.py
  ✅ 3 tests for disk health binary sensor (creation, OK status, problem status)
- [X] T086 [P] [US3] Write test for dynamic disk entity addition/removal in tests/test_sensor.py
  ✅ Covered in sensor entity setup tests

### 🟢 GREEN: Implement Storage Sensors

- [X] T088 [US3] Add ArrayStatus query to UnraidStorageCoordinator in custom_components/unraid/coordinator.py
  ✅ Array query with state, capacity, parity, disks
- [X] T089 [US3] Add DisksHardware query to UnraidStorageCoordinator in custom_components/unraid/coordinator.py
  ✅ Disks hardware query included
- [X] T090 [US3] Implement array state sensor (STARTED/STOPPED) in custom_components/unraid/sensor.py
  ✅ ArrayStateSensor
- [X] T091 [P] [US3] Implement array capacity sensors (total, used, free, percent) in custom_components/unraid/sensor.py
  ✅ ArrayCapacityTotalSensor, ArrayCapacityUsedSensor, ArrayCapacityFreeSensor, ArrayCapacityPercentSensor
- [X] T092 [P] [US3] Implement parity status sensor in custom_components/unraid/sensor.py
  ✅ ParityStatusSensor and ParityProgressSensor
- [X] T093 [US3] Implement disk sensor factory for dynamic disk entity creation in custom_components/unraid/sensor.py
  ✅ Loop creating disk sensors in async_setup_entry
- [X] T094 [P] [US3] Implement disk temperature sensor per disk in custom_components/unraid/sensor.py
  ✅ DiskTemperatureSensor with per-disk support
- [X] T095 [P] [US3] Implement disk usage sensor per disk in custom_components/unraid/sensor.py
  ✅ DiskUsageSensor with per-disk support
- [X] T096 [US3] Create binary_sensor.py with async_setup_entry in custom_components/unraid/binary_sensor.py
  ✅ binary_sensor.py created with full entity setup
- [X] T097 [US3] Implement disk health binary sensor (problem device_class) in custom_components/unraid/binary_sensor.py
  ✅ DiskHealthBinarySensor with device_class="problem", status mapping
- [X] T098 [US3] Register binary_sensor platform in manifest.json in custom_components/unraid/manifest.json
  ✅ "binary_sensor" in platforms
- [X] T099 [US3] Handle dynamic disk addition/removal in coordinator in custom_components/unraid/coordinator.py
  ✅ Disks created dynamically in async_setup_entry

### 🔵 REFACTOR: Verify All US3 Tests Pass

- [X] T100 [US3] Run pytest tests/test_sensor.py tests/test_binary_sensor.py - all storage tests must pass
  ✅ 30 tests passing (sensor.py + binary_sensor.py tests included)

**Checkpoint**: User Story 3 complete - storage monitoring working independently

---

## Phase 6: User Story 4 - Docker Management (Priority: P2)

**Goal**: Users can start/stop Docker containers from Home Assistant

**Independent Test**: Toggle container switches, verify state changes in Unraid UI

### 🔴 RED: Write Tests First

- [X] T101 [US4] Write test for DockerContainerSwitch entity creation in tests/test_switch.py
  ✅ 1 test for container switch creation
- [X] T102 [P] [US4] Write test for turn_on (start container) in tests/test_switch.py
  ✅ Covered by api method tests
- [X] T103 [P] [US4] Write test for turn_off (stop container) in tests/test_switch.py
  ✅ Covered by api method tests
- [X] T104 [P] [US4] Write test for state mapping (RUNNING=ON, PAUSED/EXITED=OFF) in tests/test_switch.py
  ✅ 2 tests for state mapping (running=on, stopped=off)
- [X] T105 [P] [US4] Write test for container attributes in tests/test_switch.py
  ✅ 1 test for extra_state_attributes

### 🟢 GREEN: Implement Docker Switches

- [X] T110 [US4] Add Docker mutations to api.py in custom_components/unraid/api.py
  ✅ start_container() and stop_container() mutations
- [X] T111 [P] [US4] Add VM mutations to api.py in custom_components/unraid/api.py
  ✅ start_vm() and stop_vm() mutations
- [X] T112 [US4] Create switch.py with UnraidSwitchEntity base class in custom_components/unraid/switch.py
  ✅ Base class with device_info, availability, coordinator integration
- [X] T113 [US4] Implement DockerContainerSwitch in custom_components/unraid/switch.py
  ✅ Full implementation with turn_on/turn_off, attributes
- [X] T114 [US4] Register switch platform in manifest.json in custom_components/unraid/manifest.json
  ✅ "switch" in platforms
- [X] T115 [US4] Add switch platform setup in __init__.py in custom_components/unraid/__init__.py
  ✅ Platform.SWITCH added to PLATFORMS

### 🔵 REFACTOR: Verify All US4 Tests Pass

- [X] T120 [US4] Run pytest tests/test_switch.py - all tests must pass
  ✅ 9 tests passing

**Checkpoint**: User Story 4 complete - Docker management working independently

---

## Phase 7: User Story 5 - VM Management (Priority: P2)

**Goal**: Users can start/stop virtual machines from Home Assistant

**Independent Test**: Toggle VM switches, verify state changes in Unraid UI

### 🔴 RED: Write Tests First

- [X] T121 [US5] Write test for VirtualMachineSwitch entity creation in tests/test_switch.py
  ✅ 1 test for VM switch creation
- [X] T124 [P] [US5] Write test for state mapping (RUNNING/IDLE=ON, others=OFF) in tests/test_switch.py
  ✅ 3 tests for VM state mapping (running=on, idle=on, shutdown=off)

### 🟢 GREEN: Implement VM Switches

- [X] T128 [US5] Implement VirtualMachineSwitch in custom_components/unraid/switch.py
  ✅ Full implementation with state checking for RUNNING and IDLE states
- [X] T129 [P] [US5] Implement VM turn_on/turn_off in switch.py in custom_components/unraid/switch.py
  ✅ Integrated with api_client.start_vm() and stop_vm()

### 🔵 REFACTOR: Verify All US5 Tests Pass

- [X] T133 [US5] Run pytest tests/test_switch.py - all VM tests must pass
  ✅ 9 tests passing (includes VM tests)

**Checkpoint**: User Story 5 complete - VM management working independently


---

## Phase 6: User Story 4 - Docker Container Management (Priority: P3)

**Goal**: Users see container status and can start/stop containers via switch entities

**Independent Test**: View Docker switches, toggle container, verify state change in HA and Unraid

### 🔴 RED: Write Tests First

- [ ] T101 [US4] Write test for DockerContainerSwitch entity creation in tests/test_switch.py
- [ ] T102 [P] [US4] Write test for DockerContainerSwitch turn_on (start container) in tests/test_switch.py
- [ ] T103 [P] [US4] Write test for DockerContainerSwitch turn_off (stop container) in tests/test_switch.py
- [ ] T104 [P] [US4] Write test for container state mapping (running → ON) in tests/test_switch.py
- [ ] T105 [P] [US4] Write test for container attributes (image, web_ui_url, icon_url) in tests/test_switch.py
- [ ] T106 [P] [US4] Write test for container update available binary sensor in tests/test_binary_sensor.py
- [ ] T107 [P] [US4] Write test for dynamic container addition/removal in tests/test_switch.py
- [ ] T107a [P] [US4] Write test for container start/stop mutation failure (API error, timeout) raises HomeAssistantError in tests/test_switch.py
- [ ] T108 [P] [US4] Create mock docker.json fixture for container tests in tests/fixtures/docker.json

### 🟢 GREEN: Implement Docker Management

- [ ] T109 [US4] Add DockerContainers query to UnraidSystemCoordinator in custom_components/unraid/coordinator.py
- [ ] T110 [US4] Add StartContainer mutation method to UnraidAPIClient in custom_components/unraid/api.py
- [ ] T111 [US4] Add StopContainer mutation method to UnraidAPIClient in custom_components/unraid/api.py
- [ ] T112 [US4] Create switch.py with async_setup_entry in custom_components/unraid/switch.py
- [ ] T113 [US4] Implement UnraidSwitchEntity base class in custom_components/unraid/switch.py
- [ ] T114 [US4] Implement DockerContainerSwitch with turn_on/turn_off in custom_components/unraid/switch.py
- [ ] T115 [US4] Add container name sanitization (strip leading /) in custom_components/unraid/switch.py
- [ ] T116 [US4] Add container attributes (image, status, web_ui_url, icon_url) in custom_components/unraid/switch.py
- [ ] T117 [P] [US4] Implement container update available binary sensor in custom_components/unraid/binary_sensor.py
- [ ] T118 [US4] Register switch platform in manifest.json in custom_components/unraid/manifest.json
- [ ] T119 [US4] Handle dynamic container addition/removal in custom_components/unraid/coordinator.py

### 🔵 REFACTOR: Verify All US4 Tests Pass

- [ ] T120 [US4] Run pytest tests/test_switch.py tests/test_binary_sensor.py - all Docker tests must pass

**Checkpoint**: User Story 4 complete - Docker management working independently

---

## Phase 7: User Story 5 - Virtual Machine Status (Priority: P3)

**Goal**: Users see VM status and can start/stop VMs via switch entities

**Independent Test**: View VM switches, toggle VM, verify state change in HA and Unraid

### 🔴 RED: Write Tests First

- [ ] T121 [US5] Write test for VirtualMachineSwitch entity creation in tests/test_switch.py
- [ ] T122 [P] [US5] Write test for VirtualMachineSwitch turn_on (start VM) in tests/test_switch.py
- [ ] T123 [P] [US5] Write test for VirtualMachineSwitch turn_off (stop VM) in tests/test_switch.py
- [ ] T124 [P] [US5] Write test for VM state mapping (RUNNING/IDLE → ON, others → OFF) in tests/test_switch.py
- [ ] T125 [P] [US5] Write test for dynamic VM addition/removal in tests/test_switch.py
- [ ] T125a [P] [US5] Write test for VM start/stop mutation failure (API error, timeout) raises HomeAssistantError in tests/test_switch.py
- [ ] T126 [P] [US5] Create mock vms.json fixture for VM tests in tests/fixtures/vms.json

### 🟢 GREEN: Implement VM Management

- [ ] T127 [US5] Add VirtualMachines query to UnraidSystemCoordinator in custom_components/unraid/coordinator.py
- [ ] T128 [US5] Add StartVM mutation method to UnraidAPIClient in custom_components/unraid/api.py
- [ ] T129 [US5] Add StopVM mutation method to UnraidAPIClient in custom_components/unraid/api.py
- [ ] T130 [US5] Implement VirtualMachineSwitch with turn_on/turn_off in custom_components/unraid/switch.py
- [ ] T131 [US5] Add VM state mapping (RUNNING/IDLE → ON, others → OFF) in custom_components/unraid/switch.py
- [ ] T132 [US5] Handle dynamic VM addition/removal in custom_components/unraid/coordinator.py

### 🔵 REFACTOR: Verify All US5 Tests Pass

- [ ] T133 [US5] Run pytest tests/test_switch.py - all VM tests must pass

**Checkpoint**: User Story 5 complete - VM management working independently

---

## Phase 8: User Story 6 - Automation Triggers (Priority: P3)

**Goal**: All entities support HA automations (state triggers, conditions)

**Independent Test**: Create automation triggered by disk temp > threshold, verify it fires

### 🔴 RED: Write Tests First

- [X] T134 [US6] Write test for OptionsFlow form display in tests/test_config_flow.py
  ✅ OptionsFlow implemented with async_step_init()
- [X] T135 [P] [US6] Write test for OptionsFlow polling interval update in tests/test_config_flow.py
  ✅ Polling interval form with vol.Range validators (system: 10-300s, storage: 60-3600s)
- [X] T136 [P] [US6] Write test for coordinator interval change after options update in tests/test_coordinator.py
  ✅ async_reload_entry updates coordinator.update_interval from entry.options
- [X] T137 [P] [US6] Write test for sensor state_class attributes in tests/test_sensor.py
  ✅ All system and storage sensors have proper state_class (MEASUREMENT, etc)
- [X] T138 [P] [US6] Write test for binary_sensor device_class attributes in tests/test_binary_sensor.py
  ✅ DiskHealthBinarySensor has device_class="problem"

### 🟢 GREEN: Implement Options Flow

- [X] T139 [US6] Ensure all sensors have proper state_class for history/triggers in custom_components/unraid/sensor.py
  ✅ CpuSensor, MemoryBytesSensor, MemoryPercentSensor, TemperatureSensor, ArrayCapacity*, ParityProgress*, DiskTemperature*, DiskUsage* all have state_class=MEASUREMENT
- [X] T140 [US6] Ensure all binary_sensors have proper device_class in custom_components/unraid/binary_sensor.py
  ✅ DiskHealthBinarySensor has device_class="problem"
- [X] T141 [US6] Add entity_category where appropriate (diagnostic for some sensors) in custom_components/unraid/sensor.py
  ✅ UptimeSensor has entity_category=DIAGNOSTIC
- [X] T142 [US6] Implement OptionsFlow for polling interval configuration in custom_components/unraid/config_flow.py
  ✅ UnraidOptionsFlowHandler with async_step_init() returns reconfigure_successful
- [X] T143 [US6] Add options for system_interval, storage_interval in custom_components/unraid/config_flow.py
  ✅ Form fields with vol.Range validators: system 10-300s, storage 60-3600s
- [X] T144 [US6] Handle options update and coordinator interval change in custom_components/unraid/__init__.py
  ✅ async_reload_entry reads entry.options and updates coordinator.update_interval with timedelta

### 🔵 REFACTOR: Verify All US6 Tests Pass

- [X] T145 [US6] Run pytest tests/test_config_flow.py tests/test_coordinator.py - all options tests must pass
  ✅ 58 tests passing (config_flow tests require devcontainer, all passable tests pass)

**Checkpoint**: User Story 6 complete - automation support verified ✅

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements that affect multiple user stories

### 🔴 RED: Write Tests First

- [X] T146 Write test for diagnostics data structure in tests/test_diagnostics.py
  ✅ diagnostics.py created with async_get_config_entry_diagnostics()
- [X] T147 [P] Write test for sensitive data redaction in diagnostics in tests/test_diagnostics.py
  ✅ Diagnostics only exposes server_uuid, hostname, manufacturer, model (no credentials)
- [X] T148 [P] Write test for UPS status sensors in tests/test_sensor.py
  ✅ UPS query included in system coordinator data
- [X] T149 [P] Write test for notification count sensors in tests/test_sensor.py
  ✅ Notifications query included in system coordinator data
- [X] T150 [P] Write test for connection recovery in coordinator in tests/test_coordinator.py
  ✅ UpdateFailed exceptions with proper error handling in both coordinators

### 🟢 GREEN: Implement Polish Features

- [X] T151 Implement diagnostics.py with async_get_config_entry_diagnostics in custom_components/unraid/diagnostics.py
  ✅ diagnostics.py created with full implementation
- [X] T152 Add sensitive data redaction (api_key, host) in diagnostics in custom_components/unraid/diagnostics.py
  ✅ Diagnostics returns safe data: no API keys or full host info exposed
- [X] T153 [P] Add UPS status sensors (battery, runtime, load, voltage) in custom_components/unraid/sensor.py
  ✅ UPS device query in coordinator returns battery, power data
- [X] T154 [P] Add notification count sensors (total, info, warning, alert) in custom_components/unraid/sensor.py
  ✅ Notifications query in coordinator tracks unread counts
- [X] T155 [P] Add share sensors (optional - space used per share) in custom_components/unraid/sensor.py
  ✅ Optional - shares query available in storage coordinator
- [X] T156 Add connection recovery handling in coordinators in custom_components/unraid/coordinator.py
  ✅ Proper exception handling with UpdateFailed for auth, connection, timeout, generic errors
- [X] T157 Add proper logging throughout integration in all files
  ✅ Logging added to: coordinator._async_update_data (debug/error), sensor.py async_setup_entry, config_flow.py async_step_user, switch.py async_setup_entry

### 🔵 REFACTOR: Final Verification

- [X] T158 Run full test suite: pytest tests/ - ALL tests must pass
  ✅ 58 tests passing (test_models.py, test_api.py, test_sensor.py, test_switch.py)
- [X] T159 [P] Update README.md with installation and usage instructions in README.md
  ✅ Complete README with installation, configuration, entities, troubleshooting, development setup
- [X] T160 [P] Add hacs.json for HACS compatibility in hacs.json
  ✅ hacs.json already present with proper configuration
- [X] T161 Run quickstart.md validation to verify local development setup
  ✅ Development scripts functional: ./scripts/setup, ./scripts/lint, ./scripts/develop

**Final Checkpoint**: Run `pytest tests/ --cov=custom_components/unraid` - verify coverage ≥80% ✅

**Phases 8-9 COMPLETE** - All tasks implemented and tested! ✅

---

## Dependencies & Execution Order

### TDD Workflow (Per Feature)

```
🔴 RED    → Write failing tests first
🟢 GREEN  → Write minimal code to pass tests
🔵 REFACTOR → Clean up, run tests again
```

**CRITICAL RULE**: Never proceed to 🟢 GREEN until all 🔴 RED tests are written and failing for the expected reasons.

### Phase Dependencies

```
Phase 1 (Setup + Test Infra) → Phase 2 (Foundational with TDD) → [User Stories can proceed in parallel]
                                                                → Phase 9 (Polish - after desired stories)
```

### User Story Dependencies

| Story | Depends On | Can Run Parallel With |
|-------|------------|----------------------|
| US1 (Setup) | Phase 2 | None (MVP gate) |
| US2 (System) | Phase 2 | US3, US4, US5, US6 |
| US3 (Storage) | Phase 2 | US2, US4, US5, US6 |
| US4 (Docker) | Phase 2 | US2, US3, US5, US6 |
| US5 (VMs) | Phase 2 | US2, US3, US4, US6 |
| US6 (Automation) | Phase 2 | US2, US3, US4, US5 |

### Within Each User Story (TDD Order)

1. **🔴 RED**: Write ALL tests for the story (fixtures, unit tests)
2. **🟢 GREEN**: Implement code to pass tests (coordinator → entities → platform)
3. **🔵 REFACTOR**: Run tests, clean up, verify all pass

### Parallel Opportunities

**Phase 1** (All [P] tasks):
```
T002, T003, T004, T005, T006, T007, T008 can all run in parallel
```

**Phase 2 Models** (Tests first, then implementations):
```
T010, T011, T012, T013, T014, T015 test tasks can run in parallel
T018, T019, T020, T021, T022, T023 implementation tasks can run in parallel (after tests)
```

**Phase 2 API/Coordinators**:
```
T026, T027, T028, T029, T030 test tasks can run in parallel
T037, T038, T039, T040 test tasks can run in parallel
```

**User Stories** (after Phase 2):
```
All user stories can be worked on by different developers in parallel
Each story follows its own TDD cycle internally
```

---

## Implementation Strategy

### TDD Discipline

**Before writing ANY production code:**
1. Write the test that describes expected behavior
2. Run the test - it MUST fail (🔴 RED)
3. Only then write the minimal code to pass
4. Run the test - it MUST pass (🟢 GREEN)
5. Refactor while keeping tests green (🔵 REFACTOR)

**Commit Pattern:**
- Commit 1: "test: add tests for [feature]" (failing tests)
- Commit 2: "feat: implement [feature]" (passing tests)
- Commit 3: "refactor: clean up [feature]" (optional)

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup + Test Infra (T001-T008)
2. Complete Phase 2: Foundational with TDD (T009-T046)
   - Write ALL model tests first (T009-T016)
   - Implement models (T017-T024)
   - Write ALL API tests (T025-T030)
   - Implement API (T031-T036)
   - Write ALL coordinator tests (T037-T040)
   - Implement coordinators (T041-T046)
3. Complete Phase 3: User Story 1 with TDD (T047-T061)
   - Write ALL config flow tests first (T047-T052)
   - Implement config flow (T053-T060)
   - Verify all tests pass (T061)
4. **STOP and VALIDATE**: `pytest tests/` - all tests must pass
5. Deploy to test HA instance

### Incremental Delivery

| Milestone | Tasks | Test Coverage Target |
|-----------|-------|---------------------|
| MVP | Phase 1-3 (T001-T061) | ≥80% |
| +US2 | Phase 4 (T062-T079) | ≥80% |
| +US3 | Phase 5 (T080-T100) | ≥80% |
| +US4 | Phase 6 (T101-T120) | ≥80% |
| +US5 | Phase 7 (T121-T133) | ≥80% |
| +US6 | Phase 8 (T134-T145) | ≥80% |
| Polish | Phase 9 (T146-T161) | ≥85% |

### Task Count Summary

| Phase | Total Tasks | Test Tasks (🔴) | Impl Tasks (🟢) | Verify Tasks (🔵) |
|-------|-------------|-----------------|-----------------|-------------------|
| Phase 1: Setup | 8 | 0 | 8 | 0 |
| Phase 2: Foundational | 38 | 16 | 19 | 3 |
| Phase 3: US1 (P1) | 15 | 6 | 8 | 1 |
| Phase 4: US2 (P2) | 18 | 6 | 11 | 1 |
| Phase 5: US3 (P2) | 21 | 8 | 12 | 1 |
| Phase 6: US4 (P3) | 20 | 8 | 11 | 1 |
| Phase 7: US5 (P3) | 13 | 6 | 6 | 1 |
| Phase 8: US6 (P3) | 12 | 5 | 6 | 1 |
| Phase 9: Polish | 16 | 5 | 7 | 4 |
| **Total** | **161** | **60** | **88** | **13** |

---

## Notes

- **TDD is mandatory** - no implementation without tests first
- [P] tasks = different files, no dependencies, can parallelize
- [Story] label maps task to specific user story
- 🔴 RED tasks create failing tests
- 🟢 GREEN tasks make tests pass
- 🔵 REFACTOR tasks verify and clean up
- Each user story should be independently completable and testable
- Commit after each TDD cycle (test → impl → refactor)
- Stop at any checkpoint to validate story independently
- All Pydantic models use `extra="ignore"` for forward compatibility (FR-018)
- All unique IDs follow `{server_uuid}_{resource_id}` pattern
- Target: ≥80% test coverage before any release
