# Architectural and Design Decisions

This document records significant architectural and design decisions made during the development of the ha-unraid integration.

## Format

Each decision is documented with:

- **Date**: When the decision was made
- **Context**: Why this decision was necessary
- **Decision**: What was decided
- **Rationale**: Why this approach was chosen
- **Consequences**: Expected impacts and trade-offs

---

## Decision Log

### Triple Coordinator Pattern

**Date:** 2025-12 (GraphQL integration rebuild)

**Context:** The integration needs to poll multiple types of data from Unraid's GraphQL API. System metrics need frequent updates (CPU, RAM), but storage queries (disk SMART data) are expensive and change slowly. Infrastructure data (plugins, services) changes even less frequently.

**Decision:** Use three `DataUpdateCoordinator` subclasses with different polling intervals: System (30s), Storage (5min), Infrastructure (15min).

**Rationale:**

- Disk SMART queries are expensive — polling every 30s would overload the server
- CPU/RAM and Docker container states need responsive updates
- Infrastructure data (plugins, services, registration) rarely changes
- HA Core guidelines require fixed polling intervals (not user-configurable)

**Consequences:**

- Entities must know which coordinator provides their data
- Three separate data classes to maintain
- More complex setup in `__init__.py` (three first-refresh calls)
- Better API efficiency and server resource usage

---

### Single Device per Server

**Date:** 2025-12

**Context:** Unraid has multiple subsystems (array, disks, Docker, VMs, UPS). Each could be a separate device in HA.

**Decision:** All entities share a single device per Unraid server, identified by `(DOMAIN, server_uuid)`.

**Rationale:**

- Unraid is a single server, not a collection of independent devices
- Containers, VMs, and disks are resources on the server, not separate physical devices
- Simpler device model for users
- Consistent with how HA treats similar integrations (e.g., Synology DSM)

**Consequences:**

- Many entities on one device (can feel crowded in UI)
- Entity categories and disabled-by-default help organize
- No sub-device removal needed when containers/VMs are removed (entity removal instead)

---

### Unique ID Format: `{server_uuid}_{resource_id}`

**Date:** 2025-12

**Context:** Entities need stable unique IDs that survive HA restarts and server reboots.

**Decision:** Use `{server_uuid}_{resource_id}` where server_uuid comes from the Unraid server's UUID and resource_id is a descriptive identifier (e.g., `cpu_usage`, `disk_sda_temp`, `container_switch_plex`).

**Rationale:**

- Server UUID is stable across reboots
- Resource IDs are descriptive and don't change
- For dynamic entities (containers, VMs), use NAME not ID (container IDs change on recreation)
- Format is simple and predictable

**Consequences:**

- If a server's UUID changes (reinstall), entities break — this is expected
- Container/VM rename causes new entity (old one becomes orphaned)
- Disk replacement creates new entity (different device ID)

---

### Optional Services Graceful Degradation

**Date:** 2025-12

**Context:** Docker, VMs, and UPS may not be enabled on all Unraid servers. The API returns errors when querying disabled services.

**Decision:** Query optional services in separate try/except blocks, returning empty lists on failure. Log at `debug` level only.

**Rationale:**

- Server without Docker should still show system metrics and storage data
- Coordinator update should not fail because an optional service is disabled
- Debug-level logging avoids spamming logs for expected conditions
- Empty list means "no data" — entities simply don't get created

**Consequences:**

- Entities for disabled services are never created (no "unavailable" state)
- If a service is enabled later, entities appear on next coordinator refresh
- Must be careful to separate core queries (must succeed) from optional queries

---

### Button Entities Without Coordinator

**Date:** 2025-12

**Context:** Button entities are action-only — they trigger mutations (start parity check, restart container) but don't display state from a coordinator.

**Decision:** `UnraidButtonEntity` extends `ButtonEntity` directly, not `UnraidBaseEntity`/`CoordinatorEntity`. It stores the API client directly.

**Rationale:**

- Buttons don't need coordinator data for state
- Inheriting from `CoordinatorEntity` would add unnecessary overhead
- Still constructs `DeviceInfo` manually to group with other entities on the same device

**Consequences:**

- Button entities have their own `DeviceInfo` construction (duplicated from base)
- No automatic availability tracking from coordinator — buttons are always available if integration is loaded
- Separate pattern from other entity types

---

### SSL Auto-Detection in Config Flow

**Date:** 2025-12

**Context:** Unraid servers may or may not have SSL enabled. Users shouldn't need to know — they just provide host and port.

**Decision:** Config flow tries HTTPS first, falls back to HTTP on `UnraidSSLError`. The `unraid-api` library also supports HTTP probe fallback.

**Rationale:**

- Better security by default (try HTTPS first)
- Zero-configuration for users
- The `CONF_SSL` flag stored in config entry tracks the detected state
- Reconfigure flow allows changing if server config changes

**Consequences:**

- Initial connection takes slightly longer (two attempts if HTTPS fails)
- `verify_ssl` flag is passed to `async_get_clientsession` for proper session handling

---

### Pydantic v2 with `extra="ignore"` for Forward Compatibility

**Date:** 2025-12

**Context:** The `unraid-api` library uses Pydantic v2 models for API responses. Unraid's API may add new fields in future versions.

**Decision:** All Pydantic models use `extra="ignore"` (configured in the library's base model).

**Rationale:**

- New API fields won't break existing models
- Integration works across Unraid API versions without code changes
- Fields we don't use yet are simply ignored

**Consequences:**

- Must explicitly add fields to models when we want to use them
- No automatic exposure of new API data
- Safe against API expansion

---

## Future Considerations

### WebSocket/Push Updates

**Status:** Not implemented

Unraid's API may support subscriptions in the future. If available, consider replacing polling with push-based updates for real-time responsiveness (especially for system metrics and Docker states).

### Multi-Server Support

**Status:** Supported via multiple config entries

Each config entry represents one Unraid server. Users can add multiple servers through the config flow. No architectural changes needed.

---

## Decision Review

These decisions should be reviewed when:

- Major Unraid API changes are released
- HA Core introduces new integration patterns
- User feedback suggests architectural issues
- Test coverage target (95%) is reached and codebase stabilizes
