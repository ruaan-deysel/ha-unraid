# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (YYYY.MM.MICRO), matching Home Assistant's versioning scheme.

## [Unreleased]

## [2026.2.2] - 2026-02-02

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

[Unreleased]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.2.2...HEAD
[2026.2.2]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.2.1...v2026.2.2
[2026.2.1]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.2.0...v2026.2.1
[2026.2.0]: https://github.com/ruaan-deysel/ha-unraid/compare/v2026.01.0...v2026.2.0
[2026.01.0]: https://github.com/ruaan-deysel/ha-unraid/compare/v2025.12.2...v2026.01.0
[2025.12.2]: https://github.com/ruaan-deysel/ha-unraid/compare/v2025.12.1...v2025.12.2
[2025.12.1]: https://github.com/ruaan-deysel/ha-unraid/releases/tag/v2025.12.1
[2025.12.0]: https://github.com/ruaan-deysel/ha-unraid/releases/tag/v2025.12.0
