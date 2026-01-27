"""Tests for Unraid sensor entities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import EntityCategory
from unraid_api.models import (
    ArrayCapacity,
    ArrayDisk,
    CapacityKilobytes,
    ParityCheck,
    Share,
    UPSBattery,
    UPSDevice,
    UPSPower,
)

from custom_components.unraid.const import DOMAIN
from custom_components.unraid.coordinator import (
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)
from custom_components.unraid.sensor import (
    ActiveNotificationsSensor,
    ArrayStateSensor,
    ArrayUsageSensor,
    CpuPowerSensor,
    CpuSensor,
    DiskTemperatureSensor,
    DiskUsageSensor,
    FlashUsageSensor,
    ParityProgressSensor,
    RAMUsageSensor,
    ShareUsageSensor,
    TemperatureSensor,
    UnraidSensorEntity,
    UPSBatterySensor,
    UPSLoadSensor,
    UPSPowerSensor,
    UPSRuntimeSensor,
    UptimeSensor,
    format_bytes,
    format_uptime,
)
from tests.conftest import make_storage_data, make_system_data

# =============================================================================
# Helper Function Tests - format_bytes
# =============================================================================


def test_formatbytes_none() -> None:
    """Test format_bytes returns None for None input."""
    assert format_bytes(None) is None


def test_formatbytes_zero() -> None:
    """Test format_bytes returns '0 B' for zero."""
    assert format_bytes(0) == "0 B"


def test_formatbytes_bytes() -> None:
    """Test format_bytes for byte values (< 1024)."""
    assert format_bytes(100) == "100 B"
    assert format_bytes(1023) == "1023 B"


def test_formatbytes_kilobytes() -> None:
    """Test format_bytes for KB values."""
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(2048) == "2.00 KB"


def test_formatbytes_megabytes() -> None:
    """Test format_bytes for MB values."""
    assert format_bytes(1048576) == "1.00 MB"


def test_formatbytes_gigabytes() -> None:
    """Test format_bytes for GB values."""
    assert format_bytes(1073741824) == "1.00 GB"


def test_formatbytes_terabytes() -> None:
    """Test format_bytes for TB values."""
    assert format_bytes(1099511627776) == "1.00 TB"


def test_formatbytes_petabytes() -> None:
    """Test format_bytes for PB values."""
    assert format_bytes(1125899906842624) == "1.00 PB"


def test_formatbytes_large_value() -> None:
    """Test format_bytes doesn't go beyond PB."""
    # 2000 PB should still display as PB
    assert "PB" in format_bytes(2 * 1125899906842624)


# =============================================================================
# Helper Function Tests - format_uptime
# =============================================================================


def test_formatuptime_none() -> None:
    """Test format_uptime returns None for None input."""
    assert format_uptime(None) is None


def test_formatuptime_future_date() -> None:
    """Test format_uptime returns '0 seconds' for future dates."""
    future = datetime.now(UTC) + timedelta(hours=1)
    assert format_uptime(future) == "0 seconds"


def test_formatuptime_seconds() -> None:
    """Test format_uptime for seconds only."""
    past = datetime.now(UTC) - timedelta(seconds=30)
    result = format_uptime(past)
    assert "30 seconds" in result


def test_formatuptime_minutes() -> None:
    """Test format_uptime for minutes."""
    past = datetime.now(UTC) - timedelta(minutes=5, seconds=30)
    result = format_uptime(past)
    assert "5 minutes" in result
    assert "30 second" in result


def test_formatuptime_hours() -> None:
    """Test format_uptime for hours."""
    past = datetime.now(UTC) - timedelta(hours=2, minutes=15)
    result = format_uptime(past)
    assert "2 hours" in result
    assert "15 minute" in result


def test_formatuptime_days() -> None:
    """Test format_uptime for days."""
    past = datetime.now(UTC) - timedelta(days=3, hours=12)
    result = format_uptime(past)
    assert "3 days" in result
    assert "12 hour" in result


def test_formatuptime_months() -> None:
    """Test format_uptime for months."""
    past = datetime.now(UTC) - timedelta(days=45)
    result = format_uptime(past)
    assert "month" in result


def test_formatuptime_years() -> None:
    """Test format_uptime for years."""
    past = datetime.now(UTC) - timedelta(days=400)
    result = format_uptime(past)
    assert "year" in result


def test_formatuptime_singular() -> None:
    """Test format_uptime uses singular form."""
    past = datetime.now(UTC) - timedelta(days=1, hours=1, minutes=1, seconds=1)
    result = format_uptime(past)
    assert "1 day" in result
    assert "1 hour" in result
    assert "1 minute" in result
    assert "1 second" in result


def test_formatuptime_zero_parts() -> None:
    """Test format_uptime with zero intermediate parts."""
    # Just a few seconds - should only show seconds
    past = datetime.now(UTC) - timedelta(seconds=5)
    result = format_uptime(past)
    assert "second" in result
    assert "minute" not in result


# =============================================================================
# Base Entity Tests
# =============================================================================


