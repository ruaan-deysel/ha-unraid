---
applyTo: "custom_components/unraid/coordinator.py"
---

# Coordinator Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Triple Coordinator Pattern

| Coordinator | Interval | Constant | Scope |
|-------------|----------|----------|-------|
| `UnraidSystemCoordinator` | 30s | `SYSTEM_POLL_INTERVAL` | Server info, CPU/RAM, Docker, VMs, UPS, notifications |
| `UnraidStorageCoordinator` | 5min | `STORAGE_POLL_INTERVAL` | Array, disks, parity, shares, capacity |
| `UnraidInfraCoordinator` | 15min | `INFRA_POLL_INTERVAL` | Services, registration, cloud, remote access, plugins |

Intervals are **fixed** (not user-configurable) per HA Core guidelines.

## Data Classes

Each coordinator returns a typed dataclass:

- `UnraidSystemData` — `info: ServerInfo`, `metrics: SystemMetrics`, `containers`, `vms`, `ups_devices`, `notification_overview`
- `UnraidStorageData` — `array: UnraidArray`, `shares`, `parity_history` + convenience properties
- `UnraidInfraData` — `services`, `registration`, `cloud`, `remote_access`, `plugins`, `vars`

## Error Handling

```python
async def _async_update_data(self) -> UnraidXxxData:
    try:
        # Core queries (must succeed)
        ...
    except UnraidAuthenticationError as err:
        raise ConfigEntryAuthFailed(...) from err
    except (UnraidConnectionError, UnraidTimeoutError) as err:
        self._previously_unavailable = True
        raise UpdateFailed(...) from err
```

## Optional Services Pattern

Docker, VMs, and UPS may not be enabled. Query them separately with graceful fallback:

```python
async def _query_optional_docker(self) -> list[DockerContainer]:
    try:
        return await self.api_client.typed_get_containers()
    except (UnraidAPIError, UnraidConnectionError) as err:
        _LOGGER.debug("Docker data not available: %s", err)
        return []
```

## Recovery Logging

Track previous unavailability and log when connection is restored:

```python
if self._previously_unavailable:
    _LOGGER.info("Connection restored to Unraid server %s", self._server_name)
    self._previously_unavailable = False
```

## Constructor

Always pass `config_entry=` to the parent:

```python
super().__init__(
    hass,
    logger=_LOGGER,
    name=f"{server_name} System",
    update_interval=timedelta(seconds=SYSTEM_POLL_INTERVAL),
    config_entry=config_entry,
)
```
