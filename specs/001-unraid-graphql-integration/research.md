````markdown
# Research: Unraid GraphQL API Integration

**Date**: 2025-12-23
**Updated**: 2025-12-23
**Feature**: 001-unraid-graphql-integration
**Source**: Official Unraid API Schema v4.29.2 (github.com/unraid/api/blob/main/api/generated-schema.graphql)

## API Endpoint and Authentication

### Decision: GraphQL Endpoint
- **Endpoint**: `https://{server_ip}/graphql`
- **Port**: Standard HTTPS port (443) or Unraid's configured web UI port (typically 443 or custom)
- **Rationale**: This is the documented endpoint for Unraid API v4.21.0+
- **Alternatives considered**: None - this is the only documented endpoint

### Decision: Authentication Method
- **Method**: API key via `x-api-key` header
- **Format**: `{"x-api-key": "YOUR_API_KEY"}`
- **Rationale**: Official Unraid API authentication method; supports role-based access
- **Available Roles**: `ADMIN`, `CONNECT`, `GUEST`, `VIEWER`
- **Required Role**: ADMIN (for full Docker/VM control mutations)
- **Alternatives considered**: Session cookies, SSO/OIDC - rejected for simplicity; API key is the recommended approach for integrations

### Decision: API Key Creation
- **Method**: Users create API keys via Unraid WebGUI: Settings → Management Access → API
- **CLI Alternative**: `unraid-api key --help` for command-line key management
- **Roles**: Integration will require ADMIN role for full access to Docker/VM control
- **Rationale**: Documented approach; provides proper access control

## GraphQL Schema (Official v4.29.2)

### Key Scalar Types

#### PrefixedID
- **Format**: `{prefix}:{id}` (e.g., `123:456` where 123 is server/resource prefix)
- **Parsing Rule**: Accept as string, extract numeric portion after colon for legacy compatibility if needed
- **Usage**: All resource IDs (containers, VMs, disks) are PrefixedID in API responses
- **Unique ID Strategy**: Use full PrefixedID as-is for entity unique IDs (format: `{server_uuid}_resource_{prefixed_id}`)
- **Null Handling**: PrefixedID fields are non-nullable in schema; treat missing field as error

#### BigInt
- **Format**: String representation of integer (e.g., "9223372036854775807")
- **Parsing Rule**: Convert to Python `int` (native support for arbitrary precision)
- **Boundaries**: No enforced max; practical range 0 to 2^63-1 for disk operations
- **Usage**: `numReads`, `numWrites`, `numErrors` (disk counters), large byte values
- **Overflow Handling**: Python int handles arbitrary precision; no overflow possible
- **Null Handling**: Treat null BigInt as 0 for counters

#### DateTime
- **Format**: ISO 8601 with timezone (e.g., "2025-12-23T10:30:00-08:00" or "2025-12-23T18:30:00Z")
- **Parsing Rule**: Use `datetime.fromisoformat()` (Python 3.11+) or `dateutil.parser.isoparse()`
- **Timezone**: Always includes timezone; convert to UTC for internal storage
- **Usage**: `info.time`, `info.os.uptime` (boot time), parity check timestamps
- **Null Handling**: Optional DateTime fields (e.g., last parity check) should default to None; display as "Never" in UI

#### Null/Missing Fields
- **Optional Fields**: Many fields can be null (e.g., UPS, GPU, disk temperature)
- **Pydantic Handling**: Use `Optional[Type]` for nullable fields; set default=None
- **Entity Behavior**: Sensors with null values should report "unavailable" state; attributes can show null/None
- **Examples**:
  - `disk.temp` can be null if disk doesn't report temperature → sensor unavailable
  - `devices.ups` can be null if no UPS connected → no UPS entities created
  - `info.cpu.packages.temp[0]` can be null → CPU temp sensor unavailable

#### Temperature Values
- **Unit**: Celsius (API always returns Celsius)
- **Valid Range**: -40°C to 150°C (practical hardware limits)
- **Threshold Values** (from `info.display`):
  - `warning`: Default 70°C (configurable per server)
  - `critical`: Default 85°C (configurable per server)
- **Out-of-Range Handling**: Values outside -40 to 150 marked as sensor error (unavailable)
- **Null Handling**: Null temperature → sensor unavailable (not all disks/CPUs report temp)
- **Conversion**: HA sensor device_class="temperature" always uses Celsius internally

