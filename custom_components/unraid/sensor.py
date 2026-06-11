"""Sensor entities for Unraid integration."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfDataRate,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from unraid_api import format_bytes

from .const import (
    CONF_UPS_CAPACITY_VA,
    CONF_UPS_NOMINAL_POWER,
    DEFAULT_UPS_CAPACITY_VA,
    DEFAULT_UPS_NOMINAL_POWER,
)
from .coordinator import (
    UnraidInfraCoordinator,
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)
from .entity import (
    UnraidBaseEntity,
    UnraidCoordinator,
    async_add_dynamic_resource_entities,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from unraid_api.models import (
        ArrayDisk,
        DockerContainerStats,
        NetworkMetrics,
        ParityHistoryEntry,
        Share,
        UPSDevice,
    )
    from unraid_api.models import (
        TemperatureSensor as TemperatureSensorModel,
    )

    from . import UnraidConfigEntry
    from .coordinator import (
        UnraidInfraData,
        UnraidStorageData,
        UnraidSystemData,
    )
    from .websocket import UnraidWebSocketManager

_LOGGER = logging.getLogger(__name__)

# Coordinator handles all data updates, no parallel entity updates needed
PARALLEL_UPDATES = 0

# Byte conversion constant
BYTES_PER_UNIT = 1024


class UnraidSensorEntity[CoordinatorT: DataUpdateCoordinator[Any] = UnraidCoordinator](
    UnraidBaseEntity[CoordinatorT], SensorEntity
):
    """Base class for Unraid sensor entities."""

    def __init__(
        self,
        coordinator: CoordinatorT,
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


class CpuSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class RAMUsageSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class RAMUsedSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class SwapUsageSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class SwapUsedSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class RAMBuffCacheSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
    """RAM buffer/cache sensor showing reclaimable memory in bytes."""

    _attr_translation_key = "ram_buffcache"
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
        """Initialize RAM buffer/cache sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="ram_buffcache",
            name="RAM Buffer/Cache",
        )

    @property
    def native_value(self) -> int | None:
        """Return buffer/cache memory in bytes."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.memory_buffcache


class RAMActiveSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
    """RAM active memory sensor showing actively used memory in bytes."""

    _attr_translation_key = "ram_active"
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
        """Initialize RAM active sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="ram_active",
            name="RAM Active",
        )

    @property
    def native_value(self) -> int | None:
        """Return active memory in bytes."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.memory_active


class SwapFreeSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
    """Swap free sensor showing available swap space in bytes."""

    _attr_translation_key = "swap_free"
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
        """Initialize swap free sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="swap_free",
            name="Swap Free",
        )

    @property
    def native_value(self) -> int | None:
        """Return free swap memory in bytes."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return data.metrics.swap_free


class TemperatureSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class SystemTemperatureSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
    """Dynamic temperature sensor for system hardware (motherboard, chipset, etc.)."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        sensor: TemperatureSensorModel,
    ) -> None:
        """Initialize system temperature sensor."""
        self._sensor_id = sensor.id
        sensor_name = sensor.name or sensor.id
        # Map sensor types to translation keys
        type_key = str(sensor.type).lower() if sensor.type else "custom"
        self._attr_translation_key = f"temperature_{type_key}"
        self._attr_translation_placeholders = {"name": sensor_name}
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"temp_{sensor.id}",
            name=f"Temperature {sensor_name}",
        )

    def _get_sensor(self) -> TemperatureSensorModel | None:
        """Find this sensor in coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None or data.metrics.temperature is None:
            return None
        for sensor in data.metrics.temperature.sensors:
            if sensor.id == self._sensor_id:
                return sensor
        return None

    @property
    def native_value(self) -> float | None:
        """Return the current temperature value."""
        sensor = self._get_sensor()
        if sensor is None or not _is_valid_system_temp_sensor(sensor):
            return None
        return sensor.temperature

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sensor metadata as attributes."""
        sensor = self._get_sensor()
        if sensor is None:
            return {}
        attrs: dict[str, Any] = {}
        if sensor.type:
            attrs["sensor_type"] = str(sensor.type)
        if sensor.location:
            attrs["location"] = sensor.location
        if sensor.warning is not None:
            attrs["warning_threshold"] = sensor.warning
        if sensor.critical is not None:
            attrs["critical_threshold"] = sensor.critical
        if sensor.current and sensor.current.status:
            attrs["status"] = str(sensor.current.status)
        if sensor.min and sensor.min.value is not None:
            attrs["min_recorded"] = sensor.min.value
        if sensor.max and sensor.max.value is not None:
            attrs["max_recorded"] = sensor.max.value
        return attrs


class TemperatureAverageSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
    """Average temperature across all sensors."""

    _attr_translation_key = "temperature_average"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize temperature average sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="temperature_average",
            name="Temperature Average",
        )

    @property
    def native_value(self) -> float | None:
        """Return the average temperature across all sensors."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        valid_sensors = _get_valid_temperature_sensors(data)
        if not valid_sensors:
            return None
        total_temperature = sum(
            sensor.temperature
            for sensor in valid_sensors
            if sensor.temperature is not None
        )
        return round(
            total_temperature / len(valid_sensors),
            1,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return summary details as attributes."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None or data.metrics.temperature is None:
            return {}
        valid_sensors = _get_valid_temperature_sensors(data)
        summary = data.metrics.temperature.summary
        attrs: dict[str, Any] = {
            "sensor_count": len(valid_sensors),
            "raw_sensor_count": len(data.metrics.temperature.sensors),
        }
        if summary is None:
            return attrs
        if summary.warningCount is not None:
            attrs["warning_count"] = summary.warningCount
        if summary.criticalCount is not None:
            attrs["critical_count"] = summary.criticalCount
        if summary.hottest and summary.hottest.name:
            attrs["hottest_sensor"] = summary.hottest.name
        if summary.coolest and summary.coolest.name:
            attrs["coolest_sensor"] = summary.coolest.name
        return attrs


class CpuPowerSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class UnraidVersionSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class ApiVersionSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
    """Sensor showing the Unraid GraphQL API version."""

    _attr_translation_key = "api_version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize API version sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="api_version",
            name="API Version",
        )

    @property
    def native_value(self) -> str | None:
        """Return the GraphQL API version string."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None or data.info is None:
            return None
        return data.info.api_version


class UptimeSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class ActiveNotificationsSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class NotificationUnreadInfoSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class NotificationUnreadWarningSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class NotificationUnreadAlertSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class NotificationArchivedTotalSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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
# Container Updates Count Sensor
# =============================================================================


class ContainerUpdatesCountSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
    """Sensor showing count of Docker containers with available updates."""

    _attr_translation_key = "container_updates_count"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "containers"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize container updates count sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="container_updates_count",
            name="Container Updates Available",
        )

    @property
    def native_value(self) -> int | None:
        """Return count of containers with updates available."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        return sum(1 for c in data.containers if c.isUpdateAvailable is True)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return list of containers with updates available."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return {}
        updatable = [
            c.name.lstrip("/") for c in data.containers if c.isUpdateAvailable is True
        ]
        return {"containers": updatable} if updatable else {}


# =============================================================================
# Registration / License Sensors
# =============================================================================


class RegistrationTypeSensor(UnraidSensorEntity[UnraidInfraCoordinator]):
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


class RegistrationStateSensor(UnraidSensorEntity[UnraidInfraCoordinator]):
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


class RegistrationExpirationSensor(UnraidSensorEntity[UnraidInfraCoordinator]):
    """Registration license expiration and update expiration sensor."""

    _attr_translation_key = "registration_expiration"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize registration expiration sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="registration_expiration",
            name="License Expiration",
        )

    @property
    def native_value(self) -> str | None:
        """Return license expiration date string."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.registration is None:
            return None
        return data.registration.expiration

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return update expiration as an attribute."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.registration is None:
            return {}
        attrs: dict[str, Any] = {}
        if data.registration.updateExpiration is not None:
            attrs["update_expiration"] = data.registration.updateExpiration
        return attrs


# =============================================================================
# Plugins Sensor
# =============================================================================


class InstalledPluginsSensor(UnraidSensorEntity[UnraidInfraCoordinator]):
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
        if data is None:
            return None
        return len(data.installed_plugins)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return plugin details as extra attributes."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or not data.installed_plugins:
            return {}
        return {"plugins": data.installed_plugins}


