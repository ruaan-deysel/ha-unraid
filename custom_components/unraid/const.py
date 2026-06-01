"""Constants for the Unraid integration."""

from __future__ import annotations

from typing import Final

# =============================================================================
# Library State Constants (for reuse across modules)
# =============================================================================
from unraid_api.const import (
    ARRAY_STATE_STARTED,
    ARRAY_STATE_STOPPED,
    CONTAINER_STATE_EXITED,
    CONTAINER_STATE_PAUSED,
    CONTAINER_STATE_RUNNING,
    VM_STATE_IDLE,
    VM_STATE_PAUSED,
    VM_STATE_RUNNING,
    VM_STATE_SHUT_OFF,
)

# =============================================================================
# Library Exception Imports (for reuse across modules)
# =============================================================================
from unraid_api.exceptions import (
    UnraidAPIError,
    UnraidAuthenticationError,
    UnraidConnectionError,
    UnraidTimeoutError,
)

__all__ = [
    "ARRAY_STATE_STARTED",
    "ARRAY_STATE_STOPPED",
    "CONTAINER_STATE_EXITED",
    "CONTAINER_STATE_PAUSED",
    "CONTAINER_STATE_RUNNING",
    "VM_STATE_IDLE",
    "VM_STATE_PAUSED",
    "VM_STATE_RUNNING",
    "VM_STATE_SHUT_OFF",
    "UnraidAPIError",
    "UnraidAuthenticationError",
    "UnraidConnectionError",
    "UnraidTimeoutError",
]

# =============================================================================
# Integration Info
# =============================================================================
DOMAIN: Final = "unraid"
MANUFACTURER: Final = "Lime Technology"

# Known placeholder UUIDs from AMI/OEM firmware that are not truly unique.
# These are common on mini PCs and certain OEM boards.
# IMPORTANT: All entries must be lowercase (compared via uuid.lower()).
PLACEHOLDER_UUIDS: Final = frozenset(
    {
        "03000200-0400-0500-0006-000700080009",
    }
)

# =============================================================================
# Configuration Keys
# =============================================================================
CONF_IGNORE_SSL: Final = "ignore_ssl"
CONF_UPS_CAPACITY_VA: Final = "ups_capacity_va"
CONF_UPS_NOMINAL_POWER: Final = "ups_nominal_power"
CONF_ENABLE_CONTAINER_UPDATES: Final = "enable_container_updates"

# =============================================================================
# Default Values
# =============================================================================
DEFAULT_PORT: Final = 80  # HTTP port for Unraid GraphQL API
DEFAULT_UPS_CAPACITY_VA: Final = 0  # 0 = informational only
DEFAULT_UPS_NOMINAL_POWER: Final = 0  # 0 = disabled, user must set for UPS Power sensor
DEFAULT_ENABLE_CONTAINER_UPDATES: Final = True  # create container update entities

# =============================================================================
# Polling Intervals (fixed per HA Core guidelines - not user-configurable)
# Users can use homeassistant.update_entity service for custom refresh rates
# =============================================================================
SYSTEM_POLL_INTERVAL: Final = 30  # seconds - system metrics, VMs, UPS, notifications
STORAGE_POLL_INTERVAL: Final = 300  # seconds (5 minutes) - array, disks, SMART
INFRA_POLL_INTERVAL: Final = 900  # seconds (15 minutes) - services, registration, cloud
# Docker container listing is comparatively expensive on the Unraid server
# (image-update checks and writable-layer size computation), so it is polled at
# a slower cadence than the rest of the 30s system data to reduce periodic CPU
# spikes on the server. Container control actions still refresh on demand via
# UnraidSystemCoordinator.async_request_docker_refresh().
DOCKER_POLL_INTERVAL: Final = 60  # seconds - Docker container list

# =============================================================================
# WebSocket Subscription Constants
# =============================================================================
WS_INITIAL_RETRY_DELAY: Final = 5  # seconds
WS_MAX_RETRY_DELAY: Final = 300  # seconds (5 minutes)
WS_RETRY_BACKOFF_FACTOR: Final = 2.0
# Leading-edge debounce: first WS event triggers refresh, subsequent events
# within this window are suppressed to prevent refresh storms.
WS_REFRESH_DEBOUNCE_SECONDS: Final = 10  # seconds


# =============================================================================
# Repair Issue IDs
# =============================================================================
REPAIR_AUTH_FAILED: Final = "auth_failed"
