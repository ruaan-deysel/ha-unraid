"""Sensor entities for Unraid integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from unraid_api import format_bytes

from .const import (
    CONF_UPS_CAPACITY_VA,
    CONF_UPS_NOMINAL_POWER,
    DEFAULT_UPS_CAPACITY_VA,
    DEFAULT_UPS_NOMINAL_POWER,
)
from .entity import UnraidBaseEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from unraid_api.models import (
        ArrayDisk,
        DockerContainer,
        ParityHistoryEntry,
        Share,
        UPSDevice,
    )

    from . import UnraidConfigEntry
    from .coordinator import (
        UnraidInfraCoordinator,
        UnraidInfraData,
        UnraidStorageCoordinator,
        UnraidStorageData,
        UnraidSystemCoordinator,
        UnraidSystemData,
    )

_LOGGER = logging.getLogger(__name__)

# Coordinator handles all data updates, no parallel entity updates needed
PARALLEL_UPDATES = 0

# Byte conversion constant
BYTES_PER_UNIT = 1024


class UnraidSensorEntity(UnraidBaseEntity, SensorEntity):
    """Base class for Unraid sensor entities."""

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator
        | UnraidStorageCoordinator
        | UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
        resource_id: str,
        name: str,
        server_info: dict | None = None,
    ) -> None:
        """
        Initialize sensor entity.

        Args:
            coordinator: Data coordinator
            server_uuid: Unraid server UUID
            server_name: Friendly server name
            resource_id: Resource identifier for unique_id
            name: Entity name
            server_info: Optional dict with manufacturer, model, sw_version, etc.

        """
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=resource_id,
            name=name,
            server_info=server_info,
        )


class CpuSensor(UnraidSensorEntity):
    """CPU usage sensor with model and core count attributes."""

    _attr_translation_key = "cpu_usage"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize CPU sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="cpu_usage",
            name="CPU Usage",
            server_info=server_info,
        )

    @property
    def native_value(self) -> float | None:
        """Return CPU usage percentage."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.cpu_percent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return CPU details as attributes."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return {}
        return {
            "cpu_model": data.info.cpu_brand,
            "cpu_cores": data.info.cpu_cores,
            "cpu_threads": data.info.cpu_threads,
        }


class RAMUsageSensor(UnraidSensorEntity):
    """RAM usage percentage sensor with human-readable attributes."""

    _attr_translation_key = "ram_usage"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize RAM usage sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="ram_usage",
            name="RAM Usage",
        )

    @property
    def native_value(self) -> float | None:
        """Return memory usage percentage."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.memory_percent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return memory details as human-readable attributes."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return {}
        return {
            "total": format_bytes(data.metrics.memory_total),
            "used": format_bytes(data.metrics.memory_used),
            "free": format_bytes(data.metrics.memory_free),
            "available": format_bytes(data.metrics.memory_available),
        }


class RAMUsedSensor(UnraidSensorEntity):
    """
    RAM used sensor showing active memory consumption.

    This calculates memory actively used by processes (System + Docker in Unraid terms)
    by using: total - available.

    The 'available' memory includes free memory plus reclaimable cache/buffers,
    so total - available gives us the memory actually consumed by running processes.
    This matches what Unraid displays as "System + Docker" usage.
    """

    _attr_translation_key = "ram_used"
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = "B"
    _attr_suggested_unit_of_measurement = "GiB"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize RAM used sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="ram_used",
            name="RAM Used",
        )

    @property
    def native_value(self) -> int | None:
        """
        Return memory actively used by processes in bytes.

        Uses total - available to match Unraid's display of actual memory consumption,
        excluding cached/buffered memory that can be reclaimed.
        """
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        total = data.metrics.memory_total
        available = data.metrics.memory_available
        if total is None or available is None:
            return None
        return total - available


class SwapUsageSensor(UnraidSensorEntity):
    """Swap usage percentage sensor."""

    _attr_translation_key = "swap_usage"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize swap usage sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="swap_usage",
            name="Swap Usage",
        )

    @property
    def native_value(self) -> float | None:
        """Return swap usage percentage."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.swap_percent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return swap details as human-readable attributes."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return {}
        attrs: dict[str, Any] = {}
        if data.metrics.swap_total is not None:
            attrs["total"] = format_bytes(data.metrics.swap_total)
        if data.metrics.swap_used is not None:
            attrs["used"] = format_bytes(data.metrics.swap_used)
        return attrs


class SwapUsedSensor(UnraidSensorEntity):
    """Swap used sensor showing swap consumption in bytes."""

    _attr_translation_key = "swap_used"
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = "B"
    _attr_suggested_unit_of_measurement = "GiB"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize swap used sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="swap_used",
            name="Swap Used",
        )

    @property
    def native_value(self) -> int | None:
        """Return swap memory used in bytes."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.swap_used


class TemperatureSensor(UnraidSensorEntity):
    """CPU temperature sensor."""

    _attr_translation_key = "cpu_temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize temperature sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="cpu_temp",
            name="CPU Temperature",
        )

    @property
    def native_value(self) -> float | None:
        """Return average CPU temperature."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.average_cpu_temperature


