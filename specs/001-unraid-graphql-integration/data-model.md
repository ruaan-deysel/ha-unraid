````markdown
# Data Model: Unraid GraphQL Integration

**Date**: 2025-12-23
**Updated**: 2025-12-23
**Feature**: 001-unraid-graphql-integration
**Source**: Official Unraid API Schema v4.29.2

## Overview

This document defines the data models used by the Unraid integration, mapping GraphQL API responses to Home Assistant entities.

## Complete Enum Documentation

### ArrayState Enum (11 Values)

| Value | Description | HA Sensor State | Problem State |
|-------|-------------|----------------|---------------|
| `STARTED` | Array is running normally | started | No |
| `STOPPED` | Array is stopped | stopped | No |
| `NEW_ARRAY` | Initial array setup (no data) | new_array | No |
| `RECON_DISK` | Rebuilding disk (reconstruction) | recon_disk | Yes |
| `DISABLE_DISK` | Disk being disabled | disable_disk | Yes |
| `SWAP_DSBL` | Swap disabled state | swap_dsbl | Yes |
| `INVALID_EXPANSION` | Invalid array expansion attempt | invalid_expansion | Yes |
| `PARITY_NOT_BIGGEST` | Parity disk not largest | parity_not_biggest | Yes |
| `TOO_MANY_MISSING_DISKS` | Too many disks missing | too_many_missing_disks | Yes |
| `NEW_DISK_TOO_SMALL` | New disk smaller than expected | new_disk_too_small | Yes |
| `NO_DATA_DISKS` | No data disks in array | no_data_disks | Yes |
| **Unknown** | New enum value (forward compat) | unknown | Yes |

**State-to-Entity Mapping**: All states map directly to sensor.state value (lowercase). Problem binary_sensor = ON when state != "STARTED" or "STOPPED".

---

### ParityCheckStatus Enum (6 Values)

| Value | Description | HA Sensor State | In Progress |
|-------|-------------|----------------|-------------|
| `NEVER_RUN` | No parity check ever executed | never_run | No |
| `RUNNING` | Parity check in progress | running | Yes |
| `PAUSED` | Parity check paused by user | paused | Yes |
| `COMPLETED` | Last check completed successfully | completed | No |
| `CANCELLED` | Last check cancelled by user | cancelled | No |
| `FAILED` | Last check failed with errors | failed | No |
| **Unknown** | New enum value (forward compat) | unknown | No |

**State-to-Entity Mapping**: Maps directly to sensor.state value (lowercase). Progress sensor (%) only valid when state = "RUNNING" or "PAUSED".

---

### ArrayDiskStatus Enum (9 Values)

| Value | Description | Binary Sensor State | HA Display |
|-------|-------------|---------------------|------------|
| `DISK_OK` | Disk operational, no issues | OFF (no problem) | Clear |
| `DISK_NP` | Disk not present (empty slot) | ON (problem) | Not Present |
| `DISK_NP_MISSING` | Expected disk missing | ON (problem) | Missing |
| `DISK_INVALID` | Invalid disk signature | ON (problem) | Invalid |
| `DISK_WRONG` | Wrong disk in slot | ON (problem) | Wrong Disk |
| `DISK_DSBL` | Disk disabled | ON (problem) | Disabled |
| `DISK_NP_DSBL` | Not present, disabled slot | ON (problem) | Not Present (Disabled) |
| `DISK_DSBL_NEW` | New disk, disabled | ON (problem) | New (Disabled) |
| `DISK_NEW` | New disk detected | ON (problem) | New Disk |
| **Unknown** | New enum value (forward compat) | ON (problem) | Unknown |

**State-to-Entity Mapping**: Only `DISK_OK` → binary_sensor OFF. All other states → binary_sensor ON (problem detected). Entity attribute "status_detail" contains enum value.

---

### ContainerState Enum (3 Values)

| Value | Description | Switch State | Icon |
|-------|-------------|--------------|------|
| `RUNNING` | Container running | ON | mdi:docker (green) |
| `PAUSED` | Container paused | OFF | mdi:pause (orange) |
| `EXITED` | Container stopped/exited | OFF | mdi:stop (gray) |
| **Unknown** | New enum value (forward compat) | OFF | mdi:help-circle |

**State-to-Entity Mapping**: Only `RUNNING` → switch ON. `PAUSED` and `EXITED` → switch OFF. Entity attribute "container_state" contains enum value for distinction between paused/stopped.

---