def test_unraidsensorentity_base_sensor_entity_properties() -> None:
    """Test base sensor entity has proper device info."""
    entity = UnraidSensorEntity(
        coordinator=MagicMock(spec=UnraidSystemCoordinator),
        server_uuid="test-uuid",
        server_name="test-server",
        resource_id="test-resource",
        name="Test Sensor",
    )

    assert entity.unique_id == "test-uuid_test-resource"
    assert entity.name == "Test Sensor"
    assert entity.device_info is not None
    assert entity.device_info["identifiers"] == {(DOMAIN, "test-uuid")}
    assert entity.device_info["name"] == "test-server"


def test_unraidsensorentity_sensor_availability_from_coordinator() -> None:
    """Test sensor availability based on coordinator."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True

    entity = UnraidSensorEntity(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        resource_id="test-resource",
        name="Test Sensor",
    )

    assert entity.available is True

    coordinator.last_update_success = False
    assert entity.available is False


# =============================================================================
# CPU Sensor Tests
# =============================================================================


def test_cpusensor_creation() -> None:
    """Test CPU sensor creation with proper attributes."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_percent=45.2)

    sensor = CpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_cpu_usage"
    assert sensor.name == "CPU Usage"
    assert sensor.device_class is None
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == "%"
    assert sensor.translation_key == "cpu_usage"


def test_cpusensor_state() -> None:
    """Test CPU sensor returns correct state."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_percent=45.2)

    sensor = CpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 45.2


def test_cpusensor_missing_data() -> None:
    """Test CPU sensor handles missing data."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_percent=None)

    sensor = CpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_cpusensor_none_data_native_value() -> None:
    """Test CPU sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = CpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_cpusensor_none_data_attributes() -> None:
    """Test CPU sensor returns empty attributes when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = CpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.extra_state_attributes == {}


# =============================================================================
# CPU Power Sensor Tests
# =============================================================================


def test_cpupowersensor_creation() -> None:
    """Test CPU power sensor creation with proper attributes."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_power=65.5)

    sensor = CpuPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_cpu_power"
    assert sensor.name == "CPU Power"
    assert sensor.device_class == SensorDeviceClass.POWER
    assert sensor.state_class == SensorStateClass.MEASUREMENT


def test_cpupowersensor_state() -> None:
    """Test CPU power sensor returns correct power value."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_power=85.5)

    sensor = CpuPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 85.5


def test_cpupowersensor_none_data() -> None:
    """Test CPU power sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = CpuPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# RAM Sensor Tests
# =============================================================================


def test_ramusagesensor_creation() -> None:
    """Test RAM usage sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        memory_total=16000000000, memory_used=8000000000, memory_percent=50.0
    )

    sensor = RAMUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_ram_usage"
    assert sensor.device_class is None
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == "%"
    assert sensor.translation_key == "ram_usage"


def test_ramusagesensor_state() -> None:
    """Test RAM usage sensor returns correct percentage state."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        memory_total=16000000000,
        memory_used=8000000000,
        memory_percent=50.0,
    )

    sensor = RAMUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 50.0


def test_ramusagesensor_attributes() -> None:
    """Test RAM usage sensor returns human-readable attributes."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        memory_total=17179869184,  # 16 GB
        memory_used=8589934592,  # 8 GB
        memory_percent=50.0,
        memory_free=8589934592,  # 8 GB
        memory_available=10000000000,  # ~9.3 GB
    )

    sensor = RAMUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = sensor.extra_state_attributes
    assert "total" in attrs
    assert "used" in attrs
    assert "free" in attrs
    assert "available" in attrs
    # Check human-readable format (should be GB)
    assert "GB" in attrs["total"]


def test_ramusagesensor_none_data_native_value() -> None:
    """Test RAM sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = RAMUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_ramusagesensor_none_data_attributes() -> None:
    """Test RAM sensor returns empty attributes when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = RAMUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.extra_state_attributes == {}


# =============================================================================
# Temperature Sensor Tests
# =============================================================================


def test_temperaturesensor_creation() -> None:
    """Test temperature sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_temps=[45.0])

    sensor = TemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_cpu_temp"
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == "°C"


def test_temperaturesensor_state() -> None:
    """Test temperature sensor returns correct state (average of all packages)."""
    cpu_temps = [45.0, 50.0, 48.0]
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_temps=cpu_temps)

    sensor = TemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    # Should average temperatures: (45.0 + 50.0 + 48.0) / 3 = 47.666...
    expected_avg = sum(cpu_temps) / len(cpu_temps)
    assert sensor.native_value == pytest.approx(expected_avg, rel=0.01)


def test_temperaturesensor_single_value() -> None:
    """Test temperature sensor with single CPU package."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_temps=[52.5])

    sensor = TemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 52.5