class CpuPowerSensor(UnraidSensorEntity):
    """CPU power consumption sensor (requires Unraid API v4.26.0+)."""

    _attr_translation_key = "cpu_power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize CPU power sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="cpu_power",
            name="CPU Power",
        )

    @property
    def native_value(self) -> float | None:
        """Return CPU power consumption in watts."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.cpu_power


class UnraidVersionSensor(UnraidSensorEntity):
    """Sensor showing the Unraid OS version (e.g. 7.2.2)."""

    _attr_translation_key = "unraid_version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize Unraid version sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="unraid_version",
            name="Unraid Version",
        )

    @property
    def native_value(self) -> str | None:
        """Return the Unraid OS version string."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None or data.info is None:
            return None
        return data.info.sw_version

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional version details."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None or data.info is None:
            return {}
        attrs: dict[str, Any] = {}
        if data.info.api_version is not None:
            attrs["api_version"] = data.info.api_version
        if data.info.os_arch is not None:
            attrs["architecture"] = data.info.os_arch
        return attrs


class UptimeSensor(UnraidSensorEntity):
    """
    System uptime sensor using timestamp device class.

    Uses device_class=TIMESTAMP which expects a datetime representing
    when the system booted. Home Assistant will automatically display
    this as a relative time (e.g., "5 days ago").
    """

    _attr_translation_key = "uptime"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize uptime sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="uptime",
            name="Up since",
        )

    @property
    def native_value(self) -> datetime | None:
        """
        Return system boot time as datetime.

        The TIMESTAMP device class expects a datetime representing the boot time.
        Home Assistant automatically displays this as relative time.
        """
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.uptime


class ActiveNotificationsSensor(UnraidSensorEntity):
    """Active notifications count sensor."""

    _attr_translation_key = "active_notifications"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "notifications"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize active notifications sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="active_notifications",
            name="Active Notifications",
        )

    @property
    def native_value(self) -> int | None:
        """Return number of unread notifications."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.notifications_unread


class NotificationUnreadInfoSensor(UnraidSensorEntity):
    """Unread info notifications count sensor."""

    _attr_translation_key = "notifications_unread_info"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "notifications"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize unread info notifications sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="notifications_unread_info",
            name="Unread Info Notifications",
        )

    @property
    def native_value(self) -> int | None:
        """Return number of unread info notifications."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        overview = data.notification_overview
        if overview is None or overview.unread is None:
            return 0
        return overview.unread.info


class NotificationUnreadWarningSensor(UnraidSensorEntity):
    """Unread warning notifications count sensor."""

    _attr_translation_key = "notifications_unread_warning"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "notifications"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize unread warning notifications sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="notifications_unread_warning",
            name="Unread Warning Notifications",
        )

    @property
    def native_value(self) -> int | None:
        """Return number of unread warning notifications."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        overview = data.notification_overview
        if overview is None or overview.unread is None:
            return 0
        return overview.unread.warning


class NotificationUnreadAlertSensor(UnraidSensorEntity):
    """Unread alert notifications count sensor."""

    _attr_translation_key = "notifications_unread_alert"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "notifications"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize unread alert notifications sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="notifications_unread_alert",
            name="Unread Alert Notifications",
        )

    @property
    def native_value(self) -> int | None:
        """Return number of unread alert notifications."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        overview = data.notification_overview
        if overview is None or overview.unread is None:
            return 0
        return overview.unread.alert


class NotificationArchivedTotalSensor(UnraidSensorEntity):
    """Archived notifications total count sensor."""

    _attr_translation_key = "notifications_archived_total"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "notifications"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize archived notifications sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="notifications_archived_total",
            name="Archived Notifications",
        )

    @property
    def native_value(self) -> int | None:
        """Return number of archived notifications."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        overview = data.notification_overview
        if overview is None or overview.archive is None:
            return 0
        return overview.archive.total


# =============================================================================
# Registration / License Sensors
# =============================================================================


class RegistrationTypeSensor(UnraidSensorEntity):
    """Registration/license type sensor (Basic, Plus, Pro, etc.)."""

    _attr_translation_key = "registration_type"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize registration type sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="registration_type",
            name="License Type",
        )

    @property
    def native_value(self) -> str | None:
        """Return license type (Basic, Plus, Pro, etc.)."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.registration is None:
            return None
        return data.registration.type

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return registration details as extra attributes."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.registration is None:
            return {}
        reg = data.registration
        attrs: dict[str, Any] = {}
        if reg.state is not None:
            attrs["state"] = reg.state
        if reg.expiration is not None:
            attrs["expiration"] = reg.expiration
        if reg.updateExpiration is not None:
            attrs["update_expiration"] = reg.updateExpiration
        return attrs


class RegistrationStateSensor(UnraidSensorEntity):
    """Registration state sensor (valid, expired, trial, etc.)."""

    _attr_translation_key = "registration_state"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize registration state sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="registration_state",
            name="License State",
        )

    @property
    def native_value(self) -> str | None:
        """Return license state."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.registration is None:
            return None
        return data.registration.state


# =============================================================================
# Plugins Sensor
# =============================================================================


class InstalledPluginsSensor(UnraidSensorEntity):
    """Sensor showing count of installed plugins."""

    _attr_translation_key = "installed_plugins"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize installed plugins sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="installed_plugins",
            name="Installed Plugins",
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of installed plugins."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.plugins is None:
            return None
        return len(data.plugins)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return plugin details as extra attributes."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or not data.plugins:
            return {}
        plugins_list = [{"name": p.name, "version": p.version} for p in data.plugins]
        return {"plugins": plugins_list}


class ArrayStateSensor(UnraidSensorEntity):
    """Array state sensor."""

    _attr_translation_key = "array_state"

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize array state sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="array_state",
            name="Array State",
        )

    @property
    def native_value(self) -> str | None:
        """Return array state."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None:
            return None
        state = data.array_state
        return state.lower() if state else None


