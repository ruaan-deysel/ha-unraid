# AI Agent Instructions — ha-unraid

> **Single source of truth** for all AI agents working on this codebase.
> Agent-specific wrappers (`CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`) reference this file.

## Project Identity

| Field | Value |
|-------|-------|
| **Domain** | `unraid` |
| **Integration name** | Unraid |
| **Class prefix** | `Unraid` |
| **Code path** | `custom_components/unraid/` |
| **Test path** | `tests/` |
| **Python** | 3.13+ |
| **HA minimum** | 2025.6.3 |
| **Key dependency** | `unraid-api>=1.5.0` |
| **iot_class** | `local_polling` |
| **Config flow** | Yes (UI only, no YAML) |
| **Platforms** | `sensor`, `binary_sensor`, `switch`, `button` |

## Quick Commands

```bash
# Lint
./scripts/lint          # or: ruff check . --fix && ruff format .

# Test
./scripts/test          # or: pytest

# Full validation
./scripts/validate

# Setup dev environment
./scripts/setup

# Start dev Home Assistant
./scripts/develop

# Type checking
mypy custom_components/unraid
```

## Architecture

### Data Flow

```
Entities ──▶ Coordinator ──▶ UnraidClient (unraid-api) ──▶ Unraid Server (GraphQL)
   ▲              │
   └──────────────┘
     (coordinator.data)
```

### Triple Coordinator Pattern

Three `DataUpdateCoordinator` subclasses poll at different intervals:

| Coordinator | Interval | Data |
|-------------|----------|------|
| `UnraidSystemCoordinator` | 30s | Server info, CPU/RAM metrics, Docker containers, VMs, UPS, notifications |
| `UnraidStorageCoordinator` | 5min | Array state, disks, parity, shares, capacity |
| `UnraidInfraCoordinator` | 15min | Services, registration, cloud, remote access, plugins |

Intervals are **fixed** per HA Core guidelines (not user-configurable). Users can call `homeassistant.update_entity` for on-demand refresh.

### Runtime Data

```python
@dataclass
class UnraidRuntimeData:
    api_client: UnraidClient
    system_coordinator: UnraidSystemCoordinator
    storage_coordinator: UnraidStorageCoordinator
    infra_coordinator: UnraidInfraCoordinator
    server_info: dict

type UnraidConfigEntry = ConfigEntry[UnraidRuntimeData]
```

Access in platform setup: `entry.runtime_data.system_coordinator`, etc.

### Data Classes

Each coordinator returns a typed dataclass:

- `UnraidSystemData` — `info`, `metrics`, `containers`, `vms`, `ups_devices`, `notification_overview`
- `UnraidStorageData` — `array`, `shares`, `parity_history` (+ convenience properties: `array_state`, `capacity`, `parity_status`, `boot`, `disks`, `parities`, `caches`)
- `UnraidInfraData` — `services`, `registration`, `cloud`, `remote_access`, `plugins`, `vars`

## Integration File Structure

```
custom_components/unraid/
├── __init__.py          # Setup/teardown, UnraidRuntimeData, platform forwarding
├── config_flow.py       # Config flow (user, reauth, reconfigure), options flow (UPS)
├── const.py             # All constants: domain, intervals, keys, icons, states
├── coordinator.py       # Triple coordinator pattern + data classes
├── entity.py            # UnraidBaseEntity, UnraidEntity, UnraidEntityDescription
├── sensor.py            # All sensor entities
├── binary_sensor.py     # All binary sensor entities
├── switch.py            # Container, VM, array, parity switches
├── button.py            # Array start/stop, parity, disk spin buttons
├── diagnostics.py       # Diagnostic data for troubleshooting
├── icons.json           # Icon definitions per translation key
├── strings.json         # English translations (source of truth)
├── translations/en.json # Generated from strings.json
├── manifest.json        # Integration metadata
└── quality_scale.yaml   # HA quality scale self-assessment
```

## Code Style & Conventions

### General

- **Line length**: 88 characters (ruff formatter)
- **Linter**: ruff (`E`, `W`, `F`, `I`, `C`, `B`, `UP` rules)
- **Target**: Python 3.13 (`target-version = "py313"`)
- **Imports**: Use `from __future__ import annotations` in every file
- **Type hints**: Required on all public functions; use `TYPE_CHECKING` guard for import-only types
- **Logging**: `_LOGGER = logging.getLogger(__name__)` — use `_LOGGER.debug()` for data updates, `.info()` for lifecycle, `.warning()` for user-visible issues, `.error()` for failures
- **Constants**: Define in `const.py` with `Final` type annotation
- **Strings**: f-strings preferred

### Entity Pattern

Entity class hierarchy:

```
CoordinatorEntity
  └── UnraidBaseEntity          # Base: device_info, unique_id, availability
        └── UnraidEntity        # + EntityDescription support
```

Entity MRO for platform entities: `PlatformEntity, UnraidBaseEntity` (e.g., `SensorEntity, UnraidBaseEntity`)