def test_temperaturesensor_missing_data() -> None:
    """Test temperature sensor handles missing data."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_temps=[])

    sensor = TemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_temperaturesensor_none_data() -> None:
    """Test temperature sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = TemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_temperaturesensor_empty_temps() -> None:
    """Test temperature sensor returns None when temp list is empty."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_temps=[])

    sensor = TemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# Uptime Sensor Tests
# =============================================================================


def test_uptimesensor_creation() -> None:
    """Test uptime sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        uptime=datetime(2025, 12, 20, 12, 0, 0, tzinfo=UTC)
    )

    sensor = UptimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_uptime"
    assert sensor.device_class is None  # Changed from TIMESTAMP
    assert sensor.state_class is None
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC


def test_uptimesensor_state() -> None:
    """Test uptime sensor returns human-readable string."""
    # Boot time 3 days, 2 hours, 30 minutes ago
    uptime_dt = datetime(2025, 12, 20, 9, 30, 0, tzinfo=UTC)
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(uptime=uptime_dt)

    sensor = UptimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    # Should return human-readable string (actual value depends on "now")
    assert sensor.native_value is not None
    assert isinstance(sensor.native_value, str)


def test_uptimesensor_none_data_native_value() -> None:
    """Test uptime sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UptimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_uptimesensor_none_data_attributes() -> None:
    """Test uptime sensor returns empty attributes when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UptimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.extra_state_attributes == {}


# =============================================================================
# Active Notifications Sensor Tests
# =============================================================================


def test_activenotificationssensor_creation() -> None:
    """Test active notifications sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(notifications_unread=5)

    sensor = ActiveNotificationsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_active_notifications"
    assert sensor.name == "Active Notifications"
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == "notifications"


def test_activenotificationssensor_state() -> None:
    """Test active notifications sensor returns correct count."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(notifications_unread=3)

    sensor = ActiveNotificationsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 3


def test_activenotificationssensor_none_data() -> None:
    """Test active notifications sensor returns None when data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = ActiveNotificationsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# Array Sensor Tests
# =============================================================================


def test_arraystatesensor_creation() -> None:
    """Test array state sensor creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        array_state="STARTED",
        capacity=ArrayCapacity(
            kilobytes=CapacityKilobytes(total=1000, used=500, free=500)
        ),
    )

    sensor = ArrayStateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_array_state"
    assert sensor.name == "Array State"
    assert sensor.translation_key == "array_state"


def test_arraystatesensor_state() -> None:
    """Test array state sensor returns correct state."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        array_state="STARTED",
        capacity=ArrayCapacity(
            kilobytes=CapacityKilobytes(total=1000, used=500, free=500)
        ),
    )

    sensor = ArrayStateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == "started"


def test_arraystatesensor_none_data() -> None:
    """Test array state sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = ArrayStateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_arraystatesensor_none_state() -> None:
    """Test array state sensor returns None when state is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state=None)

    sensor = ArrayStateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# Array Capacity Sensor Tests
# =============================================================================


def test_arrayusagesensor_creation() -> None:
    """Test array usage sensor creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        array_state="STARTED",
        capacity=ArrayCapacity(
            kilobytes=CapacityKilobytes(
                total=10737418240, used=5368709120, free=5368709120
            )
        ),
    )

    sensor = ArrayUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_array_usage"
    assert sensor.native_unit_of_measurement == "%"
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.device_class is None


def test_arrayusagesensor_state() -> None:
    """Test array usage sensor returns percentage value."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        array_state="STARTED",
        capacity=ArrayCapacity(
            kilobytes=CapacityKilobytes(
                total=10737418240, used=5368709120, free=5368709120
            )
        ),
    )

    sensor = ArrayUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 50.0


def test_arrayusagesensor_attributes() -> None:
    """Test array usage sensor has human-readable attributes."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        array_state="STARTED",
        capacity=ArrayCapacity(
            kilobytes=CapacityKilobytes(
                total=10737418240, used=5368709120, free=5368709120
            )
        ),
    )

    sensor = ArrayUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = sensor.extra_state_attributes
    assert "total" in attrs
    assert "used" in attrs
    assert "free" in attrs
    # Values should be human-readable (GB, TB, etc.)
    assert "TB" in attrs["total"] or "GB" in attrs["total"]


def test_arrayusagesensor_none_data() -> None:
    """Test array usage sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = ArrayUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_arrayusagesensor_zero_capacity() -> None:
    """Test array usage sensor returns 0 when capacity is zero."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        capacity=ArrayCapacity(kilobytes=CapacityKilobytes(total=0, used=0, free=0))
    )

    sensor = ArrayUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    # Zero capacity returns 0.0 percent (not None)
    assert sensor.native_value == 0.0
    # Attributes still available with zero values
    assert "total" in sensor.extra_state_attributes


# =============================================================================
# Disk Sensor Tests
# =============================================================================


