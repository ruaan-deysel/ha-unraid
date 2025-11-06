---
type: "always_apply"
---

# Home Assistant Unraid Integration - AI Agent Rule File

**Scope**: This rule file defines universal standards for Unraid entities in Home Assistant, applicable to all Unraid integrations regardless of communication protocol (SSH, GraphQL, REST API, etc.).

## Table of Contents
1. [Integration Overview](#integration-overview)
2. [File Organization Standards](#file-organization-standards)
3. [Entity Platform Standards](#entity-platform-standards)
4. [Naming Convention Rules](#naming-convention-rules)
5. [Entity Inventory and Groupings](#entity-inventory-and-groupings)
6. [Complete Attribute Reference](#complete-attribute-reference)
7. [Device Info Standards](#device-info-standards)
8. [State Management Patterns](#state-management-patterns)
9. [Code Templates](#code-templates)
10. [Data Coordinator Patterns](#data-coordinator-patterns)

---

## 1. Integration Overview

### Domain and Basic Information
- **Domain**: `unraid` (or variant like `unraid_graphql`, `unraid_management`)
- **Version Format**: `YYYY.MM.DD` (e.g., "2025.06.12")
- **Quality Scale**: `silver` or higher
- **IoT Class**: `local_polling` or `cloud_polling` (depending on implementation)
- **Config Flow**: UI-based configuration (no YAML)
- **Migration Version**: `2` (current standard)

### Supported Platforms
All Unraid integrations should support these four Home Assistant platforms:
1. **SENSOR** - System metrics, storage usage, network statistics, UPS monitoring
2. **BINARY_SENSOR** - Status indicators, health monitoring, connectivity checks
3. **SWITCH** - VM control, Docker container management
4. **BUTTON** - System actions (reboot, shutdown), user script execution

### Architecture Pattern
- **Coordinator Pattern**: `UnraidDataUpdateCoordinator` extends `DataUpdateCoordinator[UnraidDataDict]` to centralize data fetching from any source
- **Factory/Registry Pattern**: `SensorFactory` + `register_all_sensors()` enable dynamic sensor creation based on hardware
- **Modern Runtime Data**: Uses `entry.runtime_data` (not deprecated `hass.data`)
- **Entity Format v2**: Modern naming with `has_entity_name = True`
- **Protocol Agnostic**: Data source can be SSH, GraphQL, REST API, WebSocket, or any other communication method

---

## 2. File Organization Standards

### Directory Structure
```
custom_components/unraid*/
├── __init__.py, manifest.json, config_flow.py, const.py, coordinator.py
├── entity_naming.py, helpers.py
├── sensor.py, binary_sensor.py, button.py, switch.py
├── api/                        # Communication layer (protocol-specific: client.py, data_fetcher.py, etc.)
├── sensors/                    # Sensor implementations (base.py, factory.py, registry.py, metadata.py)
│   └── system.py, storage.py, network.py, ups.py, docker.py
├── diagnostics/                # Binary sensors (base.py, disk.py, parity.py, array.py, ups.py)
└── performance/                # Optimization (cache_manager.py, sensor_priority.py)
```

**Note**: The `api/` directory contains protocol-specific implementation (SSH client, GraphQL client, REST client, etc.) but the entity structure remains consistent.

### Naming Conventions
**Files**: `{platform}.py`, `{category}.py`, `base.py`, `const.py`
**Classes**: `Unraid{Feature}Sensor`, `Unraid{Feature}Switch`, `Unraid{Feature}Button`, `Unraid{Type}Base`, `{Feature}Mixin`

---

## 3. Entity Platform Standards

### 3.1 Sensor Platform

#### Entry Point Pattern
```python
async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data.coordinator
    register_all_sensors()
    entities = SensorFactory.create_all_sensors(coordinator)
    async_add_entities(entities)
```

#### Base Sensor Class
All sensors extend `UnraidSensorBase(CoordinatorEntity, SensorEntity)`:

```python
class UnraidSensorBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True  # REQUIRED

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        naming = EntityNaming(domain=DOMAIN, hostname=coordinator.hostname, component="system")
        self._attr_unique_id = naming.get_entity_id(description.key)

    @property
    def device_info(self):
        return get_server_device_info(self.coordinator)

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self):
        return self.coordinator.last_update_success and self.entity_description.available_fn(self.coordinator.data)
```

**Required**: `_attr_has_entity_name = True`, `unique_id` (via EntityNaming), `device_info`, `native_value`, `available`

#### Sensor Description
```python
@dataclass
class UnraidSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] = field(default=lambda _: None)
    available_fn: Callable[[dict[str, Any]], bool] = field(default=lambda _: True)
```

**Categories**: System (CPU, RAM, temps, fans, GPU), Storage (array, disks, pools), Network (interfaces), UPS (power, energy), Docker (containers)

### 3.2 Binary Sensor Platform

#### Entry Point Pattern
```python
async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data.coordinator
    entities = [UnraidArrayStatusBinarySensor(coordinator), UnraidArrayHealthSensor(coordinator)]

    if coordinator.has_ups:
        entities.append(UnraidUPSBinarySensor(coordinator))

    if coordinator.data.get("system_stats", {}).get("parity_info"):
        entities.extend([UnraidParityCheckSensor(coordinator), UnraidParityErrorsSensor(coordinator)])

    for disk in coordinator.data.get("system_stats", {}).get("individual_disks", []):
        disk_name = disk.get("name", "")
        if disk_name.startswith("disk"):
            entities.append(UnraidArrayDiskSensor(coordinator, disk_name))
        elif is_pool_disk(disk):
            entities.append(UnraidPoolDiskSensor(coordinator, disk_name))

    async_add_entities(entities)
```

#### Base Binary Sensor Class
```python
class UnraidBinarySensorBase(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        naming = EntityNaming(domain=DOMAIN, hostname=coordinator.hostname, component="diagnostics")
        self._attr_unique_id = naming.get_entity_id(description.key)

    @property
    def is_on(self):
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except (KeyError, TypeError, AttributeError) as err:
            _LOGGER.debug("Error getting binary sensor state: %s", err)
            return None
```

**Categories**: Array Status, Disk Health, Parity, UPS, System Health

### 3.3 Switch Platform

#### Entry Point Pattern
```python
async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data.coordinator
    entities = []

    for container in coordinator.data.get("docker_containers", []):
        entities.append(UnraidDockerContainerSwitch(coordinator, container["name"]))

    for vm in coordinator.data.get("vms", []):
        entities.append(UnraidVMSwitch(coordinator, vm["name"]))

    async_add_entities(entities)
```

#### Base Switch Class
```python
class UnraidSwitchEntity(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    @property
    def is_on(self) -> bool:
        raise NotImplementedError

    async def async_turn_on(self, **kwargs: Any) -> None:
        raise NotImplementedError

    async def async_turn_off(self, **kwargs: Any) -> None:
        raise NotImplementedError
```

**Required Methods**: `is_on`, `async_turn_on`, `async_turn_off`

### 3.4 Button Platform

#### Entry Point Pattern
```python
async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data.coordinator
    entities = []

    for description in BUTTON_DESCRIPTIONS:
        entities.append(UnraidButton(coordinator, description))

    for script in coordinator.data.get("user_scripts", []):
        entities.append(UnraidScriptButton(coordinator, script["name"]))

    async_add_entities(entities)
```

#### Button Description Pattern
```python
BUTTON_DESCRIPTIONS = [
    UnraidButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart",
        press_fn=lambda coordinator: coordinator.api.reboot_system(),
    ),
]
```

**Required Properties**: `entity_category = EntityCategory.CONFIG`, `entity_registry_enabled_default = False`, `press_fn`

---

## 4. Naming Convention Rules

### 4.1 Entity ID Format
**Pattern**: `{platform}.{hostname}_{feature}_{subfeature}`

**Examples**:
- `sensor.tower_cpu_usage`
- `sensor.tower_disk_disk1`
- `binary_sensor.tower_array_status`
- `switch.tower_docker_plex`
- `button.tower_reboot`

**Rules**:
- Hostname is always lowercase
- Underscores separate components
- No duplicate hostname/domain in ID

### 4.2 Unique ID Format
**Pattern**: `{entry_id}_{component}_{feature}_{subfeature}`

**Examples**:
- `abc123_system_cpu_usage`
- `abc123_storage_disk_disk1`
- `abc123_diagnostics_array_status`

**Generation**:
```python
naming = EntityNaming(
    domain=DOMAIN,
    hostname=coordinator.hostname,
    component="system"  # or "storage", "network", "diagnostics", etc.
)
unique_id = naming.get_entity_id(description.key)
```

### 4.3 Device ID Patterns
Defined in `const.py`:

```python
DEVICE_ID_SERVER = "{}_server_{}"  # DOMAIN, entry_id
DEVICE_ID_DOCKER = "{}_docker_{}_{}"  # DOMAIN, container_name, entry_id
DEVICE_ID_VM = "{}_vm_{}_{}"  # DOMAIN, vm_name, entry_id
DEVICE_ID_DISK = "{}_disk_{}_{}"  # DOMAIN, disk_name, entry_id
DEVICE_ID_UPS = "{}_ups_{}"  # DOMAIN, entry_id
```

### 4.4 Device Name Patterns
- **Main Server**: `{hostname.title()}` (e.g., "Tower")
- **System Components**: `Unraid System ({hostname})`
- **Docker Containers**: `{container_name}` (as-is)
- **Virtual Machines**: `{vm_name}` (as-is)
- **Storage Devices**: `Unraid Disk ({disk_name})`
- **UPS**: `Unraid UPS ({hostname})`

---

## 5. Entity Inventory and Groupings

### 5.1 System Sensors Group

| Entity Key | Entity Name | Device Class | Unit | State Class | Icon |
|------------|-------------|--------------|------|-------------|------|
| `cpu_usage` | CPU Usage | `power_factor` | `%` | `measurement` | `mdi:cpu-64-bit` |
| `ram_usage` | RAM Usage | `power_factor` | `%` | `measurement` | `mdi:memory` |
| `uptime` | Uptime | `duration` | `s` | `measurement` | `mdi:clock-outline` |
| `cpu_temp` | CPU Temperature | `temperature` | `°C` | `measurement` | `mdi:thermometer` |
| `motherboard_temp` | Motherboard Temperature | `temperature` | `°C` | `measurement` | `mdi:thermometer` |
| `docker_vdisk` | Docker vDisk | `power_factor` | `%` | `measurement` | `mdi:docker` |
| `log_filesystem` | Log Filesystem | `power_factor` | `%` | `measurement` | `mdi:file-document-outline` |
| `boot_usage` | Boot Usage | `power_factor` | `%` | `measurement` | `mdi:harddisk` |
| `fan_{id}` | Fan {id} | None | `RPM` | `measurement` | `mdi:fan` |
| `intel_gpu_usage` | Intel GPU Usage | `power_factor` | `%` | `measurement` | `mdi:expansion-card` |

**Update Priority**: High (2 minutes) for CPU/RAM/temps, Medium (5 minutes) for storage/fans

### 5.2 Storage Sensors Group

| Entity Key | Entity Name | Device Class | Unit | State Class | Icon |
|------------|-------------|--------------|------|-------------|------|
| `array` | Array | `power_factor` | `%` | `measurement` | `mdi:harddisk` |
| `disk_{name}` | Disk {name} | `power_factor` | `%` | `measurement` | `mdi:harddisk` |
| `pool_{name}` | Pool {name} | `power_factor` | `%` | `measurement` | `mdi:harddisk` |

**Update Priority**: Medium (5 minutes) for array, Disk Interval (60 minutes default) for individual disks

### 5.3 Network Sensors Group

| Entity Key | Entity Name | Device Class | Unit | State Class | Icon |
|------------|-------------|--------------|------|-------------|------|
| `network_{interface}_inbound` | {Interface} Inbound | `data_rate` | `MB/s` | `measurement` | `mdi:download-network` |
| `network_{interface}_outbound` | {Interface} Outbound | `data_rate` | `MB/s` | `measurement` | `mdi:upload-network` |

**Update Priority**: High (real-time, 15-60 seconds)

### 5.4 UPS Sensors Group

| Entity Key | Entity Name | Device Class | Unit | State Class | Icon |
|------------|-------------|--------------|------|-------------|------|
| `ups_server_power` | UPS Server Power | `power` | `W` | `measurement` | `mdi:server` |
| `ups_server_energy` | UPS Server Energy | `energy` | `kWh` | `total_increasing` | `mdi:lightning-bolt` |

**Update Priority**: High (2 minutes)
**Energy Dashboard**: Both sensors are compatible with Energy Dashboard

### 5.5 Docker Sensors Group

| Entity Key | Entity Name | Entity Category | Icon |
|------------|-------------|-----------------|------|
| `containers_running` | Running Containers | `diagnostic` | `mdi:docker` |
| `containers_paused` | Paused Containers | `diagnostic` | `mdi:docker` |
| `total_containers` | Total Containers | `diagnostic` | `mdi:docker` |

**Update Priority**: Medium (5 minutes)

### 5.6 Binary Sensors Group

| Entity Key | Entity Name | Device Class | Entity Category |
|------------|-------------|--------------|-----------------|
| `array_status` | Array Status | `running` | `diagnostic` |
| `array_health` | Array Health | `problem` | `diagnostic` |
| `disk_health_{name}` | {Name} Health | `problem` | `diagnostic` |
| `parity_check` | Parity Check | `running` | `diagnostic` |
| `parity_errors` | Parity Errors | `problem` | `diagnostic` |
| `ups_status` | UPS Status | `plug` | `diagnostic` |

**Update Priority**: Critical (60 seconds) for array/parity, High (2 minutes) for disk health

### 5.7 Switches Group

| Entity Type | Entity Name Pattern | Icon Pattern |
|-------------|---------------------|--------------|
| Docker Container | `{container_name}` | `mdi:docker` |
| Virtual Machine | `{vm_name}` | OS-specific (Windows/Linux/macOS) |

**Update Priority**: Medium (5 minutes)

### 5.8 Buttons Group

| Entity Key | Entity Name | Icon | Entity Category | Enabled Default |
|------------|-------------|------|-----------------|-----------------|
| `reboot` | Reboot | `mdi:restart` | `config` | `False` |
| `shutdown` | Shutdown | `mdi:power` | `config` | `False` |
| `script_{name}` | {Script Name} | `mdi:script-text` | `config` | `False` |

**Why Disabled by Default**: Safety - prevents accidental system shutdowns

---

## 6. Complete Attribute Reference

This section documents EVERY attribute for EVERY entity type.

### 6.1 CPU Usage Sensor Attributes

**Entity**: `sensor.{hostname}_cpu_usage`
**State Value**: CPU utilization percentage (0-100)

| Attribute | Data Type | Description | Example Value |
|-----------|-----------|-------------|---------------|
| `cores` | `int` | Number of physical CPU cores | `8` |
| `threads` | `int` | Number of logical CPU threads | `16` |
| `model` | `str` | CPU model name | `"Intel(R) Core(TM) i7-8700K CPU @ 3.70GHz"` |
| `architecture` | `str` | CPU architecture | `"x86_64"` |
| `current_frequency_mhz` | `float` | Current CPU frequency in MHz | `3700.0` |
| `min_frequency_mhz` | `float` | Minimum CPU frequency | `800.0` |
| `max_frequency_mhz` | `float` | Maximum CPU frequency | `4700.0` |
| `load_average_1min` | `float` | 1-minute load average | `1.2` |
| `load_average_5min` | `float` | 5-minute load average | `1.5` |
| `load_average_15min` | `float` | 15-minute load average | `1.8` |
| `temperature_status` | `str` | Temperature status description | `"Normal"` / `"Warm"` / `"Hot"` |
| `last_updated` | `str` | ISO timestamp of last update | `"2024-01-15T10:30:00Z"` |

**Implementation**:
```python
@property
def extra_state_attributes(self) -> dict[str, Any]:
    """Return CPU attributes."""
    cpu_data = self.coordinator.data.get("system_stats", {}).get("cpu", {})
    return {
        "cores": cpu_data.get("cores"),
        "threads": cpu_data.get("threads"),
        "model": cpu_data.get("model"),
        "architecture": cpu_data.get("architecture"),
        # ... etc
    }
```

### 6.2 RAM Usage Sensor Attributes
**Entity**: `sensor.{hostname}_ram_usage` | **State**: RAM usage % (0-100)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `total_gb`, `used_gb`, `available_gb`, `cached_gb`, `buffers_gb` | `float` | Memory breakdown | `32.0`, `12.5`, `19.5`, `8.2`, `0.8` |
| `system_usage_gb`, `vm_usage_gb`, `docker_usage_gb`, `zfs_cache_gb` | `float` | Usage by component | `4.5`, `8.0`, `2.5`, `6.0` |
| `memory_status` | `str` | Status | `"Healthy"` / `"High Usage"` / `"Critical"` |

### 6.3 Uptime Sensor Attributes
**Entity**: `sensor.{hostname}_uptime` | **State**: Uptime in seconds

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `uptime_days`, `uptime_hours`, `uptime_minutes` | `int` | Time components | `15`, `2`, `34` |
| `uptime_formatted` | `str` | Human-readable | `"15 days, 2 hours, 34 minutes"` |
| `boot_time` | `str` | Last boot timestamp | `"2024-01-01T08:30:00Z"` |

### 6.4-6.5 Temperature Sensor Attributes
**Entities**: `sensor.{hostname}_cpu_temp`, `sensor.{hostname}_motherboard_temp` | **State**: Temperature in °C

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `sensor_name`, `sensor_label` | `str` | Sensor identification | `"coretemp-isa-0000"`, `"Package id 0"` |
| `critical_temp`, `max_temp` | `int` | Temperature thresholds | `100`, `85` |
| `alarm` | `bool` | Alarm status | `false` |
| `temperature_status` | `str` | Status | `"Normal"` / `"Warm"` / `"Hot"` / `"Critical"` |

### 6.6 Fan Sensor Attributes
**Entity**: `sensor.{hostname}_fan_{id}` | **State**: Fan speed in RPM

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `fan_label`, `fan_id` | `str` | Fan identification | `"CPU Fan"`, `"fan1"` |
| `min_rpm`, `max_rpm` | `int` | RPM range | `0`, `2000` |
| `alarm` | `bool` | Alarm status | `false` |
| `fan_status` | `str` | Status | `"Normal"` / `"Slow"` / `"Stopped"` |

### 6.7 Intel GPU Sensor Attributes
**Entity**: `sensor.{hostname}_intel_gpu_usage` | **State**: GPU usage % (0-100)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `model`, `driver` | `str` | GPU info | `"Intel UHD Graphics 630"`, `"i915"` |
| `memory_used_mb`, `memory_total_mb`, `memory_usage_percent` | `int`/`float` | Memory stats | `256`, `1024`, `25.0` |

### 6.8-6.10 Storage Filesystem Attributes
**Entities**: `sensor.{hostname}_docker_vdisk`, `sensor.{hostname}_log_filesystem`, `sensor.{hostname}_boot_usage` | **State**: Usage % (0-100)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `total_gb`, `used_gb`, `available_gb` | `float` | Space breakdown | `20.0`, `8.5`, `11.5` |
| `mount_point`, `filesystem` | `str` | Mount info | `"/var/lib/docker"`, `"btrfs"` |
| `device` | `str` | Device path (boot only) | `"/dev/sdb1"` |
| `usage_status` | `str` | Status | `"Healthy"` / `"High Usage"` / `"Critical"` |

### 6.11 Array Sensor Attributes

**Entity**: `sensor.{hostname}_array`
**State Value**: Array usage percentage (0-100)

| Attribute | Data Type | Description | Example Value |
|-----------|-----------|-------------|---------------|
| `total_tb` | `float` | Total array size in TB | `12.5` |
| `used_tb` | `float` | Used space in TB | `8.2` |
| `free_tb` | `float` | Free space in TB | `4.3` |
| `num_disks` | `int` | Total number of disks | `6` |
| `num_data_disks` | `int` | Number of data disks | `4` |
| `num_parity_disks` | `int` | Number of parity disks | `2` |
| `array_state` | `str` | Array state | `"Started"` / `"Stopped"` |
| `protection` | `str` | Protection status | `"Protected"` / `"Unprotected"` |
| `sync_action` | `str` | Current sync action | `"idle"` / `"check"` / `"recon"` |
| `usage_status` | `str` | Status description | `"Healthy"` / `"High Usage"` / `"Critical"` |
| `last_updated` | `str` | ISO timestamp | `"2024-01-15T10:30:00Z"` |

### 6.12 Individual Disk Sensor Attributes

**Entity**: `sensor.{hostname}_disk_{name}`
**State Value**: Disk usage percentage (0-100)

| Attribute | Data Type | Description | Example Value |
|-----------|-----------|-------------|---------------|
| `total_gb` | `float` | Total disk size in GB | `2000.0` |
| `used_gb` | `float` | Used space in GB | `1200.0` |
| `free_gb` | `float` | Free space in GB | `800.0` |
| `device` | `str` | Device path | `"/dev/sdb1"` |
| `serial` | `str` | Disk serial number | `"WD-XXXXXXXXXXXX"` |
| `model` | `str` | Disk model | `"WDC WD20EFRX-68EUZN0"` |
| `filesystem` | `str` | Filesystem type | `"xfs"` |
| `mount_point` | `str` | Mount point path | `"/mnt/disk1"` |
| `disk_type` | `str` | Disk type | `"HDD"` / `"SSD"` |
| `temperature` | `int` | Disk temperature in Celsius | `35` |
| `power_state` | `str` | Power state | `"active"` / `"standby"` |
| `smart_status` | `str` | SMART status | `"PASSED"` / `"FAILED"` |
| `spin_down_delay` | `str` | Spin down delay setting | `"Never"` / `"15 minutes"` / `"30 minutes"` |
| `usage_status` | `str` | Status description | `"Healthy"` / `"High Usage"` / `"Critical"` |
| `last_updated` | `str` | ISO timestamp | `"2024-01-15T10:30:00Z"` |

**Special Behavior**: When disk is in standby, returns last known values to avoid spinning up the disk.

### 6.13 Pool Sensor Attributes

**Entity**: `sensor.{hostname}_pool_{name}`
**State Value**: Pool usage percentage (0-100)

| Attribute | Data Type | Description | Example Value |
|-----------|-----------|-------------|---------------|
| `total_gb` | `float` | Total pool size in GB | `500.0` |
| `used_gb` | `float` | Used space in GB | `250.0` |
| `free_gb` | `float` | Free space in GB | `250.0` |
| `device` | `str` | Device path | `"/dev/nvme0n1p1"` |
| `filesystem` | `str` | Filesystem type | `"btrfs"` / `"xfs"` / `"zfs"` |
| `mount_point` | `str` | Mount point path | `"/mnt/cache"` |
| `disk_type` | `str` | Disk type | `"SSD"` / `"NVMe"` |
| `pool_devices` | `list[str]` | List of devices in pool | `["/dev/nvme0n1", "/dev/nvme1n1"]` |
| `usage_status` | `str` | Status description | `"Healthy"` / `"High Usage"` / `"Critical"` |
| `last_updated` | `str` | ISO timestamp | `"2024-01-15T10:30:00Z"` |

### 6.14 Network Sensor Attributes
**Entity**: `sensor.{hostname}_network_{interface}_{direction}` | **State**: Throughput in MB/s

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `interface`, `direction` | `str` | Interface and direction | `"eth0"`, `"inbound"` / `"outbound"` |
| `bytes_total`, `packets_total` | `int` | Transfer totals | `1234567890`, `9876543` |
| `errors`, `drops` | `int` | Error/drop counts | `0`, `0` |
| `connected` | `bool` | Connection status | `true` |
| `speed_mbps`, `duplex`, `mac_address` | `int`/`str` | Link info | `1000`, `"full"`, `"00:11:22:33:44:55"` |

### 6.15 UPS Server Power Sensor Attributes
**Entity**: `sensor.{hostname}_ups_server_power` | **State**: Power in Watts | **Energy Dashboard**: Compatible

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `ups_model`, `rated_power` | `str` | UPS info | `"CyberPower CP1500PFCLCD"`, `"1000W"` |
| `current_load`, `battery_charge` | `str` | Load/battery % | `"45%"`, `"100%"` |
| `battery_status` | `str` | Battery status | `"Excellent"` / `"Good"` / `"Fair"` / `"Low"` / `"Critical"` |
| `estimated_runtime` | `str` | Runtime on battery | `"1h 30m"` / `"45m"` |
| `load_status` | `str` | Load status | `"Light"` / `"Moderate"` / `"High"` / `"Very High"` |
| `energy_dashboard_ready` | `bool` | Dashboard compatibility | `true` |

### 6.16 UPS Server Energy Sensor Attributes
**Entity**: `sensor.{hostname}_ups_server_energy` | **State**: Energy in kWh | **Energy Dashboard**: Compatible

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `ups_model`, `rated_power`, `current_power` | `str` | UPS/power info | `"CyberPower CP1500PFCLCD"`, `"1000W"`, `"450W"` |
| `total_energy_kwh`, `energy_today_kwh`, `energy_this_month_kwh` | `float` | Energy totals | `123.45`, `2.5`, `75.0` |
| `estimated_cost_today`, `estimated_cost_month` | `str` | Cost estimates | `"$0.30"`, `"$9.00"` |
| `energy_dashboard_ready` | `bool` | Dashboard compatibility | `true` |

### 6.17 Docker Container Count Sensors Attributes
**Entities**: `sensor.{hostname}_containers_running`, `sensor.{hostname}_containers_paused`, `sensor.{hostname}_total_containers` | **State**: Container count

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `container_names` | `list[str]` | Container names | `["plex", "sonarr", "radarr"]` |

### 6.18 Binary Sensor Attributes

#### Array Status Binary Sensor
**Entity**: `binary_sensor.{hostname}_array_status` | **State**: `on` (started) / `off` (stopped)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `array_state`, `protection` | `str` | State and protection | `"Started"` / `"Stopped"`, `"Protected"` / `"Unprotected"` |
| `num_disks`, `num_data_disks`, `num_parity_disks` | `int` | Disk counts | `6`, `4`, `2` |

#### Array Health Binary Sensor
**Entity**: `binary_sensor.{hostname}_array_health` | **State**: `on` (problem) / `off` (healthy)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `health_status` | `str` | Health status | `"Healthy"` / `"Warning"` / `"Critical"` |
| `issues`, `num_issues` | `list[str]`, `int` | Issues detected | `["Disk 1 temperature high"]`, `2` |

#### Disk Health Binary Sensor
**Entity**: `binary_sensor.{hostname}_disk_health_{name}` | **State**: `on` (problem) / `off` (healthy)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `disk_name`, `device`, `serial` | `str` | Disk identification | `"disk1"`, `"/dev/sdb1"`, `"WD-XXXXXXXXXXXX"` |
| `smart_status`, `temperature`, `temperature_status`, `power_state` | `str`/`int` | Disk status | `"PASSED"`, `35`, `"Normal"`, `"active"` |
| `reallocated_sectors`, `pending_sectors`, `offline_uncorrectable` | `int` | SMART attributes | `0`, `0`, `0` |
| `problems_detected` | `list[str]` | Problems list | `["Temperature high"]` |

#### Parity Check Binary Sensor
**Entity**: `binary_sensor.{hostname}_parity_check` | **State**: `on` (running) / `off` (not running)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `status`, `progress` | `str`, `float` | Check status | `"Running"`, `45.5` |
| `elapsed_time`, `estimated_finish`, `speed_mbps` | `str`/`float` | Progress info | `"2h 15m"`, `"2024-01-15T15:30:00Z"`, `125.5` |
| `errors_found`, `last_check_date`, `last_check_duration` | `int`/`str` | Check results | `0`, `"2024-01-01"`, `"4h 30m"` |

#### Parity Errors Binary Sensor
**Entity**: `binary_sensor.{hostname}_parity_errors` | **State**: `on` (errors) / `off` (no errors)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `error_count`, `last_check_date`, `last_check_errors` | `int`/`str` | Error info | `0`, `"2024-01-01"`, `0` |
| `error_history` | `list[dict]` | Error history | `[{"date": "2024-01-01", "errors": 0}]` |

#### UPS Status Binary Sensor
**Entity**: `binary_sensor.{hostname}_ups_status` | **State**: `on` (online) / `off` (offline/on battery)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `ups_model`, `status` | `str` | UPS info | `"CyberPower CP1500PFCLCD"`, `"ONLINE"` / `"ONBATT"` |
| `battery_charge`, `battery_runtime`, `load_percent` | `str` | Battery/load info | `"100%"`, `"1h 30m"`, `"45%"` |
| `input_voltage`, `output_voltage` | `str` | Voltage info | `"120V"`, `"120V"` |

### 6.19 Switch Attributes

#### Docker Container Switch
**Entity**: `switch.{hostname}_docker_{container_name}` | **State**: `on` (running) / `off` (stopped)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `container_id`, `container_name`, `status`, `image` | `str` | Container info | `"abc123def456"`, `"plex"`, `"running"`, `"plexinc/pms-docker:latest"` |
| `created`, `ports` | `str`, `list[str]` | Creation and ports | `"2024-01-01T00:00:00Z"`, `["32400:32400/tcp"]` |

#### VM Switch
**Entity**: `switch.{hostname}_vm_{vm_name}` | **State**: `on` (running) / `off` (stopped)

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `vm_name`, `status`, `os_type` | `str` | VM info | `"Windows 10"`, `"running"`, `"windows"` |
| `vcpus`, `memory_mb`, `autostart` | `int`/`bool` | Resources | `4`, `8192`, `true` |

### 6.20 Button Attributes

#### System Control Buttons
**Entities**: `button.{hostname}_reboot`, `button.{hostname}_shutdown`

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `last_pressed`, `action` | `str` | Press info | `"2024-01-15T10:30:00Z"`, `"Reboot System"` |

#### User Script Button
**Entity**: `button.{hostname}_script_{script_name}`

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `script_name`, `script_path` | `str` | Script info | `"backup"`, `"/boot/config/plugins/user.scripts/scripts/backup/script"` |
| `last_executed`, `last_result`, `execution_time` | `str` | Execution info | `"2024-01-15T10:30:00Z"`, `"success"`, `"2m 15s"` |

---

## 7. Device Info Standards

### Device Identifier Patterns

| Device Type | Identifier Pattern | Name Pattern | Manufacturer | Model |
|-------------|-------------------|--------------|--------------|-------|
| Main Server | `(DOMAIN, entry_id)` | `{hostname.title()}` | `"Lime Technology"` | `"Unraid Server"` |
| Docker | `(DOMAIN, f"{entry_id}_docker")` | `"Unraid Docker ({hostname})"` | `"Docker"` | `"Container Engine"` |
| Container | `(DOMAIN, f"docker_{container_name}_{entry_id}")` | `{container_name}` | `"Docker"` | `"Container"` |
| VM | `(DOMAIN, f"vm_{vm_name}_{entry_id}")` | `{vm_name}` | `"QEMU/KVM"` | `"{os_type} Virtual Machine"` |
| Disk | `(DOMAIN, f"disk_{disk_name}_{entry_id}")` | `"Unraid Disk ({disk_name})"` | From SMART | From SMART |
| UPS | `(DOMAIN, f"ups_{entry_id}")` | `"Unraid UPS ({hostname})"` | From UPS data | From UPS data |

### Device Info Example
```python
DeviceInfo(
    identifiers={(DOMAIN, entry.entry_id)},
    name=coordinator.hostname.replace("_", " ").title(),
    manufacturer="Lime Technology",
    model="Unraid Server",
    sw_version=coordinator.data.get("system_stats", {}).get("unraid_version"),
    configuration_url=f"http://{coordinator.hostname}",
    via_device=(DOMAIN, parent_device_id),  # For child devices
)
```

---

## 8. State Management Patterns

### 8.1 Coordinator Update Intervals
```python
DEFAULT_GENERAL_INTERVAL = 5  # minutes (range: 1-60)
DEFAULT_DISK_INTERVAL = 60  # minutes (range: 5-1440)
```
**Why Separate**: General updates system metrics frequently; disk updates less often to avoid spinning up standby disks.

### 8.2 Cache TTL Settings

| Data Type | TTL | Examples |
|-----------|-----|----------|
| Static | 1 hour | Disk mapping, device serials/models |
| Semi-Dynamic | 2-10 min | System stats, Docker/VM info |
| Real-Time | 15-60 sec | Network stats, CPU/memory |
| Critical | 30 sec | Disk power state, SMART alerts |

### 8.3 Sensor Priority Levels

| Priority | Interval | Sensor Types |
|----------|----------|--------------|
| Critical | 60 sec | Array status, parity status |
| High | 2 min | CPU, memory, temperatures, UPS |
| Medium | 5 min | Storage usage, Docker stats |
| Low | 15 min | Static information |

### 8.4 Standby Disk Handling
```python
if disk_state == "standby":
    return self._last_value  # Cached to avoid spin-up
else:
    self._last_value = current_value
    return current_value
```

---

## 9. Code Templates

### 9.1 Creating a New System Sensor

```python
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE

from .base import UnraidSensorBase
from .const import UnraidSensorEntityDescription

class UnraidNewMetricSensor(UnraidSensorBase):
    """Sensor for new metric."""

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        description = UnraidSensorEntityDescription(
            key="new_metric",
            name="New Metric",
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.POWER_FACTOR,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:icon-name",
            suggested_display_precision=1,
            value_fn=self._get_value,
            available_fn=self._is_available,
        )
        super().__init__(coordinator, description)

    def _get_value(self, data: dict) -> float | None:
        """Get sensor value from coordinator data."""
        try:
            return data.get("system_stats", {}).get("new_metric")
        except (KeyError, TypeError):
            return None

    def _is_available(self, data: dict) -> bool:
        """Check if sensor data is available."""
        return "new_metric" in data.get("system_stats", {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        stats = self.coordinator.data.get("system_stats", {})
        return {
            "attribute_1": stats.get("attr1"),
            "attribute_2": stats.get("attr2"),
            "last_updated": dt_util.now().isoformat(),
        }
```

### 9.2 Registering a New Sensor

**In**: `custom_components/unraid/sensors/registry.py`

```python
def register_system_sensors() -> None:
    """Register system sensors with the factory."""
    from .system import UnraidNewMetricSensor

    # Register sensor type
    SensorFactory.register_sensor_type("new_metric", UnraidNewMetricSensor)

    # Register creator function
    SensorFactory.register_sensor_creator(
        "system_sensors",
        create_system_sensors,
        group="system"
    )

def create_system_sensors(coordinator, _) -> List[Entity]:
    """Create system sensors."""
    from .system import UnraidNewMetricSensor

    entities = [
        UnraidNewMetricSensor(coordinator),
        # ... other sensors
    ]
    return entities
```

### 9.3 Creating a New Binary Sensor

```python
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory

from .base import UnraidBinarySensorBase
from .const import UnraidBinarySensorEntityDescription

class UnraidNewStatusSensor(UnraidBinarySensorBase):
    """Binary sensor for new status check."""

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        description = UnraidBinarySensorEntityDescription(
            key="new_status",
            name="New Status",
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:icon-name",
            value_fn=self._get_status,
        )
        super().__init__(coordinator, description)

    def _get_status(self, data: dict) -> bool:
        """Get binary sensor state."""
        # Return True for problem/on, False for normal/off
        return data.get("system_stats", {}).get("has_problem", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return {
            "status_detail": "Description of status",
            "last_checked": dt_util.now().isoformat(),
        }
```

---

## 10. Data Coordinator Patterns

### 10.1 Coordinator Data Structure

**Type**: `UnraidDataDict` (TypedDict)

```python
{
    "hostname": str,
    "system_stats": {
        "cpu": {...},
        "memory": {...},
        "temperature_data": {...},
        "network_stats": {...},
        "individual_disks": [...],
        "array_usage": {...},
        "parity_info": {...},
        "ups_info": {...},
        "intel_gpu": {...},
    },
    "docker_containers": [...],
    "vms": [...],
    "user_scripts": [...],
    "array_state": str,
    "disk_config": {...},
}
```

### 10.2 Accessing Coordinator Data

**Pattern**: Always use safe dictionary access with defaults

```python
# Good
cpu_data = self.coordinator.data.get("system_stats", {}).get("cpu", {})
value = cpu_data.get("usage", 0)

# Bad - can raise KeyError
value = self.coordinator.data["system_stats"]["cpu"]["usage"]
```

### 10.3 Coordinator Availability Check

**Pattern**: Check both coordinator success and data availability

```python
@property
def available(self) -> bool:
    """Return if entity is available."""
    return (
        self.coordinator.last_update_success
        and self.entity_description.available_fn(self.coordinator.data)
    )
```

### 10.4 Triggering Coordinator Refresh

**Pattern**: Request refresh after state-changing actions

```python
async def async_turn_on(self, **kwargs: Any) -> None:
    """Turn the entity on."""
    await self.coordinator.api.start_container(self.container_name)
    await self.coordinator.async_request_refresh()
```

---

## Summary

This rule file documents the complete architecture, patterns, and standards for Unraid Home Assistant integrations. When creating new entities:

1. **Follow the naming conventions** for entity IDs, unique IDs, and device IDs
2. **Use the appropriate base class** (UnraidSensorBase, UnraidBinarySensorBase, etc.)
3. **Register sensors** using the factory/registry pattern
4. **Document all attributes** with data types and examples
5. **Implement proper availability checks** using coordinator and custom logic
6. **Use safe data access patterns** with .get() and defaults
7. **Follow the device info structure** for proper device grouping
8. **Respect update priorities** for optimal performance
9. **Handle standby disks** by caching last known values

Every new entity should be indistinguishable from existing ones by following these patterns exactly, regardless of the underlying communication protocol (SSH, GraphQL, REST API, etc.).