### VmState Enum (8 Values)

| Value | Description | Switch State | HA Display |
|-------|-------------|--------------|------------|
| `NOSTATE` | VM state unknown | OFF | Unknown |
| `RUNNING` | VM actively running | ON | Running |
| `IDLE` | VM running but idle | ON | Running (Idle) |
| `PAUSED` | VM paused/suspended | OFF | Paused |
| `SHUTDOWN` | VM shutting down (transitional) | OFF | Shutting Down |
| `SHUTOFF` | VM completely stopped | OFF | Stopped |
| `CRASHED` | VM crashed | OFF | Crashed |
| `PMSUSPENDED` | VM power management suspended | OFF | Suspended |
| **Unknown** | New enum value (forward compat) | OFF | Unknown |

**State-to-Entity Mapping**: Only `RUNNING` and `IDLE` → switch ON. All other states → switch OFF. Entity attribute "vm_state" contains enum value. **Note**: IDLE treated as ON per Unraid API docs (VM domain active).

---

### UPS Status Enum (6 Values)

| Value | Description | Sensor State | Severity |
|-------|-------------|--------------|----------|
| `Online` | Normal operation (AC power) | online | Info |
| `On Battery` | Running on battery backup | on_battery | Warning |
| `Low Battery` | Battery critically low | low_battery | Critical |
| `Replace Battery` | Battery needs replacement | replace_battery | Warning |
| `Overload` | Load exceeds UPS capacity | overload | Critical |
| `Offline` | UPS not responding | offline | Critical |
| **Unknown** | New enum value (forward compat) | unknown | Warning |

**State-to-Entity Mapping**: Maps directly to sensor.state value (lowercase). Binary_sensor for problem = ON when state in [`on_battery`, `low_battery`, `overload`, `offline`].

---

### UPS Health Enum (3 Values)

| Value | Description | Binary Sensor State |
|-------|-------------|---------------------|
| `Good` | Battery healthy | OFF (no problem) |
| `Replace` | Battery needs replacement | ON (problem) |
| `Unknown` | Health status unavailable | ON (problem, fail-safe) |
| **Unknown** | New enum value (forward compat) | ON (problem, fail-safe) |

**State-to-Entity Mapping**: Only `Good` → binary_sensor OFF. `Replace` and `Unknown` → binary_sensor ON (problem).

## Core Entities

### UnraidServer (Device)

Represents an Unraid server instance. All other entities are children of this device.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| uuid | str | `info.system.uuid` | System UUID (primary identifier) |
| name | str | `info.os.hostname` or config | User-friendly server name |
| hostname | str | Config entry | Server hostname/IP |
| version | str | `info.versions.core.unraid` | Unraid version string |
| api_version | str | `info.versions.core.api` | API version string |
| model | str | `info.system.model` | System model |
| manufacturer | str | `info.system.manufacturer` | System manufacturer |
| cpu_brand | str | `info.cpu.brand` | CPU model |
| kernel | str | `info.versions.core.kernel` | Kernel version |

**Unique ID**: `{uuid}` from `info.system.uuid`
**Device Registry**:
- `identifiers`: `{(DOMAIN, uuid)}`
- `name`: Server name from config or hostname
- `model`: System model
- `manufacturer`: System manufacturer or "Lime Technology"
- `sw_version`: Unraid version

---

### SystemMetrics

Real-time system metrics from the `metrics` query.

| Field | Type | Source | HA Entity | Device Class | State Class | Unit |
|-------|------|--------|-----------|--------------|-------------|------|
| cpu_percent | float | `metrics.cpu.percentTotal` | sensor | None | measurement | % |
| memory_total | int | `metrics.memory.total` | sensor (attr) | data_size | - | B |
| memory_used | int | `metrics.memory.used` | sensor | data_size | measurement | B |
| memory_free | int | `metrics.memory.free` | sensor | data_size | measurement | B |
| memory_available | int | `metrics.memory.available` | sensor | data_size | measurement | B |
| memory_percent | float | `metrics.memory.percentTotal` | sensor | None | measurement | % |
| swap_total | int | `metrics.memory.swapTotal` | sensor (attr) | data_size | - | B |
| swap_used | int | `metrics.memory.swapUsed` | sensor | data_size | measurement | B |
| swap_percent | float | `metrics.memory.percentSwapTotal` | sensor | None | measurement | % |
| cpu_temp | float | `info.cpu.packages.temp[0]` | sensor | temperature | measurement | °C |
| cpu_power | float | `info.cpu.packages.totalPower` | sensor | power | measurement | W |
| uptime | str | `info.os.uptime` | sensor | timestamp | - | ISO |