#### Other Scalar Types
- **JSON**: Arbitrary JSON objects (e.g., CPU cache info)
- **Port**: TCP port number (0-65535)
- **URL**: Standard URL format

### Decision: Query Structure (Complete)

**System Information Query:**
```graphql
query SystemInfo {
  info {
    time                     # Current server time (DateTime)
    machineId               # Machine identifier
    baseboard {
      manufacturer
      model
      version
      serial
      memMax               # Max memory capacity (bytes)
      memSlots             # Number of memory slots
    }
    cpu {
      manufacturer
      brand
      vendor
      family
      model
      speed                # Current GHz
      speedmin             # Min GHz
      speedmax             # Max GHz
      threads
      cores
      processors           # Physical processor count
      socket
      cache                # JSON cache info
      flags                # CPU feature flags
      topology             # Per-package core/thread mapping
      packages {
        totalPower         # Total CPU package power (W)
        power              # Per-package power array
        temp               # Per-package temperature array
      }
    }
    memory {
      layout {
        size               # Module size (bytes)
        bank
        type               # DDR4, DDR5, etc.
        clockSpeed
        manufacturer
        partNum
        serialNum
        formFactor
        voltageConfigured
        voltageMin
        voltageMax
      }
    }
    os {
      platform
      distro
      release
      codename
      kernel
      arch
      hostname
      fqdn
      uptime               # Boot time ISO string
      uefi
    }
    system {
      manufacturer
      model
      version
      serial
      uuid                 # System UUID (use for unique ID)
      sku
      virtual              # Is VM?
    }
    devices {
      gpu {
        type
        typeid
        vendorname
        productid
        blacklisted
        class
      }
      network {
        iface
        model
        vendor
        mac
        virtual
        speed
        dhcp
      }
      pci { ... }
      usb { ... }
    }
    display {
      theme               # UI theme (azure, black, gray, white)
      unit                # Temperature unit (CELSIUS, FAHRENHEIT)
      warning             # Warning temp threshold
      critical            # Critical temp threshold
    }
    versions {
      core {
        unraid             # Unraid version string
        api                # API version
        kernel
      }
      packages {
        docker
        php
        nginx
        openssl
        node
      }
    }
  }
}
```

**Real-Time Metrics Query (for system monitoring):**
```graphql
query SystemMetrics {
  metrics {
    cpu {
      percentTotal         # Total CPU usage percentage
      cpus {               # Per-core usage
        percentTotal
        percentUser
        percentSystem
        percentIdle
        percentIrq
        percentGuest
        percentSteal
      }
    }
    memory {
      total               # Total RAM (bytes)
      used                # Used RAM (bytes)
      free                # Free RAM (bytes)
      available           # Available RAM (bytes)
      active
      buffcache
      percentTotal        # Memory usage percentage
      swapTotal
      swapUsed
      swapFree
      percentSwapTotal
    }
  }
}
```

**Array and Disk Query (Storage):**
```graphql
query ArrayStatus {
  array {
    id                    # PrefixedID
    state                 # ArrayState enum
    capacity {
      kilobytes {
        free
        used
        total
      }
      disks {
        free
        used
        total
      }
    }
    parityCheckStatus {
      date
      duration           # Seconds
      speed              # MB/s
      status             # NEVER_RUN, RUNNING, PAUSED, COMPLETED, CANCELLED, FAILED
      errors
      progress           # Percentage
      correcting
      paused
      running
    }
    boot {
      id
      idx
      name
      device
      size
      status
    }
    parities {
      id
      idx
      name
      device
      size
      status             # ArrayDiskStatus enum
      temp
      numReads
      numWrites
      numErrors
      rotational
      isSpinning
    }
    disks {
      id
      idx                # Slot number (1-28)
      name
      device
      size
      status
      temp
      numReads
      numWrites
      numErrors
      fsSize             # Filesystem size (KB)
      fsFree             # Filesystem free (KB)
      fsUsed             # Filesystem used (KB)
      fsType             # XFS, BTRFS, etc.
      rotational
      isSpinning
      transport          # ata, nvme, usb
      color              # Health indicator color enum
      warning            # Disk space warning threshold %
      critical           # Disk space critical threshold %
      comment            # User comment
    }
    caches {
      # Same structure as disks
    }
  }
}
```

