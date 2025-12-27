# Feature Specification: Unraid GraphQL Integration

**Feature Branch**: `001-unraid-graphql-integration`
**Created**: 2025-12-23
**Status**: Draft
**Input**: User description: "A Home Assistant custom integration that provides real-time data from the Unraid GraphQL API available on Unraid 7.2 systems. The integration uses pydantic and is called unraid."

## Clarifications

### Session 2025-12-23

- Q: What transport security and credential storage approach should be used? → A: HTTPS required; credentials stored in HA's encrypted config entry storage
- Q: How should entities be uniquely identified for stability? → A: Server UUID + resource native ID (container ID, disk serial, VM UUID)
- Q: How should the integration handle GraphQL schema changes across Unraid versions? → A: Minimum schema version check at connection; graceful degradation for unknown fields
- Q: What settings can users modify after initial setup? → A: Options flow for polling intervals only (system metrics, disk data intervals)
- Q: What is the API timeout for all operations? → A: 30 seconds for queries, 60 seconds for mutations (Docker/VM control)
- Q: How should rate limiting be handled? → A: API does not enforce rate limits; integration self-limits with polling intervals
- Q: What default port should be assumed? → A: Standard HTTPS port 443; allow user override in config flow hostname field

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initial Setup and Connection (Priority: P1)

As a Home Assistant user with an Unraid 7.2 server, I want to add the Unraid integration through the UI so that I can connect my Unraid server to Home Assistant and begin monitoring it.

**Why this priority**: Without successful connection setup, no other functionality is possible. This is the gateway to all other features.

**Independent Test**: Can be fully tested by adding the integration via Home Assistant's Integrations page, entering Unraid server credentials, and verifying a successful connection message appears.

**Acceptance Scenarios**:

1. **Given** Home Assistant is running and I have Unraid 7.2 installed, **When** I add the Unraid integration and enter my server's hostname/IP and API key, **Then** the integration successfully connects within 10 seconds and creates a device representing my Unraid server.

2. **Given** I am configuring the integration, **When** I enter invalid credentials, **Then** I receive error message ID "invalid_auth" with text "Authentication failed: Invalid API key or insufficient permissions (ADMIN role required)".

3. **Given** I am configuring the integration, **When** the server is unreachable (network error, DNS failure), **Then** I receive error message ID "cannot_connect" with text "Cannot reach server at {hostname}. Check network connection and firewall settings".

4. **Given** I am configuring the integration, **When** the server API version is too old (<4.21.0), **Then** I receive error message ID "unsupported_version" with text "Unraid version {version} is not supported. Minimum required: 7.2.0 (API v4.21.0)".

5. **Given** I have successfully configured the integration, **When** I view the integration details, **Then** I see the Unraid server listed as a device with connection status.

6. **Given** I am in the config flow, **When** I cancel setup before completing authentication, **Then** no config entry is created and no entities are left in the entity registry.

---

### User Story 2 - System Monitoring Dashboard (Priority: P2)

As a Home Assistant user, I want to see real-time system metrics from my Unraid server (CPU, RAM, temperature, uptime) so that I can monitor my server's health at a glance.

**Why this priority**: Core monitoring capability that provides immediate value after setup. Most users install this integration primarily for system monitoring.

**Independent Test**: Can be fully tested by viewing the automatically created sensor entities in Home Assistant and verifying they display current CPU usage, memory usage, temperature readings, and uptime.

**Acceptance Scenarios**:

1. **Given** the integration is connected to my Unraid server, **When** I view the Home Assistant dashboard, **Then** I see sensor entities for CPU usage percentage, RAM usage percentage, CPU temperature, and system uptime, all updating within 30 seconds of server changes.

2. **Given** the server metrics are being monitored, **When** the Unraid server's CPU usage changes by >5%, **Then** the CPU sensor in Home Assistant updates to reflect the new value within 30 seconds (default polling interval).

3. **Given** the integration is running, **When** I add the Unraid sensors to my Lovelace dashboard, **Then** they display formatted values with appropriate units (%, degrees, time) with values accurate to within 5% tolerance of Unraid WebGUI.

4. **Given** the integration is monitoring system metrics, **When** multiple Unraid servers are configured (>1), **Then** each server's metrics update independently without coordinator conflicts, maintaining <1 second response time per entity update.

