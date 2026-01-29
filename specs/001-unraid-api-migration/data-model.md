# Data Model: Migrate to unraid-api Python Library

**Date**: 2026-01-12
**Feature**: 001-unraid-api-migration

## Overview

This document describes the data model changes for migrating from local models to unraid-api library models. The key principle is **direct adoption** of library models rather than wrapping them.

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              UnraidClient                                    │
│                         (from unraid_api)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
    ┌───────────────────────────┐   ┌───────────────────────────────┐
    │   UnraidSystemCoordinator │   │   UnraidStorageCoordinator    │
    │      (fetch interval: 30s)│   │      (fetch interval: 300s)   │
    └───────────────────────────┘   └───────────────────────────────┘
                    │                               │
                    ▼                               ▼
    ┌───────────────────────────┐   ┌───────────────────────────────┐
    │     UnraidSystemData      │   │     UnraidStorageData         │
    │  ┌─────────────────────┐  │   │  ┌─────────────────────────┐  │
    │  │ info: ServerInfo    │  │   │  │ array: UnraidArray      │  │
    │  │ metrics: SystemMetrics│ │   │  │ shares: list[Share]    │  │
    │  │ containers: list[DC]│  │   │  └─────────────────────────┘  │
    │  │ vms: list[VmDomain] │  │   │                               │
    │  │ ups: list[UPSDevice]│  │   │  UnraidArray contains:        │
    │  │ notifications: int  │  │   │  - state: str                 │
    │  └─────────────────────┘  │   │  - capacity: ArrayCapacity    │
    └───────────────────────────┘   │  - parityCheckStatus: Parity  │
                                    │  - boot: ArrayDisk            │
                                    │  - disks: list[ArrayDisk]     │
                                    │  - parities: list[ArrayDisk]  │
                                    │  - caches: list[ArrayDisk]    │
                                    └───────────────────────────────┘
```

## Models from unraid_api.models

### Core System Models

#### ServerInfo
```python
class ServerInfo(UnraidBaseModel):
    """Server identification and version information."""
    uuid: str
    hostname: str
    manufacturer: str | None
    model: str | None
    serial: str | None
    os_version: str | None
    api_version: str | None
    unraid_version: str | None
    kernel: str | None
```

#### SystemMetrics
```python
class SystemMetrics(UnraidBaseModel):
    """CPU, memory, and uptime metrics."""
    cpu: CpuUtilization
    memory: MemoryUtilization
    uptime: datetime | None
```

#### CpuUtilization
```python
class CpuUtilization(UnraidBaseModel):
    """CPU usage metrics."""
    percentTotal: float
```

#### MemoryUtilization
```python
class MemoryUtilization(UnraidBaseModel):
    """Memory usage metrics."""
    total: int  # bytes
    used: int
    free: int
    available: int
    percentTotal: float
    swapTotal: int | None
    swapUsed: int | None
    swapFree: int | None
```

### Storage Models

#### UnraidArray
```python
class UnraidArray(UnraidBaseModel):
    """Complete array state and disk information."""
    state: str  # "STARTED", "STOPPED", etc.
    capacity: ArrayCapacity | None
    parityCheckStatus: ParityCheck | None
    boot: ArrayDisk | None
    disks: list[ArrayDisk]
    parities: list[ArrayDisk]
    caches: list[ArrayDisk]
```

#### ArrayDisk
```python
class ArrayDisk(UnraidBaseModel):
    """Individual disk in the array."""
    id: str  # e.g., "disk:1", "parity:0", "cache:0"
    idx: int | None
    device: str | None  # e.g., "sda"
    name: str  # e.g., "Disk 1", "Parity", "Cache"
    type: str  # "Data", "Parity", "Cache", "Flash"
    size: int | None  # bytes
    fsSize: int | None
    fsUsed: int | None
    fsFree: int | None
    fsType: str | None  # "xfs", "btrfs", etc.
    temp: int | None  # Celsius
    status: str | None  # "DISK_OK", "DISK_NP", etc.
    isSpinning: bool | None
    smartStatus: str | None

    # Computed properties
    @property
    def usage_percent(self) -> float | None: ...

    @property
    def fs_size_bytes(self) -> int | None: ...

    @property
    def fs_used_bytes(self) -> int | None: ...

    @property
    def fs_free_bytes(self) -> int | None: ...
```

#### ArrayCapacity
```python
class ArrayCapacity(UnraidBaseModel):
    """Array total capacity."""
    kilobytes: CapacityKilobytes

    @property
    def total_bytes(self) -> int: ...

    @property
    def used_bytes(self) -> int: ...

    @property
    def free_bytes(self) -> int: ...

    @property
    def usage_percent(self) -> float: ...
```

#### ParityCheck
```python
class ParityCheck(UnraidBaseModel):
    """Parity check status."""
    status: str | None  # "idle", "running", "paused"
    progress: int | None  # percentage
    errors: int | None
    speed: int | None  # bytes/sec
    elapsed: int | None  # seconds
    estimated: int | None  # seconds remaining
```

#### Share
```python
class Share(UnraidBaseModel):
    """User share information."""
    id: str  # e.g., "share:appdata"
    name: str
    size: int | None  # kilobytes
    used: int | None
    free: int | None

    @property
    def size_bytes(self) -> int | None: ...

    @property
    def used_bytes(self) -> int | None: ...

    @property
    def free_bytes(self) -> int | None: ...

    @property
    def usage_percent(self) -> float | None: ...
```

### Container Models

#### DockerContainer
```python
class DockerContainer(UnraidBaseModel):
    """Docker container state and metadata."""
    id: str
    name: str  # with leading "/" stripped
    state: str  # "running", "exited", "paused", etc.
    image: str | None
    webUiUrl: str | None
    iconUrl: str | None
    ports: list[ContainerPort]