class NetworkAccessSensor(UnraidSensorEntity[UnraidInfraCoordinator]):
    """Sensor showing primary LAN access URL with all access URLs as attributes."""

    _attr_translation_key = "network_access"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize network access sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="network_access",
            name="Network Access",
        )

    @property
    def native_value(self) -> str | None:
        """Return primary LAN IPv4 URL."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.network is None:
            return None
        urls = data.network.accessUrls
        if not urls:
            return None
        # Return the first LAN IPv4 URL as the primary value
        for url in urls:
            if url.type and url.type.upper() == "LAN" and url.ipv4:
                return url.ipv4
        # Fallback: first URL with an IPv4 value
        for url in urls:
            if url.ipv4:
                return url.ipv4
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all access URLs as extra attributes."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.network is None:
            return {}
        urls = data.network.accessUrls
        if not urls:
            return {}
        attrs: dict[str, Any] = {}
        for url in urls:
            name = url.name or url.type or "unknown"
            if url.ipv4:
                attrs[f"{name}_ipv4"] = url.ipv4
            if url.ipv6:
                attrs[f"{name}_ipv6"] = url.ipv6
        return attrs


class ArrayStateSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
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


class ArrayUsageSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
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


class ParityProgressSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
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


class LastParityCheckDateSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
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


class LastParityCheckErrorsSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
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


class DiskTemperatureSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
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
        self._disk_name = disk.name or disk.id
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
        attrs: dict[str, Any] = {
            "spinning": disk.isSpinning,
            "status": disk.status,
            "device": disk.device,
            "type": disk.type,
        }
        # Temperature thresholds (v1.7.0+)
        if disk.warning is not None:
            attrs["warning_temp"] = disk.warning
        if disk.critical is not None:
            attrs["critical_temp"] = disk.critical
        return attrs


class DiskErrorCountSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
    """Disk error count sensor (numErrors from SMART/array)."""

    _attr_translation_key = "disk_error_count"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "errors"
    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        disk: ArrayDisk,
    ) -> None:
        """Initialize disk error count sensor."""
        self._disk_id = disk.id
        self._disk_name = disk.name or disk.id
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"disk_{self._disk_id}_errors",
            name=f"Disk {self._disk_name} Errors",
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
        """Return disk error count."""
        disk = self._get_disk()
        if disk is None:
            return None
        return disk.numErrors


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


class DiskUsageSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
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
        self._disk_name = disk.name or disk.id
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
        # Extended disk fields (v1.7.0+)
        extended = {
            "rotational": disk.rotational,
            "transport": disk.transport,
            "format": disk.format,
            "num_reads": disk.numReads,
            "num_writes": disk.numWrites,
            "num_errors": disk.numErrors,
            "color": disk.color,
            "warning_temp": disk.warning,
            "critical_temp": disk.critical,
        }
        attrs.update({k: v for k, v in extended.items() if v is not None})
        return attrs


# UPS Sensors


class UPSBatterySensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class UPSLoadSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class UPSRuntimeSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class UPSPowerSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
    """
    UPS power consumption sensor for Energy Dashboard.

    Prefers the direct currentPower value from the API (unraid-api v1.7.0+).
    Falls back to calculating from load percentage and nominal power.
    Formula: Power (W) = Load% / 100 * Nominal Power (W)

    The UPS nominal power can be configured in the integration options
    as a fallback when the API does not report currentPower.
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
            ups_nominal_power: UPS nominal power in watts (fallback calculation)

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

        Available if the API reports currentPower or nominal power is configured.
        """
        ups = self._get_ups()
        if ups is not None and ups.power.currentPower is not None:
            return super().available
        if self._ups_nominal_power <= 0:
            return False
        return super().available

    @property
    def native_value(self) -> float | None:
        """
        Return UPS power consumption in watts.

        Prefers API-reported currentPower (v1.7.0+), falls back to
        calculation from load percentage x nominal power.
        """
        ups = self._get_ups()
        if ups is None:
            return None
        # Prefer direct API value (unraid-api v1.7.0+)
        if ups.power.currentPower is not None:
            return round(ups.power.currentPower, 1)
        # Fallback to calculated value from load% x nominal power
        if self._ups_nominal_power <= 0:
            return None
        return ups.calculate_power_watts(self._ups_nominal_power)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return UPS power details as attributes."""
        ups = self._get_ups()
        attrs: dict[str, Any] = {
            "model": self._ups_name,
        }
        # Include nominal power from API if available, else user config
        if ups is not None and ups.power.nominalPower is not None:
            attrs["nominal_power_watts"] = ups.power.nominalPower
        elif self._ups_nominal_power > 0:
            attrs["nominal_power_watts"] = self._ups_nominal_power
        # Include VA rating if configured (informational)
        if self._ups_capacity_va > 0:
            attrs["ups_capacity_va"] = self._ups_capacity_va
        if ups is not None:
            attrs["status"] = ups.status
            if ups.power.currentPower is not None:
                attrs["power_source"] = "api"
            elif self._ups_nominal_power > 0:
                attrs["power_source"] = "calculated"
            if ups.power.loadPercentage is not None:
                attrs["load_percentage"] = ups.power.loadPercentage
            if ups.power.inputVoltage is not None:
                attrs["input_voltage"] = ups.power.inputVoltage
            if ups.power.outputVoltage is not None:
                attrs["output_voltage"] = ups.power.outputVoltage
        return attrs


