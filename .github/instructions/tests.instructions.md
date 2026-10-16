---
applyTo: "tests/**/*.py"
---

# Test Guidelines — ha-unraid

Refer to `AGENTS.md` for full project documentation.

## Test Framework

- `pytest` with `pytest-asyncio` (`asyncio_mode = "auto"`)
- `pytest-homeassistant-custom-component` for HA test infrastructure
- `pytest-cov` for coverage reporting
- `syrupy` for snapshot testing

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and data factories
├── fixtures/                   # JSON API response fixtures
├── test_init.py                # Setup/teardown
├── test_identity_migration.py  # Server identity + registry migration (#351)
├── test_config_flow.py         # Config flow paths
├── test_coordinator.py         # Coordinator update logic
├── test_cleanup.py             # Stale entity / device cleanup
├── test_websocket.py           # Subscription manager
├── test_sensor.py, test_binary_sensor.py, test_switch.py, test_button.py
├── test_event.py, test_update.py
└── test_diagnostics.py, test_repairs.py, test_entity.py, test_frontend.py
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

## Registries

Use the real registries from the `hass` fixture; never mock them:

```python
entry = MockConfigEntry(domain=DOMAIN, data={...}, unique_id="...")
entry.add_to_hass(hass)
ent_reg = er.async_get(hass)
dev_reg = dr.async_get(hass)
```

Look devices up per config entry (`dev_reg.async_get_device_by_identifier(
(DOMAIN, uuid), entry.entry_id)`). Deprecated core APIs raise `RuntimeError`
under pytest because there is no integration frame, so fix the code, not the test.

## Full-Integration Setup

`await hass.config_entries.async_setup(entry.entry_id)` loads the integration
and therefore **every** entry of the domain. Patch
`custom_components.unraid.async_register_frontend` and
`custom_components.unraid.UnraidWebSocketManager` (with `AsyncMock`
`async_start`/`async_stop`), and give each mocked client `AsyncMock`s for every
method the coordinators await (see `tests/test_coordinator.py::mock_api_client`).

## Assertions

- Use `hass.states.get("sensor.unraid_...")` to verify entity state
- Check `state.state` for the value
- Check `state.attributes` for extra attributes
- For config flow: assert `result["type"]` and `result["errors"]`