class ArrayUsageSensor(UnraidSensorEntity):
    """Array usage percentage sensor with human-readable attributes."""

    _attr_translation_key = "array_usage"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize array usage sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="array_usage",
            name="Array Usage",
        )

    @property
    def native_value(self) -> float | None:
        """Return array usage percentage."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.capacity is None:
            return None
        return data.capacity.usage_percent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return capacity details as human-readable attributes."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.capacity is None:
            return {}
        cap = data.capacity
        return {
            "total": format_bytes(cap.total_bytes),
            "used": format_bytes(cap.used_bytes),
            "free": format_bytes(cap.free_bytes),
        }


class ParityProgressSensor(UnraidSensorEntity):
    """Parity check progress sensor."""

    _attr_translation_key = "parity_progress"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize parity progress sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_progress",
            name="Parity Check Progress",
        )

    @property
    def native_value(self) -> int | None:
        """Return parity check progress percentage."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return None
        return data.parity_status.progress


class LastParityCheckDateSensor(UnraidSensorEntity):
    """Last parity check date sensor with history details as attributes."""

    _attr_translation_key = "last_parity_check_date"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize last parity check date sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="last_parity_check_date",
            name="Last Parity Check",
        )

    def _get_last_entry(self) -> ParityHistoryEntry | None:
        """Get the most recent parity history entry."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or not data.parity_history:
            return None
        return data.parity_history[0]

    @property
    def native_value(self) -> datetime | None:
        """Return date of last parity check as datetime."""
        entry = self._get_last_entry()
        if entry is None or entry.date is None:
            return None
        date_val = entry.date
        if isinstance(date_val, datetime):
            return date_val
        if isinstance(date_val, str):
            try:
                dt = datetime.fromisoformat(date_val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except (ValueError, AttributeError):
                return None
        # Handle numeric timestamps (epoch seconds)
        if isinstance(date_val, (int, float)):
            return datetime.fromtimestamp(date_val, tz=UTC)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return parity check history details as attributes."""
        entry = self._get_last_entry()
        if entry is None:
            return {}
        attrs: dict[str, Any] = {}
        if entry.duration is not None:
            attrs["duration_seconds"] = entry.duration
            attrs["duration"] = entry.duration_formatted
        if entry.speed is not None:
            attrs["speed"] = entry.speed
        if entry.status is not None:
            attrs["status"] = entry.status
        if entry.errors is not None:
            attrs["errors"] = entry.errors
        return attrs


