---
description: Debug a coordinator data update issue in the Unraid integration
---

# Debug Coordinator Issue

Troubleshoot and fix coordinator-related issues (data not updating, errors, stale data).

## Context

Read these files before starting:
- `AGENTS.md` — Architecture overview
- `custom_components/unraid/coordinator.py` — All three coordinators
- `custom_components/unraid/__init__.py` — Coordinator initialization
- `custom_components/unraid/diagnostics.py` — Diagnostic output

## Diagnostic Steps

### 1. Identify which coordinator is affected

| Symptom | Likely Coordinator |
|---------|-------------------|
| CPU/RAM/Docker/VM data stale | `UnraidSystemCoordinator` (30s) |
| Disk/array/parity data stale | `UnraidStorageCoordinator` (5min) |
| Services/plugins data stale | `UnraidInfraCoordinator` (15min) |

### 2. Check error handling

The coordinator wraps API errors into HA exceptions:

```python
UnraidAuthenticationError → ConfigEntryAuthFailed  (triggers reauth)
UnraidConnectionError     → UpdateFailed           (retries next interval)
UnraidTimeoutError        → UpdateFailed           (retries next interval)
UnraidAPIError            → UpdateFailed           (retries next interval)
```

### 3. Check optional service queries

Docker, VMs, UPS, shares, and all infra queries fail gracefully. If these return empty when they shouldn't, check:
- Is the service actually enabled on Unraid?
- Does the API endpoint exist in this Unraid version?
- Is the `_query_optional_*` method catching the right exception type?

### 4. Check data class mapping

Verify the dataclass fields match what the API returns:
- `UnraidSystemData` — `info`, `metrics`, `containers`, `vms`, `ups_devices`
- `UnraidStorageData` — `array`, `shares`, `parity_history`
- `UnraidInfraData` — `services`, `registration`, `cloud`, `connect`, `remote_access`, `vars`, `plugins`

### 5. Enable debug logging

```yaml
logger:
  logs:
    custom_components.unraid: debug
    unraid_api: debug
```

## Common Issues

- **Auth expired mid-session**: Coordinator raises `ConfigEntryAuthFailed`, triggers reauth flow
- **Server rebooted**: Connection errors for a few cycles, auto-recovers with "Connection restored" log
- **API version mismatch**: New fields from API ignored (Pydantic `extra="ignore"`), missing fields default to `None`
