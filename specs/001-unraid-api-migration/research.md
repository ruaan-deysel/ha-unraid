# Research: Migrate to unraid-api Python Library

**Date**: 2026-01-12
**Feature**: 001-unraid-api-migration

## Research Topics

This document captures research findings for technical decisions required for the migration.

---

## 1. Model Field Mapping: Local vs Library

**Decision**: Library models are compatible with existing entity attribute access patterns.

**Rationale**: Detailed comparison of local models.py with unraid_api.models shows field names are identical or mappable:

### System Models

| Local Model | Library Model | Field Compatibility |
|-------------|---------------|---------------------|
| `SystemInfo` | `ServerInfo` + `SystemMetrics` | Library splits into two models; coordinator data class adapts |
| `InfoCpu` | Part of system metrics | Fields match: brand, threads, cores, packages.temp, packages.totalPower |
| `InfoOs` | Part of ServerInfo | Fields match: hostname, uptime, kernel |
| `Metrics` | `SystemMetrics` | cpu.percentTotal, memory fields identical |
| `CpuUtilization` | Part of metrics | percentTotal field identical |
| `MemoryUtilization` | Part of metrics | All fields match: total, used, free, available, percentTotal, swap* |

### Storage Models

| Local Model | Library Model | Field Compatibility |
|-------------|---------------|---------------------|
| `UnraidArray` | `UnraidArray` | Identical: state, capacity, parityCheckStatus, disks, parities, caches |
| `ArrayDisk` | `ArrayDisk` | Identical: id, idx, device, name, type, size, fs*, temp, status, isSpinning |
| `ArrayCapacity` | `ArrayCapacity` | Identical: kilobytes.total/used/free |
| `ParityCheck` | `ParityCheck` | Identical: status, progress, errors |
| `Share` | `Share` | Identical: id, name, size, used, free |

### Container/VM Models

| Local Model | Library Model | Field Compatibility |
|-------------|---------------|---------------------|
| `DockerContainer` | `DockerContainer` | Identical: id, name, state, image, webUiUrl, iconUrl, ports |
| `ContainerPort` | `ContainerPort` | Identical: privatePort, publicPort, type |
| `VmDomain` | `VmDomain` | Identical: id, name, state, memory, vcpu |

### UPS Models

| Local Model | Library Model | Field Compatibility |
|-------------|---------------|---------------------|
| `UPSDevice` | `UPSDevice` | Identical: id, name, status, battery, power |
| `UPSBattery` | `UPSBattery` | Identical: chargeLevel, estimatedRuntime |
| `UPSPower` | `UPSPower` | Identical: inputVoltage, outputVoltage, loadPercentage |

**Alternatives considered**:
- Creating adapter layer: Rejected - unnecessary overhead since fields match
- Keeping local models: Rejected - defeats purpose of migration

---

## 2. Entity unique_id Preservation

**Decision**: unique_ids will be preserved without changes.

**Rationale**: Analysis of entity unique_id construction in the integration:

| Entity Type | unique_id Pattern | Source Fields |
|-------------|-------------------|---------------|
| System sensors | `{server_uuid}_{resource_id}` | server_uuid from API, resource_id hardcoded |
| Disk sensors | `{server_uuid}_disk_{disk.id}_*` | disk.id from ArrayDisk model |
| Share sensors | `{server_uuid}_share_{share.id}_*` | share.id from Share model |
| Container switches | `{server_uuid}_container_switch_{name}` | container name (stable) |
| VM switches | `{server_uuid}_vm_switch_{name}` | VM name (stable) |
| UPS sensors | `{server_uuid}_ups_{ups.id}_*` | ups.id from UPSDevice model |

**Key finding**: The `id` field in library models matches the current API responses because the library uses the same GraphQL queries internally. Entity IDs like `disk:1`, `share:appdata`, `container:abc123` are unchanged.

**Alternatives considered**:
- Using different ID fields: Rejected - would break existing entity history

---

## 3. Library Exception Mapping

**Decision**: Map library exceptions to Home Assistant exception types.

**Rationale**: Clear 1:1 mapping available:

| Library Exception | Home Assistant Exception | Usage Context |
|-------------------|-------------------------|---------------|
| `UnraidAuthenticationError` | `ConfigEntryAuthFailed` | Config flow, reauth |
| `UnraidConnectionError` | `ConfigEntryNotReady` | Setup, coordinator refresh |
| `UnraidTimeoutError` | `ConfigEntryNotReady` | Setup, coordinator refresh |
| `UnraidAPIError` | `UpdateFailed` | Coordinator refresh |

**Implementation pattern**:
```python
from unraid_api.exceptions import (
    UnraidAuthenticationError,
    UnraidConnectionError,
    UnraidTimeoutError,
    UnraidAPIError,
)

try:
    await client.typed_get_array()
except UnraidAuthenticationError as err:
    raise ConfigEntryAuthFailed from err
except (UnraidConnectionError, UnraidTimeoutError) as err:
    raise ConfigEntryNotReady from err
except UnraidAPIError as err:
    raise UpdateFailed from err
```

**Alternatives considered**:
- Catching generic exceptions: Rejected - loses specificity for error handling

---

## 4. Session Injection Pattern

**Decision**: Use Home Assistant's async_get_clientsession with verify_ssl parameter.

**Rationale**: The unraid-api library explicitly supports session injection for Home Assistant compatibility:

```python
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from unraid_api import UnraidClient

# Get HA session with appropriate SSL verification
session = async_get_clientsession(hass, verify_ssl=verify_ssl)

# Inject into library client
client = UnraidClient(
    host=host,
    api_key=api_key,
    session=session,  # Injected session
)
```

