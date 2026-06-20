# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (YYYY.MM.MICRO), matching Home Assistant's versioning scheme.

## [Unreleased]

### Added

- **Automatic Stale Entity Cleanup** ([#257](https://github.com/ruaan-deysel/ha-unraid/issues/257)): When a Docker container, VM, disk, share, UPS device, network interface, or temperature sensor is removed from the Unraid server, all its Home Assistant entities are now pruned automatically after the next coordinator refresh. Cleanup is guarded against transient API errors — entities are only removed when the coordinator update succeeds, so a momentary network outage never causes accidental entity loss. Empty devices are also removed from the device registry. `async_remove_config_entry_device` is now implemented, enabling the "Delete" button in the device UI for orphaned devices.

## [2026.6.1] - 2026-06-11

### Added

- **Network Interface Sensors**: New inbound/outbound throughput sensors for physical NICs, bonds, and user-configured bridges (`ethN`, `bondN`, `brN`, `wlanN`, including VLAN sub-interfaces like `br0.5`) from `metrics.network`, updated every 30 seconds and displayed in human-readable units (MB/s). Attributes include the interface state plus human-readable byte totals, packet counts, errors, and drops. Auto-generated plumbing — per-container `veth*`, per-VM `vnet*`/`tap*`, loopback, and Docker/libvirt-created bridges and shims (`br-<hash>`, `docker0`, `shim-br0`, `virbr0`) — gets no entities, and any previously created sensors for such interfaces are removed automatically. Requires Unraid GraphQL API 4.35.0+ — on older servers the sensors are simply not created
- **Check Container Updates Button**: New `button.*_check_container_updates` entity that forces a re-check of remote Docker image digests (the WebGUI "Check for Updates" action). Unraid caches each container's update-available state, so update entities previously only changed after Unraid's own periodic check — this button (and automations pressing it) refreshes that state on demand ([#245](https://github.com/ruaan-deysel/ha-unraid/issues/245)). Requires Unraid GraphQL API 4.35.0+
- **Update All Containers Button**: New `button.*_update_all_containers` entity (disabled by default) that updates every Docker container with a pending image update in one action, equivalent to the WebGUI "Update All". Requires Unraid GraphQL API 4.35.0+
- **Dynamic Entity Addition**: Containers, VMs, and network interfaces created after the integration starts now get their entities (switches, buttons, sensors, update entities) automatically on the next coordinator refresh — previously a manual integration reload was required for new resources to appear

### Changed

- **Updated unraid-api to v1.12.0**: Adds `typed_get_containers_safe()`, network metrics support, bulk container updates, and `refresh_docker_digests()` ([release notes](https://github.com/ruaan-deysel/unraid-api/releases/tag/v1.12.0))
- **Test Coverage and Strict Typing**: Every integration module is now at or above 95% test coverage (964 tests, 97% total), and pyright type checking reports zero errors and zero warnings — entity base classes are now generic over their coordinator type so coordinator data and action methods are precisely typed throughout

### Fixed

- **Diagnostics Download Crash**: Downloading integration diagnostics raised `AttributeError` because the coordinators did not track `last_update_success_time` — they now extend `TimestampDataUpdateCoordinator`, and diagnostics include the real last-success timestamps

- **CPU Spikes from Docker Container Polling** ([#237](https://github.com/ruaan-deysel/ha-unraid/issues/237)): The periodic Docker container poll now uses the lightweight `typed_get_containers_safe()` query from unraid-api v1.12.0 ([unraid-api#69](https://github.com/ruaan-deysel/unraid-api/issues/69)), which omits the writable-layer size computation (`sizeRootFs`/`sizeRw`/`sizeLog`, equivalent to `docker ps --size`) and heavy payload fields (`mounts`, `networkSettings`, `labels`, port/Tailscale subselections) that the integration never used. Measured against a live server with 17 containers, the poll dropped from ~3 s of server-side work to ~0.04 s — eliminating the main remaining source of the periodic CPU spikes. All entity-visible container data (state, update availability, icons, URLs) is unaffected.

- **Array State Sensor Not Updating** ([#247](https://github.com/ruaan-deysel/ha-unraid/issues/247)): `sensor.*_array_state` now reflects changes (started → stopped / stopped → started) within seconds instead of waiting up to 5 minutes for the next storage coordinator poll. Re-introduces the `subscribe_array_updates` WebSocket subscription that was removed in v2026.4.1 — this time with guards against the regression that caused its removal ([#211](https://github.com/ruaan-deysel/ha-unraid/issues/211), [#206](https://github.com/ruaan-deysel/ha-unraid/issues/206)): the server emits periodic heartbeat events with no state (observed every ~30 s on API v4.35), and these are now ignored entirely. A storage refresh is requested only when the reported array state actually changes, so a stable array never triggers WebSocket-driven storage polling and spun-down disks stay asleep. Because an explicit array start/stop keeps disks active, no unexpected disk wake-ups occur from this trigger.

- **Docker Container CPU / Memory Sensors Becoming Stale After Container Recreate** ([#245](https://github.com/ruaan-deysel/ha-unraid/issues/245)): Container CPU, memory-usage, and memory-percent sensors now resolve the current Docker container ID from coordinator data by name on every state read, instead of using the ID frozen at entity creation time. When a container is recreated its Docker ID changes; the stale ID caused the WebSocket stats lookup to return `None` indefinitely (fixed only by an integration reload). Entities now self-heal without a reload. Aggregate Docker sensors (Total CPU, Total Memory %) are also updated to exclude stats for container IDs that are no longer present in the coordinator's container list, preventing orphaned entries from inflating totals.

- **Container CPU / Memory Sensors Stuck on "Unknown"**: The container stats WebSocket subscription streams raw `docker stats` terminal output, and the first row of every sample cycle arrives with ANSI control codes (clear-screen/cursor-home) glued onto the container ID. Because the output order is stable, the same container was affected every cycle — its stats were stored under a corrupted key that never matched, leaving that container's CPU and memory sensors permanently "Unknown". The ID is now sanitized before storing stats.

- **Stopped Containers Reporting "Unknown" or Stale Stats**: Containers that are not running never appear in the `docker stats` stream, so their CPU/memory sensors showed "Unknown" (never started since HA restart) or froze on the last streamed value (stopped while HA was running). Stopped containers now report 0% CPU, 0% memory, and `0B / 0B` memory usage, and the aggregate Docker totals exclude lingering stats from stopped containers.

## [2026.6.0] - 2026-06-01

### Added

- **Option to Disable Container Update Sensors** ([#243](https://github.com/ruaan-deysel/ha-unraid/issues/243)): New `enable_container_updates` toggle in the integration's options (Settings → Devices & Services → Unraid → Configure), enabled by default to preserve existing behaviour. Disable it to stop creating the per-container `update` entities — useful if you manage container updates externally or don't need update notifications. Changing the option reloads the integration and adds/removes the entities automatically.

### Fixed

- **CPU Spikes Every 30 Seconds** ([#237](https://github.com/ruaan-deysel/ha-unraid/issues/237), [#206](https://github.com/ruaan-deysel/ha-unraid/issues/206)): Reduced periodic CPU load on the Unraid server caused by the 30-second system poll. Static server information (UUID, model, CPU, OS, versions) is now captured once at setup and reused instead of being re-queried every cycle, and the comparatively expensive Docker container listing (image-update checks and writable-layer size computation) is now polled at a 60-second cadence with its result reused in between. System metrics, VMs, UPS, and notifications continue to update every 30 seconds, and container control actions (start/stop/update) still refresh container state immediately.

## [2026.5.0] - 2026-05-12

### Added

- **Unraid Notification Events** ([#232](https://github.com/ruaan-deysel/ha-unraid/pull/232)): New Home Assistant event entity for Unraid notifications. Exposes notification details (title, subject, description, timestamp, importance, type, link, ID) as event attributes. Now you can create Home Assistant automations that trigger on Unraid notifications. Huge thanks to **@DrBlokmeister** for this contribution! 🎉

### Fixed

- **SSL/TLS Certificate Verification for Self-Signed Certificates** ([#223](https://github.com/ruaan-deysel/ha-unraid/pull/223)): Fixed connection issues with Unraid servers using self-signed certificates. Implemented `ignore_ssl` configuration flag to separate HTTPS transport from certificate verification, with automatic fallback when initial certificate validation fails. Maintains backward compatibility with existing configurations. Huge thanks to **@DrBlokmeister** for this contribution! 🎉
- **Plugin Sensor Count Incorrect** ([#221](https://github.com/ruaan-deysel/ha-unraid/issues/221)): Fixed `sensor.unraid_plugins` reporting only API module plugins (often `1`) instead of total installed Unraid plugins. The sensor now uses `installedUnraidPlugins` from GraphQL and reports the correct installed plugin count.
- **Mover Status Stale / Incorrect** ([#226](https://github.com/ruaan-deysel/ha-unraid/issues/226)): Fixed `binary_sensor.mover_active` showing stale "not running" state by moving mover-status polling to the 30-second system coordinator cadence (from the 15-minute infrastructure cadence), so Home Assistant status now matches Unraid more closely.

## [2026.4.1] - 2026-04-15

### Changed

- **Updated unraid-api to v1.10.0**: Includes new `get_system_metrics_safe()` method that omits temperature sensor queries to prevent waking sleeping disks ([#50](https://github.com/ruaan-deysel/unraid-api/issues/50))
- **Removed Unraid OS Version Requirement**: The integration now only checks the GraphQL API version (v4.31.1+), not the Unraid OS version. Users can run any Unraid OS version as long as the API is updated via the Unraid Connect plugin ([#217](https://github.com/ruaan-deysel/ha-unraid/issues/217))

### Fixed

- **Disks Waking from Standby Every 30 Seconds**: Fixed system coordinator polling `metrics.temperature.sensors` via `get_system_metrics()` which triggers smartctl reads and wakes sleeping/standby disks ([#211](https://github.com/ruaan-deysel/ha-unraid/issues/211), [#206](https://github.com/ruaan-deysel/ha-unraid/issues/206)) — now uses `get_system_metrics_safe()` from unraid-api v1.10.0 which omits the temperature block entirely. CPU temperature remains available via `info.cpu.packages.temp`
- **Misleading "Unsupported Version" Error Message**: Fixed config flow error message showing outdated minimum version requirements (7.2.0 / API v4.21.0) that did not match the actual library-enforced minimums (7.2.4 / API v4.31.1), causing confusion for users on Unraid 7.2.3 or earlier ([#217](https://github.com/ruaan-deysel/ha-unraid/issues/217))

### Removed

- **Array Updates WebSocket Subscription**: Removed `subscribe_array_updates` WebSocket subscription that triggered storage coordinator refreshes on array state changes — these refreshes could wake spun-down disks ([#211](https://github.com/ruaan-deysel/ha-unraid/issues/211))
- **Parity History WebSocket Subscription**: Removed `subscribe_parity_history` WebSocket subscription that triggered storage coordinator refreshes on parity status changes — parity status is still available via the 5-minute storage coordinator poll
- **System Temperature Sensors**: Hardware temperature sensors (motherboard, chipset) from `metrics.temperature.sensors` are no longer created — these required smartctl reads that wake sleeping disks. Per-disk temperatures from the storage coordinator (5-minute poll, cached data) remain available

## [2026.4.0] - 2026-04-14

### Added

- **Docker Container Update Entities**: New `update` platform with per-container update entities ([#212](https://github.com/ruaan-deysel/ha-unraid/issues/212)) — shows available image updates with install action to pull the latest image directly from Home Assistant
- **Network Access Sensor**: New diagnostic sensor (`sensor.{name}_network_access`) showing the primary LAN access URL with all access URLs (LAN/WAN, IPv4/IPv6) as extra attributes — powered by the new `Network` model from unraid-api v1.9.0
- **Notification WebSocket Subscription**: Real-time notification push via `subscribe_notification_added` — new notifications trigger an immediate system coordinator refresh instead of waiting for the 30-second poll cycle
- **Parity History WebSocket Subscription**: Live parity check progress updates via `subscribe_parity_history` — parity status changes trigger an immediate storage coordinator refresh instead of waiting for the 5-minute poll cycle

### Changed

- **Updated unraid-api to v1.9.1**: Includes improved temperature filtering (bogus sensor removal in the library's `TemperatureMetrics` model validator), `ParityCheck.speed` type change from `int` to `str`, new `Network`/`AccessUrl` models, new WebSocket subscriptions for notifications and parity history, capability detection for subscription gating, and `update_container()` support
- **Parity Speed Sensor Updated**: Adapted to handle `ParityCheck.speed` being a string value (changed from `int` in unraid-api v1.9.0) — the sensor now safely converts the string to float before calculating MiB/s
- **Array Update WebSocket Throttle**: Array state WebSocket events now use a dedicated 60-second minimum interval (up from the general 10-second debounce) to prevent rapid storage coordinator refreshes from waking spun-down disks ([#211](https://github.com/ruaan-deysel/ha-unraid/issues/211), [#206](https://github.com/ruaan-deysel/ha-unraid/issues/206))

### Fixed

- **Parity Speed Sensor Type Error**: Fixed `TypeError` that would occur when `ParityCheck.speed` returned as a string (breaking change in unraid-api v1.9.0) — the sensor now handles both string and `None` values gracefully
- **WebSocket Array Heartbeats Causing Unnecessary Refreshes**: Array update events with `state=None` (periodic heartbeats) are now filtered out, preventing unnecessary storage coordinator refreshes that could wake spun-down disks and cause high CPU usage ([#211](https://github.com/ruaan-deysel/ha-unraid/issues/211))

### Removed

- **Flash Device Usage Sensor**: Removed `FlashUsageSensor` — the Unraid GraphQL API does not expose filesystem usage data for the boot/flash device, so this sensor was permanently unavailable ([#208](https://github.com/ruaan-deysel/ha-unraid/issues/208))

## [2026.3.2] - 2026-03-22

### Fixed

- **Notification Buttons Not Working**: Fixed the "Archive all unread notifications" and "Delete all archived notifications" buttons not functioning due to incorrect API method calls. The buttons now correctly call `archive_notification(notification_id)` and `delete_notification(notification_id)` for each relevant notification, allowing users to manage their Unraid notifications directly from Home Assistant.
- **Storage Coordinator Fails with HTTP 400 on Unraid 7.2.4**: Fixed storage coordinator failing to fetch array/disks/shares data on Unraid 7.2.4 due to a GraphQL schema change that added new required fields. The coordinator now uses the latest `unraid-api 1.7.1` version which includes updated queries and models compatible with Unraid 7.2.4, restoring functionality for users on that Unraid version.

## [2026.3.1] - 2026-03-20

### Added

- **WebSocket Real-Time Subscriptions**: Live data streaming via GraphQL WebSocket subscriptions for container stats, array state changes, and UPS updates — replacing polling for these data sources
  - Container CPU/memory stats pushed in real-time (no 30s poll delay)
  - Array state changes (start/stop/parity) detected instantly
  - UPS status updates received immediately
  - Automatic reconnection with exponential backoff on connection loss
- **API Version Sensor**: New diagnostic sensor showing the Unraid GraphQL API version (e.g. "4.30.1") — helps users identify if they are running the latest version of the Unraid API
- **Extended Disk Attributes**: Disk usage sensors now include rotational, transport, format, read/write/error counts, color, and temperature thresholds (warning/critical) from unraid-api v1.7.0
- **Extended Share Attributes**: Share usage sensors now include cache policy, allocator, split level, floor, COW, color, and LUKS status from unraid-api v1.7.0
- **Extended Container Attributes**: Container switches now include project URL, support URL, registry URL, auto-start order, and Tailscale status from unraid-api v1.7.0
- **Container Stats Extra Attributes**: Container CPU sensor now includes block I/O and network I/O as state attributes

### Changed

- **Updated unraid-api to v1.7.0**: New API features including WebSocket subscriptions, direct UPS power readings, extended disk/share/container metadata, and boot device fallback support
- **Container Resource Sensors Reworked**: Container CPU, memory, and memory percentage sensors now powered by WebSocket real-time data instead of coordinator polling
- **Container Resource Sensors No Longer Diagnostic**: Container CPU, memory, and memory percentage sensors moved from diagnostic entity category to primary sensors
- **UPS Power Sensor Enhanced**: Now prefers direct `currentPower` value from the API (v1.7.0+), falling back to calculated value from load percentage × nominal power. The sensor is now available when the API reports power directly, even without user-configured nominal power
- **UPS Nominal Power Auto-Detection**: UPS energy sensor now automatically detects nominal power from the API (v1.7.0+) when available, removing the need to manually configure it in integration options. User-configured nominal power is still used as a fallback for older API versions
- **Boot Device Fallback**: Storage coordinator now falls back to `bootDevices[0]` when `array.boot` is `None`, improving compatibility with different Unraid configurations

### Fixed

- **Container Stats Sensor Unique IDs**: Fixed backward-compatible unique ID format for container resource sensors (`container_{name}_{metric}`) to match existing entity registry entries, preventing duplicate/orphaned entities on upgrade
- **Disk Temperature Attributes**: Temperature thresholds (warning/critical) now included when available from the API

## [2026.3.0] - 2026-03-01

### Added

- **Unraid Version Sensor**: Diagnostic sensor showing the Unraid OS version (e.g. "7.2.3") with API version and architecture in attributes ([#168](https://github.com/ruaan-deysel/ha-unraid/discussions/168))
- **System Health Binary Sensors**: 7 binary sensors for monitoring array and system health
  - Mover active: Indicates if the Unraid mover is currently running
  - Disks disabled: Problem sensor — ON if any disks are disabled (with count attribute)
  - Disks missing: Problem sensor — ON if any disks are missing (with count attribute)
  - Disks invalid: Problem sensor — ON if any disks are invalid (with count attribute)
  - Safe mode: Problem sensor — ON if server is in safe mode (plugins/Docker disabled)
  - Config invalid: Problem sensor — ON if array configuration is invalid
  - Filesystems unmountable: Problem sensor — ON if any filesystems cannot be mounted (with count attribute)
- **Service Binary Sensors**: Per-service binary sensor (SMB, NFS, etc.) indicating if each service is online, with version and uptime attributes (disabled by default)
- **Container Resource Sensors**: Per-container CPU, memory usage (bytes), and memory percentage sensors for detailed Docker monitoring (disabled by default)
- **Container Update Available Binary Sensor**: Per-container binary sensor indicating if a Docker image update is available, with image and state attributes
- **Parity Check Speed Sensor**: Current parity check/rebuild speed in MB/s with elapsed time, estimated time, and progress attributes (disabled by default)
- **UPS Voltage & Health Sensors**: 3 additional UPS sensors (disabled by default)
  - Input voltage (V)
  - Output voltage (V)
  - Battery health status (e.g. "Good", "Replace")
- **VM Control Buttons**: Added 5 button entities per VM for fine control
  - Force Stop: Immediately power off VM
  - Reboot: Gracefully restart VM
  - Pause: Suspend VM execution
  - Resume: Resume paused VM
  - Reset: Hard reset VM
- **Notification Management**: Added 4 sensors and 2 buttons for notification tracking and management
  - **Sensors**: Active notifications count, Unread info/warning/alert notifications, Archived notifications total
  - **Buttons**: Archive all unread notifications, Delete all archived notifications
- **Parity History Sensors**: Added 2 sensors for parity check tracking
  - Last parity check date (timestamp of most recent check)
  - Last parity check errors count (number of errors found)
- **Registration/License Sensors**: Added 2 sensors for license monitoring
  - License type (Basic, Plus, Pro, Trial) with expiration details in attributes
  - License state (valid, expired, trial, etc.)
- **Cloud/Remote Access Binary Sensors**: Added 2 binary sensors for connectivity status
  - Cloud connected: Indicates if server is connected to Unraid's Cloud service
  - Remote access: Indicates if myunraid.net remote access is active
- **Installed Plugins Sensor**: Count of installed plugins with full plugin list (name, version) in attributes

### Changed

- **Updated unraid-api to v1.6.0**: New API features including typed vars access, container resource metrics, and UPS voltage/health data
- **Infrastructure Coordinator**: Extended to fetch system variables (vars), registration, cloud, remote access, and plugins data
- **Container Switch Attributes**: Added `image_id`, `auto_start`, `web_ui_url`, and `icon_url` to Docker container switch extra state attributes
- **VM Switch Attributes**: Added `memory`, `vcpu`, `auto_start`, and `primary_gpu` to VM switch extra state attributes
- **Entity Settings**: All new entities are disabled by default with appropriate entity categories (diagnostic/config) per HA guidelines

### Fixed

- **Container Update Entities Showing UNKNOWN**: Fixed all container update available binary sensors showing "unknown" state when the API returns `None` for `isUpdateAvailable` — now correctly treated as "no update available" (off)

## [2026.2.3] - 2026-02-07

### Changed

- **Updated unraid-api to v1.5.0**: Improved SSL/TLS detection and port handling with better error messages for unreachable servers ([#159](https://github.com/ruaan-deysel/ha-unraid/issues/159), [#144](https://github.com/ruaan-deysel/ha-unraid/issues/144))
  - Fixed connection failures when using non-standard ports with HTTP-only servers
  - Simplified port configuration - now uses single port value; library handles HTTPS fallback automatically
  - Better error reporting when custom ports are unreachable (no silent fallback to port 443)
- Removed dummy port workaround from config flow and entry setup
- Simplified connection testing logic (2 attempts instead of 3: with/without SSL verify)
- Using library's `restart_container()` convenience method in Docker restart button

### Fixed

- **SSL Detection for HTTP-Only Servers**: Fixed integration unable to connect to servers with SSL/TLS mode "No" (HTTP-only) when using custom ports ([#159](https://github.com/ruaan-deysel/ha-unraid/issues/159))
  - Root cause: Port configuration was preventing HTTP probe, causing library to assume HTTPS on non-standard port
  - Now correctly probes HTTP on configured port and follows redirects to discover SSL/TLS mode
- **Connection Error Messages**: Improved error reporting for unreachable custom ports - now clearly indicates port unreachable instead of SSL errors

## [2026.2.2] - 2026-02-03

### Changed

- **Fixed Polling Intervals**: Polling intervals are now fixed per Home Assistant Core integration quality guidelines ([#156](https://github.com/ruaan-deysel/ha-unraid/issues/156))
  - System data (CPU, RAM, Docker, VMs): 30 seconds
  - Storage data (array, disks, SMART): 5 minutes
  - Users needing custom refresh rates can use `homeassistant.update_entity` service with automations
- **Removed INTEGRATION_VERSION constant**: Version is sourced from `manifest.json` (standard HA practice)

### Fixed

- **HA Core Compliance**: Integration now follows appropriate-polling guidelines for HA Core compatibility

## [2026.2.1] - 2026-02-01

### Fixed

- **Docker Container Restart Button**: Button entity to restart Docker containers directly from Home Assistant UI

## [2026.2.0] - 2026-01-29

### Added

- **RAM Used Sensor**: New sensor showing active memory consumption (memory used by running processes), matching Unraid's "System + Docker" display. Uses `total - available` calculation to exclude cached/buffered memory that can be reclaimed
- **Sensor Entity Translations**: Added proper translation keys for all sensor entities in `strings.json` and `translations/en.json`
- **Docker Container Restart Button**: New button entity to restart Docker containers directly from Home Assistant UI

### Changed

- **Uptime Sensor**: Renamed from "Uptime" to "Up since" to better describe the timestamp device class behavior. Removed diagnostic entity category to make it a regular sensor (aligns with core HA integration pattern)
- **Control Switches**: Converted button pairs to switches for better UX:
  - **Array Switch**: Toggle array on/off (replaces separate start/stop buttons)
  - **Parity Check Switch**: Toggle parity check running state (replaces separate start/stop buttons)
  - **Disk Spin Switch**: Toggle disk spin up/down state per disk (replaces separate spin up/down buttons)
- **Disk Temperature Sensors**: Now disabled by default to reduce entity clutter. Users can enable per-disk temperature monitoring as needed

### Fixed

- **RAM Used Calculation**: Fixed RAM Used sensor to show actual memory used by processes instead of raw "used" value which incorrectly included cached/buffered memory

## [2026.01.0] - 2026-01-13

### Added

- **Custom Port Configuration**: Support for custom HTTP and HTTPS ports for users with reverse proxies or non-standard Unraid configurations ([#130](https://github.com/ruaan-deysel/ha-unraid/issues/130), [#131](https://github.com/ruaan-deysel/ha-unraid/issues/131))
  - Separate HTTP Port field (default: 80) - used for initial connection and redirect discovery
  - Separate HTTPS Port field (default: 443) - used for secure connections after redirect

### Fixed

- **VM Detection**: Fixed VMs not being detected due to incorrect GraphQL field name (`domains` → `domain`)
- **Log Spam Reduction**: Changed "Some optional features unavailable" messages from INFO to DEBUG level to prevent flooding logs when UPS, VMs, or Docker are not configured
- **Entity Rename Stability**: Fixed Docker container and VM switches reverting to default names after container/VM updates ([#133](https://github.com/ruaan-deysel/ha-unraid/issues/133))
  - Entity `unique_id` now uses container/VM NAME instead of ID (which changes on update)
  - Renamed entities now persist correctly across container updates and integration reloads
  - **Further Log Spam Reduction**: Changed Docker/VM service not available messages from INFO to DEBUG level during setup ([#134](https://github.com/ruaan-deysel/ha-unraid/issues/134))
  - Users without Docker or VMs enabled no longer see these messages in normal logs
  - Messages still available at DEBUG level for troubleshooting

## [2025.12.2] - 2025-12-30

### Fixed

- **SSL/TLS Mode Detection**: Fixed connection issues when Unraid SSL/TLS setting is configured as "No" (HTTP-only) or "Yes" (self-signed certificate). Previously only "Strict" mode with myunraid.net URLs was properly detected. ([#124](https://github.com/ruaan-deysel/ha-unraid/issues/124))
- **HTTP-Only Mode Support**: Integration now correctly detects and uses HTTP when Unraid's SSL/TLS is set to "No", connecting directly to `http://server-ip/graphql`
- **Self-Signed Certificate Support**: When Unraid's SSL/TLS is set to "Yes", the integration now automatically retries with SSL verification disabled after detecting self-signed certificate errors
- **SSL Verification Persistence**: The `verify_ssl` setting is now properly saved to the config entry, ensuring connections work correctly after Home Assistant restarts
- **UPS Query Failure**: Fixed integration failing when no UPS is configured on the Unraid server. UPS data is now queried separately, so users without a UPS will no longer see errors. ([#126](https://github.com/ruaan-deysel/ha-unraid/issues/126))
- **VM Query Failure**: Fixed integration failing when VMs are not enabled on the Unraid server. VM data is now queried separately, so users without VMs enabled will no longer see errors.
- **Docker Query Failure**: Fixed integration failing when Docker is not enabled on the Unraid server. Docker data is now queried separately, so users without Docker enabled will no longer see errors.

### Changed

- Improved redirect URL discovery to handle all three Unraid SSL/TLS modes:
  - **No**: HTTP-only mode (no redirect)
  - **Yes**: HTTPS with self-signed certificate (302 redirect to HTTPS)
  - **Strict**: HTTPS via myunraid.net with Let's Encrypt certificate (302 redirect to myunraid.net)
- Refactored system coordinator to query optional services (Docker, VMs, UPS) separately for better fault tolerance

## [2025.12.1] - 2025-12-29

### Important Migration Notice

> ⚠️ **SSH to GraphQL Transition**: Release **2025.06.11** is the **last stable SSH-based** version of this integration. Starting with 2025.12.0, this integration uses Unraid's official GraphQL API exclusively. **There is no direct migration path** - you must remove the old integration and configure fresh with a new Unraid API key. Users preferring SSH can continue using [release 2025.06.11](https://github.com/ruaan-deysel/ha-unraid/releases/tag/v2025.06.11).

### Changed

- Updated `iot_class` to `local_polling` (communicates with local Unraid servers, not cloud)
- Added Claude Code CLI to devcontainer for development
- Improved GraphQL error logging - errors now shown at WARNING level for easier diagnostics

### Fixed

- Security: URL validation now uses proper hostname parsing instead of substring matching
- Type safety improvements in API client

## [2025.12.0] - 2025-12-27

### Added

- Initial release with GraphQL API support for Unraid 7.2.0+
- **System Monitoring**
  - CPU usage, temperature, and power sensors
  - Memory usage (bytes and percentage)
  - System uptime sensor
  - Active notifications sensor
- **Storage Management**
  - Array state and capacity sensors
  - Parity check status and progress
  - Per-disk health binary sensors
  - Per-disk usage sensors (data and cache disks)
  - Per-share usage sensors
  - Flash (boot) device usage sensor
- **Docker Container Control**
  - Switch entities for starting/stopping containers
  - Container state, image, and status attributes
  - Automatic container discovery
- **Virtual Machine Control**
  - Switch entities for starting/stopping VMs
  - VM state attributes
  - Automatic VM discovery
- **UPS Monitoring**
  - Battery charge level sensor
  - Load percentage sensor
  - Runtime estimate sensor
  - UPS connected binary sensor
- **Array Control Buttons**
  - Array start/stop buttons
  - Parity check start/stop buttons
  - Disk spin up/down buttons
- **Binary Sensors**
  - Array started status
  - Parity check running status
  - Parity valid status
  - Per-disk health status
- **Config Flow**
  - Easy setup with host and API key
  - Connection validation during setup
  - SSL verification support
- **Options Flow**
  - Configurable system polling interval (10-300 seconds)
  - Configurable storage polling interval (60-3600 seconds)
  - UPS capacity setting for power calculation
- **Dual Coordinator Pattern**
  - System coordinator for frequent updates (default 30s)
  - Storage coordinator for disk data (default 5min)
- **Diagnostics**
  - Full diagnostic data export
  - Automatic redaction of sensitive information (API keys)
- **Pydantic Data Validation**
  - Type-safe API response parsing
  - Forward compatibility with unknown fields

### Technical Details

- Requires Home Assistant 2024.12.0+
- Requires Unraid 7.2.0+ (GraphQL API v4.21.0+)
- HTTPS required for API communication
- API key authentication via `x-api-key` header

[Unreleased]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.6.0...HEAD
[2026.6.0]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.5.0...v2026.6.0
[2026.5.0]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.4.1...v2026.5.0
[2026.4.1]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.4.0...v2026.4.1
[2026.4.0]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.3.2...v2026.4.0
[2026.3.2]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.3.1...v2026.3.2
[2026.3.1]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.3.0...v2026.3.1
[2026.3.0]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.2.3...v2026.3.0
[2026.2.3]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.2.2...v2026.2.3
[2026.2.2]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.2.1...v2026.2.2
[2026.2.1]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.2.0...v2026.2.1
[2026.2.0]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.01.0...v2026.2.0
[2026.01.0]: https://github.com/ruaan-deysel/ha-unraid/compare/v2025.12.2...v2026.01.0
[2025.12.2]: https://github.com/ruaan-deysel/ha-unraid/compare/v2025.12.1...v2025.12.2
[2025.12.1]: https://github.com/ruaan-deysel/ha-unraid/releases/tag/v2025.12.1
[2025.12.0]: https://github.com/ruaan-deysel/ha-unraid/releases/tag/v2025.12.0