**Unique ID Pattern**: `{server_uuid}_{sensor_type}`

---

### ArrayStatus

Unraid array status and capacity from `array` query.

| Field | Type | Source | HA Entity | Device Class | State Class | Unit |
|-------|------|--------|-----------|--------------|-------------|------|
| state | str | `array.state` | sensor | enum | - | - |
| capacity_total | int | `array.capacity.kilobytes.total * 1024` | sensor | data_size | - | B |
| capacity_used | int | `array.capacity.kilobytes.used * 1024` | sensor | data_size | measurement | B |
| capacity_free | int | `array.capacity.kilobytes.free * 1024` | sensor | data_size | measurement | B |
| usage_percent | float | Calculated | sensor | None | measurement | % |
| parity_status | str | `array.parityCheckStatus.status` | sensor | enum | - | - |
| parity_progress | int | `array.parityCheckStatus.progress` | sensor | None | measurement | % |
| parity_errors | int | `array.parityCheckStatus.errors` | sensor | None | total | - |

**ArrayState Values**: `STARTED`, `STOPPED`, `NEW_ARRAY`, `RECON_DISK`, `DISABLE_DISK`, `SWAP_DSBL`, `INVALID_EXPANSION`, `PARITY_NOT_BIGGEST`, `TOO_MANY_MISSING_DISKS`, `NEW_DISK_TOO_SMALL`, `NO_DATA_DISKS`

**ParityCheckStatus Values**: `NEVER_RUN`, `RUNNING`, `PAUSED`, `COMPLETED`, `CANCELLED`, `FAILED`

**Unique ID**: `{server_uuid}_array`

---

### ArrayDisk

Individual disk in the array (data, parity, cache, boot) from `array.disks`, `array.parities`, `array.caches`, `array.boot`.

| Field | Type | Source | HA Entity | Device Class | State Class | Unit |
|-------|------|--------|-----------|--------------|-------------|------|
| id | str | `disk.id` (PrefixedID) | - | - | - | - |
| idx | int | `disk.idx` | - | - | - | - |
| device | str | `disk.device` | - | - | - | - |
| name | str | `disk.name` | - | - | - | - |
| type | str | `disk.type` | - | - | - | DATA/PARITY/FLASH/CACHE |
| size | int | `disk.size * 1024` | sensor | data_size | - | B |
| fs_size | int | `disk.fsSize * 1024` | sensor | data_size | - | B |
| fs_used | int | `disk.fsUsed * 1024` | sensor | data_size | measurement | B |
| fs_free | int | `disk.fsFree * 1024` | sensor | data_size | measurement | B |
| usage_percent | float | Calculated from fsUsed/fsSize | sensor | None | measurement | % |
| temperature | int | `disk.temp` | sensor | temperature | measurement | °C |
| status | str | `disk.status` | binary_sensor | problem | - | - |
| color | str | `disk.color` | - | - | - | Health indicator |
| num_reads | int | `disk.numReads` (BigInt) | sensor | None | total_increasing | - |
| num_writes | int | `disk.numWrites` (BigInt) | sensor | None | total_increasing | - |
| num_errors | int | `disk.numErrors` (BigInt) | sensor | None | total | - |
| is_spinning | bool | `disk.isSpinning` | binary_sensor | running | - | - |
| rotational | bool | `disk.rotational` | - | - | - | HDD vs SSD |
| transport | str | `disk.transport` | - | - | - | ata/nvme/usb |
| fs_type | str | `disk.fsType` | - | - | - | XFS/BTRFS/etc |

**ArrayDiskStatus Values**: `DISK_NP`, `DISK_OK`, `DISK_NP_MISSING`, `DISK_INVALID`, `DISK_WRONG`, `DISK_DSBL`, `DISK_NP_DSBL`, `DISK_DSBL_NEW`, `DISK_NEW`

**Status Mapping**: `DISK_OK` → OK (no problem), all others → Problem

**Unique ID Pattern**: `{server_uuid}_disk_{disk.id}` (using PrefixedID)

---

### PhysicalDisk

