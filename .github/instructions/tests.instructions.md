---
applyTo: "tests/**/*.py"
---

# Test Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Test Framework

- `pytest` with `pytest-asyncio` (`asyncio_mode = "auto"`)
- `pytest-homeassistant-custom-component` for HA test infrastructure
- `pytest-cov` for coverage reporting
- `syrupy` for snapshot testing

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── fixtures/            # JSON API response fixtures
├── test_init.py         # Setup/teardown
├── test_config_flow.py  # Config flow paths
├── test_coordinator.py  # Coordinator update logic
├── test_sensor.py       # Sensor entities
├── test_binary_sensor.py
├── test_switch.py
└── test_button.py
```

## Fixture Patterns

Fixtures in `conftest.py` provide:
- Mock `UnraidClient` with pre-configured return values
- Pre-built data classes (`UnraidSystemData`, `UnraidStorageData`, `UnraidInfraData`)
- Mock config entries with realistic data
- Helper functions like `make_system_data()`, `make_storage_data()`

## Mocking

Mock at the `UnraidClient` method level, not HTTP:

```python
@pytest.fixture
def mock_api_client():
    client = AsyncMock(spec=UnraidClient)
    client.get_server_info.return_value = ServerInfo(...)
    client.get_system_metrics.return_value = SystemMetrics(...)
    return client
```

## Test Scenarios

Cover both happy path and error cases:

- **Happy path**: Normal data, all services available
- **Auth failure**: `UnraidAuthenticationError` → `ConfigEntryAuthFailed`
- **Connection loss**: `UnraidConnectionError` → `UpdateFailed`
- **Missing optional data**: Docker/VMs/UPS not enabled → empty lists, no crash
- **None data**: Coordinator data is `None` → entity returns `None`/unavailable

## Running Tests

```bash
pytest                           # All tests with coverage
pytest tests/test_sensor.py      # Single module
pytest -k "test_cpu"             # Pattern match
pytest --no-cov                  # Skip coverage for speed
```

## Assertions

- Use `hass.states.get("sensor.unraid_...")` to verify entity state
- Check `state.state` for the value
- Check `state.attributes` for extra attributes
- For config flow: assert `result["type"]` and `result["errors"]`
