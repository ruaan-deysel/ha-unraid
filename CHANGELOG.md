# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (YYYY.MM.MICRO), matching Home Assistant's versioning scheme.

## [Unreleased]

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

[Unreleased]: https://github.com/ruaan-deysel/ha-unraid/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/ruaan-deysel/ha-unraid/releases/tag/v0.0.1