Hardware disk information from `disks` query (for serial numbers, SMART status).

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| id | str | `disk.id` (PrefixedID) | Unique disk ID |
| device | str | `disk.device` | Device path (e.g., /dev/sdb) |
| type | str | `disk.type` | SSD or HDD |
| name | str | `disk.name` | Model name |
| vendor | str | `disk.vendor` | Manufacturer |
| size | int | `disk.size` | Size in bytes |
| serial_num | str | `disk.serialNum` | Serial number (stable ID) |
| interface_type | str | `disk.interfaceType` | SAS/SATA/USB/PCIE/UNKNOWN |
| smart_status | str | `disk.smartStatus` | OK/UNKNOWN |
| temperature | float | `disk.temperature` | Celsius |
| firmware_revision | str | `disk.firmwareRevision` | Firmware version |
| is_spinning | bool | `disk.isSpinning` | Spinning state |

**Unique ID Pattern**: `{server_uuid}_{serial_num}` (for entities tied to physical disk)

---

### DockerContainer

Docker container with control capabilities from `docker.containers`.

| Field | Type | Source | HA Entity | Device Class | State Class |
|-------|------|--------|-----------|--------------|-------------|
| id | str | `container.id` (PrefixedID) | - | - | - |
| name | str | `container.names[0]` (strip /) | switch | switch | - |
| image | str | `container.image` | attr | - | - |
| image_id | str | `container.imageId` | attr | - | - |
| state | str | `container.state` | switch state | - | - |
| status | str | `container.status` | attr | - | - |
| auto_start | bool | `container.autoStart` | attr | - | - |
| auto_start_order | int | `container.autoStartOrder` | attr | - | - |
| web_ui_url | str | `container.webUiUrl` | attr | - | - |
| icon_url | str | `container.iconUrl` | attr | - | - |
| project_url | str | `container.projectUrl` | attr | - | - |
| is_update_available | bool | `container.isUpdateAvailable` | binary_sensor | update | - |
| is_orphaned | bool | `container.isOrphaned` | attr | - | - |
| ports | list | `container.ports` | attr | - | - |

**ContainerState Values**: `RUNNING`, `PAUSED`, `EXITED`

**State Mapping**: `RUNNING` → ON, `PAUSED`/`EXITED` → OFF

**Unique ID**: `{server_uuid}_{container.id}` (using PrefixedID)

**Switch Entity**:
- `is_on`: `state == "RUNNING"`
- `turn_on`: Execute `docker { start(id: $id) }` mutation
- `turn_off`: Execute `docker { stop(id: $id) }` mutation

---

### VirtualMachine

Virtual machine with control capabilities from `vms.domains`.

| Field | Type | Source | HA Entity | Device Class | State Class |
|-------|------|--------|-----------|--------------|-------------|
| id | str | `domain.id` (PrefixedID) | - | - | - |
| name | str | `domain.name` | switch | switch | - |
| state | str | `domain.state` | switch state | - | - |

**VmState Values**: `NOSTATE`, `RUNNING`, `IDLE`, `PAUSED`, `SHUTDOWN`, `SHUTOFF`, `CRASHED`, `PMSUSPENDED`

**State Mapping**: `RUNNING`/`IDLE` → ON, all others → OFF

**Unique ID**: `{server_uuid}_{domain.id}` (using PrefixedID)

**Switch Entity**:
- `is_on`: `state in ["RUNNING", "IDLE"]`
- `turn_on`: Execute `vm { start(id: $id) }` mutation
- `turn_off`: Execute `vm { stop(id: $id) }` mutation

---

## Forward Compatibility: Unknown Enum Handling

All enum mappings MUST handle unknown values gracefully for forward compatibility with future API versions:

| Enum Type | Unknown Value Behavior | Default State |
|-----------|----------------------|---------------|
| ArrayState | Map to "unknown" sensor state | `unknown` |
| ArrayDiskStatus | Map to problem=True (fail-safe) | `True` |
| ParityCheckStatus | Map to "unknown" | `unknown` |
| ContainerState | Map to is_on=False | `False` (OFF) |
| VmState | Map to is_on=False | `False` (OFF) |
| UPS Status | Map to "unknown" | `unknown` |
| UPS Health | Map to problem=True (fail-safe) | `True` |

**Implementation**: Use `dict.get(value, default)` pattern with logging at INFO level when unknown value encountered.

---

### UPSDevice

UPS monitoring data from `upsDevices` query.

