# AI Coding Agent Instructions

Home Assistant custom integration for Unraid servers via the official GraphQL API.

## Project Overview

- **Type**: Home Assistant custom component (HACS compatible)
- **Domain**: `unraid`
- **Language**: Python 3.13+
- **Library**: `unraid-api>=1.3.1` (GraphQL client)
- **Connectivity**: Local polling via HTTPS/GraphQL
- **Platforms**: sensor, binary_sensor, switch, button, diagnostics

## Project Structure

```
custom_components/unraid/
├── __init__.py        # Entry point, async_setup_entry/async_unload_entry
├── config_flow.py     # UI configuration flow with reauth support
├── coordinator.py     # DataUpdateCoordinator for API polling
├── entity.py          # Base UnraidEntity class
├── const.py           # Constants, keys, icons
├── sensor.py          # Sensor entities (CPU, RAM, storage, UPS)
├── binary_sensor.py   # Binary sensors (array, disk health)
├── switch.py          # Docker container and VM controls
├── button.py          # Array/parity/disk control buttons
├── diagnostics.py     # Debug data export
├── strings.json       # User-facing text/translations
└── manifest.json      # Integration metadata

tests/                  # pytest test suite
├── conftest.py        # Fixtures and mocks
├── fixtures/          # JSON test data
└── test_*.py          # Test modules per component
```

## Commands

```bash
# Install dependencies
uv sync --all-extras

# Lint and format (run after every change)
ruff check . --fix && ruff format .

# Run tests with coverage
pytest

# Run specific test file
pytest tests/test_sensor.py -v

# Type checking
mypy custom_components/unraid

# Start dev Home Assistant
./scripts/develop
```

## Code Style

- **Formatter**: Ruff (line-length 88)
- **Type hints**: Required on all functions
- **Imports**: Use `from __future__ import annotations`
- **Strings**: f-strings preferred
- **Docstrings**: Required for modules, classes, and public functions

### Entity Pattern

```python
class UnraidSensor(UnraidEntity, SensorEntity):
    """Sensor entity for Unraid integration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
```

### Coordinator Pattern

```python
class UnraidDataUpdateCoordinator(DataUpdateCoordinator[UnraidData]):
    """Data update coordinator for Unraid."""

    config_entry: ConfigEntry

    async def _async_update_data(self) -> UnraidData:
        """Fetch data from API."""
        try:
            return await self.client.fetch_data()
        except UnraidConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except UnraidAuthenticationError as err:
            raise ConfigEntryAuthFailed("Invalid API key") from err
```

## Testing

- **Framework**: pytest with pytest-homeassistant-custom-component
- **Coverage**: Target 95%+ for all modules
- **Snapshots**: Use syrupy for entity state verification

```python
@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_API_KEY: "test-key"},
        unique_id="test-server-id",
    )

async def test_sensor_setup(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test sensor platform setup."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.unraid_cpu_usage")
    assert state is not None
```

## Git Workflow

- **Branch**: Create feature branches from `main`
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)
- **PR**: Include test coverage for new code
- **Lint**: All code must pass `ruff check` before commit

## Boundaries

### Always Do
- Run `ruff check . --fix && ruff format .` after changes
- Add type hints to all functions
- Write tests for new functionality
- Use constants from `const.py` instead of hardcoding
- Handle exceptions from `unraid_api` library
- Pass `config_entry` to DataUpdateCoordinator
- Use `_attr_has_entity_name = True` for entities

### Ask First
- Adding new dependencies to `pyproject.toml`
- Creating new entity platforms
- Modifying the config flow schema
- Changing polling intervals
- Updating the unraid-api library version

### Never Do
- Commit secrets, API keys, or credentials
- Skip running linting before commits
- Remove existing tests without replacement
- Use `hass.data[DOMAIN]` directly (use `config_entry.runtime_data`)
- Make polling intervals user-configurable
- Use blocking I/O in async functions

## Key Patterns

### Error Handling
```python
# Config flow - broad exception allowed
try:
    await client.test_connection()
except Exception:
    errors["base"] = "cannot_connect"

# Regular code - specific exceptions required
try:
    data = await client.get_system_info()
except UnraidConnectionError:
    raise UpdateFailed("Connection failed")
except UnraidAuthenticationError:
    raise ConfigEntryAuthFailed("Auth failed")
```

### Unique IDs
```python
# Entity unique ID format
self._attr_unique_id = f"{entry.entry_id}_{entity_key}"

# For per-device entities (disks, containers)
self._attr_unique_id = f"{entry.entry_id}_{disk_id}_temperature"
```

### Device Info
```python
@property
def device_info(self) -> DeviceInfo:
    """Return device info."""
    return DeviceInfo(
        identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
        name=self.coordinator.data.system.hostname,
        manufacturer=MANUFACTURER,
        model="Unraid Server",
        sw_version=self.coordinator.data.system.version,
    )
```

## API Reference

The integration uses `unraid-api` library. Key data structures:
- `UnraidData`: Combined coordinator data
- `SystemInfo`: CPU, memory, uptime
- `ArrayInfo`: Array status, parity, capacity
- `DiskInfo`: Individual disk data
- `ContainerInfo`: Docker container state
- `VMInfo`: Virtual machine state
- `UPSInfo`: UPS status and metrics

## Debugging

```bash
# Enable debug logging in configuration.yaml
logger:
  default: info
  logs:
    custom_components.unraid: debug
    unraid_api: debug
```

Check diagnostics via: Settings > Devices & Services > Unraid > (⋮) > Download diagnostics