class UPSEnergySensor(UnraidSensorEntity[UnraidSystemCoordinator], RestoreEntity):
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

    def _get_effective_nominal_power(self) -> int | float:
        """Return nominal power: prefer API value, fall back to user config."""
        ups = self._get_ups()
        if ups is not None and ups.power.nominalPower is not None:
            return ups.power.nominalPower
        return self._ups_nominal_power

    def _calculate_current_power(self) -> float | None:
        """Calculate current power consumption in watts."""
        ups = self._get_ups()
        if ups is None:
            return None
        # Prefer direct API power reading (v1.7.0+)
        if ups.power.currentPower is not None:
            return round(ups.power.currentPower, 1)
        # Fall back to load% x nominal power
        nominal = self._get_effective_nominal_power()
        if nominal <= 0:
            return None
        return ups.calculate_power_watts(int(nominal))

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
        nominal = self._get_effective_nominal_power()
        if nominal <= 0:
            return False
        return super().available

    @property
    def native_value(self) -> float | None:
        """Return cumulative energy consumption in kWh."""
        nominal = self._get_effective_nominal_power()
        if nominal <= 0:
            return None
        return round(self._total_energy_kwh, 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return energy tracking details as attributes."""
        nominal = self._get_effective_nominal_power()
        attrs: dict[str, Any] = {
            "model": self._ups_name,
            "nominal_power_watts": nominal,
        }
        if self._last_power_watts is not None:
            attrs["current_power_watts"] = round(self._last_power_watts, 1)
        if self._last_update_time is not None:
            attrs["last_updated"] = self._last_update_time.isoformat()
        return attrs


# Share Sensors


class ShareUsageSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
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
        attrs: dict[str, Any] = {
            "total": format_bytes(share.size_bytes),
            "used": format_bytes(share.used_bytes),
            "free": format_bytes(share.free_bytes),
        }
        # Extended share fields (v1.7.0+)
        extended = {
            "cache": share.cache,
            "allocator": share.allocator,
            "split_level": share.splitLevel,
            "floor": share.floor,
            "cow": share.cow,
            "color": share.color,
            "luks_status": share.luksStatus,
        }
        attrs.update({k: v for k, v in extended.items() if v is not None})
        return attrs


# =============================================================================
# Container Resource Sensors — WebSocket-powered (v1.7.0+)
# =============================================================================
# Container stats (CPU, memory) are available via WebSocket subscriptions
# (subscribe_container_stats()). The WebSocket manager feeds real-time stats
# to these sensor entities.


class _ContainerStatsMixin:
    """
    Shared lookup logic for per-container WebSocket stat sensors.

    Resolves the current Docker container ID dynamically from coordinator
    data on each call. This handles the case where a container is recreated
    and receives a new Docker ID — the frozen ID stored at entity creation
    time would otherwise yield stale (None) stats.
    """

    _container_name: str
    _container_id: str

    if TYPE_CHECKING:
        from .coordinator import UnraidSystemData
        from .websocket import UnraidWebSocketManager

        coordinator: UnraidSystemCoordinator
        _ws_manager: UnraidWebSocketManager

    def _get_current_stats(self) -> DockerContainerStats | None:
        """Resolve stats via a fresh container ID lookup from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data  # type: ignore[attr-defined]
        if data is not None:
            for container in data.containers:
                if container.name.lstrip("/") == self._container_name:
                    stats = self._ws_manager.container_stats.stats.get(container.id)  # type: ignore[attr-defined]
                    if stats is not None:
                        return stats
        return self._ws_manager.container_stats.stats.get(self._container_id)  # type: ignore[attr-defined]

    def _is_container_stopped(self) -> bool:
        """
        Return True when coordinator data shows the container is not running.

        Stopped containers never appear in the `docker stats` stream, so
        without this check their sensors would show "unknown" (never started)
        or the last value streamed before they stopped (stale).
        """
        data: UnraidSystemData | None = self.coordinator.data  # type: ignore[attr-defined]
        if data is None:
            return False
        for container in data.containers:
            if container.name.lstrip("/") == self._container_name:
                return not container.is_running
        return False


class ContainerCpuSensor(
    _ContainerStatsMixin, UnraidBaseEntity[UnraidSystemCoordinator], SensorEntity
):
    """Container CPU usage sensor (WebSocket-powered)."""

    _attr_translation_key = "container_cpu"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        container_name: str,
        container_id: str,
        ws_manager: UnraidWebSocketManager,
    ) -> None:
        """Initialize container CPU sensor."""
        self._container_name = container_name
        self._container_id = container_id
        self._ws_manager = ws_manager
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_{container_name}_cpu",
            name=f"Container {container_name} CPU",
        )
        self._attr_translation_placeholders = {
            "name": container_name,
        }

    @property
    def native_value(self) -> float | None:
        """Return container CPU usage from WebSocket stats (0 when stopped)."""
        if self._is_container_stopped():
            return 0.0
        stats = self._get_current_stats()
        if stats is None:
            return None
        return stats.cpuPercent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return container stats attributes."""
        if self._is_container_stopped():
            return {}
        stats = self._get_current_stats()
        if stats is None:
            return {}
        attrs: dict[str, Any] = {}
        if stats.blockIO is not None:
            attrs["block_io"] = stats.blockIO
        if stats.netIO is not None:
            attrs["net_io"] = stats.netIO
        return attrs


class ContainerMemoryUsageSensor(
    _ContainerStatsMixin, UnraidBaseEntity[UnraidSystemCoordinator], SensorEntity
):
    """Container memory usage sensor (WebSocket-powered)."""

    _attr_translation_key = "container_memory_usage"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        container_name: str,
        container_id: str,
        ws_manager: UnraidWebSocketManager,
    ) -> None:
        """Initialize container memory usage sensor."""
        self._container_name = container_name
        self._container_id = container_id
        self._ws_manager = ws_manager
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_{container_name}_memory",
            name=f"Container {container_name} Memory",
        )
        self._attr_translation_placeholders = {
            "name": container_name,
        }

    @property
    def native_value(self) -> str | None:
        """Return container memory usage string ("0B / 0B" when stopped)."""
        if self._is_container_stopped():
            return "0B / 0B"
        stats = self._get_current_stats()
        if stats is None:
            return None
        return stats.memUsage


class ContainerMemoryPercentSensor(
    _ContainerStatsMixin, UnraidBaseEntity[UnraidSystemCoordinator], SensorEntity
):
    """Container memory percentage sensor (WebSocket-powered)."""

    _attr_translation_key = "container_memory_percent"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        container_name: str,
        container_id: str,
        ws_manager: UnraidWebSocketManager,
    ) -> None:
        """Initialize container memory percent sensor."""
        self._container_name = container_name
        self._container_id = container_id
        self._ws_manager = ws_manager
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_{container_name}_memory_pct",
            name=f"Container {container_name} Memory %",
        )
        self._attr_translation_placeholders = {
            "name": container_name,
        }

    @property
    def native_value(self) -> float | None:
        """Return container memory percentage (0 when stopped)."""
        if self._is_container_stopped():
            return 0.0
        stats = self._get_current_stats()
        if stats is None:
            return None
        return stats.memPercent


# =============================================================================
# Docker Aggregate Sensors
# =============================================================================


class DockerTotalCpuSensor(UnraidBaseEntity[UnraidSystemCoordinator], SensorEntity):
    """Total Docker CPU usage sensor (sum of all containers, WebSocket-powered)."""

    _attr_translation_key = "docker_total_cpu"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ws_manager: UnraidWebSocketManager,
    ) -> None:
        """Initialize Docker total CPU sensor."""
        self._ws_manager = ws_manager
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="docker_total_cpu",
            name="Docker Total CPU",
        )

    @property
    def native_value(self) -> float | None:
        """Return sum of CPU usage across currently active containers."""
        all_stats = self._ws_manager.container_stats.stats
        if not all_stats:
            return None
        data: UnraidSystemData | None = self.coordinator.data
        if data is not None:
            # Running containers only: stats of stopped containers linger in
            # the snapshot (the stream stops sending them) and would otherwise
            # keep counting toward the total forever.
            valid_ids = {c.id for c in data.containers if c.is_running}
            values = [
                s.cpuPercent
                for cid, s in all_stats.items()
                if cid in valid_ids and s.cpuPercent is not None
            ]
        else:
            values = [
                s.cpuPercent for s in all_stats.values() if s.cpuPercent is not None
            ]
        if not values:
            return None
        return round(sum(values), 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return running container count as attribute."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is not None:
            return {"container_count": sum(1 for c in data.containers if c.is_running)}
        return {"container_count": len(self._ws_manager.container_stats.stats)}


class DockerTotalMemoryPercentSensor(
    UnraidBaseEntity[UnraidSystemCoordinator], SensorEntity
):
    """Total Docker memory usage sensor (sum of all containers, WebSocket-powered)."""

    _attr_translation_key = "docker_total_memory_percent"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ws_manager: UnraidWebSocketManager,
    ) -> None:
        """Initialize Docker total memory percent sensor."""
        self._ws_manager = ws_manager
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="docker_total_memory_pct",
            name="Docker Total Memory %",
        )

    @property
    def native_value(self) -> float | None:
        """Return sum of memory percentage across currently active containers."""
        all_stats = self._ws_manager.container_stats.stats
        if not all_stats:
            return None
        data: UnraidSystemData | None = self.coordinator.data
        if data is not None:
            valid_ids = {c.id for c in data.containers if c.is_running}
            values = [
                s.memPercent
                for cid, s in all_stats.items()
                if cid in valid_ids and s.memPercent is not None
            ]
        else:
            values = [
                s.memPercent for s in all_stats.values() if s.memPercent is not None
            ]
        if not values:
            return None
        return round(sum(values), 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return running container count as attribute."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is not None:
            return {"container_count": sum(1 for c in data.containers if c.is_running)}
        return {"container_count": len(self._ws_manager.container_stats.stats)}


class DockerTotalMemoryBytesSensor(
    UnraidBaseEntity[UnraidSystemCoordinator], SensorEntity
):
    """Total Docker memory used in bytes (derived from memory % x system RAM)."""

    _attr_translation_key = "docker_total_memory_bytes"
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = "B"
    _attr_suggested_unit_of_measurement = "GiB"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ws_manager: UnraidWebSocketManager,
    ) -> None:
        """Initialize Docker total memory bytes sensor."""
        self._ws_manager = ws_manager
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="docker_total_memory_bytes",
            name="Docker Total Memory Used",
        )

    @property
    def native_value(self) -> int | None:
        """
        Return total Docker memory used in bytes.

        Computed as sum(container memPercent) x system_memory_total / 100.
        """
        all_stats = self._ws_manager.container_stats.stats
        if not all_stats:
            return None
        data: UnraidSystemData | None = self.coordinator.data
        if data is None or data.metrics.memory_total is None:
            return None
        valid_ids = {c.id for c in data.containers if c.is_running}
        total_pct = sum(
            s.memPercent
            for cid, s in all_stats.items()
            if cid in valid_ids and s.memPercent is not None
        )
        return int(total_pct * data.metrics.memory_total / 100)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return running container count as attribute."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is not None:
            return {"container_count": sum(1 for c in data.containers if c.is_running)}
        return {"container_count": len(self._ws_manager.container_stats.stats)}


# =============================================================================
# Network Interface Sensors (metrics.network, Unraid API 4.35+)
# =============================================================================

# Only physical NICs, bonds, and user-configured bridges get entities —
# Unraid names these ethN, bondN, brN/wlanN (plus VLAN sub-interfaces like
# br0.5). Everything else is auto-generated plumbing that churns constantly
# and carries no dashboard value: per-container veth pairs, VM vnet/tap
# devices, loopback, and Docker/libvirt-created bridges and shims
# (br-<hash>, docker0, shim-br0, virbr0).
_MONITORABLE_INTERFACE_RE = re.compile(r"^(?:eth|bond|br|wlan)\d+(?:\.\d+)?$")


def _is_monitorable_interface(name: str | None) -> bool:
    """Return True if the interface should get sensor entities."""
    if not name:
        return False
    return _MONITORABLE_INTERFACE_RE.match(name) is not None


class NetworkInterfaceSensorBase(UnraidSensorEntity[UnraidSystemCoordinator]):
    """
    Base class for per-interface network throughput sensors.

    Values come from metrics.network (rxSec/txSec, server-computed bytes per
    second). HA's data-rate device class renders them in human-readable
    units (MB/s) via the suggested unit and precision.
    """

    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_native_unit_of_measurement = UnitOfDataRate.BYTES_PER_SECOND
    _attr_suggested_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        interface_name: str,
        direction: str,
        name: str,
    ) -> None:
        """Initialize network interface sensor."""
        self._interface_name = interface_name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"network_{interface_name}_{direction}",
            name=name,
        )
        self._attr_translation_placeholders = {"name": interface_name}

    def _get_interface(self) -> NetworkMetrics | None:
        """Look up this interface in the current coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for interface in data.network_metrics:
            if interface.name == self._interface_name:
                return interface
        return None