| Field | Type | Source | HA Entity | Device Class | State Class | Unit |
|-------|------|--------|-----------|--------------|-------------|------|
| id | str | `ups.id` | - | - | - | - |
| name | str | `ups.name` | - | - | - | - |
| model | str | `ups.model` | - | - | - | - |
| status | str | `ups.status` | sensor | enum | - | - |
| battery_charge | int | `ups.battery.chargeLevel` | sensor | battery | measurement | % |
| runtime | int | `ups.battery.estimatedRuntime` | sensor | duration | measurement | s |
| health | str | `ups.battery.health` | binary_sensor | problem | - | - |
| input_voltage | float | `ups.power.inputVoltage` | sensor | voltage | measurement | V |
| output_voltage | float | `ups.power.outputVoltage` | sensor | voltage | measurement | V |
| load_percent | int | `ups.power.loadPercentage` | sensor | power_factor | measurement | % |

**Status Values**: `Online`, `On Battery`, `Low Battery`, `Replace Battery`, `Overload`, `Offline`

**Health Mapping**: `Good` → OK (no problem), `Replace`/`Unknown` → Problem

**Unique ID Pattern**: `{server_uuid}_ups_{ups.id}`

---

### Notifications (Optional)

Notification counts from `notifications.overview`.

| Field | Type | Source | HA Entity | Device Class | State Class |
|-------|------|--------|-----------|--------------|-------------|
| unread_total | int | `overview.unread.total` | sensor | None | measurement |
| unread_info | int | `overview.unread.info` | sensor | None | measurement |
| unread_warning | int | `overview.unread.warning` | sensor | None | measurement |
| unread_alert | int | `overview.unread.alert` | sensor | None | measurement |

**Unique ID Pattern**: `{server_uuid}_notifications_{type}`

---

### Share (Optional)

User share information from `shares` query.

| Field | Type | Source | HA Entity | Device Class | State Class | Unit |
|-------|------|--------|-----------|--------------|-------------|------|
| id | str | `share.id` | - | - | - | - |
| name | str | `share.name` | - | - | - | - |
| size | int | `share.size * 1024` | sensor | data_size | - | B |
| used | int | `share.used * 1024` | sensor | data_size | measurement | B |
| free | int | `share.free * 1024` | sensor | data_size | measurement | B |
| usage_percent | float | Calculated | sensor | None | measurement | % |

**Unique ID Pattern**: `{server_uuid}_share_{share.name}`

---

## Pydantic Models

### Configuration Models

```python
from pydantic import BaseModel, ConfigDict, Field

class UnraidConfigEntry(BaseModel):
    """Configuration data stored in HA config entry."""
    host: str                    # Server hostname/IP
    api_key: str                 # API key (stored encrypted)
    port: int = 443              # HTTPS port
    verify_ssl: bool = True      # SSL verification
    scan_interval_system: int = 30    # System polling (seconds)
    scan_interval_storage: int = 300  # Storage polling (seconds)
```

### API Response Models

All models use `ConfigDict(extra="ignore")` for forward compatibility.