def test_disksensors_temperature_sensor() -> None:
    """Test disk temperature sensor creation."""
    disk = ArrayDisk(
        id="disk1",
        idx=0,
        name="disk1",
        device="sda",
        temp=45,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert sensor.unique_id == "test-uuid_disk_disk1_temp"
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.native_unit_of_measurement == "°C"
    assert sensor.native_value == 45


def test_disksensors_usage_sensor() -> None:
    """Test disk usage sensor returns percentage."""
    disk = ArrayDisk(
        id="disk1",
        idx=0,
        name="disk1",
        device="sda",
        fsSize=1000,
        fsUsed=500,
        fsFree=500,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert sensor.unique_id == "test-uuid_disk_disk1_usage"
    assert sensor.device_class is None  # Changed from DATA_SIZE
    assert sensor.native_unit_of_measurement == "%"
    assert sensor.native_value == 50.0  # 500/1000 * 100


def test_disksensors_usage_sensor_attributes() -> None:
    """Test disk usage sensor has human-readable attributes."""
    disk = ArrayDisk(
        id="disk1",
        idx=0,
        name="disk1",
        device="sda",
        type="DATA",
        status="DISK_OK",
        fsSize=1000000,  # ~1 GB in KB
        fsUsed=500000,
        fsFree=500000,
        isSpinning=True,
        temp=35,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    attrs = sensor.extra_state_attributes
    assert "total" in attrs
    assert "used" in attrs
    assert "free" in attrs
    assert attrs.get("spin_state") == "active"
    assert "device" in attrs
    assert "type" in attrs
    assert attrs.get("status") == "DISK_OK"
    assert attrs.get("temperature_celsius") == 35


def test_disksensors_temperature_missing() -> None:
    """Test disk temperature sensor handles missing temperature."""
    disk = ArrayDisk(
        id="disk1",
        idx=0,
        name="disk1",
        device="sda",
        temp=None,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert sensor.native_value is None


def test_disksensors_temperature_none_data() -> None:
    """Test disk temperature sensor returns None when coordinator data is None."""
    disk = ArrayDisk(id="disk1", name="Disk 1")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = DiskTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert sensor.native_value is None


def test_disksensors_temperature_none_data_attributes() -> None:
    """Test disk temperature sensor returns empty attributes when data is None."""
    disk = ArrayDisk(id="disk1", name="Disk 1")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = DiskTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert sensor.extra_state_attributes == {}


def test_disksensors_usage_none_data() -> None:
    """Test disk usage sensor returns None when coordinator data is None."""
    disk = ArrayDisk(id="disk1", name="Disk 1")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert sensor.native_value is None


def test_disksensors_usage_none_data_attributes() -> None:
    """Test disk usage sensor returns empty attributes when data is None."""
    disk = ArrayDisk(id="disk1", name="Disk 1")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert sensor.extra_state_attributes == {}


def test_disksensors_usage_missing_disk() -> None:
    """Test disk usage sensor returns None when disk not found in data."""
    disk = ArrayDisk(id="disk_missing", name="Missing Disk")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


# =============================================================================
# Disk Usage Sensor Attributes Edge Cases
# =============================================================================


def test_diskusagesensorattributes_with_fstype() -> None:
    """Test disk usage sensor includes filesystem type when available."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        fsType="xfs",
        fsSize=1000,
        fsUsed=500,
        fsFree=500,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    attrs = sensor.extra_state_attributes
    assert attrs.get("filesystem") == "xfs"


def test_diskusagesensorattributes_spinning_false() -> None:
    """Test disk usage sensor shows standby when not spinning."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        isSpinning=False,
        fsSize=1000,
        fsUsed=500,
        fsFree=500,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    attrs = sensor.extra_state_attributes
    assert attrs.get("spin_state") == "standby"


def test_diskusagesensorattributes_smart_status() -> None:
    """Test disk usage sensor includes SMART status when available."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        smartStatus="PASSED",
        fsSize=1000,
        fsUsed=500,
        fsFree=500,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    attrs = sensor.extra_state_attributes
    assert attrs.get("smart_status") == "PASSED"


# =============================================================================
# Sensor Updates From Coordinator Tests
# =============================================================================


def test_sensorupdatesfromcoordinator_on_data_change() -> None:
    """Test sensor updates when coordinator data changes."""
    # This would be an integration test - testing via async_update_listeners
    # For now, verify the sensor reads from coordinator.data
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(cpu_percent=25.0)
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock()

    sensor = CpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 25.0

    # Simulate data update
    coordinator.data = make_system_data(cpu_percent=75.0)
    assert sensor.native_value == 75.0


# =============================================================================
# Parity Progress Sensor Tests
# =============================================================================


def test_parityprogresssensor_creation() -> None:
    """Test parity progress sensor creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        array_state="STARTED",
        capacity=ArrayCapacity(
            kilobytes=CapacityKilobytes(total=1000, used=500, free=500)
        ),
        parity_status=ParityCheck(status="RUNNING", progress=50, errors=0),
    )

    sensor = ParityProgressSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_parity_progress"
    assert sensor.native_unit_of_measurement == "%"
    assert sensor.native_value == 50


def test_parityprogresssensor_none_data() -> None:
    """Test parity progress sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = ParityProgressSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_parityprogresssensor_none_status() -> None:
    """Test parity progress sensor returns None when parity_status is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=None)

    sensor = ParityProgressSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# Disk Health Binary Sensor Tests
# =============================================================================


def test_diskhealthbinarysensor_creation() -> None:
    """Test disk health binary sensor creation."""
    disk = ArrayDisk(
        id="disk1",
        idx=0,
        name="disk1",
        device="sda",
        status="DISK_OK",
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    from custom_components.unraid.binary_sensor import DiskHealthBinarySensor

    sensor = DiskHealthBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert sensor.unique_id == "test-uuid_disk_health_disk1"
    assert sensor.device_class == "problem"
    assert sensor.name == "Disk disk1 Health"


def test_diskhealthbinarysensor_ok_status() -> None:
    """Test disk health binary sensor is OFF when disk is OK."""
    disk = ArrayDisk(
        id="disk1",
        idx=0,
        name="disk1",
        device="sda",
        status="DISK_OK",
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    from custom_components.unraid.binary_sensor import DiskHealthBinarySensor

    sensor = DiskHealthBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    # DISK_OK should be OFF (not a problem)
    assert sensor.is_on is False


def test_diskhealthbinarysensor_problem_status() -> None:
    """Test disk health binary sensor is ON when disk has issues."""
    disk = ArrayDisk(
        id="disk1",
        idx=0,
        name="disk1",
        device="sda",
        status="DISK_ERROR",
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    from custom_components.unraid.binary_sensor import DiskHealthBinarySensor

    sensor = DiskHealthBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    # Any non-DISK_OK status should be ON (is a problem)
    assert sensor.is_on is True


# =============================================================================
# Array Started Binary Sensor Tests
# =============================================================================


def test_arraystartedbinarysensor_creation() -> None:
    """Test array started sensor creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STARTED")

    from custom_components.unraid.binary_sensor import ArrayStartedBinarySensor

    sensor = ArrayStartedBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_array_started"
    assert sensor.name == "Array Started"


def test_arraystartedbinarysensor_is_on_when_started() -> None:
    """Test array started sensor is ON when array is started."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STARTED")

    from custom_components.unraid.binary_sensor import ArrayStartedBinarySensor

    sensor = ArrayStartedBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.is_on is True


def test_arraystartedbinarysensor_is_off_when_stopped() -> None:
    """Test array started sensor is OFF when array is stopped."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STOPPED")

    from custom_components.unraid.binary_sensor import ArrayStartedBinarySensor

    sensor = ArrayStartedBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.is_on is False


# =============================================================================
# Parity Check Running Binary Sensor Tests
# =============================================================================


def test_paritycheckrunningbinarysensor_creation() -> None:
    """Test parity check running sensor creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(status="RUNNING", progress=50, errors=0)
    )

    from custom_components.unraid.binary_sensor import (
        ParityCheckRunningBinarySensor,
    )

    sensor = ParityCheckRunningBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_parity_check_running"
    assert sensor.name == "Parity Check Running"


def test_paritycheckrunningbinarysensor_when_running() -> None:
    """Test parity check running sensor is ON when parity check is running."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(status="RUNNING", progress=50, errors=0)
    )

    from custom_components.unraid.binary_sensor import (
        ParityCheckRunningBinarySensor,
    )

    sensor = ParityCheckRunningBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.is_on is True


def test_paritycheckrunningbinarysensor_when_paused() -> None:
    """Test parity check running sensor is ON when paused."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(status="PAUSED", progress=50, errors=0)
    )

    from custom_components.unraid.binary_sensor import (
        ParityCheckRunningBinarySensor,
    )

    sensor = ParityCheckRunningBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.is_on is True


def test_paritycheckrunningbinarysensor_not_running_when_completed() -> None:
    """Test parity check running sensor is OFF when completed."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(status="COMPLETED", progress=100, errors=0)
    )

    from custom_components.unraid.binary_sensor import (
        ParityCheckRunningBinarySensor,
    )

    sensor = ParityCheckRunningBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.is_on is False


# =============================================================================
# Parity Valid Binary Sensor Tests
# =============================================================================


def test_parityvalidbinarysensor_creation() -> None:
    """Test parity valid sensor creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(status="COMPLETED", progress=100, errors=0)
    )

    from custom_components.unraid.binary_sensor import ParityValidBinarySensor

    sensor = ParityValidBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_parity_valid"
    assert sensor.name == "Parity Valid"


def test_parityvalidbinarysensor_no_problem_when_completed() -> None:
    """Test parity valid sensor is OFF (no problem) when completed successfully."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(status="COMPLETED", progress=100, errors=0)
    )

    from custom_components.unraid.binary_sensor import ParityValidBinarySensor

    sensor = ParityValidBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.is_on is False


def test_parityvalidbinarysensor_problem_when_failed() -> None:
    """Test parity valid sensor is ON (problem) when failed."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(status="FAILED", progress=100, errors=0)
    )

    from custom_components.unraid.binary_sensor import ParityValidBinarySensor

    sensor = ParityValidBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.is_on is True