---

### User Story 3 - Storage Monitoring (Priority: P2)

As a Home Assistant user, I want to monitor my Unraid array and disk health so that I can be alerted to potential storage issues before data loss occurs.

**Why this priority**: Storage health is a primary concern for Unraid users. This provides critical visibility into array status and individual disk health.

**Independent Test**: Can be fully tested by viewing storage-related entities showing array status, individual disk usage, and disk health indicators.

**Acceptance Scenarios**:

1. **Given** the integration is connected, **When** I view storage entities, **Then** I see the array status (started/stopped), total array capacity, and used space updating within 5 minutes (storage polling interval).

2. **Given** I have multiple disks in my array, **When** I view disk entities, **Then** each disk shows its capacity, used space, temperature (if available), and health status as binary_sensor.

3. **Given** a disk enters a warning state (e.g., SMART warning), **When** the integration polls for updates, **Then** the disk's health binary_sensor changes to "on" (problem detected) within 5 minutes.

4. **Given** the array has no data disks (NEW_ARRAY state), **When** storage entities are created, **Then** array sensors show 0 capacity and "new_array" state without errors.

5. **Given** I add a new disk to the array, **When** the next storage poll occurs (<5min), **Then** new disk entities appear automatically with unique IDs based on disk serial number.

6. **Given** I remove a disk from the array, **When** the next storage poll occurs, **Then** the disk's entities become unavailable and are removed from the entity registry after 24 hours of unavailability.

---

### User Story 4 - Docker Container Management (Priority: P3)

As a Home Assistant user, I want to see the status of my Docker containers and be able to start/stop them so that I can manage my containerized applications from Home Assistant.

**Why this priority**: Docker management extends the integration beyond monitoring into active control, valuable for automation but not essential for basic monitoring.

**Independent Test**: Can be fully tested by viewing Docker container entities, verifying status reflects actual container state, and using switch entities to start/stop containers.

**Acceptance Scenarios**:

1. **Given** the integration is connected and Docker containers are running on Unraid, **When** I view Docker entities, **Then** I see each container with its current status (running/stopped/paused) updating within 30 seconds.

2. **Given** a Docker container entity exists, **When** I toggle the container's switch entity to "off", **Then** the container stops within 10 seconds and the entity state updates to "off" within one polling cycle (<30s).

3. **Given** a stopped container, **When** I toggle the switch entity to "on", **Then** the container starts within 10 seconds and the entity state shows "on" within one polling cycle.

4. **Given** a Docker container switch entity, **When** a start/stop mutation fails (API error, timeout >60s, or container in invalid state), **Then** the entity state remains unchanged, an error is logged at WARNING level with mutation response details, and the user sees a persistent notification: "Failed to control container '{name}': {error_message}".

5. **Given** Docker service is disabled on Unraid, **When** the integration polls for data, **Then** no Docker container entities are created and logs show INFO message "Docker service not available on server {name}".

6. **Given** I have zero Docker containers configured, **When** storage polls occur, **Then** no container entities are created without errors.

7. **Given** a container name exceeds 255 characters, **When** entities are created, **Then** the entity friendly_name is truncated to 250 chars + "..." for display.

8. **Given** I have 50+ Docker containers, **When** all container entities update, **Then** Home Assistant memory usage remains <200MB incremental per server and entity updates complete within 3 seconds.

---

### User Story 5 - Virtual Machine Status (Priority: P3)

As a Home Assistant user, I want to see the status of my Unraid VMs so that I can monitor and control my virtual machines from Home Assistant.

**Why this priority**: VM control provides additional value for users running VMs on Unraid, extending the integration's management capabilities.

**Independent Test**: Can be fully tested by viewing VM entities, verifying status matches actual VM state, and using controls to start/stop VMs.

**Acceptance Scenarios**:

1. **Given** the integration is connected and VMs exist on Unraid, **When** I view VM entities, **Then** I see each VM with its current state (running/stopped/paused) updating within 30 seconds.

2. **Given** a running VM, **When** I use the VM control to stop it, **Then** the VM shuts down gracefully within 10 seconds and the entity reflects the stopped state within one polling cycle.