**Key behaviors**:
- Library will NOT close injected sessions (HA manages lifecycle)
- SSL verification follows session configuration
- Connection pooling shared across HA integrations

**Alternatives considered**:
- Let library create own session: Rejected - violates HA best practices for connection pooling

---

## 5. Coordinator Data Class Updates

**Decision**: Update coordinator data classes to use library models directly where possible.

**Rationale**: Current data classes (`UnraidSystemData`, `UnraidStorageData`) can use library models with minimal adaptation:

### UnraidSystemData Migration

| Current Field | Library Source | Change Required |
|---------------|----------------|-----------------|
| `info: SystemInfo` | `client.get_system_info()` | Use ServerInfo from library |
| `metrics: Metrics` | `client.get_system_metrics()` | Use SystemMetrics from library |
| `containers: list[DockerContainer]` | `client.typed_get_containers()` | Direct library model |
| `vms: list[VmDomain]` | `client.typed_get_vms()` | Direct library model |
| `ups_devices: list[UPSDevice]` | `client.typed_get_ups_devices()` | Direct library model |
| `notifications_unread: int` | `client.get_notification_overview().unread.total` | Extract from NotificationOverview |

### UnraidStorageData Migration

| Current Field | Library Source | Change Required |
|---------------|----------------|-----------------|
| `array_state: str` | `array.state` from typed_get_array() | Direct field access |
| `capacity: ArrayCapacity` | `array.capacity` from typed_get_array() | Direct library model |
| `parity_status: ParityCheck` | `array.parityCheckStatus` from typed_get_array() | Direct library model |
| `boot: ArrayDisk` | `array.boot` from typed_get_array() | Direct library model |
| `disks: list[ArrayDisk]` | `array.disks` from typed_get_array() | Direct library model |
| `parities: list[ArrayDisk]` | `array.parities` from typed_get_array() | Direct library model |
| `caches: list[ArrayDisk]` | `array.caches` from typed_get_array() | Direct library model |
| `shares: list[Share]` | `client.typed_get_shares()` | Direct library model |

**Alternatives considered**:
- Wrapping all library models: Rejected - adds complexity without benefit

---

## 6. Optional Feature Handling

**Decision**: Use try/except pattern matching current behavior.

**Rationale**: Library typed methods raise exceptions when features are unavailable (Docker disabled, no VMs, no UPS). Current integration already handles this gracefully:

```python
async def _query_optional_docker(self) -> list[DockerContainer]:
    """Query Docker containers (fails gracefully if Docker not enabled)."""
    try:
        return await self.client.typed_get_containers()
    except (UnraidAPIError, UnraidConnectionError) as err:
        _LOGGER.debug("Docker data not available: %s", err)
        return []
```

This pattern is already implemented for Docker, VMs, UPS, and Shares. Migration preserves this pattern using library exceptions.

**Alternatives considered**:
- Pre-checking feature availability: Rejected - adds extra API call, current pattern is cleaner

---

## 7. Method Mapping: Current API to Library

**Decision**: Use library's typed methods where available, fall back to raw query() for edge cases.

| Current Method | Library Method | Notes |
|----------------|----------------|-------|
| `test_connection()` | `client.test_connection()` | Identical |
| `get_version()` | `client.get_version()` | Returns dict with unraid/api versions |
| `query(info query)` | `client.get_server_info()` | For server UUID/hostname |
| `query(metrics query)` | `client.get_system_metrics()` | Typed SystemMetrics |
| `query(array query)` | `client.typed_get_array()` | Typed UnraidArray |
| `query(shares query)` | `client.typed_get_shares()` | Typed list[Share] |
| `query(docker query)` | `client.typed_get_containers()` | Typed list[DockerContainer] |
| `query(vms query)` | `client.typed_get_vms()` | Typed list[VmDomain] |
| `query(ups query)` | `client.typed_get_ups_devices()` | Typed list[UPSDevice] |
| `query(notifications)` | `client.get_notification_overview()` | Typed NotificationOverview |
| `start_container(id)` | `client.start_container(id)` | Identical |
| `stop_container(id)` | `client.stop_container(id)` | Identical |
| `start_vm(id)` | `client.start_vm(id)` | Identical |
| `stop_vm(id)` | `client.stop_vm(id)` | Identical |
| `start_array()` | `client.start_array()` | Identical |
| `stop_array()` | `client.stop_array()` | Identical |
| `spin_up_disk(id)` | `client.spin_up_disk(id)` | Identical |
| `spin_down_disk(id)` | `client.spin_down_disk(id)` | Identical |
| `start_parity_check(correct)` | `client.start_parity_check(correct=)` | Identical |
| `pause_parity_check()` | `client.pause_parity_check()` | Identical |
| `resume_parity_check()` | `client.resume_parity_check()` | Identical |
| `cancel_parity_check()` | `client.cancel_parity_check()` | Identical |

**Alternatives considered**:
- Using raw query() for everything: Rejected - loses type safety benefits

---

## Summary

All research topics resolved. Key findings:

1. **Model compatibility**: Library models have identical field names - no adapter layer needed
2. **Entity IDs**: Will be preserved - same ID format from API
3. **Exceptions**: Clear mapping to HA exception types
4. **Session**: Use HA's async_get_clientsession with injection
5. **Coordinators**: Update to use library typed methods directly
6. **Optional features**: Maintain try/except pattern with library exceptions
7. **Methods**: 1:1 mapping available for all current functionality