def test_parityvalidbinarysensor_problem_when_errors() -> None:
    """Test parity valid sensor is ON (problem) when errors exist."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(status="COMPLETED", progress=100, errors=5)
    )

    from custom_components.unraid.binary_sensor import ParityValidBinarySensor

    sensor = ParityValidBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.is_on is True


# =============================================================================
# UPS Battery Sensor Tests
# =============================================================================


def test_upsbatterysensor_creation() -> None:
    """Test UPS battery sensor entity creation."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatterySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.unique_id == "test-uuid_ups_ups:1_battery"
    assert sensor.name == "UPS Battery"
    assert sensor.device_class == SensorDeviceClass.BATTERY
    assert sensor.native_unit_of_measurement == "%"


def test_upsbatterysensor_state() -> None:
    """Test UPS battery sensor returns correct charge level."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatterySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == 95


def test_upsbatterysensor_none_data() -> None:
    """Test UPS battery sensor returns None when coordinator data is None."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSBatterySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


def test_upsbatterysensor_none_data_attributes() -> None:
    """Test UPS battery sensor returns empty attributes when data is None."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSBatterySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.extra_state_attributes == {}


# =============================================================================
# UPS Load Sensor Tests
# =============================================================================


def test_upsloadsensor_creation() -> None:
    """Test UPS load sensor entity creation."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSLoadSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.unique_id == "test-uuid_ups_ups:1_load"
    assert sensor.name == "UPS Load"
    assert sensor.native_unit_of_measurement == "%"