3. **Given** a VM switch entity, **When** a start/stop mutation fails (API error, timeout >60s, or VM in transitional state), **Then** the entity state remains unchanged, an error is logged at WARNING level with mutation response details, and the user sees a persistent notification: "Failed to control VM '{name}': {error_message}".

4. **Given** VM/libvirt service is disabled on Unraid, **When** the integration polls for data, **Then** no VM entities are created and logs show INFO message "VM service not available on server {name}".

5. **Given** I have zero VMs configured, **When** system polls occur, **Then** no VM entities are created without errors.

6. **Given** I have 10+ VMs, **When** all VM entities update, **Then** Home Assistant performance remains stable with <1s response time per entity update.

---

### User Story 6 - Automation Triggers (Priority: P3)

As a Home Assistant user, I want to create automations based on Unraid events and states so that I can automate responses to server conditions.

**Why this priority**: Automations unlock the full potential of Home Assistant integration, allowing users to respond to server events automatically.

**Independent Test**: Can be fully tested by creating an automation that triggers on a state change (e.g., disk temperature above threshold) and verifying the automation executes.

**Acceptance Scenarios**:

1. **Given** sensor entities exist for Unraid metrics, **When** I create an automation using these entities as triggers, **Then** the automation executes when conditions are met.

2. **Given** I want to be notified of array issues, **When** the array status changes to a problem state, **Then** Home Assistant can trigger a notification automation.

---

### Edge Cases