**Disk Hardware Query (Physical Disks):**
```graphql
query DisksHardware {
  disks {
    id
    device              # /dev/sdb
    type                # SSD, HDD
    name                # Model name
    vendor
    size                # Total size (bytes)
    bytesPerSector
    firmwareRevision
    serialNum           # Use for unique ID
    interfaceType       # SAS, SATA, USB, PCIE, UNKNOWN
    smartStatus         # OK, UNKNOWN
    temperature         # Celsius
    isSpinning
    partitions {
      name
      fsType            # XFS, BTRFS, VFAT, ZFS, EXT4, NTFS
      size              # Bytes
    }
  }
}
```

**Docker Containers Query:**
```graphql
query DockerContainers {
  docker {
    containers(skipCache: Boolean = false) {
      id                  # PrefixedID - use for mutations
      names               # Array of names
      image
      imageId
      command
      created             # Unix timestamp
      ports {
        ip
        privatePort
        publicPort
        type              # TCP, UDP
      }
      lanIpPorts          # LAN-accessible host:port values
      sizeRootFs          # Total file size (bytes)
      sizeRw              # Writable layer size
      sizeLog             # Log size
      labels              # JSON
      state               # RUNNING, PAUSED, EXITED
      status              # Human-readable status string
      hostConfig {
        networkMode
      }
      autoStart           # Boolean
      autoStartOrder      # Zero-based order
      autoStartWait       # Wait seconds after start
      templatePath
      projectUrl          # Product homepage
      registryUrl         # Docker Hub URL
      supportUrl
      iconUrl
      webUiUrl            # Resolved WebUI URL
      shell               # Console shell
      isOrphaned          # No template found
      isUpdateAvailable   # Boolean - container has update
      isRebuildReady
      tailscaleEnabled
      tailscaleStatus {
        online
        version
        hostname
        tailscaleIps
        isExitNode
        webUiUrl
      }
    }
    networks {
      id
      name
      driver
      scope
    }
    portConflicts {
      containerPorts { ... }
      lanPorts { ... }
    }
    container(id: PrefixedID!) {
      # Single container details
    }
    logs(id: PrefixedID!, since: DateTime, tail: Int) {
      containerId
      lines {
        timestamp
        message
      }
      cursor
    }
    containerUpdateStatuses {
      name
      updateStatus        # UP_TO_DATE, UPDATE_AVAILABLE, REBUILD_READY, UNKNOWN
    }
  }
}
```

**Virtual Machines Query:**
```graphql
query VirtualMachines {
  vms {
    id
    domains {
      id                  # PrefixedID (was uuid)
      name
      state               # VmState enum
    }
    domain {
      # Same as domains (legacy)
    }
  }
}
```
**VmState Enum Values**: `NOSTATE`, `RUNNING`, `IDLE`, `PAUSED`, `SHUTDOWN`, `SHUTOFF`, `CRASHED`, `PMSUSPENDED`

**UPS Query (CORRECTED STRUCTURE):**
```graphql
query UPSDevices {
  upsDevices {
    id                    # Unique UPS identifier
    name                  # Display name
    model                 # e.g., "APC Back-UPS Pro 1500"
    status                # "Online", "On Battery", "Low Battery", etc.
    battery {
      chargeLevel         # 0-100 percentage
      estimatedRuntime    # Seconds
      health              # "Good", "Replace", "Unknown"
    }
    power {
      inputVoltage        # Volts
      outputVoltage       # Volts
      loadPercentage      # 0-100 percentage
    }
  }
  upsConfiguration {
    service               # "enable" or "disable"
    upsCable              # "usb", "smart", "ether", "custom"
    upsType               # "usb", "net", "snmp", etc.
    device                # Device path or network address
    batteryLevel          # Shutdown threshold %
    minutes               # Runtime shutdown threshold
    timeout               # Communication timeout
    killUps               # Kill power after shutdown
  }
}
```

**Shares Query:**
```graphql
query Shares {
  shares {
    id
    name
    free                  # KB
    used                  # KB
    size                  # KB
    include               # Included disks
    exclude               # Excluded disks
    cache                 # Is cached
    comment
    allocator
    splitLevel
    color                 # Health color
    luksStatus            # Encryption status
  }
}
```

**Notifications Query:**
```graphql
query Notifications {
  notifications {
    overview {
      unread {
        info
        warning
        alert
        total
      }
      archive { ... }
    }
    list(filter: { type: UNREAD, offset: 0, limit: 50 }) {
      id
      title
      subject
      description
      importance          # ALERT, INFO, WARNING
      type                # UNREAD, ARCHIVE
      timestamp
      link
    }
    warningsAndAlerts {
      # Deduplicated urgent notifications
    }
  }
}
```