Key patterns:
- `_attr_has_entity_name = True` (always, set on `UnraidBaseEntity`)
- `_attr_translation_key = "..."` for translated names via `strings.json`
- Unique ID format: `{server_uuid}_{resource_id}`
- Access coordinator data: `data: UnraidSystemData | None = self.coordinator.data`
- Use `@property` for `native_value`, `is_on`, `extra_state_attributes`
- Per-resource entities (disks, containers, VMs) store `_disk_id` / `_container_id` and implement `_get_disk()` / `_get_container()` helper

### Coordinator Pattern

- Extend `DataUpdateCoordinator[UnraidXxxData]`
- Authentication errors → `raise ConfigEntryAuthFailed`
- Connection/timeout errors → `raise UpdateFailed`
- Optional services (Docker, VMs, UPS) → fail gracefully with `_LOGGER.debug()`, return empty list
- Log recovery when connection restored after previous failure
- Pass `config_entry=` to `super().__init__()`

### Config Flow

- Steps: `user` → `reauth_confirm` → `reconfigure`
- SSL auto-detection: Try HTTPS first, fall back to HTTP on `UnraidSSLError`
- Version checking: `MIN_API_VERSION = "4.21.0"`, `MIN_UNRAID_VERSION = "7.2.0"`
- Options flow: `OptionsFlowWithReload` for UPS capacity/power settings
- Unique ID: server UUID from `api_client.get_server_info()`

### Error Handling

- Use HA translation system for user-facing errors: `translation_domain=DOMAIN`, `translation_key="..."`, `translation_placeholders={...}`
- Wrap API errors in `HomeAssistantError` for entity actions (switch on/off, button press)
- Create repair issues (`ir.async_create_issue`) for persistent auth failures
- Clear repair issues on successful reconnection

### Models & Data

- All API data comes as Pydantic v2 models from `unraid-api` library
- Use `extra="ignore"` on Pydantic models to handle API evolution
- Enum values from API: always compare with `.upper()` for case-insensitive matching

## Testing

### Setup

```bash
pip install -e ".[dev]"
# or
./scripts/setup
```

### Structure

```
tests/
├── conftest.py          # Shared fixtures: mock API client, coordinators, config entries
├── fixtures/            # JSON fixtures for API responses
├── test_init.py         # Setup/teardown tests
├── test_config_flow.py  # Config flow tests
├── test_coordinator.py  # Coordinator tests
├── test_sensor.py       # Sensor entity tests
├── test_binary_sensor.py
├── test_switch.py
└── test_button.py
```

### Patterns

- Use `pytest-homeassistant-custom-component` for HA test infrastructure
- Mock `UnraidClient` methods, not HTTP calls
- Use `pytest-asyncio` with `asyncio_mode = "auto"`
- Fixtures provide pre-built coordinator data classes
- Test both happy path and error scenarios (auth failure, connection loss, missing optional data)

### Running Tests

```bash
pytest                           # All tests with coverage
pytest tests/test_sensor.py      # Single module
pytest -k "test_cpu"             # Pattern match
pytest --no-cov                  # Skip coverage for speed
```

## Boundaries

### Always Do

- Read existing code before modifying — understand patterns in place
- Follow the entity class hierarchy (`UnraidBaseEntity` or `UnraidEntity`)
- Use `_attr_translation_key` for entity names (not hardcoded strings)
- Add translation keys to `strings.json` when creating new entities
- Match existing icon patterns in `icons.json`
- Use typed coordinator data access (e.g., `data: UnraidSystemData | None = self.coordinator.data`)
- Handle `None` coordinator data gracefully
- Use `Final` type annotations for constants in `const.py`
- Run `./scripts/lint` before committing
- Pass `config_entry=` to coordinator `super().__init__()`
- Use `entry.runtime_data` to access runtime data (not `hass.data[DOMAIN]`)

### Ask First

- Adding new platforms (beyond sensor, binary_sensor, switch, button)
- Changing coordinator polling intervals
- Modifying the config flow steps
- Adding new dependencies to `manifest.json` or `pyproject.toml`
- Changing entity unique ID format (breaks existing installations)
- Modifying `UnraidRuntimeData` structure
- Updating the `unraid-api` library version

### Never Do

- Make polling intervals user-configurable (HA Core policy)
- Skip `from __future__ import annotations`
- Use bare `except:` — always catch specific exceptions
- Hardcode entity names (use translation keys)
- Auto-update `translations/` files other than `en.json`
- Import from `homeassistant.core` at module level in entity files (use `TYPE_CHECKING`)
- Use `entity_id` for identification (use `unique_id`)
- Store state in the entity that should be in the coordinator
- Commit secrets, API keys, or credentials
- Use `hass.data[DOMAIN]` directly (use `config_entry.runtime_data`)
- Use blocking I/O in async functions
- Remove existing tests without replacement

## Commit Format

```
type: short description

Longer explanation if needed.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `build`

## Debugging

```yaml
# Enable debug logging in configuration.yaml
logger:
  default: info
  logs:
    custom_components.unraid: debug
    unraid_api: debug
```

Check diagnostics via: Settings > Devices & Services > Unraid > (...) > Download diagnostics

## Quality Scale

The integration targets **Platinum** level on the [HA Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/). Current status:

- **Bronze**: All rules done/exempt
- **Silver**: All done except test coverage (63% → 95% target)
- **Gold**: All done/exempt
- **Platinum**: All done (async dependency, inject websession, strict typing)