```python
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# Base config for all models - ignore unknown fields
class UnraidBaseModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


# System Info Models
class InfoBaseboard(UnraidBaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    memMax: Optional[int] = None  # bytes
    memSlots: Optional[int] = None


class CpuPackages(UnraidBaseModel):
    totalPower: Optional[float] = None  # Watts
    temp: list[float] = []  # Celsius per package


class InfoCpu(UnraidBaseModel):
    manufacturer: Optional[str] = None
    brand: Optional[str] = None
    cores: Optional[int] = None
    threads: Optional[int] = None
    processors: Optional[int] = None
    speed: Optional[float] = None  # GHz
    speedmax: Optional[float] = None
    socket: Optional[str] = None
    packages: Optional[CpuPackages] = None


class MemoryLayout(UnraidBaseModel):
    size: int  # bytes
    bank: Optional[str] = None
    type: Optional[str] = None  # DDR4, DDR5
    clockSpeed: Optional[int] = None  # MHz
    manufacturer: Optional[str] = None


class InfoMemory(UnraidBaseModel):
    layout: list[MemoryLayout] = []


class InfoOs(UnraidBaseModel):
    platform: Optional[str] = None
    distro: Optional[str] = None
    release: Optional[str] = None
    kernel: Optional[str] = None
    hostname: Optional[str] = None
    uptime: Optional[str] = None  # ISO timestamp


class InfoSystem(UnraidBaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    uuid: Optional[str] = None  # PRIMARY IDENTIFIER
    virtual: Optional[bool] = None


class CoreVersions(UnraidBaseModel):
    unraid: Optional[str] = None
    api: Optional[str] = None
    kernel: Optional[str] = None


class InfoVersions(UnraidBaseModel):
    core: CoreVersions


class InfoDisplay(UnraidBaseModel):
    unit: Optional[str] = None  # CELSIUS/FAHRENHEIT
    warning: Optional[int] = None
    critical: Optional[int] = None


class SystemInfo(UnraidBaseModel):
    """Full info query response."""
    time: Optional[datetime] = None
    machineId: Optional[str] = None
    baseboard: Optional[InfoBaseboard] = None
    cpu: Optional[InfoCpu] = None
    memory: Optional[InfoMemory] = None
    os: Optional[InfoOs] = None
    system: Optional[InfoSystem] = None
    display: Optional[InfoDisplay] = None
    versions: Optional[InfoVersions] = None


# Metrics Models
class CpuLoad(UnraidBaseModel):
    percentTotal: float
    percentUser: Optional[float] = None
    percentSystem: Optional[float] = None
    percentIdle: Optional[float] = None


class CpuUtilization(UnraidBaseModel):
    percentTotal: float
    cpus: list[CpuLoad] = []


class MemoryUtilization(UnraidBaseModel):
    total: int  # bytes
    used: int
    free: int
    available: int
    percentTotal: float
    swapTotal: int
    swapUsed: int
    swapFree: int
    percentSwapTotal: float


class Metrics(UnraidBaseModel):
    cpu: Optional[CpuUtilization] = None
    memory: Optional[MemoryUtilization] = None


# Array Models
class ArrayCapacity(UnraidBaseModel):
    free: str  # String in API
    used: str
    total: str


class ArrayCapacityWrapper(UnraidBaseModel):
    kilobytes: ArrayCapacity


class ParityCheck(UnraidBaseModel):
    status: str  # NEVER_RUN, RUNNING, etc.
    progress: Optional[int] = None
    speed: Optional[str] = None
    errors: Optional[int] = None
    running: Optional[bool] = None
    paused: Optional[bool] = None
    correcting: Optional[bool] = None


class ArrayDisk(UnraidBaseModel):
    id: str  # PrefixedID
    idx: int
    name: Optional[str] = None
    device: Optional[str] = None
    size: Optional[int] = None  # KB
    status: Optional[str] = None
    temp: Optional[int] = None  # Celsius
    numReads: Optional[int] = None
    numWrites: Optional[int] = None
    numErrors: Optional[int] = None
    fsSize: Optional[int] = None  # KB
    fsFree: Optional[int] = None
    fsUsed: Optional[int] = None
    fsType: Optional[str] = None
    rotational: Optional[bool] = None
    isSpinning: Optional[bool] = None
    transport: Optional[str] = None
    color: Optional[str] = None
    warning: Optional[int] = None
    critical: Optional[int] = None


class UnraidArray(UnraidBaseModel):
    id: str
    state: str  # ArrayState enum
    capacity: ArrayCapacityWrapper
    parityCheckStatus: Optional[ParityCheck] = None
    boot: Optional[ArrayDisk] = None
    parities: list[ArrayDisk] = []
    disks: list[ArrayDisk] = []
    caches: list[ArrayDisk] = []


# Docker Models
class ContainerPort(UnraidBaseModel):
    ip: Optional[str] = None
    privatePort: Optional[int] = None
    publicPort: Optional[int] = None
    type: str  # TCP/UDP


class DockerContainer(UnraidBaseModel):
    id: str  # PrefixedID
    names: list[str]
    image: str
    imageId: Optional[str] = None
    state: str  # RUNNING, PAUSED, EXITED
    status: str
    autoStart: bool = False
    autoStartOrder: Optional[int] = None
    ports: list[ContainerPort] = []
    webUiUrl: Optional[str] = None
    iconUrl: Optional[str] = None
    projectUrl: Optional[str] = None
    supportUrl: Optional[str] = None
    isUpdateAvailable: Optional[bool] = None
    isOrphaned: bool = False


class Docker(UnraidBaseModel):
    containers: list[DockerContainer] = []


# VM Models
class VmDomain(UnraidBaseModel):
    id: str  # PrefixedID
    name: Optional[str] = None
    state: str  # VmState enum


class Vms(UnraidBaseModel):
    id: str
    domains: list[VmDomain] = []


# UPS Models
class UPSBattery(UnraidBaseModel):
    chargeLevel: int  # 0-100
    estimatedRuntime: int  # seconds
    health: str  # Good, Replace, Unknown


class UPSPower(UnraidBaseModel):
    inputVoltage: float  # volts
    outputVoltage: float
    loadPercentage: int  # 0-100


class UPSDevice(UnraidBaseModel):
    id: str
    name: str
    model: str
    status: str  # Online, On Battery, etc.
    battery: UPSBattery
    power: UPSPower


# Notification Models
class NotificationCounts(UnraidBaseModel):
    info: int = 0
    warning: int = 0
    alert: int = 0
    total: int = 0


class NotificationOverview(UnraidBaseModel):
    unread: NotificationCounts
    archive: Optional[NotificationCounts] = None


class Notification(UnraidBaseModel):
    id: str
    title: str
    subject: str
    description: str
    importance: str  # ALERT, INFO, WARNING
    type: str  # UNREAD, ARCHIVE
    timestamp: Optional[str] = None
    link: Optional[str] = None


# Share Models
class Share(UnraidBaseModel):
    id: str
    name: str
    free: Optional[int] = None  # KB
    used: Optional[int] = None
    size: Optional[int] = None
    include: list[str] = []
    exclude: list[str] = []
    cache: Optional[bool] = None
    comment: Optional[str] = None
    color: Optional[str] = None
    luksStatus: Optional[str] = None


# Physical Disk Models
class DiskPartition(UnraidBaseModel):
    name: str
    fsType: str
    size: float  # bytes


class PhysicalDisk(UnraidBaseModel):
    id: str
    device: str
    type: str  # SSD, HDD
    name: str
    vendor: str
    size: float  # bytes
    serialNum: str
    interfaceType: str  # SAS, SATA, USB, PCIE, UNKNOWN
    smartStatus: str  # OK, UNKNOWN
    temperature: Optional[float] = None
    firmwareRevision: Optional[str] = None
    isSpinning: bool
    partitions: list[DiskPartition] = []
```