**Registration (License) Query:**
```graphql
query Registration {
  registration {
    id
    type                  # BASIC, PLUS, PRO, STARTER, UNLEASHED, LIFETIME, TRIAL
    state                 # Current registration state
    expiration
    updateExpiration
    keyFile {
      location
      contents
    }
  }
}
```

**Vars (System Variables) Query:**
```graphql
query SystemVars {
  vars {
    id
    version               # Unraid version
    name                  # Hostname
    timeZone
    comment
    maxArraysz            # Max array size
    maxCachesz            # Max cache size
    useSsl                # HTTPS enabled
    port                  # HTTP port
    portssl               # HTTPS port
    startArray            # Auto-start array
    spindownDelay         # Disk spindown delay
    shareCount            # Total user shares
    shareSmbCount         # SMB-enabled shares
    shareNfsCount         # NFS-enabled shares
    flashGuid             # Flash drive GUID
    flashProduct
    flashVendor
    regTo                 # Registered owner
    regTy                 # Registration type
    regState              # Registration state
    mdState               # Array state string
    mdNumDisks
    mdNumDisabled
    mdNumInvalid
    mdNumMissing
    fsState               # Filesystem state
    fsProgress            # Current operation progress
    shareMoverActive      # Mover running
    # ... many more system variables
  }
}
```

**Services Query:**
```graphql
query Services {
  services {
    id
    name
    online                # Boolean
    uptime {
      timestamp
    }
    version
  }
}
```

**Network Query:**
```graphql
query Network {
  network {
    id
    accessUrls {
      type                # LAN, WIREGUARD, WAN, MDNS, OTHER, DEFAULT
      name
      ipv4
      ipv6
    }
  }
}
```

**Flash Drive Query:**
```graphql
query Flash {
  flash {
    id
    guid
    vendor
    product
  }
}
```

**Parity History Query:**
```graphql
query ParityHistory {
  parityHistory {
    date
    duration
    speed
    status
    errors
    progress
    correcting
  }
}
```

### Decision: Mutation Structure (CORRECTED)

**Docker Container Control:**
```graphql
mutation StartContainer($id: PrefixedID!) {
  docker {
    start(id: $id) {
      id
      state
      status
    }
  }
}

mutation StopContainer($id: PrefixedID!) {
  docker {
    stop(id: $id) {
      id
      state
      status
    }
  }
}

mutation PauseContainer($id: PrefixedID!) {
  docker {
    pause(id: $id) {
      id
      state
    }
  }
}

mutation UnpauseContainer($id: PrefixedID!) {
  docker {
    unpause(id: $id) {
      id
      state
    }
  }
}

mutation UpdateContainer($id: PrefixedID!) {
  docker {
    updateContainer(id: $id) {
      id
      isUpdateAvailable
    }
  }
}
```

**VM Control:**
```graphql
mutation StartVM($id: PrefixedID!) {
  vm {
    start(id: $id)       # Returns Boolean!
  }
}

mutation StopVM($id: PrefixedID!) {
  vm {
    stop(id: $id)        # Returns Boolean! (graceful)
  }
}

mutation ForceStopVM($id: PrefixedID!) {
  vm {
    forceStop(id: $id)   # Returns Boolean! (hard stop)
  }
}

mutation PauseVM($id: PrefixedID!) {
  vm {
    pause(id: $id)       # Returns Boolean!
  }
}

mutation ResumeVM($id: PrefixedID!) {
  vm {
    resume(id: $id)      # Returns Boolean!
  }
}

mutation RebootVM($id: PrefixedID!) {
  vm {
    reboot(id: $id)      # Returns Boolean!
  }
}
```

**Array Control:**
```graphql
mutation StartArray {
  array {
    setState(input: { desiredState: START }) {
      state
    }
  }
}

mutation StopArray {
  array {
    setState(input: { desiredState: STOP }) {
      state
    }
  }
}
```

**Parity Check Control:**
```graphql
mutation StartParityCheck($correct: Boolean!) {
  parityCheck {
    start(correct: $correct)
  }
}

mutation PauseParityCheck {
  parityCheck {
    pause
  }
}

mutation ResumeParityCheck {
  parityCheck {
    resume
  }
}

mutation CancelParityCheck {
  parityCheck {
    cancel
  }
}
```

