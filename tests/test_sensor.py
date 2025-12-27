"""Tests for Unraid sensor entities."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import EntityCategory

from custom_components.unraid.const import DOMAIN
from custom_components.unraid.coordinator import (
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)
from custom_components.unraid.models import (
    ArrayCapacity,
    ArrayDisk,
    CapacityKilobytes,
    ParityCheck,
    UPSBattery,
    UPSDevice,
    UPSPower,
)
from custom_components.unraid.sensor import (
    ArrayStateSensor,
    ArrayUsageSensor,
    CpuSensor,
    DiskTemperatureSensor,
    DiskUsageSensor,
    ParityProgressSensor,
    RAMUsageSensor,
    TemperatureSensor,
    UnraidSensorEntity,
    UPSBatterySensor,
    UPSLoadSensor,
    UPSPowerSensor,
    UPSRuntimeSensor,
    UptimeSensor,
)
from tests.conftest import make_storage_data, make_system_data


class TestUnraidSensorEntity:
    """Test UnraidSensorEntity base class."""

    def test_base_sensor_entity_properties(self) -> None:
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

    def test_sensor_availability_from_coordinator(self) -> None:
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


class TestCpuSensor:
    """Test CPU usage sensor."""

    def test_cpu_sensor_creation(self) -> None:
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

    def test_cpu_sensor_state(self) -> None:
        """Test CPU sensor returns correct state."""
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(cpu_percent=45.2)

        sensor = CpuSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
        )

        assert sensor.native_value == 45.2

    def test_cpu_sensor_missing_data(self) -> None:
        """Test CPU sensor handles missing data."""
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(cpu_percent=None)

        sensor = CpuSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
        )

        assert sensor.native_value is None


class TestRAMSensor:
    """Test RAM usage sensor."""

    def test_ram_usage_sensor_creation(self) -> None:
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

    def test_ram_usage_sensor_state(self) -> None:
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

    def test_ram_usage_sensor_attributes(self) -> None:
        """Test RAM usage sensor returns human-readable attributes."""
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(
            memory_total=17179869184,  # 16 GB
            memory_used=8589934592,  # 8 GB
            memory_percent=50.0,
        )
        # Add free and available values
        coordinator.data.metrics.memory.free = 8589934592
        coordinator.data.metrics.memory.available = 10000000000

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


class TestTemperatureSensor:
    """Test CPU temperature sensor."""

    def test_temperature_sensor_creation(self) -> None:
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

    def test_temperature_sensor_state(self) -> None:
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

    def test_temperature_sensor_single_value(self) -> None:
        """Test temperature sensor with single CPU package."""
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(cpu_temps=[52.5])

        sensor = TemperatureSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
        )

        assert sensor.native_value == 52.5

    def test_temperature_sensor_missing_data(self) -> None:
        """Test temperature sensor handles missing data."""
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(cpu_temps=[])

        sensor = TemperatureSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
        )

        assert sensor.native_value is None


class TestUptimeSensor:
    """Test uptime sensor."""

    def test_uptime_sensor_creation(self) -> None:
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

    def test_uptime_sensor_state(self) -> None:
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


class TestArraySensor:
    """Test array state sensor."""

    def test_array_state_sensor_creation(self) -> None:
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

    def test_array_state_sensor_state(self) -> None:
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


class TestArrayCapacitySensors:
    """Test array capacity sensors."""

    def test_array_usage_sensor_creation(self) -> None:
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

    def test_array_usage_sensor_state(self) -> None:
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

    def test_array_usage_sensor_attributes(self) -> None:
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


class TestDiskSensors:
    """Test disk sensor entities."""

    def test_disk_temperature_sensor(self) -> None:
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

    def test_disk_usage_sensor(self) -> None:
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

    def test_disk_usage_sensor_attributes(self) -> None:
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

    def test_disk_temperature_missing(self) -> None:
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


class TestSensorUpdatesFromCoordinator:
    """Test sensor state updates from coordinator."""

    def test_sensor_updates_on_coordinator_data_change(self) -> None:
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


class TestParityProgressSensor:
    """Test parity progress sensor."""

    def test_parity_progress_sensor_creation(self) -> None:
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


class TestDiskHealthBinarySensor:
    """Test disk health binary sensor."""

    def test_disk_health_binary_sensor_creation(self) -> None:
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

    def test_disk_health_binary_sensor_ok_status(self) -> None:
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

    def test_disk_health_binary_sensor_problem_status(self) -> None:
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


class TestArrayStartedBinarySensor:
    """Test Array Started binary sensor."""

    def test_array_started_sensor_creation(self) -> None:
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

    def test_array_started_sensor_is_on_when_started(self) -> None:
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

    def test_array_started_sensor_is_off_when_stopped(self) -> None:
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


class TestParityCheckRunningBinarySensor:
    """Test Parity Check Running binary sensor."""

    def test_parity_check_running_sensor_creation(self) -> None:
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

    def test_parity_check_running_when_running(self) -> None:
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

    def test_parity_check_running_when_paused(self) -> None:
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

    def test_parity_check_not_running_when_completed(self) -> None:
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


class TestParityValidBinarySensor:
    """Test Parity Valid binary sensor."""

    def test_parity_valid_sensor_creation(self) -> None:
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

    def test_parity_valid_no_problem_when_completed(self) -> None:
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

    def test_parity_valid_problem_when_failed(self) -> None:
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

    def test_parity_valid_problem_when_errors(self) -> None:
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


class TestUPSBatterySensor:
    """Tests for UPS battery sensor."""

    def test_ups_battery_sensor_creation(self) -> None:
        """Test UPS battery sensor entity creation."""
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
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

    def test_ups_battery_sensor_state(self) -> None:
        """Test UPS battery sensor returns correct charge level."""
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
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


class TestUPSLoadSensor:
    """Tests for UPS load sensor."""

    def test_ups_load_sensor_creation(self) -> None:
        """Test UPS load sensor entity creation."""
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
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

    def test_ups_load_sensor_state(self) -> None:
        """Test UPS load sensor returns correct load percentage."""
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
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

    def test_ups_load_sensor_attributes(self) -> None:
        """Test UPS load sensor has correct attributes."""
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
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


class TestUPSRuntimeSensor:
    """Tests for UPS runtime sensor."""

    def test_ups_runtime_sensor_creation(self) -> None:
        """Test UPS runtime sensor entity creation."""
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
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

    def test_ups_runtime_sensor_state(self) -> None:
        """Test UPS runtime sensor returns human-readable duration."""
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=3660),  # 1h 1m
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
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


class TestUPSPowerSensor:
    """Tests for UPS power consumption sensor."""

    def test_ups_power_sensor_creation(self) -> None:
        """Test UPS power sensor entity creation."""
        from homeassistant.const import UnitOfPower

        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
        )
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(ups_devices=[ups])

        sensor = UPSPowerSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
            ups=ups,
            ups_capacity_va=1000,
        )

        assert sensor.unique_id == "test-uuid_ups_ups:1_power"
        assert sensor.name == "UPS Power"
        assert sensor.device_class == SensorDeviceClass.POWER
        assert sensor.native_unit_of_measurement == UnitOfPower.WATT
        assert sensor.state_class == SensorStateClass.MEASUREMENT

    def test_ups_power_sensor_calculates_power(self) -> None:
        """Test UPS power sensor calculates power from load and capacity."""
        # Load: 20.5%, Capacity: 1000VA, Power Factor: 0.6
        # Expected: 20.5 / 100 * 1000 * 0.6 = 123W
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
        )
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(ups_devices=[ups])

        sensor = UPSPowerSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
            ups=ups,
            ups_capacity_va=1000,
        )

        assert sensor.native_value == 123.0

    def test_ups_power_sensor_unavailable_when_capacity_zero(self) -> None:
        """Test UPS power sensor is unavailable when capacity is 0."""
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
        )
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(ups_devices=[ups])
        coordinator.last_update_success = True

        sensor = UPSPowerSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
            ups=ups,
            ups_capacity_va=0,
        )

        assert sensor.available is False
        assert sensor.native_value is None

    def test_ups_power_sensor_attributes(self) -> None:
        """Test UPS power sensor has correct attributes."""
        ups = UPSDevice(
            id="ups:1",
            name="APC",
            status="Online",
            battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
            power=UPSPower(
                inputVoltage=120.0, outputVoltage=118.5, loadPercentage=20.5
            ),
        )
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(ups_devices=[ups])

        sensor = UPSPowerSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
            ups=ups,
            ups_capacity_va=1000,
        )

        attrs = sensor.extra_state_attributes
        assert attrs["model"] == "APC"
        assert attrs["status"] == "Online"
        assert attrs["ups_capacity_va"] == 1000
        assert attrs["power_factor"] == 0.6
        assert attrs["load_percentage"] == 20.5
        assert attrs["input_voltage"] == 120.0
        assert attrs["output_voltage"] == 118.5

    def test_ups_power_sensor_real_world_example(self) -> None:
        """Test UPS power sensor with real-world values from API."""
        # Based on actual UPS data: PR1000ELCDRT1U (1000VA), 12% load
        # Expected: 12 / 100 * 1000 * 0.6 = 72W
        ups = UPSDevice(
            id="PR1000ELCDRT1U",
            name="PR1000ELCDRT1U",
            status="ONLINE",
            battery=UPSBattery(chargeLevel=100, estimatedRuntime=6360),
            power=UPSPower(
                inputVoltage=236.0, outputVoltage=236.0, loadPercentage=12.0
            ),
        )
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data(ups_devices=[ups])

        sensor = UPSPowerSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
            ups=ups,
            ups_capacity_va=1000,
        )

        assert sensor.native_value == 72.0
