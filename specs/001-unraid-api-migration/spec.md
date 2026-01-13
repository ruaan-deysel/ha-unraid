# Feature Specification: Migrate to unraid-api Python Library

**Feature Branch**: `001-unraid-api-migration`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Migrate the current code to fully and completely use the unraid-api 1.3.1 and get rid of api.py and models.py. Its HA best practise to use python library and not let HA handle any data wrangling. All graphql must be removed from the code and just make use of the unraid-api python library."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Transparent Migration for Existing Users (Priority: P1)

As an existing ha-unraid user, when I upgrade to the new version, my integration continues to work seamlessly without any reconfiguration. All my existing sensors, switches, and buttons maintain their entity IDs and historical data.

**Why this priority**: This is the most critical requirement. Existing users must not lose functionality or data when upgrading. A breaking change would cause significant user frustration and support burden.

**Independent Test**: Can be fully tested by upgrading an existing ha-unraid installation and verifying all entities remain functional with preserved history.

**Acceptance Scenarios**:

1. **Given** an existing ha-unraid installation with configured sensors and switches, **When** the user upgrades to the new version, **Then** all entities continue to report data without reconfiguration.
2. **Given** historical sensor data exists in Home Assistant, **When** the integration migrates, **Then** all historical data remains accessible and linked to the same entities.
3. **Given** user automation rules reference ha-unraid entities, **When** the migration completes, **Then** all automations continue to function without modification.

---

### User Story 2 - Complete GraphQL Removal (Priority: P1)

As a maintainer, the integration no longer contains any GraphQL queries or mutations within the codebase. All Unraid server communication is handled exclusively through the unraid-api Python library's typed methods.

**Why this priority**: This is the core technical objective. Removing GraphQL from the integration aligns with Home Assistant best practices and eliminates duplication between the integration and the library.

**Independent Test**: Can be fully tested by code review confirming no GraphQL strings exist in the integration codebase and all API calls use library methods.

**Acceptance Scenarios**:

1. **Given** the migrated codebase, **When** searching for GraphQL query strings, **Then** zero results are found in custom_components/unraid/.
2. **Given** any coordinator data fetch operation, **When** examining the code path, **Then** only unraid-api library methods are used for data retrieval.
3. **Given** any entity control operation (start/stop container, VM, etc.), **When** examining the code path, **Then** only unraid-api library methods are used for mutations.

---

### User Story 3 - Remove Custom API and Model Files (Priority: P2)

As a maintainer, the files api.py and models.py are completely removed from the integration codebase. All data models come from the unraid-api library.

**Why this priority**: This is a key deliverable that reduces code duplication and maintenance burden. However, it depends on P1 work being completed first.

**Independent Test**: Can be fully tested by verifying api.py and models.py do not exist in the codebase and all imports reference unraid_api library models.

**Acceptance Scenarios**:

1. **Given** the migrated codebase, **When** checking for api.py in custom_components/unraid/, **Then** the file does not exist.
2. **Given** the migrated codebase, **When** checking for models.py in custom_components/unraid/, **Then** the file does not exist.
3. **Given** any Python file in the integration, **When** examining import statements, **Then** all data models are imported from unraid_api, not local modules.

---

### User Story 4 - Session Injection for Home Assistant Compatibility (Priority: P2)

As a Home Assistant developer, the integration properly uses Home Assistant's aiohttp session management by injecting the HA session into the unraid-api client. This ensures proper connection pooling and SSL handling.

**Why this priority**: Critical for Home Assistant integration quality and connection management, but the library already supports this pattern.

**Independent Test**: Can be fully tested by verifying the async_get_clientsession() session is passed to UnraidClient during initialization.

**Acceptance Scenarios**:

1. **Given** the integration initialization code, **When** creating the UnraidClient, **Then** Home Assistant's async_get_clientsession() is passed as the session parameter.
2. **Given** SSL verification settings from config entry, **When** creating the client session, **Then** the verify_ssl setting is respected.
3. **Given** the integration unloads, **When** cleanup occurs, **Then** the client is properly closed without affecting the shared HA session.

---

### User Story 5 - Exception Handling Alignment (Priority: P3)

As a developer, error handling uses the exception classes from the unraid-api library (UnraidAuthenticationError, UnraidConnectionError, UnraidTimeoutError, UnraidAPIError) instead of custom exceptions.

**Why this priority**: Improves consistency and error handling but is primarily an internal quality improvement.

**Independent Test**: Can be fully tested by examining exception handling code and confirming library exceptions are caught and handled appropriately.

**Acceptance Scenarios**:

1. **Given** an authentication failure occurs, **When** the error is caught, **Then** UnraidAuthenticationError from unraid_api is used.
2. **Given** a connection failure occurs, **When** the error is caught, **Then** UnraidConnectionError from unraid_api is used.
3. **Given** an API error response, **When** the error is caught, **Then** UnraidAPIError from unraid_api is used.

