# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (YYYY.MM.MICRO), matching Home Assistant's versioning scheme.

## [Unreleased]

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

[Unreleased]: https://github.com/ruaan-deysel/ha-unraid/compare/v2025.12.1...HEAD
[2025.12.1]: https://github.com/ruaan-deysel/ha-unraid/releases/tag/v2025.12.1
[2025.12.0]: https://github.com/ruaan-deysel/ha-unraid/releases/tag/v2025.12.0