- What happens when the Unraid server is unreachable after initial setup? The integration marks all entities as unavailable immediately. Connection retry occurs with exponential backoff: 60s, 120s, 240s, 300s (max 5min), maintaining 300s interval thereafter.
- How does the system handle when a disk is removed or added to the array? New disks are discovered automatically on next storage poll (<5min) and entities created with unique IDs `{server_uuid}_disk_{serial}`. Removed disk entities become unavailable immediately and are removed from entity registry after 24 hours of unavailability.
- What happens when Docker or VM services are disabled on Unraid? The integration detects missing services via GraphQL query response. No entities are created for unavailable features. Logs INFO message: "Service {docker|vm} not available on server {name}". Existing entities from previously-enabled services become unavailable.
- How does the integration behave during an Unraid server reboot? All entities become unavailable during reboot (network unreachable). Integration retries connection per exponential backoff schedule. Upon server availability, entities recover within 60 seconds (first successful poll after reconnection). Recovery time measured from server responding to GraphQL queries.
- What happens if the GraphQL API schema changes? At connection time, integration queries API version from `info.versions.core.api`. If version <4.21.0, connection fails with ConfigEntryNotReady and error message ID "unsupported_version". For versions ≥4.21.0 and <6.0.0 (major version change), graceful degradation applies: unknown fields ignored (pydantic `extra="ignore"`), new fields cause no errors. For deprecated fields, integration continues using field if present; if field removed, fallback behavior activates (see data-model.md forward compatibility section). Version range explicitly supported: 4.21.0 to 5.99.99.
- What happens when a Docker/VM mutation fails? The integration does NOT optimistically update entity state. Service call waits for mutation response (timeout 60s). On failure: logs WARNING with full mutation error details, raises HomeAssistantError to caller (service call fails), creates persistent notification with message "Failed to control {container|VM} '{name}': {API error message}". Entity state reflects actual resource state from next poll cycle.
- What happens when API returns unknown enum values? The integration maps unknown enum values to safe defaults per type: ArrayState unknown → "unknown" state, ContainerState unknown → "unknown" (switch OFF), VmState unknown → "unknown" (switch OFF), ArrayDiskStatus unknown → "unknown" (binary_sensor ON/problem). Logs INFO message: "Unknown enum value '{value}' for {enum_type}, using fallback '{fallback}'". See data-model.md §Forward Compatibility for complete mapping.
- What happens if no UPS is connected? If `devices.ups` query returns empty list or null, no UPS entities are created. No errors logged (expected scenario).
- What happens when user configures multiple servers with identical hostnames? Each server is uniquely identified by its system UUID from `info.system.uuid`. Config entry stores hostname but device identity uses UUID. Multiple servers with same hostname are supported; device registry shows each with unique identifier.
- What happens if setup fails mid-process (e.g., after connection succeeds but before coordinator starts)? Integration uses HA's config entry lifecycle: if `async_setup_entry` raises exception, config entry remains in failed state. No partial entities are created. User can retry setup via "Reload" action in integrations UI. No rollback needed as entities only created after full coordinator initialization.
- What happens when API key is revoked/expired? Next API request returns 401/403 HTTP status. Integration catches AuthenticationError, marks all entities unavailable, logs ERROR: "API key authentication failed for server {name}. Please reconfigure integration.". Creates repair issue prompting user to reconfigure with new API key. Integration does NOT auto-remove config entry.
- What happens if user disables SSL verification (verify_ssl=false)? SSL certificate validation is bypassed (for self-signed certs). Integration logs WARNING at startup: "SSL verification disabled for server {name}. Connection is encrypted but server identity not verified." Option available in config flow and options flow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Integration MUST provide a config flow UI for adding and configuring Unraid servers.
- **FR-002**: Integration MUST authenticate with the Unraid GraphQL API using the server's API key.
- **FR-003**: Integration MUST create sensor entities for system metrics: CPU usage, RAM usage, CPU temperature, motherboard temperature, and uptime.
- **FR-004**: Integration MUST create sensor entities for array status including total capacity, used space, and array state.
- **FR-005**: Integration MUST create sensor entities for each disk showing capacity, used space, temperature, and health status.
- **FR-006**: Integration MUST create switch entities for Docker containers allowing start/stop control.
- **FR-007**: Integration MUST create entities for virtual machines showing status and allowing start/stop control.
- **FR-008**: Integration MUST poll the Unraid server for updates at a configurable interval (default: 30 seconds for system metrics, 5 minutes for disk data).
- **FR-009**: Integration MUST handle connection failures gracefully, marking entities as unavailable and retrying automatically.
- **FR-010**: Integration MUST support multiple Unraid servers (multiple instances of the integration).
- **FR-011**: Integration MUST provide diagnostics data for troubleshooting (redacting sensitive information).
- **FR-012**: Integration MUST use pydantic for data validation of GraphQL API responses.
- **FR-013**: Integration MUST support Unraid 7.2 and later versions that provide the GraphQL API.
- **FR-014**: Integration MUST use Home Assistant's DataUpdateCoordinator pattern for efficient polling.
- **FR-015**: Integration MUST require HTTPS for all API communication with the Unraid server.
- **FR-016**: Integration MUST store API credentials in Home Assistant's encrypted config entry storage.
- **FR-017**: Integration MUST verify minimum GraphQL API schema version at connection time and reject incompatible Unraid versions with a clear error message.
- **FR-018**: Integration MUST gracefully handle unknown or additional fields in API responses without failing (forward compatibility).
- **FR-019**: Integration MUST provide an options flow allowing users to modify polling intervals (system metrics interval: 10-300s default 30s, disk data interval: 60-3600s default 300s) and SSL verification (verify_ssl: true/false default true) after initial setup.
- **FR-020**: Integration MUST provide entity_category="diagnostic" for diagnostic sensors (uptime, error counts) and entity_category="config" for configuration-related binary_sensors.
- **FR-021**: Integration MUST provide icon overrides for custom entity types: `mdi:server` for server device, `mdi:harddisk` for disk sensors, `mdi:docker` for container entities, `mdi:desktop-tower` for VM entities, `mdi:battery` for UPS entities.
- **FR-022**: Integration MUST provide friendly_name for all entities in format "{Server Name} {Resource Type} {Resource Name}" for screen reader accessibility.
- **FR-023**: All config flow steps MUST include descriptive labels and help text accessible to screen readers via HA's translation system (strings.json).
- **FR-024**: Integration MUST handle API timeout of 30 seconds for queries and 60 seconds for mutations, raising TimeoutError on expiration.
- **FR-025**: Integration MUST use aiohttp with explicit version constraint in manifest.json requirements (aiohttp>=3.9.0).
- **FR-026**: Integration MUST assume default HTTPS port 443 unless user specifies custom port in config flow hostname field (format: "hostname:port").

### Key Entities

**Unique ID Strategy**: All entities use Server UUID + resource native ID for stable identification across restarts and resource recreation.