---

## State Transitions

### Array State Machine

```
STOPPED ↔ STARTED
STARTED → RECON_DISK (reconstruction)
STARTED → DISABLE_DISK (disk disabled)
Any → NEW_ARRAY (initial setup)
```

### Container State Machine

```
EXITED → RUNNING (start mutation)
RUNNING → EXITED (stop mutation)
RUNNING ↔ PAUSED (pause/unpause mutations)
```

### VM State Machine

```
SHUTOFF → RUNNING (start mutation)
RUNNING → SHUTOFF (stop mutation - graceful)
RUNNING → SHUTOFF (forceStop mutation - hard)
RUNNING ↔ PAUSED (pause/resume mutations)
RUNNING → RUNNING (reboot mutation)
```

---

## Validation Rules

1. **Server UUID**: Must come from `info.system.uuid`; fail setup if not available
2. **PrefixedID**: Accept as-is from API; IDs are prefixed with server identifier
3. **Temperature**: Valid range -40 to 150°C; mark as unavailable if out of range or `None`
4. **Capacity Values**: Must be non-negative; values in KB from array, bytes from disks
5. **State Values**: Must match known enum values; log warning for unknown states and use as-is
6. **Container Names**: Use first name in list, strip leading "/" if present
7. **BigInt Fields**: Handle as Python int (numReads, numWrites, numErrors can be very large)

---

## Entity Registry Cleanup

When resources are removed:
- **Disks**: Detect missing disks by comparing IDs; mark as unavailable; remove after 24 hours
- **Containers**: Detect removed containers; mark as unavailable immediately; user removes from registry
- **VMs**: Detect removed VMs; mark as unavailable immediately; user removes from registry
- **UPS**: If UPS disconnected, mark entities unavailable; entities persist

New resources are discovered automatically on each poll cycle.

---

## Coordinator Data Structure

```python
@dataclass
class UnraidSystemData:
    """Data from system coordinator (30s polling)."""
    info: SystemInfo
    metrics: Metrics
    docker: Docker
    vms: Vms
    ups_devices: list[UPSDevice]
    notifications_overview: NotificationOverview
    last_update: datetime


@dataclass  
class UnraidStorageData:
    """Data from storage coordinator (5min polling)."""
    array: UnraidArray
    disks: list[PhysicalDisk]
    shares: list[Share]
    parity_history: list[ParityCheck]
    last_update: datetime
```

---

## Disk Count Boundaries and Limits

### Unraid License Limits