def test_upsloadsensor_state() -> None:
    """Test UPS load sensor returns correct load percentage."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSLoadSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == 20.5


def test_upsloadsensor_attributes() -> None:
    """Test UPS load sensor has correct attributes."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSLoadSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["model"] == "APC"
    assert attrs["status"] == "Online"
    assert attrs["input_voltage"] == 120.0
    assert attrs["output_voltage"] == 118.5


def test_upsloadsensor_none_data() -> None:
    """Test UPS load sensor returns None when coordinator data is None."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSLoadSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


def test_upsloadsensor_none_data_attributes() -> None:
    """Test UPS load sensor returns empty attributes when data is None."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSLoadSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.extra_state_attributes == {}


# =============================================================================
# UPS Runtime Sensor Tests
# =============================================================================


def test_upsruntimesensor_creation() -> None:
    """Test UPS runtime sensor entity creation."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.unique_id == "test-uuid_ups_ups:1_runtime"
    assert sensor.name == "UPS Runtime"


def test_upsruntimesensor_state() -> None:
    """Test UPS runtime sensor returns human-readable duration."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=3660),  # 1h 1m
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == "1 hour 1 minute"


def test_upsruntimesensor_none_data() -> None:
    """Test UPS runtime sensor returns None when coordinator data is None."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


def test_upsruntimesensor_none_runtime() -> None:
    """Test UPS runtime sensor returns None when runtime is None."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=None),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


def test_upsruntimesensor_none_data_attributes() -> None:
    """Test UPS runtime sensor returns empty attributes when data is None."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.extra_state_attributes == {}


def test_upsruntimesensor_minutes_only() -> None:
    """Test UPS runtime with only minutes (no hours)."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        battery=UPSBattery(estimatedRuntime=1800),  # 30 minutes
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == "30 minutes"


def test_upsruntimesensor_singular_units() -> None:
    """Test UPS runtime with singular minute."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        battery=UPSBattery(estimatedRuntime=60),  # 1 minute
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == "1 minute"


def test_upsruntimesensor_1_hour_1_minute() -> None:
    """Test UPS runtime with singular hour and minute."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        battery=UPSBattery(estimatedRuntime=3660),  # 1 hour 1 minute
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == "1 hour 1 minute"


def test_upsruntimesensor_attributes_with_runtime() -> None:
    """Test UPS runtime sensor attributes include runtime info."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(estimatedRuntime=1800),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["runtime_seconds"] == 1800
    assert attrs["runtime_minutes"] == 30


# =============================================================================
# UPS Power Sensor Tests
# =============================================================================


def test_upspowersensor_creation() -> None:
    """Test UPS power sensor entity creation."""
    from homeassistant.const import UnitOfPower

    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_capacity_va=1000,
        ups_nominal_power=800,
    )

    assert sensor.unique_id == "test-uuid_ups_ups:1_power"
    assert sensor.name == "UPS Power"
    assert sensor.device_class == SensorDeviceClass.POWER
    assert sensor.native_unit_of_measurement == UnitOfPower.WATT
    assert sensor.state_class == SensorStateClass.MEASUREMENT


def test_upspowersensor_calculates_power() -> None:
    """Test UPS power sensor calculates power from load and nominal power."""
    # Load: 20.5%, Nominal Power: 800W
    # Expected: 20.5 / 100 * 800 = 164W
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_capacity_va=1000,
        ups_nominal_power=800,
    )

    assert sensor.native_value == 164.0


def test_upspowersensor_unavailable_when_nominal_power_zero() -> None:
    """Test UPS power sensor is unavailable when nominal power is 0."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    coordinator.last_update_success = True

    sensor = UPSPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_capacity_va=1000,
        ups_nominal_power=0,
    )

    assert sensor.available is False
    assert sensor.native_value is None