- **Unraid Server (Device)**: Represents the Unraid server instance, serves as the parent device for all entities. Unique ID: Server UUID. Attributes include server name, Unraid version, and connection status.
- **System Sensors**: CPU usage, RAM usage, CPU temperature, motherboard temperature, uptime. Unique ID: Server UUID + sensor type. Each sensor has appropriate device class and state class for proper HA integration.
- **Array Sensor**: Overall array status, capacity, and usage. Unique ID: Server UUID + "array". Includes state for array started/stopped/degraded.
- **Disk Sensors**: Individual sensors for each disk in the array and cache. Unique ID: Server UUID + disk serial number. Shows capacity, usage, temperature, and health.
- **Docker Container Switches**: Switch entities for each container. Unique ID: Server UUID + container ID. State reflects running/stopped.
- **VM Switches**: Switch entities for each virtual machine. Unique ID: Server UUID + VM UUID. Allows start/stop control.
- **UPS Sensor** (if UPS connected): Unique ID: Server UUID + UPS serial/ID. Power status and battery level.

## Assumptions

- Unraid 7.2 systems expose a GraphQL API endpoint (default port assumed to be standard Unraid web UI port).
- API authentication uses an API key that users can generate in Unraid's settings.
- The GraphQL API provides real-time data for system metrics, storage, Docker, and VM status.
- Users have network access from Home Assistant to their Unraid server.
- Polling intervals are acceptable for monitoring (real-time subscriptions not required for MVP).

## Success Criteria *(mandatory)*

## Traceability Mapping

### Functional Requirements to Tasks

| Requirement | Tasks | Phase | Notes |
|-------------|-------|-------|-------|
| FR-001 (Config flow UI) | T037-T040 | Phase 2 | Config flow implementation |
| FR-002 (API authentication) | T023-T029 | Phase 2 | API client with auth |
| FR-003 (System metrics) | T046-T056 | Phase 3 | System sensor entities |
| FR-004 (Array status) | T063-T069 | Phase 4 | Storage sensor entities |
| FR-005 (Disk sensors) | T072-T080 | Phase 4 | Per-disk entities |
| FR-006 (Docker switches) | T093-T108 | Phase 5 | Container control |
| FR-007 (VM control) | T109-T127 | Phase 6 | VM management |
| FR-008 (Polling intervals) | T030-T036 | Phase 2 | Dual coordinator pattern |
| FR-009 (Connection failures) | T043-T045 | Phase 2 | Error handling |
| FR-010 (Multiple servers) | T037-T042 | Phase 2 | Multi-instance support |
| FR-011 (Diagnostics) | T157-T160 | Phase 9 | Diagnostics handler |
| FR-012 (Pydantic validation) | T009-T018 | Phase 2 | Data models |
| FR-013 (Unraid 7.2+) | T027-T029 | Phase 2 | Version check in API |
| FR-014 (DataUpdateCoordinator) | T030-T036 | Phase 2 | Coordinator implementation |
| FR-015 (HTTPS required) | T023-T026 | Phase 2 | API client with SSL |
| FR-016 (Encrypted storage) | T037-T042 | Phase 2 | Config entry storage |
| FR-017 (Schema version check) | T027-T029 | Phase 2 | API version validation |
| FR-018 (Forward compatibility) | T009-T018 | Phase 2 | Pydantic extra="ignore" |
| FR-019 (Options flow) | T139-T146 | Phase 8 | Options flow for intervals |
| FR-020 (entity_category) | T046-T127 | Phase 3-6 | Entity metadata |
| FR-021 (Icon overrides) | T046-T127 | Phase 3-6 | Entity icons |
| FR-022 (friendly_name) | T046-T127 | Phase 3-6 | Entity names |
| FR-023 (Accessibility) | T037-T042, T139-T146 | Phase 2, 8 | Config/Options UI |
| FR-024 (API timeouts) | T023-T029 | Phase 2 | HTTP client config |
| FR-025 (aiohttp dependency) | T001-T003 | Phase 1 | manifest.json |
| FR-026 (Port handling) | T037-T042 | Phase 2 | Config flow validation |

### Success Criteria to Test Tasks