class NetworkInterfaceRxSensor(NetworkInterfaceSensorBase):
    """Inbound throughput sensor for a network interface."""

    _attr_translation_key = "network_interface_rx"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        interface_name: str,
    ) -> None:
        """Initialize inbound network sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            interface_name=interface_name,
            direction="rx",
            name=f"Network {interface_name} Inbound",
        )

    @property
    def native_value(self) -> float | None:
        """Return inbound throughput in bytes per second."""
        interface = self._get_interface()
        if interface is None:
            return None
        return interface.rxSec

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return interface state and human-readable receive totals."""
        interface = self._get_interface()
        if interface is None:
            return {}
        attrs: dict[str, Any] = {}
        if interface.operstate is not None:
            attrs["interface_state"] = interface.operstate
        if interface.bytesReceived is not None:
            attrs["total_received"] = format_bytes(interface.bytesReceived)
        if interface.packetsReceived is not None:
            attrs["packets_received"] = interface.packetsReceived
        if interface.receiveErrors is not None:
            attrs["receive_errors"] = interface.receiveErrors
        if interface.receiveDropped is not None:
            attrs["receive_dropped"] = interface.receiveDropped
        return attrs


class NetworkInterfaceTxSensor(NetworkInterfaceSensorBase):
    """Outbound throughput sensor for a network interface."""

    _attr_translation_key = "network_interface_tx"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        interface_name: str,
    ) -> None:
        """Initialize outbound network sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            interface_name=interface_name,
            direction="tx",
            name=f"Network {interface_name} Outbound",
        )

    @property
    def native_value(self) -> float | None:
        """Return outbound throughput in bytes per second."""
        interface = self._get_interface()
        if interface is None:
            return None
        return interface.txSec

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return interface state and human-readable transmit totals."""
        interface = self._get_interface()
        if interface is None:
            return {}
        attrs: dict[str, Any] = {}
        if interface.operstate is not None:
            attrs["interface_state"] = interface.operstate
        if interface.bytesSent is not None:
            attrs["total_sent"] = format_bytes(interface.bytesSent)
        if interface.packetsSent is not None:
            attrs["packets_sent"] = interface.packetsSent
        if interface.transmitErrors is not None:
            attrs["transmit_errors"] = interface.transmitErrors
        if interface.transmitDropped is not None:
            attrs["transmit_dropped"] = interface.transmitDropped
        return attrs