---

### User Story 6 - Update Test Suite (Priority: P3)

As a developer, the test suite is updated to work with the new library-based implementation, removing tests for deleted files and updating mocks to use library classes.

**Why this priority**: Important for code quality but follows naturally from the main migration work.

**Independent Test**: Can be fully tested by running the full test suite and confirming all tests pass.

**Acceptance Scenarios**:

1. **Given** tests/test_api.py exists, **When** the migration completes, **Then** this file is removed.
2. **Given** tests/test_models.py exists, **When** the migration completes, **Then** this file is removed or updated to test library model usage.
3. **Given** the complete test suite, **When** pytest runs, **Then** all tests pass with the new implementation.

---

### Edge Cases

- What happens when the unraid-api library returns None for optional fields? The integration must handle null/missing data gracefully, using library models' default values.
- How does the system handle library version mismatches? The integration specifies minimum library version (>=1.3.1) in manifest.json requirements.
- What happens if the library's Pydantic model structure changes in future versions? Forward compatibility is maintained by the library's use of ConfigDict(extra="ignore").
- How are optional features handled (Docker disabled, no VMs, no UPS)? Each optional query fails gracefully without affecting core functionality, matching current behavior.
- What happens if the server is unreachable during coordinator refresh? Existing retry and error handling patterns are maintained using library exceptions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use UnraidClient from unraid-api library for all server communication
- **FR-002**: System MUST NOT contain any GraphQL query or mutation strings in the integration code
- **FR-003**: System MUST remove api.py file from custom_components/unraid/
- **FR-004**: System MUST remove models.py file from custom_components/unraid/
- **FR-005**: System MUST import all Pydantic models from unraid_api.models
- **FR-006**: System MUST inject Home Assistant's aiohttp ClientSession into UnraidClient
- **FR-007**: System MUST use library's typed methods (typed_get_array, typed_get_containers, etc.) where available
- **FR-008**: System MUST preserve all existing entity unique_ids for backwards compatibility
- **FR-009**: System MUST use library exception classes for error handling
- **FR-010**: System MUST specify unraid-api>=1.3.1 as a dependency in manifest.json
- **FR-011**: System MUST handle optional features (Docker, VMs, UPS) gracefully when disabled or unavailable
- **FR-012**: System MUST maintain current polling intervals and coordinator patterns
- **FR-013**: System MUST update imports across all entity files (sensor.py, switch.py, button.py, binary_sensor.py)
- **FR-014**: System MUST update coordinator.py to use library's typed methods instead of raw queries
- **FR-015**: System MUST update config_flow.py to use library client for connection testing

### Key Entities *(include if feature involves data)*

- **UnraidClient**: The main client class from unraid-api library that handles all server communication, replacing the custom UnraidAPIClient
- **UnraidSystemCoordinator**: Data coordinator for system metrics (CPU, memory, Docker, VMs, UPS) - migrates from raw queries to typed library methods
- **UnraidStorageCoordinator**: Data coordinator for storage data (array, disks, shares) - migrates from raw queries to typed library methods
- **Library Models**: SystemMetrics, UnraidArray, ArrayDisk, DockerContainer, VmDomain, Share, UPSDevice, ParityCheck, ServerInfo, and other Pydantic models from unraid_api.models replace local models

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero GraphQL query strings exist in custom_components/unraid/ directory (verifiable by grep search for "query", "mutation", "graphql")
- **SC-002**: api.py and models.py files are removed from custom_components/unraid/ (verifiable by file system check)
- **SC-003**: All existing entity unique_ids remain unchanged (verifiable by comparing entity lists before/after migration)
- **SC-004**: 100% of tests pass after migration (verifiable by pytest execution)
- **SC-005**: Integration loads successfully with unraid-api>=1.3.1 dependency (verifiable by installation test)
- **SC-006**: All sensors report correct values matching pre-migration behavior (verifiable by functional testing)
- **SC-007**: All control operations (container start/stop, VM start/stop, array start/stop, disk spin up/down, parity check) function correctly (verifiable by functional testing)
- **SC-008**: Optional features (Docker, VMs, UPS) fail gracefully when unavailable without crashing the integration (verifiable by testing against servers with features disabled)

## Assumptions

- The unraid-api 1.3.1 library provides all necessary typed methods for the integration's current functionality (verified by library documentation review)
- The library's Pydantic models are compatible with Home Assistant's data patterns (verified: library uses Pydantic v2)
- The library's session injection pattern aligns with Home Assistant's async_get_clientsession() usage (verified: library accepts external aiohttp.ClientSession)
- The library handles SSL certificate modes (No, Yes, Strict) and myunraid.net redirects automatically (verified: documented feature)
- Existing users have Unraid servers compatible with unraid-api requirements (Unraid 7.1.4+, API 4.21.0+) - this matches current integration requirements
- Field names and structures in library models align closely enough with current models that entity attribute names can be preserved
