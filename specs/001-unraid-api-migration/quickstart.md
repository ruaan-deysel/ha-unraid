# Quickstart: Migrate to unraid-api Python Library

**Date**: 2026-01-12
**Feature**: 001-unraid-api-migration

## Overview

This guide provides quick reference for developers implementing the migration from custom GraphQL-based API client to the `unraid-api` Python library.

## Prerequisites

- Python 3.12+
- Home Assistant development environment
- Understanding of async Python patterns
- Access to Unraid server for testing (7.1.4+, API 4.21.0+)

## Key Changes Summary

| Before | After |
|--------|-------|
| `from .api import UnraidAPIClient` | `from unraid_api import UnraidClient` |
| `from .models import DockerContainer` | `from unraid_api.models import DockerContainer` |
| `client.query(GRAPHQL_STRING)` | `client.typed_get_*()` methods |
| Custom exception handling | `unraid_api.exceptions` |

## Migration Patterns

### 1. Client Initialization

**Before (api.py):**
```python
from .api import UnraidAPIClient

client = UnraidAPIClient(
    host=host,
    http_port=http_port,
    https_port=https_port,
    api_key=api_key,
    verify_ssl=verify_ssl,
    session=session,
)
```

**After (using library):**
```python
from unraid_api import UnraidClient

client = UnraidClient(
    host=host,
    api_key=api_key,
    session=session,  # HA's async_get_clientsession
)
```

> Note: Library handles port discovery and SSL mode automatically.

### 2. Data Fetching

**Before (coordinator.py):**
```python
result = await self._api_client.query("""
    query {
        array {
            state
            capacity { kilobytes { total used free } }
            disks { id name temp status }
        }
    }
""")
array_data = UnraidArray.model_validate(result["array"])
```

**After (using library):**
```python
array = await self._api_client.typed_get_array()
# array is already typed as UnraidArray
```

### 3. Model Imports

**Before:**
```python
from .models import (
    DockerContainer,
    VmDomain,
    Share,
    ArrayDisk,
    UPSDevice,
)
```

**After:**
```python
from unraid_api.models import (
    DockerContainer,
    VmDomain,
    Share,
    ArrayDisk,
    UPSDevice,
)
```

### 4. Exception Handling

**Before:**
```python
try:
    await client.test_connection()
except Exception as err:
    if "401" in str(err) or "403" in str(err):
        raise ConfigEntryAuthFailed from err
    raise ConfigEntryNotReady from err
```

**After:**
```python
from unraid_api.exceptions import (
    UnraidAuthenticationError,
    UnraidConnectionError,
)

try:
    await client.test_connection()
except UnraidAuthenticationError as err:
    raise ConfigEntryAuthFailed from err
except UnraidConnectionError as err:
    raise ConfigEntryNotReady from err
```

### 5. Control Operations

**Before:**
```python
await self._api_client.mutate(
    """mutation StartContainer($id: ID!) { startContainer(id: $id) { success } }""",
    variables={"id": container_id}
)
```

**After:**
```python
await self._api_client.start_container(container_id)
```

## Method Cheatsheet

| Operation | Library Method |
|-----------|----------------|
| Test connection | `client.test_connection()` |
| Get server info | `client.get_server_info()` |
| Get system metrics | `client.get_system_metrics()` |
| Get array | `client.typed_get_array()` |
| Get shares | `client.typed_get_shares()` |
| Get containers | `client.typed_get_containers()` |
| Get VMs | `client.typed_get_vms()` |
| Get UPS devices | `client.typed_get_ups_devices()` |
| Get notifications | `client.get_notification_overview()` |
| Start container | `client.start_container(id)` |
| Stop container | `client.stop_container(id)` |
| Start VM | `client.start_vm(id)` |
| Stop VM | `client.stop_vm(id)` |
| Start array | `client.start_array()` |
| Stop array | `client.stop_array()` |
| Spin up disk | `client.spin_up_disk(id)` |
| Spin down disk | `client.spin_down_disk(id)` |
| Start parity check | `client.start_parity_check(correct=False)` |
| Pause parity check | `client.pause_parity_check()` |
| Resume parity check | `client.resume_parity_check()` |
| Cancel parity check | `client.cancel_parity_check()` |

## Files to Modify

### High Priority (Core Changes)

1. **manifest.json**: Add `"unraid-api>=1.3.1"` to requirements
2. **coordinator.py**: Replace GraphQL with typed methods
3. **__init__.py**: Update client import and initialization
4. **config_flow.py**: Update connection testing

### Medium Priority (Import Updates)

5. **sensor.py**: Update model imports
6. **switch.py**: Update model imports and API calls
7. **binary_sensor.py**: Update model imports
8. **button.py**: Update model imports and API calls
9. **diagnostics.py**: Update client usage

### Low Priority (Cleanup)

10. **api.py**: DELETE entire file
11. **models.py**: DELETE entire file
12. **tests/test_api.py**: DELETE
13. **tests/test_models.py**: DELETE or refactor
14. **tests/*.py**: Update mocks for library client

## Testing Checklist

- [ ] Integration loads without errors
- [ ] Config flow works (new setup)
- [ ] All sensors show correct values
- [ ] All binary sensors report correct states
- [ ] Container switches work (start/stop)
- [ ] VM switches work (start/stop)
- [ ] Array buttons work (start/stop, parity check)
- [ ] Disk buttons work (spin up/down)
- [ ] UPS sensors show correct values (if UPS connected)
- [ ] Diagnostics download works
- [ ] Options flow works
- [ ] Entity unique_ids unchanged (check entity registry)
- [ ] All tests pass

## Common Gotchas

1. **SSL Verification**: Library auto-discovers SSL mode, don't pass verify_ssl to client
2. **Port Configuration**: Library handles port discovery, no need for http_port/https_port
3. **Session Management**: Library won't close injected sessions - HA manages lifecycle
4. **Optional Features**: Docker/VMs/UPS queries fail if disabled - wrap in try/except
5. **Model Validation**: Library models use `extra="ignore"` - future fields won't break
6. **Field Names**: Library uses camelCase (webUiUrl), entities may need attribute mapping

## Development Commands

```bash
# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_coordinator.py -v

# Check for GraphQL strings (should be zero after migration)
grep -r "query\|mutation" custom_components/unraid/ --include="*.py"

# Verify api.py and models.py deleted
ls custom_components/unraid/api.py 2>/dev/null && echo "ERROR: api.py exists" || echo "OK: api.py removed"
ls custom_components/unraid/models.py 2>/dev/null && echo "ERROR: models.py exists" || echo "OK: models.py removed"

# Lint check
ruff check custom_components/unraid/
```