def test_upspowersensor_attributes() -> None:
    """Test UPS power sensor has correct attributes."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_capacity_va=1000,
        ups_nominal_power=800,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["model"] == "APC"
    assert attrs["status"] == "Online"
    assert attrs["ups_capacity_va"] == 1000
    assert attrs["nominal_power_watts"] == 800
    assert attrs["load_percentage"] == 20.5
    assert attrs["input_voltage"] == 120.0
    assert attrs["output_voltage"] == 118.5


def test_upspowersensor_real_world_example() -> None:
    """Test UPS power sensor with real-world values from API."""
    # Based on actual UPS data: PR1000ELCDRT1U (1000VA, 800W nominal), 12% load
    # Expected: 12 / 100 * 800 = 96W (matches Unraid UI)
    ups = UPSDevice(
        id="PR1000ELCDRT1U",
        name="PR1000ELCDRT1U",
        status="ONLINE",
        battery=UPSBattery(chargeLevel=100, estimatedRuntime=6360),
        power=UPSPower(inputVoltage=236.0, outputVoltage=236.0, loadPercentage=12.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_capacity_va=1000,
        ups_nominal_power=800,
    )

    assert sensor.native_value == 96.0


def test_upspowersensor_none_data() -> None:
    """Test UPS power sensor returns None when coordinator data is None."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_capacity_va=1000,
        ups_nominal_power=800,
    )

    assert sensor.native_value is None


def test_upspowersensor_none_load() -> None:
    """Test UPS power sensor returns None when load percentage is None."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(loadPercentage=None),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_capacity_va=1000,
        ups_nominal_power=800,
    )

    assert sensor.native_value is None


# =============================================================================
# Share Usage Sensor Tests
# =============================================================================


def test_shareusagesensor_creation() -> None:
    """Test share usage sensor creation."""
    share = Share(id="share:1", name="appdata", size=1000000, used=500000, free=500000)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(shares=[share])

    sensor = ShareUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        share=share,
    )

    assert sensor.unique_id == "test-uuid_share_share:1_usage"
    assert sensor.name == "Share appdata Usage"
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == "%"


def test_shareusagesensor_state() -> None:
    """Test share usage sensor returns correct percentage."""
    share = Share(id="share:1", name="appdata", size=1000, used=500, free=500)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(shares=[share])

    sensor = ShareUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        share=share,
    )

    assert sensor.native_value == 50.0


def test_shareusagesensor_none_data() -> None:
    """Test share usage sensor returns None when coordinator data is None."""
    share = Share(id="share:1", name="appdata")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = ShareUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        share=share,
    )

    assert sensor.native_value is None


def test_shareusagesensor_missing_share() -> None:
    """Test share usage sensor returns None when share not found."""
    share = Share(id="share_missing", name="missing")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(shares=[])

    sensor = ShareUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        share=share,
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_shareusagesensor_attributes() -> None:
    """Test share usage sensor returns human-readable attributes."""
    share = Share(
        id="share:1",
        name="appdata",
        size=1073741824,
        used=536870912,
        free=536870912,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(shares=[share])

    sensor = ShareUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        share=share,
    )

    attrs = sensor.extra_state_attributes
    assert "total" in attrs
    assert "used" in attrs
    assert "free" in attrs


# =============================================================================
# Flash Usage Sensor Tests
# =============================================================================


def test_flashusagesensor_creation() -> None:
    """Test flash usage sensor creation."""
    boot = ArrayDisk(
        id="boot", name="Flash", fsSize=16000000, fsUsed=8000000, fsFree=8000000
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(boot=boot)

    sensor = FlashUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_flash_usage"
    assert sensor.name == "Flash Device Usage"
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == "%"


def test_flashusagesensor_state() -> None:
    """Test flash usage sensor returns correct percentage."""
    boot = ArrayDisk(id="boot", name="Flash", fsSize=16000, fsUsed=8000, fsFree=8000)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(boot=boot)

    sensor = FlashUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 50.0


def test_flashusagesensor_none_data() -> None:
    """Test flash usage sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = FlashUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_flashusagesensor_none_boot() -> None:
    """Test flash usage sensor returns None when boot is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(boot=None)

    sensor = FlashUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_flashusagesensor_attributes() -> None:
    """Test flash usage sensor returns correct attributes."""
    boot = ArrayDisk(
        id="boot",
        name="Flash",
        device="sdc",
        status="DISK_OK",
        fsSize=16000000,
        fsUsed=8000000,
        fsFree=8000000,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(boot=boot)

    sensor = FlashUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = sensor.extra_state_attributes
    assert "total" in attrs
    assert "used" in attrs
    assert "free" in attrs
    assert attrs["device"] == "sdc"
    assert attrs["status"] == "DISK_OK"


# =============================================================================
# async_setup_entry Tests
# =============================================================================


@pytest.mark.asyncio
async def test_asyncsetupentry_creates_system_sensors(hass) -> None:
    """Test setup creates system sensors."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data()

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = make_storage_data()

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info={
            "uuid": "test-uuid",
            "name": "tower",
            "manufacturer": "Supermicro",
            "model": "X11",
        },
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Should create system sensors (CPU, RAM, Temp, Uptime, etc.)
    assert len(added_entities) > 0

    # Check some expected sensor types exist
    entity_types = {type(e).__name__ for e in added_entities}
    assert "CpuSensor" in entity_types
    assert "RAMUsageSensor" in entity_types
    assert "ArrayStateSensor" in entity_types