class LastParityCheckErrorsSensor(UnraidSensorEntity):
    """Last parity check errors count sensor."""

    _attr_translation_key = "last_parity_check_errors"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "errors"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize last parity check errors sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="last_parity_check_errors",
            name="Last Parity Check Errors",
        )

    @property
    def native_value(self) -> int | None:
        """Return error count from last parity check."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or not data.parity_history:
            return None
        entry = data.parity_history[0]
        return entry.errors


class DiskTemperatureSensor(UnraidSensorEntity):
    """Disk temperature sensor."""

    _attr_translation_key = "disk_temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False  # User enables per-disk as needed

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        disk: ArrayDisk,
    ) -> None:
        """Initialize disk temperature sensor."""
        self._disk_id = disk.id
        self._disk_name = disk.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"disk_{self._disk_id}_temp",
            name=f"Disk {self._disk_name} Temperature",
        )
        self._attr_translation_placeholders = {"name": self._disk_name}

    def _get_disk(self) -> ArrayDisk | None:
        """Get current disk from coordinator data."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None:
            return None
        all_disks = (data.disks or []) + (data.parities or []) + (data.caches or [])
        for disk in all_disks:
            if disk.id == self._disk_id:
                return disk
        return None

    @property
    def native_value(self) -> int | None:
        """Return disk temperature."""
        disk = self._get_disk()
        if disk is None:
            return None
        return disk.temp

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes including spinning state."""
        disk = self._get_disk()
        if disk is None:
            return {}
        return {
            "spinning": disk.isSpinning,
            "status": disk.status,
            "device": disk.device,
            "type": disk.type,
        }


def _compute_disk_usage_percent(disk: ArrayDisk) -> float | None:
    """
    Compute disk usage percentage with fsSize-fsFree fallback.

    The primary calculation uses fsUsed/fsSize (via the library's usage_percent).
    As a defensive fallback for cases where fsUsed may be 0 or None while fsSize
    and fsFree are correct, usage is calculated from (fsSize - fsFree) / fsSize.
    """
    # Try the library's usage_percent first (uses fsUsed / fsSize)
    usage = disk.usage_percent
    if usage is not None and usage > 0:
        return usage

    # Fallback: calculate from fsSize - fsFree when fsUsed is 0 or None
    # This handles edge cases where the API may not populate fsUsed correctly
    if disk.fsSize is not None and disk.fsSize > 0 and disk.fsFree is not None:
        used = disk.fsSize - disk.fsFree
        if used > 0:
            return (used / disk.fsSize) * 100

    return usage


def _compute_disk_used_bytes(disk: ArrayDisk) -> int | None:
    """
    Compute disk used bytes with fsSize-fsFree fallback.

    When fsUsed is 0 or None but fsSize and fsFree are available,
    calculate used space as fsSize - fsFree.
    """
    # Use fsUsed if it's available and non-zero
    if disk.fsUsed is not None and disk.fsUsed > 0:
        return disk.fsUsed * BYTES_PER_UNIT

    # Fallback: calculate from fsSize - fsFree
    if disk.fsSize is not None and disk.fsFree is not None:
        used_kb = disk.fsSize - disk.fsFree
        if used_kb >= 0:
            return used_kb * BYTES_PER_UNIT

    return disk.fs_used_bytes


class DiskUsageSensor(UnraidSensorEntity):
    """Disk usage percentage sensor with human-readable attributes."""

    _attr_translation_key = "disk_usage"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        disk: ArrayDisk,
    ) -> None:
        """Initialize disk usage sensor."""
        self._disk_id = disk.id
        self._disk_name = disk.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"disk_{self._disk_id}_usage",
            name=f"Disk {self._disk_name} Usage",
        )
        self._attr_translation_placeholders = {"name": self._disk_name}

    def _get_disk(self) -> ArrayDisk | None:
        """Get current disk from coordinator data."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None:
            return None
        all_disks = (data.disks or []) + (data.parities or []) + (data.caches or [])
        for disk in all_disks:
            if disk.id == self._disk_id:
                return disk
        return None

    @property
    def native_value(self) -> float | None:
        """
        Return disk usage percentage.

        Uses a fallback calculation (fsSize - fsFree) when fsUsed is 0 or None,
        which can occur on some API versions or filesystem types.
        """
        disk = self._get_disk()
        if disk is None:
            return None
        return _compute_disk_usage_percent(disk)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return disk details as human-readable attributes."""
        disk = self._get_disk()
        if disk is None:
            return {}
        # Build attributes - only include what's available
        # Use computed used bytes to handle ZFS pool fallback
        attrs: dict[str, Any] = {
            "total": format_bytes(disk.fs_size_bytes),
            "used": format_bytes(_compute_disk_used_bytes(disk)),
            "free": format_bytes(disk.fs_free_bytes),
            "device": disk.device,
            "type": disk.type,
            "status": disk.status,
        }
        # Add filesystem type if available
        if disk.fsType:
            attrs["filesystem"] = disk.fsType
        # Add spin_state (derived from isSpinning)
        if disk.isSpinning is not None:
            attrs["spin_state"] = "active" if disk.isSpinning else "standby"
        # Add temperature if available
        if disk.temp is not None:
            attrs["temperature_celsius"] = disk.temp
        # Add SMART status if available
        if disk.smartStatus:
            attrs["smart_status"] = disk.smartStatus
        return attrs


# UPS Sensors


class UPSBatterySensor(UnraidSensorEntity):
    """UPS battery charge level sensor."""

    _attr_translation_key = "ups_battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
    ) -> None:
        """Initialize UPS battery sensor."""
        self._ups_id = ups.id
        self._ups_name = ups.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{self._ups_id}_battery",
            name="UPS Battery",
        )
        self._attr_translation_placeholders = {"name": self._ups_name}

    def _get_ups(self) -> UPSDevice | None:
        """Get current UPS from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for ups in data.ups_devices:
            if ups.id == self._ups_id:
                return ups
        return None

    @property
    def native_value(self) -> int | None:
        """Return UPS battery charge level."""
        ups = self._get_ups()
        if ups is None:
            return None
        return ups.battery.chargeLevel

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return UPS details as attributes."""
        ups = self._get_ups()
        if ups is None:
            return {}
        attrs: dict[str, Any] = {
            "model": self._ups_name,
            "status": ups.status,
        }
        if ups.battery.health is not None:
            attrs["health"] = ups.battery.health
        return attrs


class UPSLoadSensor(UnraidSensorEntity):
    """UPS load percentage sensor."""

    _attr_translation_key = "ups_load"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
    ) -> None:
        """Initialize UPS load sensor."""
        self._ups_id = ups.id
        self._ups_name = ups.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{self._ups_id}_load",
            name="UPS Load",
        )
        self._attr_translation_placeholders = {"name": self._ups_name}

    def _get_ups(self) -> UPSDevice | None:
        """Get current UPS from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for ups in data.ups_devices:
            if ups.id == self._ups_id:
                return ups
        return None

    @property
    def native_value(self) -> float | None:
        """Return UPS load percentage."""
        ups = self._get_ups()
        if ups is None:
            return None
        return ups.power.loadPercentage

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return UPS details as attributes."""
        ups = self._get_ups()
        if ups is None:
            return {}
        attrs: dict[str, Any] = {
            "model": self._ups_name,
            "status": ups.status,
        }
        if ups.power.inputVoltage is not None:
            attrs["input_voltage"] = ups.power.inputVoltage
        if ups.power.outputVoltage is not None:
            attrs["output_voltage"] = ups.power.outputVoltage
        return attrs


class UPSRuntimeSensor(UnraidSensorEntity):
    """UPS estimated runtime sensor showing human-readable duration."""

    _attr_translation_key = "ups_runtime"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
    ) -> None:
        """Initialize UPS runtime sensor."""
        self._ups_id = ups.id
        self._ups_name = ups.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{self._ups_id}_runtime",
            name="UPS Runtime",
        )
        self._attr_translation_placeholders = {"name": self._ups_name}

    def _get_ups(self) -> UPSDevice | None:
        """Get current UPS from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for ups in data.ups_devices:
            if ups.id == self._ups_id:
                return ups
        return None

    @property
    def native_value(self) -> str | None:
        """Return UPS estimated runtime as human-readable string."""
        ups = self._get_ups()
        if ups is None:
            return None
        return ups.battery.runtime_formatted

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return UPS details as attributes."""
        ups = self._get_ups()
        if ups is None:
            return {}
        attrs: dict[str, Any] = {
            "model": self._ups_name,
            "status": ups.status,
        }
        if ups.battery.estimatedRuntime is not None:
            attrs["runtime_seconds"] = ups.battery.estimatedRuntime
            attrs["runtime_minutes"] = round(ups.battery.estimatedRuntime / 60)
        return attrs


class UPSPowerSensor(UnraidSensorEntity):
    """
    UPS power consumption sensor for Energy Dashboard.

    Calculates power consumption from load percentage and UPS nominal power.
    Formula: Power (W) = Load% / 100 * Nominal Power (W)

    Example: 12% load on UPS with 800W nominal power = 96W

    The UPS nominal power must be configured in the integration options.
    This value is shown in the Unraid UI under Power > Nominal power.
    If not configured (0), this sensor will be unavailable.
    """

    _attr_translation_key = "ups_power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
        ups_capacity_va: int = DEFAULT_UPS_CAPACITY_VA,
        ups_nominal_power: int = DEFAULT_UPS_NOMINAL_POWER,
    ) -> None:
        """
        Initialize UPS power sensor.

        Args:
            coordinator: System coordinator
            server_uuid: Server unique identifier
            server_name: Server friendly name
            ups: UPS device data
            ups_capacity_va: UPS capacity in VA (informational)
            ups_nominal_power: UPS nominal power in watts (used for calculation)

        """
        self._ups_id = ups.id
        self._ups_name = ups.name
        self._ups_capacity_va = ups_capacity_va
        self._ups_nominal_power = ups_nominal_power
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{self._ups_id}_power",
            name="UPS Power",
        )
        self._attr_translation_placeholders = {"name": self._ups_name}

    def _get_ups(self) -> UPSDevice | None:
        """Get current UPS from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for ups in data.ups_devices:
            if ups.id == self._ups_id:
                return ups
        return None

    @property
    def available(self) -> bool:
        """
        Return if entity is available.

        Only available if UPS nominal power is configured (> 0).
        """
        if self._ups_nominal_power <= 0:
            return False
        return super().available

    @property
    def native_value(self) -> float | None:
        """
        Return calculated UPS power consumption in watts.

        Uses the library's calculate_power_watts helper.
        """
        if self._ups_nominal_power <= 0:
            return None
        ups = self._get_ups()
        if ups is None:
            return None
        return ups.calculate_power_watts(self._ups_nominal_power)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return UPS power calculation details as attributes."""
        ups = self._get_ups()
        attrs: dict[str, Any] = {
            "model": self._ups_name,
            "nominal_power_watts": self._ups_nominal_power,
        }
        # Include VA rating if configured (informational)
        if self._ups_capacity_va > 0:
            attrs["ups_capacity_va"] = self._ups_capacity_va
        if ups is not None:
            attrs["status"] = ups.status
            if ups.power.loadPercentage is not None:
                attrs["load_percentage"] = ups.power.loadPercentage
            if ups.power.inputVoltage is not None:
                attrs["input_voltage"] = ups.power.inputVoltage
            if ups.power.outputVoltage is not None:
                attrs["output_voltage"] = ups.power.outputVoltage
        return attrs


class UPSEnergySensor(UnraidSensorEntity, RestoreEntity):
    """
    UPS energy consumption sensor for Energy Dashboard.

    Calculates cumulative energy (kWh) from UPS power using Riemann sum
    (trapezoidal integration). The value persists across restarts.

    This sensor is compatible with the Energy Dashboard's
    "Device energy consumption" dropdown.

    Requirements:
    - device_class: energy
    - state_class: total_increasing
    - unit: kWh
    """

    _attr_translation_key = "ups_energy"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 3
    _attr_entity_category = None  # Primary entity, not diagnostic

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
        ups_nominal_power: int,
    ) -> None:
        """
        Initialize UPS energy sensor.

        Args:
            coordinator: System coordinator
            server_uuid: Server unique identifier
            server_name: Server friendly name
            ups: UPS device data
            ups_nominal_power: UPS nominal power in watts (used for calculation)

        """
        self._ups_id = ups.id
        self._ups_name = ups.name
        self._ups_nominal_power = ups_nominal_power
        self._total_energy_kwh: float = 0.0
        self._last_power_watts: float | None = None
        self._last_update_time: datetime | None = None
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{self._ups_id}_energy",
            name="UPS Energy",
        )
        self._attr_translation_placeholders = {"name": self._ups_name}

    async def async_added_to_hass(self) -> None:
        """Restore previous energy value when entity is added."""
        await super().async_added_to_hass()

        # Restore previous state if available
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (
            "unknown",
            "unavailable",
        ):
            try:
                self._total_energy_kwh = float(last_state.state)
                _LOGGER.debug(
                    "Restored UPS energy value: %.3f kWh",
                    self._total_energy_kwh,
                )
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Could not restore UPS energy value from state: %s",
                    last_state.state,
                )

    def _get_ups(self) -> UPSDevice | None:
        """Get current UPS from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for ups in data.ups_devices:
            if ups.id == self._ups_id:
                return ups
        return None

    def _calculate_current_power(self) -> float | None:
        """Calculate current power consumption in watts."""
        if self._ups_nominal_power <= 0:
            return None
        ups = self._get_ups()
        if ups is None:
            return None
        return ups.calculate_power_watts(self._ups_nominal_power)

    def _update_energy(self) -> None:
        """Update cumulative energy using trapezoidal integration."""
        current_power = self._calculate_current_power()
        current_time = datetime.now(UTC)

        if (
            current_power is not None
            and self._last_power_watts is not None
            and self._last_update_time is not None
        ):
            # Calculate time elapsed in hours
            time_delta = current_time - self._last_update_time
            hours_elapsed = time_delta.total_seconds() / 3600

            # Trapezoidal integration: average of old and new power
            avg_power_watts = (self._last_power_watts + current_power) / 2
            energy_kwh = (avg_power_watts * hours_elapsed) / 1000

            self._total_energy_kwh += energy_kwh

        # Update tracking values
        self._last_power_watts = current_power
        self._last_update_time = current_time

    def _handle_coordinator_update(self) -> None:
        """Update energy accumulation on each coordinator data push."""
        self._update_energy()
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if self._ups_nominal_power <= 0:
            return False
        return super().available

    @property
    def native_value(self) -> float | None:
        """Return cumulative energy consumption in kWh."""
        if self._ups_nominal_power <= 0:
            return None
        return round(self._total_energy_kwh, 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return energy tracking details as attributes."""
        attrs: dict[str, Any] = {
            "model": self._ups_name,
            "nominal_power_watts": self._ups_nominal_power,
        }
        if self._last_power_watts is not None:
            attrs["current_power_watts"] = round(self._last_power_watts, 1)
        if self._last_update_time is not None:
            attrs["last_updated"] = self._last_update_time.isoformat()
        return attrs


# Share Sensors


class ShareUsageSensor(UnraidSensorEntity):
    """Share usage percentage sensor with human-readable attributes."""

    _attr_translation_key = "share_usage"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        share: Share,
    ) -> None:
        """Initialize share usage sensor."""
        self._share_id = share.id
        self._share_name = share.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"share_{self._share_id}_usage",
            name=f"Share {self._share_name} Usage",
        )
        self._attr_translation_placeholders = {"name": self._share_name}

    def _get_share(self) -> Share | None:
        """Get current share from coordinator data."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None:
            return None
        for share in data.shares:
            if share.id == self._share_id:
                return share
        return None

    @property
    def native_value(self) -> float | None:
        """Return share usage percentage."""
        share = self._get_share()
        if share is None:
            return None
        return share.usage_percent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return share details as human-readable attributes."""
        share = self._get_share()
        if share is None:
            return {}
        return {
            "total": format_bytes(share.size_bytes),
            "used": format_bytes(share.used_bytes),
            "free": format_bytes(share.free_bytes),
        }


# Flash Device Sensor


class FlashUsageSensor(UnraidSensorEntity):
    """Flash/boot device usage percentage sensor with human-readable attributes."""

    _attr_translation_key = "flash_usage"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize flash usage sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="flash_usage",
            name="Flash Device Usage",
        )

    @property
    def native_value(self) -> float | None:
        """Return flash device usage percentage."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.boot is None:
            return None
        return data.boot.usage_percent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return flash details as human-readable attributes."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.boot is None:
            return {}
        boot = data.boot
        return {
            "total": format_bytes(boot.fs_size_bytes),
            "used": format_bytes(boot.fs_used_bytes),
            "free": format_bytes(boot.fs_free_bytes),
            "device": boot.device,
            "status": boot.status,
        }


# =============================================================================
# Container Resource Sensors (disabled by default)
# =============================================================================


class ContainerCpuSensor(UnraidSensorEntity):
    """Container CPU usage percentage sensor."""

    _attr_translation_key = "container_cpu"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        container: DockerContainer,
    ) -> None:
        """Initialize container CPU sensor."""
        self._container_name = container.name.lstrip("/")
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_{self._container_name}_cpu",
            name=f"Container {self._container_name} CPU",
        )
        self._attr_translation_placeholders = {"name": self._container_name}

    def _get_container(self) -> DockerContainer | None:
        """Get current container from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for c in data.containers:
            if c.name.lstrip("/") == self._container_name:
                return c
        return None

    @property
    def native_value(self) -> float | None:
        """Return container CPU usage percentage."""
        container = self._get_container()
        if container is None or container.stats is None:
            return None
        return container.stats.cpuPercent


class ContainerMemoryUsageSensor(UnraidSensorEntity):
    """Container memory usage sensor in bytes."""

    _attr_translation_key = "container_memory_usage"
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = "B"
    _attr_suggested_unit_of_measurement = "MiB"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        container: DockerContainer,
    ) -> None:
        """Initialize container memory usage sensor."""
        self._container_name = container.name.lstrip("/")
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_{self._container_name}_memory",
            name=f"Container {self._container_name} Memory",
        )
        self._attr_translation_placeholders = {"name": self._container_name}

    def _get_container(self) -> DockerContainer | None:
        """Get current container from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for c in data.containers:
            if c.name.lstrip("/") == self._container_name:
                return c
        return None

    @property
    def native_value(self) -> int | None:
        """Return container memory usage in bytes."""
        container = self._get_container()
        if container is None or container.stats is None:
            return None
        return container.stats.memoryUsage