# =============================================================================
# Parity Speed Sensor
# =============================================================================


class ParitySpeedSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
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
        # speed is str | None since unraid-api v1.9.0
        try:
            speed_val = float(speed)
        except (TypeError, ValueError):
            return None
        # Convert from bytes/s to MiB/s
        return round(speed_val / (1024 * 1024), 1)

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


class ParityElapsedSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
    """Parity check elapsed time sensor (seconds)."""

    _attr_translation_key = "parity_elapsed"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize parity elapsed sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_elapsed",
            name="Parity Check Elapsed",
        )

    @property
    def native_value(self) -> int | None:
        """Return parity check elapsed time in seconds."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return None
        # Return 0 when no check is running (elapsed is None)
        return data.parity_status.elapsed or 0


class ParityEstimatedSensor(UnraidSensorEntity[UnraidStorageCoordinator]):
    """Parity check estimated remaining time sensor (seconds)."""

    _attr_translation_key = "parity_estimated"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize parity estimated sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_estimated",
            name="Parity Check Estimated",
        )

    @property
    def native_value(self) -> int | None:
        """Return parity check estimated remaining time in seconds."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return None
        # Return 0 when no check is running (estimated is None)
        return data.parity_status.estimated or 0


# =============================================================================
# UPS Voltage & Health Sensors
# =============================================================================


class UPSInputVoltageSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class UPSOutputVoltageSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class UPSBatteryHealthSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
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