@pytest.mark.asyncio
async def test_asyncsetupentry_creates_ups_sensors(hass) -> None:
    """Test setup creates UPS sensors when UPS devices exist."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=100),
        power=UPSPower(loadPercentage=20.0),
    )

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data(ups_devices=[ups])

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = make_storage_data()

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {"ups_capacity_va": 1000}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info={"uuid": "test-uuid", "name": "tower"},
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    entity_types = {type(e).__name__ for e in added_entities}
    assert "UPSBatterySensor" in entity_types
    assert "UPSLoadSensor" in entity_types
    assert "UPSRuntimeSensor" in entity_types
    assert "UPSPowerSensor" in entity_types


@pytest.mark.asyncio
async def test_asyncsetupentry_creates_disk_sensors(hass) -> None:
    """Test setup creates disk sensors for disks in storage data."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    disk = ArrayDisk(id="disk:1", name="Disk 1", status="DISK_OK")

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data()

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = make_storage_data(disks=[disk])

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info={"uuid": "test-uuid", "name": "tower"},
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    entity_types = {type(e).__name__ for e in added_entities}
    assert "DiskUsageSensor" in entity_types


@pytest.mark.asyncio
async def test_asyncsetupentry_no_storage_data(hass) -> None:
    """Test setup handles None storage data."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data()

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = None

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info={"uuid": "test-uuid", "name": "tower"},
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    # Should not raise, just skip disk/share sensors
    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Should still create system sensors
    assert len(added_entities) > 0


@pytest.mark.asyncio
async def test_asyncsetupentry_creates_share_sensors(hass) -> None:
    """Test setup creates share sensors for shares in storage data."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    share = Share(id="share:1", name="appdata", size=1000, used=500, free=500)

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data()

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = make_storage_data(shares=[share])

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info={"uuid": "test-uuid", "name": "tower"},
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    entity_types = {type(e).__name__ for e in added_entities}
    assert "ShareUsageSensor" in entity_types


@pytest.mark.asyncio
async def test_asyncsetupentry_creates_flash_sensor(hass) -> None:
    """Test setup creates flash sensor when boot device exists."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    boot = ArrayDisk(id="boot", name="Flash", fsSize=16000, fsUsed=8000)

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data()

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = make_storage_data(boot=boot)

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info={"uuid": "test-uuid", "name": "tower"},
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    entity_types = {type(e).__name__ for e in added_entities}
    assert "FlashUsageSensor" in entity_types


@pytest.mark.asyncio
async def test_asyncsetupentry_creates_cache_disk_sensors(hass) -> None:
    """Test setup creates disk usage sensors for cache disks."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    cache_disk = ArrayDisk(id="cache:1", name="Cache", type="CACHE")

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data()

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = make_storage_data(caches=[cache_disk])

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info={"uuid": "test-uuid", "name": "tower"},
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Find the DiskUsageSensor for the cache disk
    cache_sensors = [
        e
        for e in added_entities
        if isinstance(e, DiskUsageSensor) and "cache:1" in e.unique_id
    ]
    assert len(cache_sensors) == 1


@pytest.mark.asyncio
async def test_asyncsetupentry_no_ups_sensors_when_no_ups(hass) -> None:
    """Test setup doesn't create UPS sensors when no UPS devices."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data(ups_devices=[])

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = make_storage_data()

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info={"uuid": "test-uuid", "name": "tower"},
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    entity_types = {type(e).__name__ for e in added_entities}
    assert "UPSBatterySensor" not in entity_types


@pytest.mark.asyncio
async def test_asyncsetupentry_uses_ups_capacity_from_options(hass) -> None:
    """Test setup uses UPS capacity from entry options."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.const import (
        CONF_UPS_CAPACITY_VA,
        CONF_UPS_NOMINAL_POWER,
    )
    from custom_components.unraid.sensor import async_setup_entry

    ups = UPSDevice(
        id="ups:1",
        name="APC",
        battery=UPSBattery(chargeLevel=95),
        power=UPSPower(loadPercentage=20.0),
    )

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data(ups_devices=[ups])

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = make_storage_data()

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {CONF_UPS_CAPACITY_VA: 1500, CONF_UPS_NOMINAL_POWER: 1200}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        server_info={"uuid": "test-uuid", "name": "tower"},
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Find the UPSPowerSensor and verify capacity and nominal power
    power_sensors = [e for e in added_entities if isinstance(e, UPSPowerSensor)]
    assert len(power_sensors) == 1
    assert power_sensors[0]._ups_capacity_va == 1500
    assert power_sensors[0]._ups_nominal_power == 1200
