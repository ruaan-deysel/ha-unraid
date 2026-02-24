---
applyTo: "custom_components/unraid/sensor.py,custom_components/unraid/binary_sensor.py,custom_components/unraid/switch.py,custom_components/unraid/button.py,custom_components/unraid/entity.py"
---

# Entity Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Entity Class Hierarchy

```
CoordinatorEntity
  └── UnraidBaseEntity          # device_info, unique_id, availability
        └── UnraidEntity        # + EntityDescription support
```

## MRO Pattern

Platform entities inherit from both the HA platform entity and the Unraid base:

```python
class MySwitch(UnraidBaseEntity, SwitchEntity):
    """Description."""
```

Order matters: `PlatformEntity` last in MRO so `UnraidBaseEntity.__init__` runs correctly.

## Required Attributes

- `_attr_has_entity_name = True` (set on `UnraidBaseEntity`)
- `_attr_translation_key = "..."` — maps to `strings.json` and `icons.json`
- Unique ID: constructed as `{server_uuid}_{resource_id}` in `UnraidBaseEntity.__init__`

## Constructor Pattern

```python
def __init__(
    self,
    coordinator: UnraidSystemCoordinator,
    server_uuid: str,
    server_name: str,
    server_info: dict | None = None,
) -> None:
    super().__init__(
        coordinator=coordinator,
        server_uuid=server_uuid,
        server_name=server_name,
        resource_id="my_resource",
        name="My Resource",
        server_info=server_info,
    )
```

## State Properties

Use `@property` — never store mutable state on the entity:

```python
@property
def native_value(self) -> float | None:
    data: UnraidSystemData | None = self.coordinator.data
    if data is None:
        return None
    return data.metrics.cpu_usage
```

## Per-Resource Entities (Disks, Containers, VMs)

Store the resource ID and implement a lookup helper:

```python
def __init__(self, ..., disk: ArrayDisk) -> None:
    self._disk_id = disk.id
    super().__init__(..., resource_id=f"disk_{disk.id}_temp", ...)

def _get_disk(self) -> ArrayDisk | None:
    data: UnraidStorageData | None = self.coordinator.data
    if data is None:
        return None
    for disk in data.disks + data.parities + data.caches:
        if disk.id == self._disk_id:
            return disk
    return None
```

## Entity Actions (Switches, Buttons)

Wrap API calls in try/except with translated errors:

```python
async def async_turn_on(self, **kwargs: Any) -> None:
    try:
        await self.api_client.start_container(self._container_id)
        await self.coordinator.async_request_refresh()
    except Exception as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="container_start_failed",
            translation_placeholders={"error": str(err)},
        ) from err
```

## Device Info

All entities share a single device per server, identified by `(DOMAIN, server_uuid)`.

## Translation Keys

- Add entity translation keys to `strings.json` under `entity.{platform}.{key}.name`
- Add icon mappings to `icons.json` under `entity.{platform}.{key}.default`