class UPSStatusSensor(UnraidSensorEntity[UnraidSystemCoordinator]):
    """UPS status sensor (OL, OB, OB LB, OL CHRG, etc.)."""

    _attr_translation_key = "ups_status"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
    ) -> None:
        """Initialize UPS status sensor."""
        self._ups_id = ups.id
        self._ups_name = ups.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{self._ups_id}_status",
            name="UPS Status",
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
        """Return UPS status string."""
        ups = self._get_ups()
        if ups is None:
            return None
        return ups.status


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
                UPSStatusSensor(system_coordinator, server_uuid, server_name, ups),
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
        # Add UPS Energy sensor (kWh) - created if nominal power is
        # configured by user OR available from the API (v1.7.0+).
        api_nominal = (
            ups.power.nominalPower if ups.power.nominalPower is not None else 0
        )
        effective_nominal = ups_nominal_power if ups_nominal_power > 0 else api_nominal
        if effective_nominal > 0:
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
                "Created UPS Energy sensor for UPS %s "
                "(user nominal: %dW, api nominal: %sW)",
                ups.name,
                ups_nominal_power,
                api_nominal or "N/A",
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

    # Data disks - usage, temperature, and error count sensors
    for disk in data.disks or []:
        entities.append(
            DiskUsageSensor(storage_coordinator, server_uuid, server_name, disk)
        )
        entities.append(
            DiskTemperatureSensor(storage_coordinator, server_uuid, server_name, disk)
        )
        entities.append(
            DiskErrorCountSensor(storage_coordinator, server_uuid, server_name, disk)
        )

    # Parity disks - temperature and error count sensors
    for disk in data.parities or []:
        entities.append(
            DiskTemperatureSensor(storage_coordinator, server_uuid, server_name, disk)
        )
        entities.append(
            DiskErrorCountSensor(storage_coordinator, server_uuid, server_name, disk)
        )

    # Cache disks - usage, temperature, and error count sensors
    for disk in data.caches or []:
        entities.append(
            DiskUsageSensor(storage_coordinator, server_uuid, server_name, disk)
        )
        entities.append(
            DiskTemperatureSensor(storage_coordinator, server_uuid, server_name, disk)
        )
        entities.append(
            DiskErrorCountSensor(storage_coordinator, server_uuid, server_name, disk)
        )

    # Share sensors
    for share in data.shares or []:
        entities.append(
            ShareUsageSensor(storage_coordinator, server_uuid, server_name, share)
        )

    return entities


# Sensor types that are either already represented elsewhere (DISK/NVME have their
# own per-disk temperature entities) or are too noisy to display individually.
_TEMP_SKIP_TYPES: frozenset[str] = frozenset({"DISK", "NVME", "CPU_CORE"})
# Temperatures above this value are usually bogus board sensors (AUXTIN/SYSTIN).
_TEMP_MAX_VALID: float = 100.0  # °C
# Ignore near-zero readings from voltage rails incorrectly exposed as temperatures.
_TEMP_MIN_VALID: float = 10.0  # °C
_TEMP_SKIP_NAME_PARTS: tuple[str, ...] = ("auxtin", " in")


def _looks_like_voltage_channel_sensor(name: str) -> bool:
    """Return True for Nuvoton-style voltage channels (e.g. in0, in12)."""
    lowered = name.lower()
    return any(f" in{index}" in lowered for index in range(16))


def _is_valid_system_temp_sensor(sensor: TemperatureSensorModel) -> bool:
    """
    Return True if this hardware sensor should be exposed as a HA entity.

    Filters out sensors that are:
    - Already shown via per-disk entities (DISK / NVME)
    - Too noisy to be useful individually (CPU_CORE — use CPU package instead)
    - Reporting obviously invalid values (0 °C disconnected thermistors, >120 °C
      bogus readings from unconnected pads, -999 °C placeholder values)
    """
    if str(sensor.type) in _TEMP_SKIP_TYPES:
        return False
    sensor_name = (sensor.name or "").strip()
    lowered_name = sensor_name.lower()
    if any(part in lowered_name for part in _TEMP_SKIP_NAME_PARTS):
        return False
    if _looks_like_voltage_channel_sensor(sensor_name):
        return False
    if sensor.current is not None and sensor.current.unit != "CELSIUS":
        return False
    temp = sensor.temperature
    # Disconnected thermistors and mis-reported rails read near 0 °C.
    if temp is None or temp < _TEMP_MIN_VALID:
        return False
    # Values above 100 °C are usually bogus board readings in practice.
    return not temp > _TEMP_MAX_VALID


def _get_valid_temperature_sensors(
    data: UnraidSystemData,
) -> list[TemperatureSensorModel]:
    """Return only valid system temperature sensors for entity creation/averages."""
    if data.metrics.temperature is None:
        return []
    return [
        sensor
        for sensor in data.metrics.temperature.sensors
        if _is_valid_system_temp_sensor(sensor)
    ]