| Success Criterion | Test Tasks | Verification Method |
|------------------|------------|---------------------|
| SC-001 (Setup <2min) | T038, T040 | Manual UI test + timer |
| SC-002 (Metrics update 30s) | T033, T049 | Mock data change + coordinator test |
| SC-003 (5% tolerance) | T049-T056 | Compare mock values to sensor output |
| SC-004 (Control <10s) | T097, T113 | Measure service call duration |
| SC-005 (Recovery 60s) | T043-T045 | Network failure simulation |
| SC-006 (Reboot recovery 2min) | T043-T045 | Server restart test |
| SC-007 (50+ containers) | T165-T168 | Load test with fixtures |
| SC-008 (Diagnostics safety) | T157-T160 | Regex validation for secrets |
| SC-009 (Boundary conditions) | T038, T040 | Config flow validation tests |
| SC-010 (Critical temp threshold) | T078-T080 | Mock disk temp=85°C |

### User Stories to Task Phases

| User Story | Primary Phase | Task Range | Success Criteria |
|------------|--------------|------------|------------------|
| US1 (Initial Setup) | Phase 2 | T037-T045 | SC-001, SC-009 |
| US2 (System Monitoring) | Phase 3 | T046-T062 | SC-002, SC-003 |
| US3 (Storage Monitoring) | Phase 4 | T063-T092 | SC-002, SC-003, SC-010 |
| US4 (Docker Management) | Phase 5 | T093-T108 | SC-004, SC-007 |
| US5 (VM Status) | Phase 6 | T109-T127 | SC-004 |
| US6 (Automation Triggers) | Phase 8 | T128-T146 | All (integration tests) |

---


### Measurable Outcomes

- **SC-001**: Users can complete integration setup in under 2 minutes with valid credentials. **Measurement**: Time from clicking "Add Integration" to seeing "Success" confirmation, measured via automated UI test with pre-generated API key.
- **SC-002**: System metric sensors update within 30 seconds of changes on the Unraid server. **Measurement**: Trigger CPU load change on Unraid, measure time until HA sensor reflects change >5% delta. Must be ≤30s.
- **SC-003**: All sensor entities display accurate values matching the Unraid web UI within 5% tolerance. **Measurement**: Compare HA sensor values to Unraid WebGUI values for 10 test cases (CPU%, RAM%, disk usage). Calculate percentage difference: `|HA - WebGUI| / WebGUI * 100 ≤ 5`.
- **SC-004**: Docker container start/stop actions complete within 10 seconds of user request. **Measurement**: Call `switch.turn_on` service, measure time until service call returns (not state change). Must be ≤10s. Separate measurement for state propagation: ≤30s.
- **SC-005**: Integration recovers from temporary network disconnections within 60 seconds of connectivity restoration. **Measurement**: Simulate network interruption (drop packets for 30s), restore network, measure time from first successful ping to Unraid until first successful coordinator update. Must be ≤60s.
- **SC-006**: Integration handles Unraid server reboots gracefully, recovering full functionality within 2 minutes of server availability. **Measurement**: Reboot Unraid server, measure time from server responding to HTTPS port 443 until all entities show available state (not "unavailable"). Must be ≤120s. "Full functionality" = all entities available + sensors showing current values.
- **SC-007**: Users can monitor 10+ Docker containers and 5+ VMs without noticeable performance degradation in Home Assistant. **Measurement**: Load test with 50 Docker containers + 10 VMs. HA memory usage increase must be ≤200MB per server. Entity update latency must remain <1s (time from coordinator refresh to entity state written to HA state machine). UI responsiveness: no frame drops >16ms during entity updates.
- **SC-008**: Diagnostics download provides sufficient information for troubleshooting without exposing API keys or passwords. **Measurement**: Automated check that diagnostics JSON does not contain patterns matching API keys (regex: `[A-Za-z0-9]{32,}`), passwords, or `x-api-key` header values. Must include: server info, coordinator timestamps, entity counts, last 5 error log messages (redacted).
- **SC-009**: Config flow boundary conditions handled gracefully. **Measurement**: Test setup with (1) hostname >253 chars: shows validation error, (2) API key with invalid characters: shows auth error, (3) timeout during version check: shows timeout error with retry option.
- **SC-010**: Integration supports disk temperatures at critical thresholds. **Measurement**: Mock API response with disk temp=85°C (critical threshold per research.md). Entity must show temperature value, logs must not show errors. Binary_sensor for disk health must indicate problem state if temp ≥80°C.
