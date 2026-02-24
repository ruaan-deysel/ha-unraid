# Architecture Overview

This document describes the technical architecture of the ha-unraid custom component for Home Assistant.

For AI agent instructions, see [`AGENTS.md`](/AGENTS.md).

## Directory Structure

```text
custom_components/unraid/
├── __init__.py          # Integration setup/teardown, UnraidRuntimeData, platform forwarding
├── config_flow.py       # Config flow (user, reauth, reconfigure) + options flow (UPS)
├── const.py             # All constants: domain, intervals, keys, icons, states
├── coordinator.py       # Triple coordinator pattern + data classes
├── entity.py            # UnraidBaseEntity, UnraidEntity, UnraidEntityDescription
├── sensor.py            # Sensor entities (CPU, RAM, storage, UPS, notifications, infra)
├── binary_sensor.py     # Binary sensors (array, disk health, parity)
├── switch.py            # Docker container, VM, array, parity switches
├── button.py            # Parity check, container restart buttons
├── diagnostics.py       # Diagnostic data export (sanitized)
├── repairs.py           # Repair flows (auth failure → reauth)
├── icons.json           # MDI icons per entity translation key
├── strings.json         # English translations (source of truth)
├── translations/en.json # Generated from strings.json
├── manifest.json        # Integration metadata
├── quality_scale.yaml   # HA quality scale self-assessment
└── py.typed             # PEP 561 marker for type checking
```

## Core Components

### API Client

**Library:** `unraid-api>=1.5.0` (PyPI)

The integration uses the `unraid-api` library which provides:

- `UnraidClient` — Async GraphQL client with session injection
- Typed methods (`get_server_info()`, `get_system_metrics()`, `typed_get_array()`, etc.)
- Pydantic v2 models for all responses (`ServerInfo`, `SystemMetrics`, `UnraidArray`, etc.)
- Custom exceptions (`UnraidAuthenticationError`, `UnraidConnectionError`, etc.)

The HA integration injects its own `aiohttp.ClientSession` via `async_get_clientsession()` for proper connection pooling and SSL handling.

### Triple Coordinator Pattern

Three `DataUpdateCoordinator` subclasses manage data at different polling intervals:

| Coordinator | Interval | Rationale |
|-------------|----------|-----------|
| `UnraidSystemCoordinator` | 30s | System metrics need responsiveness (CPU, RAM, Docker states) |
| `UnraidStorageCoordinator` | 5min | Disk/SMART queries are expensive, storage changes slowly |
| `UnraidInfraCoordinator` | 15min | Services/plugins rarely change, reduces API load |

Each coordinator:

- Returns a typed dataclass (`UnraidSystemData`, `UnraidStorageData`, `UnraidInfraData`)
- Handles auth errors → `ConfigEntryAuthFailed` (triggers reauth)
- Handles connection errors → `UpdateFailed` (retries next interval)
- Queries optional services (Docker, VMs, UPS) with graceful fallback to empty lists
- Tracks `_previously_unavailable` for recovery logging

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

Stored in `entry.runtime_data` (HA 2024.4+ pattern). Never use `hass.data[DOMAIN]`.

### Entity Hierarchy

```text
CoordinatorEntity
  └── UnraidBaseEntity          # device_info, unique_id, availability, has_entity_name
        └── UnraidEntity        # + UnraidEntityDescription support (available_fn, supported_fn)
```

Platform entities use MRO: `PlatformEntity, UnraidBaseEntity` (e.g., `SensorEntity, UnraidBaseEntity`).

Exception: `UnraidButtonEntity` extends `ButtonEntity` directly (buttons are action-only, no coordinator state).

### Config Flow

- **User step**: Host, port, API key → SSL auto-detection → version checks → unique ID from server UUID
- **Reauth**: New API key entry → re-validate → update entry
- **Reconfigure**: Change host/port/key
- **Options flow**: UPS capacity/power settings (only shown when UPS devices detected)

### Device Model

All entities share a **single device per Unraid server**, identified by `(DOMAIN, server_uuid)`. Containers, VMs, and disks are entities (not sub-devices).

## Data Flow

```text
┌─────────────────┐
│  Config Entry    │ ← Created by config flow
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  UnraidClient   │ ← API client from unraid-api library
└────────┬────────┘
         │
    ┌────┴────────────────┬──────────────────┐
    │                     │                  │
    ▼                     ▼                  ▼
┌──────────┐       ┌──────────┐       ┌──────────┐
│  System  │       │ Storage  │       │  Infra   │
│  30s     │       │  5min    │       │  15min   │
└────┬─────┘       └────┬─────┘       └────┬─────┘
     │                  │                  │
     ▼                  ▼                  ▼
┌──────────┐       ┌──────────┐       ┌──────────┐
│ Sensors  │       │ Sensors  │       │ Sensors  │
│ Switches │       │ Bin.Sens │       │ (infra)  │
│ Buttons  │       │ Switches │       └──────────┘
└──────────┘       └──────────┘
```

## Key Design Decisions

See [DECISIONS.md](./DECISIONS.md) for the full decision log.

## Quality Scale

The integration targets **Platinum** level. See `custom_components/unraid/quality_scale.yaml` for the full self-assessment.