async def async_setup_entry(
    hass: HomeAssistant,
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
            RAMBuffCacheSensor(system_coordinator, server_uuid, server_name),
            RAMActiveSensor(system_coordinator, server_uuid, server_name),
            SwapFreeSensor(system_coordinator, server_uuid, server_name),
            TemperatureSensor(system_coordinator, server_uuid, server_name),
            UnraidVersionSensor(system_coordinator, server_uuid, server_name),
            ApiVersionSensor(system_coordinator, server_uuid, server_name),
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
            ContainerUpdatesCountSensor(system_coordinator, server_uuid, server_name),
        ]
    )

    # UPS sensors
    entities.extend(
        _create_ups_sensors(system_coordinator, server_uuid, server_name, entry)
    )

    # System temperature sensors (dynamic, per hardware sensor)
    if (
        system_coordinator.data
        and system_coordinator.data.metrics.temperature is not None
    ):
        valid_temp_sensors = _get_valid_temperature_sensors(system_coordinator.data)
        if valid_temp_sensors:
            entities.append(
                TemperatureAverageSensor(system_coordinator, server_uuid, server_name)
            )
            for sensor in valid_temp_sensors:
                entities.append(
                    SystemTemperatureSensor(
                        system_coordinator, server_uuid, server_name, sensor
                    )
                )

    # Storage sensors
    entities.extend(
        [
            ArrayStateSensor(storage_coordinator, server_uuid, server_name),
            ArrayUsageSensor(storage_coordinator, server_uuid, server_name),
            ParityProgressSensor(storage_coordinator, server_uuid, server_name),
            ParitySpeedSensor(storage_coordinator, server_uuid, server_name),
            ParityElapsedSensor(storage_coordinator, server_uuid, server_name),
            ParityEstimatedSensor(storage_coordinator, server_uuid, server_name),
            LastParityCheckDateSensor(storage_coordinator, server_uuid, server_name),
            LastParityCheckErrorsSensor(storage_coordinator, server_uuid, server_name),
        ]
    )

    # Disk, share, and flash sensors
    entities.extend(_create_disk_sensors(storage_coordinator, server_uuid, server_name))

    # Infrastructure sensors (registration/license, plugins, network)
    infra_coordinator = runtime_data.infra_coordinator
    entities.extend(
        [
            RegistrationTypeSensor(infra_coordinator, server_uuid, server_name),
            RegistrationStateSensor(infra_coordinator, server_uuid, server_name),
            RegistrationExpirationSensor(infra_coordinator, server_uuid, server_name),
            InstalledPluginsSensor(infra_coordinator, server_uuid, server_name),
            NetworkAccessSensor(infra_coordinator, server_uuid, server_name),
        ]
    )

    # Docker aggregate sensors (total CPU/memory across all containers)
    ws_manager = runtime_data.websocket_manager
    entities.extend(
        [
            DockerTotalCpuSensor(
                system_coordinator, server_uuid, server_name, ws_manager
            ),
            DockerTotalMemoryPercentSensor(
                system_coordinator, server_uuid, server_name, ws_manager
            ),
            DockerTotalMemoryBytesSensor(
                system_coordinator, server_uuid, server_name, ws_manager
            ),
        ]
    )

    _LOGGER.debug("Adding %d sensor entities", len(entities))
    async_add_entities(entities)

    # Container stats sensors (WebSocket-powered). Containers created after
    # setup get sensors on the next coordinator refresh — no reload needed.
    entry.async_on_unload(
        async_add_dynamic_resource_entities(
            coordinator=system_coordinator,
            async_add_entities=async_add_entities,
            get_resources=lambda: (
                system_coordinator.data.containers if system_coordinator.data else []
            ),
            get_key=lambda container: container.name.lstrip("/"),
            create_entities=lambda container: [
                ContainerCpuSensor(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    container.name.lstrip("/"),
                    container.id or container.name.lstrip("/"),
                    ws_manager,
                ),
                ContainerMemoryUsageSensor(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    container.name.lstrip("/"),
                    container.id or container.name.lstrip("/"),
                    ws_manager,
                ),
                ContainerMemoryPercentSensor(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    container.name.lstrip("/"),
                    container.id or container.name.lstrip("/"),
                    ws_manager,
                ),
            ],
        )
    )

    # Remove registry entries for network interfaces that no longer pass the
    # monitorable filter (e.g. Docker bridges and shims that earlier versions
    # created sensors for — they'd otherwise linger as unavailable entities).
    entity_registry = er.async_get(hass)
    network_uid_prefix = f"{server_uuid}_network_"
    for registry_entry in er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    ):
        # Throughput unique_id format: {server_uuid}_network_{interface}_{rx|tx}.
        # The suffix check keeps other network-prefixed sensors (such as
        # {server_uuid}_network_access) out of the cleanup.
        if not registry_entry.unique_id.startswith(
            network_uid_prefix
        ) or not registry_entry.unique_id.endswith(("_rx", "_tx")):
            continue
        interface_name = registry_entry.unique_id.removeprefix(
            network_uid_prefix
        ).rsplit("_", 1)[0]
        if not _is_monitorable_interface(interface_name):
            _LOGGER.debug(
                "Removing sensor for non-monitorable interface %s (%s)",
                interface_name,
                registry_entry.entity_id,
            )
            entity_registry.async_remove(registry_entry.entity_id)

    # Network interface throughput sensors (Unraid API 4.35+; the list is
    # empty on older servers, so no entities are created there). Interfaces
    # appearing later (e.g. a new bridge) also get sensors dynamically.
    entry.async_on_unload(
        async_add_dynamic_resource_entities(
            coordinator=system_coordinator,
            async_add_entities=async_add_entities,
            get_resources=lambda: [
                interface
                for interface in (
                    system_coordinator.data.network_metrics
                    if system_coordinator.data
                    else []
                )
                if interface.name is not None
                and _is_monitorable_interface(interface.name)
            ],
            get_key=lambda interface: interface.name or "",
            create_entities=lambda interface: [
                NetworkInterfaceRxSensor(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    interface.name or "",
                ),
                NetworkInterfaceTxSensor(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    interface.name or "",
                ),
            ],
        )
    )