**Notification Management:**
```graphql
mutation ArchiveNotification($id: PrefixedID!) {
  archiveNotification(id: $id) {
    id
    type
  }
}

mutation ArchiveAllNotifications {
  archiveAll {
    unread { total }
    archive { total }
  }
}
```

### Decision: Subscription Support (Future Enhancement)

The API supports real-time subscriptions via WebSocket:
```graphql
subscription DockerStats {
  dockerContainerStats {
    id
    cpuPercent
    memUsage
    memPercent
    netIO
    blockIO
  }
}

subscription SystemMetricsCpu {
  systemMetricsCpu {
    percentTotal
    cpus { percentTotal }
  }
}

subscription SystemMetricsMemory {
  systemMetricsMemory {
    total
    used
    percentTotal
  }
}

subscription ArrayUpdates {
  arraySubscription {
    state
    capacity { ... }
  }
}

subscription NotificationAdded {
  notificationAdded {
    id
    title
    importance
  }
}

subscription UPSUpdates {
  upsUpdates {
    status
    battery { chargeLevel }
  }
}
```

- **Rationale for MVP**: Polling is simpler and sufficient; subscriptions add complexity
- **Future consideration**: Subscriptions could replace polling for real-time metrics

### Key Enums Reference

**ArrayState**: `STARTED`, `STOPPED`, `NEW_ARRAY`, `RECON_DISK`, `DISABLE_DISK`, `SWAP_DSBL`, `INVALID_EXPANSION`, `PARITY_NOT_BIGGEST`, `TOO_MANY_MISSING_DISKS`, `NEW_DISK_TOO_SMALL`, `NO_DATA_DISKS`

**ArrayDiskStatus**: `DISK_NP`, `DISK_OK`, `DISK_NP_MISSING`, `DISK_INVALID`, `DISK_WRONG`, `DISK_DSBL`, `DISK_NP_DSBL`, `DISK_DSBL_NEW`, `DISK_NEW`

**ArrayDiskType**: `DATA`, `PARITY`, `FLASH`, `CACHE`

**ArrayDiskFsColor**: `GREEN_ON`, `GREEN_BLINK`, `BLUE_ON`, `BLUE_BLINK`, `YELLOW_ON`, `YELLOW_BLINK`, `RED_ON`, `RED_OFF`, `GREY_OFF`

**ContainerState**: `RUNNING`, `PAUSED`, `EXITED`

**VmState**: `NOSTATE`, `RUNNING`, `IDLE`, `PAUSED`, `SHUTDOWN`, `SHUTOFF`, `CRASHED`, `PMSUSPENDED`

**DiskSmartStatus**: `OK`, `UNKNOWN`

**NotificationImportance**: `ALERT`, `INFO`, `WARNING`

**Temperature**: `CELSIUS`, `FAHRENHEIT`

**UpdateStatus**: `UP_TO_DATE`, `UPDATE_AVAILABLE`, `REBUILD_READY`, `UNKNOWN`

## GraphQL Client Implementation

### Decision: HTTP Client
- **Library**: aiohttp
- **Rationale**: Already used by Home Assistant core; async-native; well-tested
- **Alternatives considered**:
  - `gql` (dedicated GraphQL client) - rejected as adds dependency; aiohttp is sufficient for simple queries
  - `httpx` - rejected as not used by HA core

### Decision: Query Approach
- **Method**: Static query strings with variable substitution
- **Rationale**: Simpler than dynamic query building; queries are known at development time
- **Alternatives considered**:
  - Query builder library - rejected as overkill for static queries
  - Introspection-based - rejected as adds complexity

### Decision: ID Handling
- **Method**: Accept and pass PrefixedID format as-is
- **Rationale**: The API handles prefix stripping on input; always returns prefixed IDs
- **Note**: Store entity unique_ids with the full prefixed ID for stability

## Data Validation

### Decision: Pydantic Models
- **Library**: Pydantic v2 (as specified in requirements)
- **Approach**: Define models for each API response type with `model_config = ConfigDict(extra="ignore")`
- **Rationale**:
  - Specified in FR-012
  - `extra="ignore"` supports FR-018 (graceful handling of unknown fields)
  - Provides type safety and validation
- **Alternatives considered**: dataclasses - rejected as pydantic is explicitly required

