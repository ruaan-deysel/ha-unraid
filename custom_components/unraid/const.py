"""Constants for the Unraid integration."""

from typing import Final

# =============================================================================
# Integration Info
# =============================================================================
DOMAIN: Final = "unraid"

# =============================================================================
# Configuration Keys
# =============================================================================
CONF_SYSTEM_INTERVAL: Final = "system_interval"
CONF_STORAGE_INTERVAL: Final = "storage_interval"
CONF_UPS_CAPACITY_VA: Final = "ups_capacity_va"
CONF_UPS_NOMINAL_POWER: Final = "ups_nominal_power"

# =============================================================================
# Default Values
# =============================================================================
DEFAULT_SYSTEM_POLL_INTERVAL: Final = 30  # seconds
DEFAULT_STORAGE_POLL_INTERVAL: Final = 300  # seconds (5 minutes)
DEFAULT_UPS_CAPACITY_VA: Final = 0  # 0 = informational only
DEFAULT_UPS_NOMINAL_POWER: Final = 0  # 0 = disabled, user must set for UPS Power sensor

# =============================================================================
# State Values (for consistent state comparisons)
# =============================================================================
# Array states
STATE_ARRAY_STARTED: Final = "STARTED"

# Container states
STATE_CONTAINER_RUNNING: Final = "RUNNING"

# VM states (used by VM_RUNNING_STATES)
STATE_VM_RUNNING: Final = "RUNNING"
STATE_VM_IDLE: Final = "IDLE"

# Running states for VMs (states where VM is considered "on")
VM_RUNNING_STATES: Final = frozenset({STATE_VM_RUNNING, STATE_VM_IDLE})

# =============================================================================
# Repair Issue IDs
# =============================================================================
REPAIR_AUTH_FAILED: Final = "auth_failed"