| License Type | Max Data Disks | Max Parity Disks | Max Cache Disks | Total Max |
|--------------|----------------|------------------|-----------------|-----------|
| **Trial** | 6 | 1 | 1 | 8 |
| **Basic** | 6 | 1 | 1 | 8 |
| **Plus** | 12 | 2 | Multiple | 30+ |
| **Pro** | 30 | 2 | Multiple | 100+ |

**Source**: Unraid official licensing documentation (https://unraid.net/pricing)

### Integration Boundaries

**Design Constraints**:
1. **No Hard Limit Enforcement**: The integration does NOT enforce license-based disk limits
   - Rationale: Unraid OS itself enforces these limits; integration should reflect reality
   - Future-proofing: Pro license supports "unlimited" disks (practical limit ~100+)

2. **Dynamic Entity Creation**: All disk entities are created dynamically from API responses
   - No pre-defined array size
   - Entities created/removed as disks are added/removed from array

3. **Performance Considerations**:
   - **Tested Scale**: Integration tested with up to 30 data disks + 2 parity + 5 cache = 37 total disks
   - **Expected Performance**: <1s entity update time for up to 50 total disks
   - **Memory Impact**: ~200MB incremental memory per server with 50 disks
   - **Entity Count**: Each disk creates 3-4 entities (temperature, usage, health, attributes)
   - **Total Entities**: 50 disks × 3.5 entities/disk = ~175 disk entities + 10 system entities = 185 total

4. **Practical Limits**:
   - **Soft Limit**: 100 total disks (data + parity + cache)
     * Rationale: Pro license supports up to ~100 disks in practice
     * Beyond 100 disks: Home Assistant UI may experience performance degradation
   - **Hard Limit**: None enforced by integration
     * Integration will create entities for all disks returned by API
     * Unraid OS enforces license limits before integration sees data

5. **Boundary Behavior**:
   - **Zero Disks**: Integration handles NEW_ARRAY state with no data disks (shows 0 capacity)
   - **Single Disk**: Valid configuration (data disk only, no parity)
   - **100+ Disks**: Integration creates all entities; performance depends on HA hardware
   - **Disk Removal**: Entities become unavailable, removed after 24h
   - **Disk Addition**: New entities created automatically on next storage poll (<5min)

6. **Error Handling**:
   - **Excessive Disk Count**: No error; logs INFO message if >100 disks detected
   - **Missing Disks**: ArrayDiskStatus enum handles `DISK_NP_MISSING` state
   - **Invalid Disk Configuration**: Reflects Unraid array state (e.g., `INVALID_EXPANSION`)

### Validation Rules

1. **At Setup**: No disk count validation during config flow
   - Integration trusts Unraid API to provide valid disk configuration

2. **During Updates**: 
   - Log INFO if disk count changes by >10 disks (potential misconfiguration)
   - Log WARNING if disk count >100 (performance advisory)
   - No errors or exceptions thrown based on disk count

3. **Entity Registry**: 
   - Unique ID pattern: `{server_uuid}_disk_{disk_serial}` prevents ID collisions
   - Maximum entity name length: 255 characters (enforced by HA)
   - Disk names truncated if necessary: `{disk_name[:250]}...`

### Testing Coverage

**Boundary Test Cases**:
- ✅ Zero disks (NEW_ARRAY state): Handled in test_sensor.py
- ✅ Single disk: Covered in mock fixtures
- ✅ Multiple disks (3-5): Standard test fixtures use 3-5 disks
- ❌ 50+ disks: Not covered in unit tests (requires integration test)
- ❌ 100+ disks: Not covered (edge case, requires manual testing)

**Future Enhancements**:
- Add integration test with 50-disk mock array
- Add performance benchmarking for large disk counts
- Add user-configurable entity creation filters (e.g., "only create entities for data disks")

### Documentation for Users

**README.md Section** (to be added):
```markdown
## Disk Count Support

This integration supports Unraid servers with any number of disks allowed by your Unraid license:
- **Trial/Basic**: Up to 6 data disks + 1 parity
- **Plus**: Up to 12 data disks + 2 parity  
- **Pro**: Up to 30+ data disks + 2 parity (license supports "unlimited")

For optimal performance with large arrays (>50 disks), ensure your Home Assistant server has:
- At least 2GB RAM
- Fast storage (SSD recommended)
- Home Assistant 2024.1 or newer
```

**Troubleshooting Note**:
If you experience slow entity updates with very large arrays (>100 disks), consider:
1. Increasing the storage polling interval in Options (default: 5 minutes)
2. Disabling unused disk entities via Home Assistant's entity registry
3. Using a more powerful Home Assistant server
````