### Decision: Version Compatibility Check
- **Method**: Query `info.versions.core.unraid` on connection; validate minimum version
- **Minimum Version**: 7.2.0 (first version with stable GraphQL API)
- **Rationale**: Supports FR-017 (minimum schema version check)
- **Alternatives considered**: Schema introspection - rejected as too complex; version check is sufficient

## Polling Strategy

### Decision: Dual Coordinator Pattern
- **System Coordinator**: Polls every 30 seconds (configurable)
  - `metrics { cpu, memory }` - Real-time utilization
  - `docker { containers }` - Container states
  - `vms { domains }` - VM states
  - `upsDevices` - UPS status
  - `notifications { overview }` - Notification counts
- **Storage Coordinator**: Polls every 5 minutes (configurable)
  - `array` - Array status and disk health
  - `disks` - Hardware disk info
  - `shares` - Share information
- **Rationale**:
  - Different data has different freshness requirements
  - Reduces load on Unraid server
  - Matches FR-008 defaults
- **Alternatives considered**:
  - Single coordinator - rejected as disk polling every 30s is unnecessary
  - Three+ coordinators - rejected as overcomplicates
  - Subscriptions - deferred to future enhancement

### Decision: Container/VM Updates
- **Method**: Included in System Coordinator polling
- **Rationale**: Container/VM state changes are relatively frequent; users expect responsive control
- **Alternatives considered**: Separate coordinator - rejected to limit complexity

## Entity Unique ID Strategy

### Decision: Composite Unique IDs
Based on clarification session and API structure:
- **Server Device**: `{system_uuid}` from `info.system.uuid`
- **System Sensors**: `{system_uuid}_{sensor_type}` (e.g., `abc123_cpu_usage`)
- **Array Sensor**: `{system_uuid}_array`
- **Disk Sensors**: `{system_uuid}_{disk_serial}` from `disk.serialNum`
- **Docker Switches**: `{system_uuid}_{container_id}` (using PrefixedID)
- **VM Switches**: `{system_uuid}_{vm_id}` (using PrefixedID)
- **UPS Sensor**: `{system_uuid}_{ups_id}` from UPS device id
- **Share Sensors**: `{system_uuid}_share_{share_name}`

- **Rationale**: Stable across restarts; survives resource recreation; supports multiple servers
- **Alternatives considered**: Name-based IDs - rejected as unstable

## Error Handling Strategy

### Decision: HA Exception Hierarchy
- **ConfigEntryNotReady**: Connection failures during setup
- **HomeAssistantError**: Runtime errors (API failures, invalid responses)
- **UpdateFailed**: Coordinator update failures (marks entities unavailable)

- **Rationale**: Follows HA standards (Constitution principle V); proper user feedback
- **Alternatives considered**: Custom exceptions - rejected as HA hierarchy is sufficient

### Decision: GraphQL Error Handling
- **Method**: Check response for `errors` array; parse error messages
- **Common Errors**:
  - `FORBIDDEN`: Insufficient permissions (wrong API key role)
  - `UNAUTHORIZED`: Invalid or expired API key
  - `NOT_FOUND`: Resource doesn't exist
- **Rationale**: GraphQL returns errors in response body, not HTTP status codes

## Sources

- [Unraid API Official Schema](https://github.com/unraid/api/blob/main/api/generated-schema.graphql) - Primary source, v4.29.2
- [Unraid API Documentation](https://docs.unraid.net/API/)
- [Unraid API Usage Guide](https://docs.unraid.net/API/how-to-use-the-api/)
- [Unraid API GitHub Repository](https://github.com/unraid/api)
- [Unraid API Developer Docs](https://github.com/unraid/api/tree/main/api/docs/developer)

## Additional API Capabilities (Not in MVP Scope)

The following are available in the API but not planned for MVP:

1. **Log Files** (`logFiles`, `logFile`) - System log access
2. **RClone Backup** (`rclone`) - Cloud backup configuration
3. **Settings** (`settings`) - System settings management
4. **API Key Management** (`apiKeys`, `apiKey`) - Key CRUD operations
5. **Customization** (`customization`) - UI theme settings
6. **Connect** (`connect`) - Unraid Connect cloud features
7. **Flash Backup** (`initiateFlashBackup`) - Flash drive backup
8. **Docker Folders** (`createDockerFolder`, etc.) - Container organization
9. **SSO/OIDC** (`ssoSettings`, `oidcProviders`) - Authentication providers
````