class ContainerMemoryPercentSensor(UnraidSensorEntity):
    """Container memory usage percentage sensor."""

    _attr_translation_key = "container_memory_percent"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        container: DockerContainer,
    ) -> None:
        """Initialize container memory percent sensor."""
        self._container_name = container.name.lstrip("/")
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_{self._container_name}_memory_pct",
            name=f"Container {self._container_name} Memory %",
        )
        self._attr_translation_placeholders = {"name": self._container_name}

    def _get_container(self) -> DockerContainer | None:
        """Get current container from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for c in data.containers:
            if c.name.lstrip("/") == self._container_name:
                return c
        return None

    @property
    def native_value(self) -> float | None:
        """Return container memory usage percentage."""
        container = self._get_container()
        if container is None or container.stats is None:
            return None
        return container.stats.memoryPercent


# =============================================================================
# Parity Speed Sensor
# =============================================================================


class ParitySpeedSensor(UnraidSensorEntity):
    """Parity check speed sensor (disabled by default)."""

    _attr_translation_key = "parity_speed"
    _attr_native_unit_of_measurement = "MiB/s"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize parity speed sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_speed",
            name="Parity Check Speed",
        )

    @property
    def native_value(self) -> float | None:
        """Return current parity check speed in MiB/s."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return None
        speed = data.parity_status.speed
        if speed is None:
            return None
        # Convert from bytes/s to MiB/s
        return round(speed / (1024 * 1024), 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return parity check speed details."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return {}
        parity = data.parity_status
        attrs: dict[str, Any] = {}
        if parity.elapsed is not None:
            attrs["elapsed_seconds"] = parity.elapsed
        if parity.estimated is not None:
            attrs["estimated_seconds"] = parity.estimated
        if parity.progress is not None:
            attrs["progress"] = parity.progress
        return attrs


# =============================================================================
# UPS Voltage & Health Sensors
# =============================================================================


class UPSInputVoltageSensor(UnraidSensorEntity):
    """UPS input voltage sensor."""

    _attr_translation_key = "ups_input_voltage"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
    ) -> None:
        """Initialize UPS input voltage sensor."""
        self._ups_id = ups.id
        self._ups_name = ups.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{self._ups_id}_input_voltage",
            name="UPS Input Voltage",
        )
        self._attr_translation_placeholders = {"name": self._ups_name}

    def _get_ups(self) -> UPSDevice | None:
        """Get current UPS from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for ups in data.ups_devices:
            if ups.id == self._ups_id:
                return ups
        return None

    @property
    def native_value(self) -> float | None:
        """Return UPS input voltage."""
        ups = self._get_ups()
        if ups is None:
            return None
        return ups.power.inputVoltage


class UPSOutputVoltageSensor(UnraidSensorEntity):
    """UPS output voltage sensor."""

    _attr_translation_key = "ups_output_voltage"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
    ) -> None:
        """Initialize UPS output voltage sensor."""
        self._ups_id = ups.id
        self._ups_name = ups.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{self._ups_id}_output_voltage",
            name="UPS Output Voltage",
        )
        self._attr_translation_placeholders = {"name": self._ups_name}

    def _get_ups(self) -> UPSDevice | None:
        """Get current UPS from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for ups in data.ups_devices:
            if ups.id == self._ups_id:
                return ups
        return None

    @property
    def native_value(self) -> float | None:
        """Return UPS output voltage."""
        ups = self._get_ups()
        if ups is None:
            return None
        return ups.power.outputVoltage