```

#### ContainerPort
```python
class ContainerPort(UnraidBaseModel):
    """Container port mapping."""
    privatePort: int
    publicPort: int | None
    type: str  # "tcp", "udp"
```

### VM Models

#### VmDomain
```python
class VmDomain(UnraidBaseModel):
    """Virtual machine state and configuration."""
    id: str
    name: str
    state: str  # "running", "shutoff", "paused", "idle"
    memory: int | None  # MiB
    vcpu: int | None
    autostart: bool | None
```

### UPS Models

#### UPSDevice
```python
class UPSDevice(UnraidBaseModel):
    """UPS device status."""
    id: str
    name: str
    status: str  # "OL" (online), "OB" (on battery), etc.
    battery: UPSBattery
    power: UPSPower
```

#### UPSBattery
```python
class UPSBattery(UnraidBaseModel):
    """UPS battery status."""
    chargeLevel: int | None  # percentage
    estimatedRuntime: int | None  # seconds
    health: str | None
```

#### UPSPower
```python
class UPSPower(UnraidBaseModel):
    """UPS power status."""
    inputVoltage: float | None
    outputVoltage: float | None
    loadPercentage: float | None
```

### Notification Models

#### NotificationOverview
```python
class NotificationOverview(UnraidBaseModel):
    """Notification counts by category."""
    unread: NotificationOverviewCounts
    archive: NotificationOverviewCounts
```

#### NotificationOverviewCounts
```python
class NotificationOverviewCounts(UnraidBaseModel):
    """Notification count breakdown."""
    info: int
    warning: int
    alert: int
    total: int
```

## Coordinator Data Classes

These remain in the integration but use library models:

### UnraidSystemData
```python
@dataclass
class UnraidSystemData:
    """Data from system coordinator."""
    info: ServerInfo  # from unraid_api.models
    metrics: SystemMetrics  # from unraid_api.models
    containers: list[DockerContainer]  # from unraid_api.models
    vms: list[VmDomain]  # from unraid_api.models
    ups_devices: list[UPSDevice]  # from unraid_api.models
    notifications_unread: int
```

### UnraidStorageData
```python
@dataclass
class UnraidStorageData:
    """Data from storage coordinator."""
    array: UnraidArray  # from unraid_api.models - contains all storage data
    shares: list[Share]  # from unraid_api.models

    # Convenience accessors delegating to array
    @property
    def array_state(self) -> str: ...

    @property
    def capacity(self) -> ArrayCapacity | None: ...

    @property
    def parity_status(self) -> ParityCheck | None: ...

    @property
    def boot(self) -> ArrayDisk | None: ...

    @property
    def disks(self) -> list[ArrayDisk]: ...

    @property
    def parities(self) -> list[ArrayDisk]: ...

    @property
    def caches(self) -> list[ArrayDisk]: ...
```

## Validation Rules

### Entity unique_id Construction

| Entity | Pattern | Source |
|--------|---------|--------|
| CPU Sensor | `{uuid}_cpu_usage` | ServerInfo.uuid |
| RAM Sensor | `{uuid}_ram_usage` | ServerInfo.uuid |
| Temp Sensor | `{uuid}_cpu_temp` | ServerInfo.uuid |
| Power Sensor | `{uuid}_cpu_power` | ServerInfo.uuid |
| Uptime Sensor | `{uuid}_uptime` | ServerInfo.uuid |
| Array State | `{uuid}_array_state` | ServerInfo.uuid |
| Array Usage | `{uuid}_array_usage` | ServerInfo.uuid |
| Parity Progress | `{uuid}_parity_progress` | ServerInfo.uuid |
| Disk Usage | `{uuid}_disk_{disk.id}_usage` | ArrayDisk.id |
| Share Usage | `{uuid}_share_{share.id}_usage` | Share.id |
| Flash Usage | `{uuid}_flash_usage` | ServerInfo.uuid |
| Container Switch | `{uuid}_container_switch_{name}` | DockerContainer.name |
| VM Switch | `{uuid}_vm_switch_{name}` | VmDomain.name |
| UPS Battery | `{uuid}_ups_{ups.id}_battery` | UPSDevice.id |
| UPS Load | `{uuid}_ups_{ups.id}_load` | UPSDevice.id |
| UPS Runtime | `{uuid}_ups_{ups.id}_runtime` | UPSDevice.id |
| UPS Power | `{uuid}_ups_{ups.id}_power` | UPSDevice.id |

### State Transitions

#### Array States
```
STOPPED → STARTING → STARTED
STARTED → STOPPING → STOPPED
STARTED → SYNC_STARTING → SYNC_IN_PROGRESS
SYNC_IN_PROGRESS → SYNC_COMPLETED → STARTED
```

#### Container States
```
created → running → paused → running
running → stopped/exited
stopped → running
```

#### VM States
```
shutoff → running → paused → running
running → shutoff
running → idle → running
```

## Files to Remove (models.py content replaced by library)

All of these models are now provided by `unraid_api.models`:

- SystemInfo, InfoSystem, InfoCpu, InfoOs, CoreVersions
- Metrics, CpuUtilization, MemoryUtilization
- UnraidArray, ArrayDisk, ArrayCapacity, ParityCheck, CapacityKilobytes
- Share
- DockerContainer, ContainerPort, ContainerHostConfig, DockerContainerStats
- VmDomain
- UPSDevice, UPSBattery, UPSPower
- Notification, NotificationOverview, NotificationOverviewCounts
- Registration, Service, Plugin, Flash, Owner, Cloud, Connect, RemoteAccess, LogFile
