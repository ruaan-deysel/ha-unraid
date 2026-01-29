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
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_UPS_CAPACITY_VA,
    CONF_UPS_NOMINAL_POWER,
    DEFAULT_UPS_CAPACITY_VA,
    DEFAULT_UPS_NOMINAL_POWER,
)
from .entity import UnraidBaseEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from unraid_api.models import ArrayDisk, Share, UPSDevice

    from . import UnraidConfigEntry
    from .coordinator import (
        UnraidStorageCoordinator,
        UnraidStorageData,
        UnraidSystemCoordinator,
        UnraidSystemData,
    )

_LOGGER = logging.getLogger(__name__)

# Coordinator handles all data updates, no parallel entity updates needed
PARALLEL_UPDATES = 0

# Export PARALLEL_UPDATES for Home Assistant
__all__ = ["PARALLEL_UPDATES", "async_setup_entry"]

# Byte conversion constant
BYTES_PER_UNIT = 1024


def format_bytes(bytes_value: int | None) -> str | None:
    """Format bytes to human-readable string (KB, MB, GB, TB, PB)."""
    if bytes_value is None:
        return None
    if bytes_value == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    value = float(bytes_value)

    while value >= BYTES_PER_UNIT and unit_index < len(units) - 1:
        value /= BYTES_PER_UNIT
        unit_index += 1

    # Format with appropriate decimal places
    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    return f"{value:.2f} {units[unit_index]}"


class UnraidSensorEntity(UnraidBaseEntity, SensorEntity):
    """Base class for Unraid sensor entities."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator | UnraidStorageCoordinator,
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


class TemperatureSensor(UnraidSensorEntity):
    """CPU temperature sensor."""

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
        temps = data.metrics.cpu_temperatures

        if not temps:
            return None

        return sum(temps) / len(temps)


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


class DiskTemperatureSensor(UnraidSensorEntity):
    """Disk temperature sensor."""

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

    def _get_disk(self) -> ArrayDisk | None:
        """Get current disk from coordinator data."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None:
            return None
        all_disks = data.disks + data.parities + data.caches
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

    def _get_disk(self) -> ArrayDisk | None:
        """Get current disk from coordinator data."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None:
            return None
        all_disks = data.disks + data.parities + data.caches
        for disk in all_disks:
            if disk.id == self._disk_id:
                return disk
        return None

    @property
    def native_value(self) -> float | None:
        """Return disk usage percentage."""
        disk = self._get_disk()
        if disk is None:
            return None
        return disk.usage_percent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return disk details as human-readable attributes."""
        disk = self._get_disk()
        if disk is None:
            return {}
        # Build attributes - only include what's available
        attrs: dict[str, Any] = {
            "total": format_bytes(disk.fs_size_bytes),
            "used": format_bytes(disk.fs_used_bytes),
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
        return {
            "model": self._ups_name,
            "status": ups.status,
        }


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
        runtime_seconds = ups.battery.estimatedRuntime
        if runtime_seconds is None:
            return None
        # Convert to human-readable format
        hours, remainder = divmod(runtime_seconds, 3600)
        minutes = remainder // 60
        if hours > 0:
            h_suffix = "s" if hours != 1 else ""
            m_suffix = "s" if minutes != 1 else ""
            return f"{hours} hour{h_suffix} {minutes} minute{m_suffix}"
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

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

        Formula: Power (W) = Load% / 100 * Nominal Power (W)
        """
        if self._ups_nominal_power <= 0:
            return None
        ups = self._get_ups()
        if ups is None:
            return None
        load_percent = ups.power.loadPercentage
        if load_percent is None:
            return None
        # Calculate power: Load% * Nominal Power
        power_watts = (load_percent / 100) * self._ups_nominal_power
        return round(power_watts, 1)

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
        load_percent = ups.power.loadPercentage
        if load_percent is None:
            return None
        return (load_percent / 100) * self._ups_nominal_power

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
        # Update energy calculation on each read
        self._update_energy()
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


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
    async_add_entities: Any,
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
            TemperatureSensor(system_coordinator, server_uuid, server_name),
            UptimeSensor(system_coordinator, server_uuid, server_name),
            ActiveNotificationsSensor(system_coordinator, server_uuid, server_name),
        ]
    )

    # UPS sensors (only created when UPS devices are connected)
    if system_coordinator.data and system_coordinator.data.ups_devices:
        # Get UPS config from entry options (user configurable)
        ups_capacity_va = entry.options.get(
            CONF_UPS_CAPACITY_VA, DEFAULT_UPS_CAPACITY_VA
        )
        ups_nominal_power = entry.options.get(
            CONF_UPS_NOMINAL_POWER, DEFAULT_UPS_NOMINAL_POWER
        )
        _LOGGER.debug(
            "Found %d UPS device(s), creating sensors (VA: %d, Nominal Power: %dW)",
            len(system_coordinator.data.ups_devices),
            ups_capacity_va,
            ups_nominal_power,
        )
        for ups in system_coordinator.data.ups_devices:
            entities.extend(
                [
                    UPSBatterySensor(system_coordinator, server_uuid, server_name, ups),
                    UPSLoadSensor(system_coordinator, server_uuid, server_name, ups),
                    UPSRuntimeSensor(system_coordinator, server_uuid, server_name, ups),
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
            # This tracks cumulative energy using trapezoidal integration
            if ups_nominal_power > 0:
                energy_sensor = UPSEnergySensor(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    ups,
                    ups_nominal_power,
                )
                entities.append(energy_sensor)
                _LOGGER.debug(
                    "Created UPS Energy sensor for UPS %s (nominal power: %dW)",
                    ups.name,
                    ups_nominal_power,
                )
    else:
        _LOGGER.debug("No UPS devices connected, skipping UPS sensors")

    # Storage sensors
    entities.extend(
        [
            ArrayStateSensor(storage_coordinator, server_uuid, server_name),
            ArrayUsageSensor(storage_coordinator, server_uuid, server_name),
            ParityProgressSensor(storage_coordinator, server_uuid, server_name),
        ]
    )

    # Add disk sensors dynamically from parsed data (all disk types)
    if storage_coordinator.data:
        # Data disks - usage and temperature sensors (health handled by binary_sensor)
        for disk in storage_coordinator.data.disks:
            entities.append(
                DiskUsageSensor(storage_coordinator, server_uuid, server_name, disk)
            )
            entities.append(
                DiskTemperatureSensor(
                    storage_coordinator, server_uuid, server_name, disk
                )
            )

        # Parity disks - temperature sensors only (health via binary_sensor, no usage)
        for disk in storage_coordinator.data.parities:
            entities.append(
                DiskTemperatureSensor(
                    storage_coordinator, server_uuid, server_name, disk
                )
            )

        # Cache disks - usage and temperature sensors (health handled by binary_sensor)
        for disk in storage_coordinator.data.caches:
            entities.append(
                DiskUsageSensor(storage_coordinator, server_uuid, server_name, disk)
            )
            entities.append(
                DiskTemperatureSensor(
                    storage_coordinator, server_uuid, server_name, disk
                )
            )

    # Add share sensors dynamically
    if storage_coordinator.data:
        for share in storage_coordinator.data.shares:
            entities.append(
                ShareUsageSensor(storage_coordinator, server_uuid, server_name, share)
            )

    # Flash device sensor (if boot device exists)
    if storage_coordinator.data and storage_coordinator.data.boot:
        entities.append(FlashUsageSensor(storage_coordinator, server_uuid, server_name))

    _LOGGER.debug("Adding %d sensor entities", len(entities))
    async_add_entities(entities)