class UPSBatteryHealthSensor(UnraidSensorEntity):
    """UPS battery health status sensor."""

    _attr_translation_key = "ups_battery_health"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
    ) -> None:
        """Initialize UPS battery health sensor."""
        self._ups_id = ups.id
        self._ups_name = ups.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{self._ups_id}_battery_health",
            name="UPS Battery Health",
        )
        self._attr_translation_placeholders = {"name": self._ups_name}

    def _get_ups(self) -> UPSDevice | None:
        """Get current UPS from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for ups in data.ups_devices:
            if ups.id == self._ups_id:
                return ups
        return None

    @property
    def native_value(self) -> str | None:
        """Return UPS battery health status."""
        ups = self._get_ups()
        if ups is None:
            return None
        return ups.battery.health


def _create_ups_sensors(
    system_coordinator: UnraidSystemCoordinator,
    server_uuid: str,
    server_name: str,
    entry: UnraidConfigEntry,
) -> list[SensorEntity]:
    """Create UPS sensor entities if UPS devices are present."""
    if not system_coordinator.data or not system_coordinator.data.ups_devices:
        _LOGGER.debug("No UPS devices connected, skipping UPS sensors")
        return []

    ups_capacity_va = entry.options.get(CONF_UPS_CAPACITY_VA, DEFAULT_UPS_CAPACITY_VA)
    ups_nominal_power = entry.options.get(
        CONF_UPS_NOMINAL_POWER, DEFAULT_UPS_NOMINAL_POWER
    )
    _LOGGER.debug(
        "Found %d UPS device(s), creating sensors (VA: %d, Nominal Power: %dW)",
        len(system_coordinator.data.ups_devices),
        ups_capacity_va,
        ups_nominal_power,
    )

    entities: list[SensorEntity] = []
    for ups in system_coordinator.data.ups_devices:
        entities.extend(
            [
                UPSBatterySensor(system_coordinator, server_uuid, server_name, ups),
                UPSLoadSensor(system_coordinator, server_uuid, server_name, ups),
                UPSRuntimeSensor(system_coordinator, server_uuid, server_name, ups),
                UPSInputVoltageSensor(
                    system_coordinator, server_uuid, server_name, ups
                ),
                UPSOutputVoltageSensor(
                    system_coordinator, server_uuid, server_name, ups
                ),
                UPSBatteryHealthSensor(
                    system_coordinator, server_uuid, server_name, ups
                ),
                UPSPowerSensor(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    ups,
                    ups_capacity_va,
                    ups_nominal_power,
                ),
            ]
        )
        # Add UPS Energy sensor (kWh) - only if nominal power is configured
        if ups_nominal_power > 0:
            entities.append(
                UPSEnergySensor(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    ups,
                    ups_nominal_power,
                )
            )
            _LOGGER.debug(
                "Created UPS Energy sensor for UPS %s (nominal power: %dW)",
                ups.name,
                ups_nominal_power,
            )
    return entities


def _create_container_sensors(
    system_coordinator: UnraidSystemCoordinator,
    server_uuid: str,
    server_name: str,
) -> list[SensorEntity]:
    """Create container resource sensor entities if containers exist."""
    if not system_coordinator.data or not system_coordinator.data.containers:
        return []

    entities: list[SensorEntity] = []
    for container in system_coordinator.data.containers:
        entities.extend(
            [
                ContainerCpuSensor(
                    system_coordinator, server_uuid, server_name, container
                ),
                ContainerMemoryUsageSensor(
                    system_coordinator, server_uuid, server_name, container
                ),
                ContainerMemoryPercentSensor(
                    system_coordinator, server_uuid, server_name, container
                ),
            ]
        )
    return entities


def _create_disk_sensors(
    storage_coordinator: UnraidStorageCoordinator,
    server_uuid: str,
    server_name: str,
) -> list[SensorEntity]:
    """Create disk, share, and flash sensor entities from storage data."""
    if not storage_coordinator.data:
        return []

    entities: list[SensorEntity] = []
    data = storage_coordinator.data

    # Data disks - usage and temperature sensors
    for disk in data.disks or []:
        entities.append(
            DiskUsageSensor(storage_coordinator, server_uuid, server_name, disk)
        )
        entities.append(
            DiskTemperatureSensor(storage_coordinator, server_uuid, server_name, disk)
        )

    # Parity disks - temperature sensors only
    for disk in data.parities or []:
        entities.append(
            DiskTemperatureSensor(storage_coordinator, server_uuid, server_name, disk)
        )

    # Cache disks - usage and temperature sensors
    for disk in data.caches or []:
        entities.append(
            DiskUsageSensor(storage_coordinator, server_uuid, server_name, disk)
        )
        entities.append(
            DiskTemperatureSensor(storage_coordinator, server_uuid, server_name, disk)
        )

    # Share sensors
    for share in data.shares or []:
        entities.append(
            ShareUsageSensor(storage_coordinator, server_uuid, server_name, share)
        )

    # Flash device sensor (if boot device exists)
    if data.boot:
        entities.append(FlashUsageSensor(storage_coordinator, server_uuid, server_name))

    return entities


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    _LOGGER.debug("Setting up Unraid sensor platform")

    # Get coordinators from runtime_data (HA 2024.4+ pattern)
    runtime_data = entry.runtime_data
    system_coordinator = runtime_data.system_coordinator
    storage_coordinator = runtime_data.storage_coordinator
    server_info = runtime_data.server_info

    # Server info is now a flat dict with uuid, name, manufacturer, etc.
    server_uuid = server_info.get("uuid", "unknown")
    server_name = server_info.get("name", entry.data.get("host", "Unraid"))

    entities: list[SensorEntity] = []

    # System sensors - pass server_info to first entity to set device info
    entities.extend(
        [
            CpuSensor(system_coordinator, server_uuid, server_name, server_info),
            CpuPowerSensor(system_coordinator, server_uuid, server_name),
            RAMUsageSensor(system_coordinator, server_uuid, server_name),
            RAMUsedSensor(system_coordinator, server_uuid, server_name),
            SwapUsageSensor(system_coordinator, server_uuid, server_name),
            SwapUsedSensor(system_coordinator, server_uuid, server_name),
            TemperatureSensor(system_coordinator, server_uuid, server_name),
            UnraidVersionSensor(system_coordinator, server_uuid, server_name),
            UptimeSensor(system_coordinator, server_uuid, server_name),
            ActiveNotificationsSensor(system_coordinator, server_uuid, server_name),
            NotificationUnreadInfoSensor(system_coordinator, server_uuid, server_name),
            NotificationUnreadWarningSensor(
                system_coordinator, server_uuid, server_name
            ),
            NotificationUnreadAlertSensor(system_coordinator, server_uuid, server_name),
            NotificationArchivedTotalSensor(
                system_coordinator, server_uuid, server_name
            ),
        ]
    )

    # UPS sensors
    entities.extend(
        _create_ups_sensors(system_coordinator, server_uuid, server_name, entry)
    )

    # Container resource sensors (disabled by default)
    entities.extend(
        _create_container_sensors(system_coordinator, server_uuid, server_name)
    )

    # Storage sensors
    entities.extend(
        [
            ArrayStateSensor(storage_coordinator, server_uuid, server_name),
            ArrayUsageSensor(storage_coordinator, server_uuid, server_name),
            ParityProgressSensor(storage_coordinator, server_uuid, server_name),
            ParitySpeedSensor(storage_coordinator, server_uuid, server_name),
            LastParityCheckDateSensor(storage_coordinator, server_uuid, server_name),
            LastParityCheckErrorsSensor(storage_coordinator, server_uuid, server_name),
        ]
    )

    # Disk, share, and flash sensors
    entities.extend(_create_disk_sensors(storage_coordinator, server_uuid, server_name))

    # Infrastructure sensors (registration/license, plugins)
    infra_coordinator = runtime_data.infra_coordinator
    entities.extend(
        [
            RegistrationTypeSensor(infra_coordinator, server_uuid, server_name),
            RegistrationStateSensor(infra_coordinator, server_uuid, server_name),
            InstalledPluginsSensor(infra_coordinator, server_uuid, server_name),
        ]
    )

    _LOGGER.debug("Adding %d sensor entities", len(entities))
    async_add_entities(entities)
