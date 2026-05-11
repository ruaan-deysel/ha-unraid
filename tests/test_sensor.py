"""Tests for Unraid sensor entities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import EntityCategory
from unraid_api.models import (
    ArrayCapacity,
    ArrayDisk,
    CapacityKilobytes,
    DockerContainer,
    NotificationOverview,
    NotificationOverviewCounts,
    ParityCheck,
    ParityHistoryEntry,
    Plugin,
    Registration,
    SensorType,
    Share,
    TemperatureMetrics,
    TemperatureReading,
    TemperatureSensorSummary,
    TemperatureStatus,
    TemperatureSummary,
    UPSBattery,
    UPSDevice,
    UPSPower,
)
from unraid_api.models import (
    TemperatureSensor as TemperatureSensorModel,
)

from custom_components.unraid.const import DOMAIN
from custom_components.unraid.coordinator import (
    UnraidInfraCoordinator,
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)
from custom_components.unraid.sensor import (
    ActiveNotificationsSensor,
    ApiVersionSensor,
    ArrayStateSensor,
    ArrayUsageSensor,
    ContainerUpdatesCountSensor,
    CpuPowerSensor,
    CpuSensor,
    DiskErrorCountSensor,
    DiskTemperatureSensor,
    DiskUsageSensor,
    DockerTotalCpuSensor,
    DockerTotalMemoryPercentSensor,
    InstalledPluginsSensor,
    LastParityCheckDateSensor,
    LastParityCheckErrorsSensor,
    NotificationArchivedTotalSensor,
    NotificationUnreadAlertSensor,
    NotificationUnreadInfoSensor,
    NotificationUnreadWarningSensor,
    ParityElapsedSensor,
    ParityEstimatedSensor,
    ParityProgressSensor,
    ParitySpeedSensor,
    RAMActiveSensor,
    RAMBuffCacheSensor,
    RAMUsageSensor,
    RAMUsedSensor,
    RegistrationExpirationSensor,
    RegistrationStateSensor,
    RegistrationTypeSensor,
    ShareUsageSensor,
    SwapFreeSensor,
    SwapUsageSensor,
    SwapUsedSensor,
    SystemTemperatureSensor,
    TemperatureAverageSensor,
    TemperatureSensor,
    UnraidSensorEntity,
    UnraidVersionSensor,
    UPSBatteryHealthSensor,
    UPSBatterySensor,
    UPSEnergySensor,
    UPSInputVoltageSensor,
    UPSLoadSensor,
    UPSOutputVoltageSensor,
    UPSPowerSensor,
    UPSRuntimeSensor,
    UPSStatusSensor,
    UptimeSensor,
    _compute_disk_usage_percent,
    _compute_disk_used_bytes,
    _is_valid_system_temp_sensor,
    format_bytes,
)
from tests.conftest import make_infra_data, make_storage_data, make_system_data

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
    assert format_bytes(1024) == "1 KB"
    assert format_bytes(2048) == "2 KB"


def test_formatbytes_megabytes() -> None:
    """Test format_bytes for MB values."""
    assert format_bytes(1048576) == "1 MB"


def test_formatbytes_gigabytes() -> None:
    """Test format_bytes for GB values."""
    assert format_bytes(1073741824) == "1 GB"


def test_formatbytes_terabytes() -> None:
    """Test format_bytes for TB values."""
    assert format_bytes(1099511627776) == "1 TB"


def test_formatbytes_petabytes() -> None:
    """Test format_bytes for PB values."""
    assert format_bytes(1125899906842624) == "1 PB"


def test_formatbytes_large_value() -> None:
    """Test format_bytes doesn't go beyond PB."""
    # 2000 PB should still display as PB
    assert "PB" in format_bytes(2 * 1125899906842624)


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
    assert sensor._attr_translation_key == "cpu_usage"
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


def test_cpusensor_extra_attributes_with_data() -> None:
    """Test CPU sensor returns CPU details when data is available."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    data = make_system_data()
    # Set CPU info on the ServerInfo
    data.info.cpu_brand = "AMD Ryzen 7"
    data.info.cpu_cores = 8
    data.info.cpu_threads = 16
    coordinator.data = data

    sensor = CpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = sensor.extra_state_attributes
    assert attrs["cpu_model"] == "AMD Ryzen 7"
    assert attrs["cpu_cores"] == 8
    assert attrs["cpu_threads"] == 16


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
    assert sensor._attr_translation_key == "cpu_power"
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
# RAM Used Sensor Tests
# =============================================================================


def test_ramusedsensor_creation() -> None:
    """Test RAM used sensor is created with correct attributes."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    # 32 GB total, 28 GB available -> 4 GB active (used by processes)
    coordinator.data = make_system_data(
        memory_total=34359738368,  # 32 GB
        memory_available=30064771072,  # 28 GB
    )

    sensor = RAMUsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_ram_used"
    assert sensor.device_class == SensorDeviceClass.DATA_SIZE
    assert sensor.native_unit_of_measurement == "B"
    assert sensor.suggested_unit_of_measurement == "GiB"
    assert sensor.state_class == SensorStateClass.MEASUREMENT


def test_ramusedsensor_state() -> None:
    """
    Test RAM used sensor returns active memory (total - available).

    This matches Unraid's display of System + Docker usage, excluding
    cached/buffered memory that can be reclaimed.
    """
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    # 32 GB total, 28 GB available -> 4 GB active
    coordinator.data = make_system_data(
        memory_total=34359738368,  # 32 GB
        memory_available=30064771072,  # ~28 GB
    )

    sensor = RAMUsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    # Expected: 32 GB - 28 GB = ~4 GB active memory
    expected = 34359738368 - 30064771072  # 4294967296 bytes = 4 GB
    assert sensor.native_value == expected


def test_ramusedsensor_none_data_native_value() -> None:
    """Test RAM used sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = RAMUsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_ramusedsensor_none_memory_values() -> None:
    """Test RAM used sensor returns None when memory values are None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        memory_total=None,
        memory_available=None,
    )

    sensor = RAMUsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


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
    """Test uptime sensor creation with TIMESTAMP device class."""
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
    assert sensor.device_class == SensorDeviceClass.TIMESTAMP
    assert sensor.state_class is None
    # No entity_category - uptime is a regular sensor (matches core HA integration)
    assert sensor.entity_category is None


def test_uptimesensor_state() -> None:
    """Test uptime sensor returns datetime (boot time)."""
    # Boot time as a specific datetime
    uptime_dt = datetime(2025, 12, 20, 9, 30, 0, tzinfo=UTC)
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(uptime=uptime_dt)

    sensor = UptimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    # Should return the datetime directly (HA formats as relative time)
    assert sensor.native_value == uptime_dt
    assert isinstance(sensor.native_value, datetime)


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
    assert sensor._attr_translation_key == "active_notifications"
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
# Notification Overview Sensor Tests
# =============================================================================


def _make_overview(
    unread_info: int = 0,
    unread_warning: int = 0,
    unread_alert: int = 0,
    unread_total: int = 0,
    archive_info: int = 0,
    archive_warning: int = 0,
    archive_alert: int = 0,
    archive_total: int = 0,
) -> NotificationOverview:
    """Create a NotificationOverview for testing."""
    return NotificationOverview(
        unread=NotificationOverviewCounts(
            info=unread_info,
            warning=unread_warning,
            alert=unread_alert,
            total=unread_total,
        ),
        archive=NotificationOverviewCounts(
            info=archive_info,
            warning=archive_warning,
            alert=archive_alert,
            total=archive_total,
        ),
    )


def test_notification_unread_info_creation() -> None:
    """Test unread info notifications sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    overview = _make_overview(unread_info=3)
    coordinator.data = make_system_data(notification_overview=overview)

    sensor = NotificationUnreadInfoSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_notifications_unread_info"
    assert sensor._attr_translation_key == "notifications_unread_info"
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.entity_registry_enabled_default is False


def test_notification_unread_info_state() -> None:
    """Test unread info notifications sensor returns correct count."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    overview = _make_overview(unread_info=7)
    coordinator.data = make_system_data(notification_overview=overview)

    sensor = NotificationUnreadInfoSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 7


def test_notification_unread_info_none_data() -> None:
    """Test unread info sensor returns None when data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = NotificationUnreadInfoSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_notification_unread_info_no_overview() -> None:
    """Test unread info sensor returns 0 when overview is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(notification_overview=None)

    sensor = NotificationUnreadInfoSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 0


def test_notification_unread_warning_state() -> None:
    """Test unread warning notifications sensor returns correct count."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    overview = _make_overview(unread_warning=2)
    coordinator.data = make_system_data(notification_overview=overview)

    sensor = NotificationUnreadWarningSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 2


def test_notification_unread_warning_creation() -> None:
    """Test unread warning notifications sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        notification_overview=_make_overview(unread_warning=1)
    )

    sensor = NotificationUnreadWarningSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_notifications_unread_warning"
    assert sensor.entity_registry_enabled_default is False


def test_notification_unread_warning_none_data() -> None:
    """Test unread warning sensor returns None when data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = NotificationUnreadWarningSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_notification_unread_alert_state() -> None:
    """Test unread alert notifications sensor returns correct count."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    overview = _make_overview(unread_alert=5)
    coordinator.data = make_system_data(notification_overview=overview)

    sensor = NotificationUnreadAlertSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 5


def test_notification_unread_alert_creation() -> None:
    """Test unread alert notifications sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        notification_overview=_make_overview(unread_alert=1)
    )

    sensor = NotificationUnreadAlertSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_notifications_unread_alert"
    assert sensor.entity_registry_enabled_default is False


def test_notification_unread_alert_none_data() -> None:
    """Test unread alert sensor returns None when data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = NotificationUnreadAlertSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_notification_archived_total_state() -> None:
    """Test archived total notifications sensor returns correct count."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    overview = _make_overview(archive_total=10)
    coordinator.data = make_system_data(notification_overview=overview)

    sensor = NotificationArchivedTotalSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 10


def test_notification_archived_total_creation() -> None:
    """Test archived total notifications sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        notification_overview=_make_overview(archive_total=3)
    )

    sensor = NotificationArchivedTotalSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_notifications_archived_total"
    assert sensor.entity_registry_enabled_default is False


def test_notification_archived_total_none_data() -> None:
    """Test archived total sensor returns None when data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = NotificationArchivedTotalSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_notification_archived_total_no_overview() -> None:
    """Test archived total sensor returns 0 when overview is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(notification_overview=None)

    sensor = NotificationArchivedTotalSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 0


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
    assert sensor._attr_translation_key == "array_state"
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
# ZFS Pool / Disk Usage Fallback Tests (Issue #161)
# =============================================================================


def test_compute_disk_usage_percent_normal() -> None:
    """Test _compute_disk_usage_percent with normal disk data."""
    disk = ArrayDisk(id="disk1", fsSize=1000, fsUsed=500, fsFree=500)
    assert _compute_disk_usage_percent(disk) == 50.0


def test_compute_disk_usage_percent_zfs_pool_real_data() -> None:
    """
    Test _compute_disk_usage_percent with real ZFS pool data.

    Real data from a live Unraid server: ZFS pool "garbage" returns
    fsUsed=860, fsSize=230988710, fsFree=230987850. The library's
    usage_percent calculates correctly from fsUsed/fsSize.
    """
    disk = ArrayDisk(
        id="cache:garbage",
        name="garbage",
        fsSize=230988710,
        fsUsed=860,
        fsFree=230987850,
        fsType="zfs",
    )
    expected = 860 / 230988710 * 100
    assert _compute_disk_usage_percent(disk) == pytest.approx(expected, rel=1e-5)


def test_compute_disk_usage_percent_fallback_fsused_zero() -> None:
    """
    Test _compute_disk_usage_percent falls back to fsSize-fsFree when fsUsed=0.

    Defensive fallback: if an API version ever reports fsUsed=0 while
    fsSize and fsFree are valid, usage should be calculated from the delta.
    """
    disk = ArrayDisk(
        id="cache:pool1",
        name="pool1",
        fsSize=9544371,
        fsUsed=0,
        fsFree=5558193,
        fsType="zfs",
    )
    expected = (9544371 - 5558193) / 9544371 * 100
    assert _compute_disk_usage_percent(disk) == pytest.approx(expected, rel=1e-5)


def test_compute_disk_usage_percent_fallback_fsused_none() -> None:
    """Test _compute_disk_usage_percent when fsUsed is None but fsFree available."""
    disk = ArrayDisk(
        id="cache:pool1",
        name="pool1",
        fsSize=2000000,
        fsUsed=None,
        fsFree=1200000,
        fsType="zfs",
    )
    expected = (2000000 - 1200000) / 2000000 * 100
    assert _compute_disk_usage_percent(disk) == pytest.approx(expected, rel=1e-5)


def test_compute_disk_usage_percent_no_data() -> None:
    """Test _compute_disk_usage_percent returns None with no filesystem data."""
    disk = ArrayDisk(id="disk1", fsSize=None, fsUsed=None, fsFree=None)
    assert _compute_disk_usage_percent(disk) is None


def test_compute_disk_usage_percent_empty_pool() -> None:
    """Test _compute_disk_usage_percent returns 0.0 for truly empty pool."""
    disk = ArrayDisk(
        id="cache:empty",
        name="empty",
        fsSize=1000000,
        fsUsed=0,
        fsFree=1000000,
        fsType="zfs",
    )
    # fsSize == fsFree means nothing used, usage is 0.0
    assert _compute_disk_usage_percent(disk) == 0.0


def test_compute_disk_used_bytes_normal() -> None:
    """Test _compute_disk_used_bytes with normal disk data."""
    disk = ArrayDisk(id="disk1", fsSize=1000, fsUsed=500, fsFree=500)
    assert _compute_disk_used_bytes(disk) == 500 * 1024


def test_compute_disk_used_bytes_zfs_pool_real_data() -> None:
    """Test _compute_disk_used_bytes with real ZFS pool data (fsUsed populated)."""
    disk = ArrayDisk(
        id="cache:garbage",
        name="garbage",
        fsSize=230988710,
        fsUsed=860,
        fsFree=230987850,
        fsType="zfs",
    )
    assert _compute_disk_used_bytes(disk) == 860 * 1024


def test_compute_disk_used_bytes_fallback_fsused_zero() -> None:
    """Test _compute_disk_used_bytes falls back when fsUsed=0."""
    disk = ArrayDisk(
        id="cache:pool1",
        name="pool1",
        fsSize=9544371,
        fsUsed=0,
        fsFree=5558193,
    )
    expected = (9544371 - 5558193) * 1024
    assert _compute_disk_used_bytes(disk) == expected


def test_compute_disk_used_bytes_fallback_fsused_none() -> None:
    """Test _compute_disk_used_bytes when fsUsed is None."""
    disk = ArrayDisk(
        id="cache:pool1",
        name="pool1",
        fsSize=2000000,
        fsUsed=None,
        fsFree=1200000,
    )
    expected = (2000000 - 1200000) * 1024
    assert _compute_disk_used_bytes(disk) == expected


def test_zfs_pool_disk_usage_sensor_real_data() -> None:
    """
    Test DiskUsageSensor with real ZFS pool data from a live server.

    Real data: ZFS pool "garbage" on device sdg.
    fsSize=230988710, fsUsed=860, fsFree=230987850
    The library correctly populates fsUsed for ZFS pools.
    """
    zfs_disk = ArrayDisk(
        id="cache:garbage",
        idx=0,
        device="sdg",
        name="garbage",
        type="Cache",
        size=234437632,
        fsSize=230988710,
        fsUsed=860,
        fsFree=230987850,
        fsType="zfs",
        temp=40,
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(caches=[zfs_disk])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=zfs_disk,
    )

    expected = 860 / 230988710 * 100
    assert sensor.native_value == pytest.approx(expected, rel=1e-5)


def test_zfs_pool_disk_usage_sensor_fallback() -> None:
    """
    Test DiskUsageSensor falls back to fsSize-fsFree when fsUsed=0.

    Defensive test for issue #161: some API versions or configurations
    may report fsUsed=0. The fallback ensures usage is still calculated.
    """
    zfs_disk = ArrayDisk(
        id="cache:pool1",
        idx=0,
        device="sdb",
        name="pool1",
        type="Cache",
        size=9544371,
        fsSize=9544371,
        fsUsed=0,
        fsFree=5558193,
        fsType="zfs",
        temp=40,
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(caches=[zfs_disk])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=zfs_disk,
    )

    # Should NOT be 0.0 — fallback calculates from fsSize - fsFree
    expected = (9544371 - 5558193) / 9544371 * 100
    assert sensor.native_value == pytest.approx(expected, rel=1e-5)
    assert sensor.native_value > 0


def test_zfs_pool_disk_usage_sensor_attributes() -> None:
    """Test DiskUsageSensor attributes for ZFS pool."""
    zfs_disk = ArrayDisk(
        id="cache:garbage",
        idx=0,
        device="sdg",
        name="garbage",
        type="Cache",
        size=234437632,
        fsSize=230988710,
        fsUsed=860,
        fsFree=230987850,
        fsType="zfs",
        temp=40,
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(caches=[zfs_disk])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=zfs_disk,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["used"] is not None
    assert attrs["filesystem"] == "zfs"
    assert attrs["type"] == "Cache"
    assert attrs["device"] == "sdg"


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
# Last Parity Check Sensor Tests
# =============================================================================


def test_last_parity_check_date_creation() -> None:
    """Test last parity check date sensor creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_history=[
            ParityHistoryEntry(
                date="2025-01-15T10:00:00Z",
                duration=3600,
                speed=150000000,
                status="OK",
                errors=0,
            )
        ]
    )

    sensor = LastParityCheckDateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_last_parity_check_date"
    assert sensor._attr_translation_key == "last_parity_check_date"
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert sensor.device_class == SensorDeviceClass.TIMESTAMP
    assert sensor.entity_registry_enabled_default is False


def test_last_parity_check_date_state() -> None:
    """Test last parity check date returns correct datetime."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_history=[
            ParityHistoryEntry(
                date="2025-01-15T10:00:00Z",
                duration=3600,
                speed=150000000,
                status="OK",
                errors=0,
            )
        ]
    )

    sensor = LastParityCheckDateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    value = sensor.native_value
    assert value is not None
    assert value.year == 2025
    assert value.month == 1
    assert value.day == 15


def test_last_parity_check_date_none_data() -> None:
    """Test last parity check date returns None when data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = LastParityCheckDateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_last_parity_check_date_empty_history() -> None:
    """Test last parity check date returns None with empty history."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_history=[])

    sensor = LastParityCheckDateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_last_parity_check_date_numeric_timestamp() -> None:
    """Test last parity check date handles numeric epoch timestamps."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_history=[
            ParityHistoryEntry(
                date=1705312800,  # epoch timestamp
                duration=7200,
                speed=100000000,
                status="OK",
                errors=0,
            )
        ]
    )

    sensor = LastParityCheckDateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    value = sensor.native_value
    assert value is not None
    assert value.year == 2024


def test_last_parity_check_date_extra_attributes() -> None:
    """Test last parity check date returns history details as attributes."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_history=[
            ParityHistoryEntry(
                date="2025-01-15T10:00:00Z",
                duration=5400,
                speed=150000000,
                status="OK",
                errors=2,
            )
        ]
    )

    sensor = LastParityCheckDateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = sensor.extra_state_attributes
    assert attrs["duration_seconds"] == 5400
    assert attrs["duration"] == "1 hour 30 minutes"
    assert attrs["speed"] == 150000000
    assert attrs["status"] == "OK"
    assert attrs["errors"] == 2


def test_last_parity_check_date_attributes_empty() -> None:
    """Test last parity check date returns empty attrs with no history."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_history=[])

    sensor = LastParityCheckDateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.extra_state_attributes == {}


def test_last_parity_check_errors_creation() -> None:
    """Test last parity check errors sensor creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_history=[ParityHistoryEntry(date="2025-01-15", errors=3)]
    )

    sensor = LastParityCheckErrorsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_last_parity_check_errors"
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.entity_registry_enabled_default is False


def test_last_parity_check_errors_state() -> None:
    """Test last parity check errors returns correct count."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_history=[ParityHistoryEntry(date="2025-01-15", errors=5)]
    )

    sensor = LastParityCheckErrorsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 5


def test_last_parity_check_errors_none_data() -> None:
    """Test last parity check errors returns None when data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = LastParityCheckErrorsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_last_parity_check_errors_empty_history() -> None:
    """Test last parity check errors returns None with empty history."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_history=[])

    sensor = LastParityCheckErrorsSensor(
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
    assert sensor._attr_translation_key == "disk_health"
    assert sensor._attr_translation_placeholders == {"name": "disk1"}


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
    assert sensor._attr_translation_key == "array_started"


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
    assert sensor._attr_translation_key == "parity_check_running"


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
    assert sensor._attr_translation_key == "parity_valid"


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
    assert sensor._attr_translation_key == "ups_battery"
    assert sensor._attr_translation_placeholders == {"name": "APC"}
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


def test_upsbatterysensor_extra_attributes_valid_ups() -> None:
    """Test UPS battery sensor returns model and status when UPS found."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS 1000",
        status="ONLINE",
        battery=UPSBattery(chargeLevel=95),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatterySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["model"] == "APC UPS 1000"
    assert attrs["status"] == "ONLINE"


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
    assert sensor._attr_translation_key == "ups_load"
    assert sensor._attr_translation_placeholders == {"name": "APC"}
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
    assert sensor._attr_translation_key == "ups_runtime"
    assert sensor._attr_translation_placeholders == {"name": "APC"}


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
    assert sensor._attr_translation_key == "ups_power"
    assert sensor._attr_translation_placeholders == {"name": "APC"}
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
    """Test UPS power sensor unavailable without nominal power or API currentPower."""
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


def test_upspowersensor_available_when_nominal_power_set() -> None:
    """Test UPS power sensor is available when nominal power is configured."""
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
        ups_nominal_power=800,  # Non-zero
    )

    assert sensor.available is True


def test_upspowersensor_attributes() -> None:
    """Test UPS power sensor has correct attributes (fallback calculation mode)."""
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
    assert attrs["power_source"] == "calculated"


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


def test_upspowersensor_prefers_api_current_power() -> None:
    """Test UPS power sensor prefers currentPower from API (v1.7.0+)."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        battery=UPSBattery(chargeLevel=95, estimatedRuntime=1200),
        power=UPSPower(
            inputVoltage=120.0,
            outputVoltage=118.5,
            loadPercentage=20.5,
            currentPower=150.0,
            nominalPower=800,
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
        ups_nominal_power=800,
    )

    # Should use API currentPower (150.0), not calculated (164.0)
    assert sensor.native_value == 150.0


def test_upspowersensor_available_with_api_current_power_no_nominal() -> None:
    """Test UPS power sensor available when API provides currentPower."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        power=UPSPower(currentPower=100.0),
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
        ups_nominal_power=0,
    )

    assert sensor.available is True
    assert sensor.native_value == 100.0


def test_upspowersensor_attributes_with_api_power() -> None:
    """Test UPS power sensor attributes when API provides currentPower."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        status="Online",
        power=UPSPower(
            inputVoltage=120.0,
            outputVoltage=118.5,
            loadPercentage=20.5,
            currentPower=150.0,
            nominalPower=800,
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
        ups_nominal_power=600,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["model"] == "APC"
    assert attrs["power_source"] == "api"
    # nominalPower from API takes precedence over user config
    assert attrs["nominal_power_watts"] == 800


# =============================================================================
# UPS Energy Sensor Tests
# =============================================================================


def test_upsenergysensor_creation() -> None:
    """Test UPS energy sensor creation."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=25.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,
    )

    assert sensor.unique_id == "test-uuid_ups_ups:1_energy"
    assert sensor._attr_translation_key == "ups_energy"
    assert sensor._attr_translation_placeholders == {"name": "APC UPS"}
    assert sensor.device_class == SensorDeviceClass.ENERGY
    assert sensor.state_class == SensorStateClass.TOTAL_INCREASING
    assert sensor.native_unit_of_measurement == "kWh"


def test_upsenergysensor_unavailable_when_nominal_power_zero() -> None:
    """Test UPS energy sensor is unavailable when nominal power is 0."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(loadPercentage=20.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    coordinator.last_update_success = True

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=0,
    )

    assert sensor.available is False


def test_upsenergysensor_tracks_energy_accumulation() -> None:
    """Test UPS energy sensor accumulates energy over time."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(loadPercentage=50.0),  # 50% of 1000W = 500W
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=1000,  # 1000W nominal
    )

    # First coordinator update - initializes tracking
    sensor._update_energy()
    assert sensor.native_value == 0.0

    # After first update, _last_power_watts and _last_update_time are set
    assert sensor._last_power_watts == 500.0  # 50% of 1000W

    # Manually simulate time passing and another update
    sensor._last_update_time = datetime.now(UTC) - timedelta(hours=1)
    # Now update again - should show energy accumulated over 1 hour at 500W
    sensor._update_energy()
    energy = sensor.native_value
    # 500W for 1 hour = 0.5 kWh
    assert energy is not None
    assert 0.4 <= energy <= 0.6  # Allow some tolerance for timing


def test_upsenergysensor_none_data() -> None:
    """Test UPS energy sensor returns None when coordinator data is None."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(loadPercentage=20.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,
    )

    assert sensor.native_value == 0.0  # Energy starts at 0
    assert sensor._last_power_watts is None  # Can't calculate power


def test_upsenergysensor_attributes() -> None:
    """Test UPS energy sensor extra state attributes."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS Pro",
        power=UPSPower(loadPercentage=25.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,
    )

    # Trigger an update to populate _last_power_watts
    sensor._update_energy()

    attrs = sensor.extra_state_attributes
    assert attrs["model"] == "APC UPS Pro"
    assert attrs["nominal_power_watts"] == 800
    assert attrs["current_power_watts"] == 200.0  # 25% of 800W
    assert "last_updated" in attrs


# =============================================================================
# UPS Input Voltage Sensor Tests
# =============================================================================


def test_upsinputvoltagesensor_creation() -> None:
    """Test UPS input voltage sensor entity creation."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(inputVoltage=120.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSInputVoltageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor._attr_unique_id == "test-uuid_ups_ups:1_input_voltage"
    assert sensor._attr_translation_key == "ups_input_voltage"
    assert sensor._attr_device_class == SensorDeviceClass.VOLTAGE
    assert sensor._attr_native_unit_of_measurement == "V"
    assert sensor._attr_entity_registry_enabled_default is False


def test_upsinputvoltagesensor_state() -> None:
    """Test UPS input voltage sensor returns correct value."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(inputVoltage=121.3),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSInputVoltageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == 121.3


def test_upsinputvoltagesensor_none_data() -> None:
    """Test UPS input voltage sensor returns None when no data."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSInputVoltageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


def test_upsinputvoltagesensor_none_voltage() -> None:
    """Test UPS input voltage sensor returns None when voltage is not available."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(inputVoltage=None),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSInputVoltageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


# =============================================================================
# UPS Output Voltage Sensor Tests
# =============================================================================


def test_upsoutputvoltagesensor_creation() -> None:
    """Test UPS output voltage sensor entity creation."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(outputVoltage=118.2),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSOutputVoltageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor._attr_unique_id == "test-uuid_ups_ups:1_output_voltage"
    assert sensor._attr_translation_key == "ups_output_voltage"
    assert sensor._attr_device_class == SensorDeviceClass.VOLTAGE
    assert sensor._attr_native_unit_of_measurement == "V"
    assert sensor._attr_entity_registry_enabled_default is False


def test_upsoutputvoltagesensor_state() -> None:
    """Test UPS output voltage sensor returns correct value."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(outputVoltage=118.5),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSOutputVoltageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == 118.5


def test_upsoutputvoltagesensor_none_data() -> None:
    """Test UPS output voltage sensor returns None when no data."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSOutputVoltageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


def test_upsoutputvoltagesensor_none_voltage() -> None:
    """Test UPS output voltage sensor returns None when voltage is not available."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(outputVoltage=None),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSOutputVoltageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


# =============================================================================
# UPS Battery Health Sensor Tests
# =============================================================================


def test_upsbatteryhealthsensor_creation() -> None:
    """Test UPS battery health sensor entity creation."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        battery=UPSBattery(health="GOOD"),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatteryHealthSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor._attr_unique_id == "test-uuid_ups_ups:1_battery_health"
    assert sensor._attr_translation_key == "ups_battery_health"
    assert sensor._attr_entity_registry_enabled_default is False


def test_upsbatteryhealthsensor_state() -> None:
    """Test UPS battery health sensor returns correct value."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        battery=UPSBattery(health="GOOD"),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatteryHealthSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == "GOOD"


def test_upsbatteryhealthsensor_replace_needed() -> None:
    """Test UPS battery health sensor with REPLACE BATTERY status."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        battery=UPSBattery(health="REPLACE BATTERY"),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatteryHealthSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == "REPLACE BATTERY"


def test_upsbatteryhealthsensor_none_data() -> None:
    """Test UPS battery health sensor returns None when no data."""
    ups = UPSDevice(id="ups:1", name="APC")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UPSBatteryHealthSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


def test_upsbatteryhealthsensor_none_health() -> None:
    """Test UPS battery health sensor returns None when health is not available."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        battery=UPSBattery(health=None),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatteryHealthSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value is None


# =============================================================================
# UPS Battery Sensor - Health Attribute Tests
# =============================================================================


def test_upsbatterysensor_extra_attributes_includes_health() -> None:
    """Test UPS battery sensor includes health in extra_state_attributes."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        status="ONLINE",
        battery=UPSBattery(chargeLevel=95, health="GOOD"),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatterySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["model"] == "APC UPS"
    assert attrs["status"] == "ONLINE"
    assert attrs["health"] == "GOOD"


def test_upsbatterysensor_extra_attributes_no_health() -> None:
    """Test UPS battery sensor omits health when not available."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        status="ONLINE",
        battery=UPSBattery(chargeLevel=95, health=None),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatterySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["model"] == "APC UPS"
    assert attrs["status"] == "ONLINE"
    assert "health" not in attrs


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
    assert sensor._attr_translation_key == "share_usage"
    assert sensor._attr_translation_placeholders == {"name": "appdata"}
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
        infra_coordinator=MagicMock(),
        server_info={
            "uuid": "test-uuid",
            "name": "tower",
            "manufacturer": "Supermicro",
            "model": "X11",
        },
        websocket_manager=MagicMock(),
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Should create system sensors (CPU, RAM, RAM used, Temp, Uptime, etc.)
    assert len(added_entities) > 0

    # Check some expected sensor types exist
    entity_types = {type(e).__name__ for e in added_entities}
    assert "CpuSensor" in entity_types
    assert "RAMUsageSensor" in entity_types
    assert "RAMUsedSensor" in entity_types
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
        infra_coordinator=MagicMock(),
        server_info={"uuid": "test-uuid", "name": "tower"},
        websocket_manager=MagicMock(),
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
    """Test setup creates disk usage and temperature sensors for data disks."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    disk = ArrayDisk(id="disk:1", name="Disk 1", status="DISK_OK", temp=45)

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
        infra_coordinator=MagicMock(),
        server_info={"uuid": "test-uuid", "name": "tower"},
        websocket_manager=MagicMock(),
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    entity_types = {type(e).__name__ for e in added_entities}
    assert "DiskUsageSensor" in entity_types
    assert "DiskTemperatureSensor" in entity_types


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
        infra_coordinator=MagicMock(),
        server_info={"uuid": "test-uuid", "name": "tower"},
        websocket_manager=MagicMock(),
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
        infra_coordinator=MagicMock(),
        server_info={"uuid": "test-uuid", "name": "tower"},
        websocket_manager=MagicMock(),
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    entity_types = {type(e).__name__ for e in added_entities}
    assert "ShareUsageSensor" in entity_types


@pytest.mark.asyncio
async def test_asyncsetupentry_creates_cache_disk_sensors(hass) -> None:
    """Test setup creates disk usage and temperature sensors for cache disks."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    cache_disk = ArrayDisk(id="cache:1", name="Cache", type="CACHE", temp=38)

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
        infra_coordinator=MagicMock(),
        server_info={"uuid": "test-uuid", "name": "tower"},
        websocket_manager=MagicMock(),
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Find the DiskUsageSensor for the cache disk
    cache_usage_sensors = [
        e
        for e in added_entities
        if isinstance(e, DiskUsageSensor) and "cache:1" in e.unique_id
    ]
    assert len(cache_usage_sensors) == 1

    # Find the DiskTemperatureSensor for the cache disk
    cache_temp_sensors = [
        e
        for e in added_entities
        if isinstance(e, DiskTemperatureSensor) and "cache:1" in e.unique_id
    ]
    assert len(cache_temp_sensors) == 1


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
        infra_coordinator=MagicMock(),
        server_info={"uuid": "test-uuid", "name": "tower"},
        websocket_manager=MagicMock(),
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
        infra_coordinator=MagicMock(),
        server_info={"uuid": "test-uuid", "name": "tower"},
        websocket_manager=MagicMock(),
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


@pytest.mark.asyncio
async def test_asyncsetupentry_creates_parity_disk_temperature_sensors(hass) -> None:
    """Test setup creates temperature sensors for parity disks (issue #136)."""
    from custom_components.unraid import UnraidRuntimeData
    from custom_components.unraid.sensor import async_setup_entry

    # Parity disks don't have usage stats, only temperature
    parity_disk = ArrayDisk(
        id="parity:1", name="Parity", type="PARITY", temp=42, status="DISK_OK"
    )

    system_coordinator = MagicMock(spec=UnraidSystemCoordinator)
    system_coordinator.data = make_system_data()

    storage_coordinator = MagicMock(spec=UnraidStorageCoordinator)
    storage_coordinator.data = make_storage_data(parities=[parity_disk])

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.options = {}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        infra_coordinator=MagicMock(),
        server_info={"uuid": "test-uuid", "name": "tower"},
        websocket_manager=MagicMock(),
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Find the DiskTemperatureSensor for the parity disk
    parity_temp_sensors = [
        e
        for e in added_entities
        if isinstance(e, DiskTemperatureSensor) and "parity:1" in e.unique_id
    ]
    assert len(parity_temp_sensors) == 1
    assert parity_temp_sensors[0].native_value == 42

    # Parity disks should NOT have usage sensors (no filesystem)
    parity_usage_sensors = [
        e
        for e in added_entities
        if isinstance(e, DiskUsageSensor) and "parity:1" in e.unique_id
    ]
    assert len(parity_usage_sensors) == 0


# =============================================================================
# Additional Coverage Tests - Extra State Attributes with None Data
# =============================================================================


def test_cpuusagesensor_extra_attributes_none_data() -> None:
    """Test CPU extra_state_attributes returns empty dict when data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = CpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.extra_state_attributes == {}


def test_arrayusagesensor_extra_attributes_none_data() -> None:
    """Test array usage extra_state_attributes returns empty when data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = ArrayUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.extra_state_attributes == {}


def test_disktemperaturesensor_extra_attributes_none_disk() -> None:
    """Test disk temp extra_state_attributes returns empty when disk not found."""
    disk = ArrayDisk(id="disk:1", name="Disk 1", type="DATA", temp=45, status="DISK_OK")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    # Now remove the disk from coordinator data
    coordinator.data = make_storage_data(disks=[])

    # Verify attributes return empty dict when disk not found
    assert sensor.extra_state_attributes == {}


def test_disktemperaturesensor_extra_attributes_valid_disk() -> None:
    """Test disk temp extra_state_attributes returns disk info when found."""
    disk = ArrayDisk(
        id="disk:1",
        name="Disk 1",
        type="DATA",
        temp=45,
        status="DISK_OK",
        device="sda",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["spinning"] is True
    assert attrs["status"] == "DISK_OK"
    assert attrs["device"] == "sda"
    assert attrs["type"] == "DATA"


def test_diskusagesensor_returns_none_when_disk_missing() -> None:
    """Test disk usage sensor returns None when disk is missing from data."""
    disk = ArrayDisk(
        id="disk:1",
        name="Disk 1",
        type="DATA",
        total_bytes=1000000000,
        used_bytes=500000000,
        status="DISK_OK",
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    sensor = DiskUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    # Remove disk from data
    coordinator.data = make_storage_data(disks=[])

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_upschargesensor_extra_attributes_none_ups() -> None:
    """Test UPS battery extra_state_attributes returns empty when UPS not found."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        battery=UPSBattery(chargeLevel=75),
        status="ONLINE",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSBatterySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    # Remove UPS from data
    coordinator.data = make_system_data(ups_devices=[])

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_upsloadsensor_extra_attributes_none_ups() -> None:
    """Test UPS load extra_state_attributes returns empty when UPS not found."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=25.0),
        status="ONLINE",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSLoadSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    # Remove UPS from data
    coordinator.data = make_system_data(ups_devices=[])

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_upsruntimesensor_returns_none_when_ups_missing() -> None:
    """Test UPS runtime sensor returns None when UPS is missing from data."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        battery=UPSBattery(estimatedRuntime=3600),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    # Remove UPS from data
    coordinator.data = make_system_data(ups_devices=[])

    assert sensor.native_value is None


def test_upspowersensor_extra_attributes_none_ups() -> None:
    """Test UPS power sensor extra_state_attributes when UPS is not found."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=25.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,
    )

    # Remove UPS from data
    coordinator.data = make_system_data(ups_devices=[])

    assert sensor.native_value is None


def test_upsenergysensor_extra_attributes_returns_dict() -> None:
    """Test UPS energy extra_state_attributes returns dict with model and power."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=25.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,
    )

    attrs = sensor.extra_state_attributes
    assert "model" in attrs
    assert "nominal_power_watts" in attrs
    assert attrs["nominal_power_watts"] == 800


def test_shareusagesensor_returns_none_when_share_missing() -> None:
    """Test share usage sensor returns None when share is missing from data."""
    share = Share(id="share:1", name="appdata", size_bytes=5000000, used_bytes=2500000)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(shares=[share])

    sensor = ShareUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        share=share,
    )

    # Remove share from data
    coordinator.data = make_storage_data(shares=[])

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_upsruntimesensor_formats_hours_and_minutes() -> None:
    """Test UPS runtime sensor formats hours and minutes correctly."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        battery=UPSBattery(estimatedRuntime=7380),  # 2 hours 3 minutes
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == "2 hours 3 minutes"


def test_upsruntimesensor_formats_singular_units() -> None:
    """Test UPS runtime sensor formats singular hour/minute correctly."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
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


def test_upsruntimesensor_formats_zero_minutes() -> None:
    """Test UPS runtime sensor with exactly 1 hour (0 minutes)."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        battery=UPSBattery(estimatedRuntime=3600),  # Exactly 1 hour
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSRuntimeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
    )

    assert sensor.native_value == "1 hour"


def test_upsloadsensor_extra_attributes_with_voltage() -> None:
    """Test UPS load sensor extra_state_attributes includes voltage when available."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=25.0, inputVoltage=120.5, outputVoltage=118.2),
        status="ONLINE",
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
    assert attrs["input_voltage"] == 120.5
    assert attrs["output_voltage"] == 118.2


def test_upspowersensor_extra_attributes_with_va_capacity() -> None:
    """Test UPS power sensor extra_state_attributes includes VA capacity when set."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=25.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSPowerSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,
        ups_capacity_va=1000,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["ups_capacity_va"] == 1000
    assert attrs["nominal_power_watts"] == 800


@pytest.mark.asyncio
async def test_upsenergysensor_async_added_to_hass_restores_state(hass) -> None:
    """Test UPS energy sensor restores state on add to hass."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=50.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test-entry-id"

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=1000,
    )

    # Set entity_id for hass state tracking
    sensor._attr_has_entity_name = True
    sensor.hass = hass
    sensor.entity_id = "sensor.test_ups_energy"

    # Mock the state restoration with valid last state
    mock_state = MagicMock()
    mock_state.state = "12.345"

    with patch.object(sensor, "async_get_last_state", return_value=mock_state):
        await sensor.async_added_to_hass()

    # Verify state was restored
    assert sensor._total_energy_kwh == pytest.approx(12.345)


@pytest.mark.asyncio
async def test_upsenergysensor_async_added_to_hass_handles_invalid_state(hass) -> None:
    """Test UPS energy sensor handles invalid restored state gracefully."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=50.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test-entry-id"

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=1000,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_ups_energy"

    # Mock the state restoration with invalid state
    mock_state = MagicMock()
    mock_state.state = "not_a_number"

    with patch.object(sensor, "async_get_last_state", return_value=mock_state):
        await sensor.async_added_to_hass()

    # Verify state remains at default 0.0
    assert sensor._total_energy_kwh == 0.0


@pytest.mark.asyncio
async def test_upsenergysensor_async_added_to_hass_skips_unknown_state(hass) -> None:
    """Test UPS energy sensor skips restoration when state is unknown."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=50.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test-entry-id"

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=1000,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_ups_energy"

    # Mock the state restoration with "unknown" state
    mock_state = MagicMock()
    mock_state.state = "unknown"

    with patch.object(sensor, "async_get_last_state", return_value=mock_state):
        await sensor.async_added_to_hass()

    # Verify state remains at default 0.0
    assert sensor._total_energy_kwh == 0.0


@pytest.mark.asyncio
async def test_upsenergysensor_async_added_to_hass_no_previous_state(hass) -> None:
    """Test UPS energy sensor handles no previous state."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=50.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test-entry-id"

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=1000,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_ups_energy"

    with patch.object(sensor, "async_get_last_state", return_value=None):
        await sensor.async_added_to_hass()

    # Verify state remains at default 0.0
    assert sensor._total_energy_kwh == 0.0


# =============================================================================
# Registration Sensor Tests
# =============================================================================


def test_registration_type_sensor_init() -> None:
    """Test RegistrationTypeSensor initialization."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    sensor = RegistrationTypeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_registration_type"
    assert sensor._attr_translation_key == "registration_type"
    assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert sensor._attr_entity_registry_enabled_default is False


def test_registration_type_sensor_value() -> None:
    """Test RegistrationTypeSensor returns license type."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    reg = Registration(id="key-id", type="Pro", state="valid")
    coordinator.data = make_infra_data(registration=reg)
    sensor = RegistrationTypeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == "Pro"


def test_registration_type_sensor_none_data() -> None:
    """Test RegistrationTypeSensor returns None when no data."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = None
    sensor = RegistrationTypeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_registration_type_sensor_none_registration() -> None:
    """Test RegistrationTypeSensor returns None when registration is None."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = make_infra_data(registration=None)
    sensor = RegistrationTypeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_registration_type_sensor_extra_attributes() -> None:
    """Test RegistrationTypeSensor extra state attributes."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    reg = Registration(
        id="key-id",
        type="Pro",
        state="valid",
        expiration="2026-01-01",
        updateExpiration="2025-06-01",
    )
    coordinator.data = make_infra_data(registration=reg)
    sensor = RegistrationTypeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert attrs["state"] == "valid"
    assert attrs["expiration"] == "2026-01-01"
    assert attrs["update_expiration"] == "2025-06-01"


def test_registration_type_sensor_extra_attributes_minimal() -> None:
    """Test RegistrationTypeSensor extra attributes with minimal data."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    reg = Registration(id="key-id", type="Basic")
    coordinator.data = make_infra_data(registration=reg)
    sensor = RegistrationTypeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert attrs == {}


def test_registration_type_sensor_extra_attributes_no_data() -> None:
    """Test RegistrationTypeSensor extra attributes when no data."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = None
    sensor = RegistrationTypeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


def test_registration_state_sensor_init() -> None:
    """Test RegistrationStateSensor initialization."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    sensor = RegistrationStateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_registration_state"
    assert sensor._attr_translation_key == "registration_state"
    assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert sensor._attr_entity_registry_enabled_default is False


def test_registration_state_sensor_value() -> None:
    """Test RegistrationStateSensor returns license state."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    reg = Registration(id="key-id", type="Pro", state="valid")
    coordinator.data = make_infra_data(registration=reg)
    sensor = RegistrationStateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == "valid"


def test_registration_state_sensor_none_data() -> None:
    """Test RegistrationStateSensor returns None when no data."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = None
    sensor = RegistrationStateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_registration_state_sensor_none_registration() -> None:
    """Test RegistrationStateSensor returns None when registration is None."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = make_infra_data(registration=None)
    sensor = RegistrationStateSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


# =============================================================================
# InstalledPluginsSensor Tests
# =============================================================================


def test_installed_plugins_sensor_init() -> None:
    """Test InstalledPluginsSensor initialization."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    sensor = InstalledPluginsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_installed_plugins"
    assert sensor._attr_translation_key == "installed_plugins"
    assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert sensor._attr_entity_registry_enabled_default is False
    assert sensor._attr_state_class == SensorStateClass.MEASUREMENT


def test_installed_plugins_sensor_value() -> None:
    """Test InstalledPluginsSensor returns plugin count."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    plugins = [
        Plugin(name="dynamix", version="2024.01.01"),
        Plugin(name="unassigned.devices", version="2024.02.15"),
        Plugin(name="compose.manager", version="2024.03.10"),
    ]
    coordinator.data = make_infra_data(plugins=plugins)
    sensor = InstalledPluginsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == 3


def test_installed_plugins_sensor_no_plugins() -> None:
    """Test InstalledPluginsSensor returns 0 when no plugins."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = make_infra_data(plugins=[])
    sensor = InstalledPluginsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == 0


def test_installed_plugins_sensor_none_data() -> None:
    """Test InstalledPluginsSensor returns None when no data."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = None
    sensor = InstalledPluginsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_installed_plugins_sensor_extra_attributes() -> None:
    """Test InstalledPluginsSensor extra state attributes."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    plugins = [
        Plugin(name="dynamix", version="2024.01.01"),
        Plugin(name="unassigned.devices", version="2024.02.15"),
    ]
    coordinator.data = make_infra_data(plugins=plugins)
    sensor = InstalledPluginsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert len(attrs["plugins"]) == 2
    assert attrs["plugins"][0] == {"name": "dynamix", "version": "2024.01.01"}
    assert attrs["plugins"][1] == {
        "name": "unassigned.devices",
        "version": "2024.02.15",
    }


def test_installed_plugins_sensor_extra_attributes_no_data() -> None:
    """Test InstalledPluginsSensor extra attributes when no data."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = None
    sensor = InstalledPluginsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


def test_installed_plugins_sensor_extra_attributes_empty() -> None:
    """Test InstalledPluginsSensor extra attributes when no plugins."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = make_infra_data(plugins=[])
    sensor = InstalledPluginsSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# Swap Usage Sensor Tests
# =============================================================================


def test_swapusagesensor_creation() -> None:
    """Test swap usage sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        swap_percent=25.0, swap_total=8000000000, swap_used=2000000000
    )

    sensor = SwapUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_swap_usage"
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == "%"
    assert sensor.translation_key == "swap_usage"
    assert sensor.entity_registry_enabled_default is False


def test_swapusagesensor_state() -> None:
    """Test swap usage sensor returns correct percentage."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(swap_percent=42.5)

    sensor = SwapUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 42.5


def test_swapusagesensor_attributes() -> None:
    """Test swap usage sensor returns human-readable attributes."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        swap_percent=25.0,
        swap_total=8589934592,  # 8 GB
        swap_used=2147483648,  # 2 GB
    )

    sensor = SwapUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = sensor.extra_state_attributes
    assert "total" in attrs
    assert "used" in attrs
    assert "GB" in attrs["total"]


def test_swapusagesensor_none_data() -> None:
    """Test swap usage sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = SwapUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_swapusagesensor_none_swap_values() -> None:
    """Test swap usage sensor attributes when swap values are None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(
        swap_percent=None, swap_total=None, swap_used=None
    )

    sensor = SwapUsageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


# =============================================================================
# Swap Used Sensor Tests
# =============================================================================


def test_swapusedsensor_creation() -> None:
    """Test swap used sensor is created with correct attributes."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(swap_used=4000000000)

    sensor = SwapUsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_swap_used"
    assert sensor.device_class == SensorDeviceClass.DATA_SIZE
    assert sensor.native_unit_of_measurement == "B"
    assert sensor.suggested_unit_of_measurement == "GiB"
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.entity_registry_enabled_default is False


def test_swapusedsensor_state() -> None:
    """Test swap used sensor returns correct bytes value."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(swap_used=2147483648)

    sensor = SwapUsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 2147483648


def test_swapusedsensor_none_data() -> None:
    """Test swap used sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = SwapUsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_swapusedsensor_none_swap_used() -> None:
    """Test swap used sensor returns None when swap_used is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(swap_used=None)

    sensor = SwapUsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# Container Stats Sensors — REMOVED in v1.7.0
# =============================================================================
# ContainerCpuSensor, ContainerMemoryUsageSensor, ContainerMemoryPercentSensor
# were removed because container.stats was removed from DockerContainer in
# unraid-api v1.7.0. Stats are now only available via WebSocket subscriptions.


# =============================================================================
# Parity Speed Sensor Tests
# =============================================================================


def test_parityspeedsensor_creation() -> None:
    """Test parity speed sensor creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(speed="104857600", progress=50.0)
    )

    sensor = ParitySpeedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_parity_speed"
    assert sensor.native_unit_of_measurement == "MiB/s"
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.translation_key == "parity_speed"
    assert sensor.entity_registry_enabled_default is False
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC


def test_parityspeedsensor_state() -> None:
    """Test parity speed sensor returns speed in MiB/s."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    # 100 MiB/s = 104857600 bytes/s
    coordinator.data = make_storage_data(parity_status=ParityCheck(speed="104857600"))

    sensor = ParitySpeedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 100.0


def test_parityspeedsensor_attributes() -> None:
    """Test parity speed sensor returns elapsed/estimated attributes."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(
            speed="52428800", elapsed=3600, estimated=7200, progress=50.0
        )
    )

    sensor = ParitySpeedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = sensor.extra_state_attributes
    assert attrs["elapsed_seconds"] == 3600
    assert attrs["estimated_seconds"] == 7200
    assert attrs["progress"] == 50.0


def test_parityspeedsensor_none_data() -> None:
    """Test parity speed sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    sensor = ParitySpeedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_parityspeedsensor_none_speed() -> None:
    """Test parity speed sensor returns None when speed is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(speed=None))

    sensor = ParitySpeedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_parityspeedsensor_attributes_no_data() -> None:
    """Test parity speed sensor returns empty attributes when no parity status."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=None)

    sensor = ParitySpeedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.extra_state_attributes == {}


# =============================================================================
# Unraid Version Sensor Tests
# =============================================================================


def test_unraidversionsensor_creation() -> None:
    """Test Unraid version sensor creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data()

    sensor = UnraidVersionSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_unraid_version"
    assert sensor.translation_key == "unraid_version"
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC


def test_unraidversionsensor_state() -> None:
    """Test Unraid version sensor returns the version string."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data()
    from unraid_api.models import ServerInfo

    coordinator.data.info = ServerInfo(
        uuid="test-uuid", hostname="tower", sw_version="7.2.2"
    )

    sensor = UnraidVersionSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == "7.2.2"


def test_unraidversionsensor_attributes() -> None:
    """Test Unraid version sensor returns api_version and architecture."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data()
    from unraid_api.models import ServerInfo

    coordinator.data.info = ServerInfo(
        uuid="test-uuid",
        hostname="tower",
        sw_version="7.2.2",
        api_version="4.31.1",
        os_arch="x86_64",
    )

    sensor = UnraidVersionSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = sensor.extra_state_attributes
    assert attrs["api_version"] == "4.31.1"
    assert attrs["architecture"] == "x86_64"


def test_unraidversionsensor_none_data() -> None:
    """Test Unraid version sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = UnraidVersionSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


def test_unraidversionsensor_attributes_minimal() -> None:
    """Test Unraid version sensor with minimal info (no optional fields)."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data()
    from unraid_api.models import ServerInfo

    coordinator.data.info = ServerInfo(
        uuid="test-uuid", hostname="tower", sw_version="7.2.2"
    )

    sensor = UnraidVersionSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    # No api_version or os_arch in ServerInfo
    assert sensor.extra_state_attributes == {}


# =============================================================================
# API Version Sensor Tests
# =============================================================================


def test_apiversionsensor_creation() -> None:
    """Test API version sensor entity creation."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data()

    sensor = ApiVersionSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_api_version"
    assert sensor.translation_key == "api_version"
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC


def test_apiversionsensor_state() -> None:
    """Test API version sensor returns the API version string."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data()
    from unraid_api.models import ServerInfo

    coordinator.data.info = ServerInfo(
        uuid="test-uuid",
        hostname="tower",
        sw_version="7.2.4",
        api_version="4.30.1",
    )

    sensor = ApiVersionSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == "4.30.1"


def test_apiversionsensor_none_data() -> None:
    """Test API version sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = ApiVersionSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_apiversionsensor_none_info() -> None:
    """Test API version sensor returns None when info is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data()
    coordinator.data.info = None

    sensor = ApiVersionSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# UPS Energy Sensor — Auto-Detection Tests
# =============================================================================


def test_upsenergysensor_api_nominal_power_preferred() -> None:
    """Test UPS energy sensor prefers API nominal power over user config."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(loadPercentage=50.0, nominalPower=900),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,  # User config value
    )

    # API value (900) should be preferred over user config (800)
    assert sensor._get_effective_nominal_power() == 900


def test_upsenergysensor_falls_back_to_user_config() -> None:
    """Test energy sensor falls back to user config."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(loadPercentage=50.0),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,
    )

    assert sensor._get_effective_nominal_power() == 800


def test_upsenergysensor_available_with_api_nominal_power() -> None:
    """Test sensor available when API provides nominal power."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(loadPercentage=20.0, nominalPower=900),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    coordinator.last_update_success = True

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=0,  # User didn't configure
    )

    assert sensor.available is True


def test_upsenergysensor_prefers_current_power_from_api() -> None:
    """Test UPS energy sensor prefers direct currentPower from API."""
    ups = UPSDevice(
        id="ups:1",
        name="APC",
        power=UPSPower(loadPercentage=50.0, currentPower=350.0, nominalPower=900),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,
    )

    # Should use currentPower (350.0), not load% * nominal (50% * 900 = 450)
    assert sensor._calculate_current_power() == 350.0


def test_upsenergysensor_attributes_with_api_nominal() -> None:
    """Test UPS energy sensor attributes reflect API nominal power."""
    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        power=UPSPower(loadPercentage=25.0, nominalPower=1000),
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])

    sensor = UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        ups=ups,
        ups_nominal_power=800,  # User config, should be overridden by API
    )

    sensor._update_energy()
    attrs = sensor.extra_state_attributes
    assert attrs["nominal_power_watts"] == 1000  # From API, not user config


# =============================================================================
# ParityElapsedSensor Tests
# =============================================================================


def test_parity_elapsed_sensor_init() -> None:
    """Test ParityElapsedSensor initialization."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    sensor = ParityElapsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_parity_elapsed"
    assert sensor._attr_translation_key == "parity_elapsed"
    assert sensor._attr_device_class == SensorDeviceClass.DURATION
    assert sensor._attr_native_unit_of_measurement == "s"
    assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert sensor._attr_entity_registry_enabled_default is False


def test_parity_elapsed_sensor_value() -> None:
    """Test ParityElapsedSensor returns elapsed seconds."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(running=True, elapsed=3600, estimated=7200)
    )
    sensor = ParityElapsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == 3600


def test_parity_elapsed_sensor_none_data() -> None:
    """Test ParityElapsedSensor returns None when no data."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None
    sensor = ParityElapsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_parity_elapsed_sensor_none_parity() -> None:
    """Test ParityElapsedSensor returns None when parity_status is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    data = MagicMock()
    data.parity_status = None
    coordinator.data = data
    sensor = ParityElapsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_parity_elapsed_sensor_none_elapsed() -> None:
    """Test ParityElapsedSensor returns 0 when elapsed is None (no check running)."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(running=False))
    sensor = ParityElapsedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == 0


# =============================================================================
# ParityEstimatedSensor Tests
# =============================================================================


def test_parity_estimated_sensor_init() -> None:
    """Test ParityEstimatedSensor initialization."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    sensor = ParityEstimatedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_parity_estimated"
    assert sensor._attr_translation_key == "parity_estimated"
    assert sensor._attr_device_class == SensorDeviceClass.DURATION
    assert sensor._attr_native_unit_of_measurement == "s"
    assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert sensor._attr_entity_registry_enabled_default is False


def test_parity_estimated_sensor_value() -> None:
    """Test ParityEstimatedSensor returns estimated seconds."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_status=ParityCheck(running=True, elapsed=3600, estimated=7200)
    )
    sensor = ParityEstimatedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == 7200


def test_parity_estimated_sensor_none_data() -> None:
    """Test ParityEstimatedSensor returns None when no data."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None
    sensor = ParityEstimatedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_parity_estimated_sensor_none_estimated() -> None:
    """Test ParityEstimatedSensor returns 0 when estimated is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(running=False))
    sensor = ParityEstimatedSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == 0


# =============================================================================
# UPSStatusSensor Tests
# =============================================================================


def test_ups_status_sensor_init() -> None:
    """Test UPSStatusSensor initialization."""
    ups = UPSDevice(id="ups:1", name="APC UPS", status="OL")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    sensor = UPSStatusSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=ups,
    )
    assert sensor._attr_unique_id == "test-uuid_ups_ups:1_status"
    assert sensor._attr_translation_key == "ups_status"
    assert sensor._attr_translation_placeholders == {"name": "APC UPS"}


def test_ups_status_sensor_value_online() -> None:
    """Test UPSStatusSensor returns OL for online."""
    ups = UPSDevice(id="ups:1", name="APC UPS", status="OL")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    sensor = UPSStatusSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=ups,
    )
    assert sensor.native_value == "OL"


def test_ups_status_sensor_value_on_battery() -> None:
    """Test UPSStatusSensor returns OB for on battery."""
    ups = UPSDevice(id="ups:1", name="APC UPS", status="OB")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    sensor = UPSStatusSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=ups,
    )
    assert sensor.native_value == "OB"


def test_ups_status_sensor_value_on_battery_low() -> None:
    """Test UPSStatusSensor returns OB LB for low battery."""
    ups = UPSDevice(id="ups:1", name="APC UPS", status="OB LB")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    sensor = UPSStatusSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=ups,
    )
    assert sensor.native_value == "OB LB"


def test_ups_status_sensor_none_data() -> None:
    """Test UPSStatusSensor returns None when no data."""
    ups = UPSDevice(id="ups:1", name="APC UPS", status="OL")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None
    sensor = UPSStatusSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=ups,
    )
    assert sensor.native_value is None


def test_ups_status_sensor_ups_not_found() -> None:
    """Test UPSStatusSensor returns None when UPS removed."""
    ups = UPSDevice(id="ups:1", name="APC UPS", status="OL")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[])
    sensor = UPSStatusSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=ups,
    )
    assert sensor.native_value is None


# =============================================================================
# ContainerUpdatesCountSensor Tests
# =============================================================================


def test_container_updates_count_sensor_init() -> None:
    """Test ContainerUpdatesCountSensor initialization."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    sensor = ContainerUpdatesCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_container_updates_count"
    assert sensor._attr_translation_key == "container_updates_count"
    assert sensor._attr_state_class == SensorStateClass.MEASUREMENT


def test_container_updates_count_sensor_value() -> None:
    """Test ContainerUpdatesCountSensor returns count of updatable containers."""
    containers = [
        DockerContainer(id="c1", name="nginx", isUpdateAvailable=True),
        DockerContainer(id="c2", name="plex", isUpdateAvailable=False),
        DockerContainer(id="c3", name="sonarr", isUpdateAvailable=True),
        DockerContainer(id="c4", name="radarr", isUpdateAvailable=None),
    ]
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=containers)
    sensor = ContainerUpdatesCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == 2


def test_container_updates_count_sensor_zero() -> None:
    """Test ContainerUpdatesCountSensor returns 0 when no updates."""
    containers = [
        DockerContainer(id="c1", name="nginx", isUpdateAvailable=False),
        DockerContainer(id="c2", name="plex", isUpdateAvailable=False),
    ]
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=containers)
    sensor = ContainerUpdatesCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == 0


def test_container_updates_count_sensor_none_data() -> None:
    """Test ContainerUpdatesCountSensor returns None when no data."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None
    sensor = ContainerUpdatesCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_container_updates_count_sensor_extra_attributes() -> None:
    """Test ContainerUpdatesCountSensor extra attributes list updatable containers."""
    containers = [
        DockerContainer(id="c1", name="/nginx", isUpdateAvailable=True),
        DockerContainer(id="c2", name="plex", isUpdateAvailable=False),
        DockerContainer(id="c3", name="/sonarr", isUpdateAvailable=True),
    ]
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=containers)
    sensor = ContainerUpdatesCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert "containers" in attrs
    assert "nginx" in attrs["containers"]
    assert "sonarr" in attrs["containers"]
    assert len(attrs["containers"]) == 2


def test_container_updates_count_sensor_extra_attributes_none() -> None:
    """Test ContainerUpdatesCountSensor extra attributes when no data."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None
    sensor = ContainerUpdatesCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


def test_container_updates_count_sensor_extra_attributes_empty() -> None:
    """Test ContainerUpdatesCountSensor extra attributes when no updates."""
    containers = [
        DockerContainer(id="c1", name="nginx", isUpdateAvailable=False),
    ]
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=containers)
    sensor = ContainerUpdatesCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# RegistrationExpirationSensor Tests
# =============================================================================


def test_registration_expiration_sensor_init() -> None:
    """Test RegistrationExpirationSensor initialization."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    sensor = RegistrationExpirationSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_registration_expiration"
    assert sensor._attr_translation_key == "registration_expiration"
    assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert sensor._attr_entity_registry_enabled_default is False


def test_registration_expiration_sensor_value() -> None:
    """Test RegistrationExpirationSensor returns expiration date."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    reg = Registration(
        id="key-id",
        type="Pro",
        state="valid",
        expiration="2026-12-31",
    )
    coordinator.data = make_infra_data(registration=reg)
    sensor = RegistrationExpirationSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value == "2026-12-31"


def test_registration_expiration_sensor_none_data() -> None:
    """Test RegistrationExpirationSensor returns None when no data."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = None
    sensor = RegistrationExpirationSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_registration_expiration_sensor_none_registration() -> None:
    """Test RegistrationExpirationSensor returns None when no registration."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    coordinator.data = make_infra_data(registration=None)
    sensor = RegistrationExpirationSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.native_value is None


def test_registration_expiration_sensor_extra_attributes() -> None:
    """Test RegistrationExpirationSensor extra attributes."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    reg = Registration(
        id="key-id",
        type="Pro",
        state="valid",
        expiration="2026-12-31",
        updateExpiration="2026-06-30",
    )
    coordinator.data = make_infra_data(registration=reg)
    sensor = RegistrationExpirationSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert attrs["update_expiration"] == "2026-06-30"


def test_registration_expiration_sensor_extra_attributes_no_update_exp() -> None:
    """Test RegistrationExpirationSensor extra attributes without update expiration."""
    coordinator = MagicMock(spec=UnraidInfraCoordinator)
    reg = Registration(
        id="key-id",
        type="Basic",
        state="valid",
        expiration="2026-12-31",
    )
    coordinator.data = make_infra_data(registration=reg)
    sensor = RegistrationExpirationSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# DiskErrorCountSensor Tests
# =============================================================================


def test_disk_error_count_sensor_init() -> None:
    """Test DiskErrorCountSensor initialization."""
    disk = ArrayDisk(id="disk1", name="Disk 1")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    sensor = DiskErrorCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=disk,
    )
    assert sensor._attr_unique_id == "test-uuid_disk_disk1_errors"
    assert sensor._attr_translation_key == "disk_error_count"
    assert sensor._attr_state_class == SensorStateClass.TOTAL_INCREASING
    assert sensor._attr_native_unit_of_measurement == "errors"
    assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert sensor._attr_entity_registry_enabled_default is False
    assert sensor._attr_translation_placeholders == {"name": "Disk 1"}


def test_disk_error_count_sensor_value() -> None:
    """Test DiskErrorCountSensor returns error count."""
    disk = ArrayDisk(id="disk1", name="Disk 1", numErrors=5)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    sensor = DiskErrorCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=disk,
    )
    assert sensor.native_value == 5


def test_disk_error_count_sensor_zero() -> None:
    """Test DiskErrorCountSensor returns 0 for no errors."""
    disk = ArrayDisk(id="disk1", name="Disk 1", numErrors=0)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    sensor = DiskErrorCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=disk,
    )
    assert sensor.native_value == 0


def test_disk_error_count_sensor_none_data() -> None:
    """Test DiskErrorCountSensor returns None when no data."""
    disk = ArrayDisk(id="disk1", name="Disk 1")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None
    sensor = DiskErrorCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=disk,
    )
    assert sensor.native_value is None


def test_disk_error_count_sensor_disk_not_found() -> None:
    """Test DiskErrorCountSensor returns None when disk not in data."""
    disk = ArrayDisk(id="disk1", name="Disk 1")
    other_disk = ArrayDisk(id="disk2", name="Disk 2", numErrors=3)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[other_disk])
    sensor = DiskErrorCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=disk,
    )
    assert sensor.native_value is None


def test_disk_error_count_sensor_parity_disk() -> None:
    """Test DiskErrorCountSensor works for parity disks."""
    disk = ArrayDisk(id="parity1", name="Parity", numErrors=2)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parities=[disk])
    sensor = DiskErrorCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=disk,
    )
    assert sensor.native_value == 2


def test_disk_error_count_sensor_cache_disk() -> None:
    """Test DiskErrorCountSensor works for cache disks."""
    disk = ArrayDisk(id="cache1", name="Cache", numErrors=1)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(caches=[disk])
    sensor = DiskErrorCountSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=disk,
    )
    assert sensor.native_value == 1


# =============================================================================
# Docker Aggregate Sensor Tests
# =============================================================================


def _make_ws_manager(**kwargs: Any) -> Any:
    """Create a mock WebSocket manager with container stats."""
    from unittest.mock import MagicMock

    from unraid_api.models import DockerContainerStats

    from custom_components.unraid.websocket import ContainerStatsSnapshot

    ws = MagicMock()
    stats = kwargs.get("stats", {})
    snapshot = ContainerStatsSnapshot()
    for cid, s in stats.items():
        snapshot.stats[cid] = DockerContainerStats(**s)
    ws.container_stats = snapshot
    return ws


def test_docker_total_cpu_sensor_init() -> None:
    """Test DockerTotalCpuSensor initialization."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager()
    sensor = DockerTotalCpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    assert sensor._attr_translation_key == "docker_total_cpu"
    assert sensor._attr_native_unit_of_measurement == "%"
    assert sensor._attr_state_class == SensorStateClass.MEASUREMENT
    assert sensor.unique_id == "test-uuid_docker_total_cpu"


def test_docker_total_cpu_sensor_value() -> None:
    """Test DockerTotalCpuSensor sums container CPU usage."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager(
        stats={
            "c1": {"id": "c1", "cpuPercent": 25.5},
            "c2": {"id": "c2", "cpuPercent": 10.3},
            "c3": {"id": "c3", "cpuPercent": 5.0},
        }
    )
    sensor = DockerTotalCpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    assert sensor.native_value == 40.8


def test_docker_total_cpu_sensor_empty_stats() -> None:
    """Test DockerTotalCpuSensor returns None when no stats."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager()
    sensor = DockerTotalCpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    assert sensor.native_value is None


def test_docker_total_cpu_sensor_some_none() -> None:
    """Test DockerTotalCpuSensor skips containers with None cpuPercent."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager(
        stats={
            "c1": {"id": "c1", "cpuPercent": 10.0},
            "c2": {"id": "c2", "cpuPercent": None},
        }
    )
    sensor = DockerTotalCpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    assert sensor.native_value == 10.0


def test_docker_total_cpu_sensor_extra_attributes() -> None:
    """Test DockerTotalCpuSensor extra attributes include container count."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager(
        stats={
            "c1": {"id": "c1", "cpuPercent": 5.0},
            "c2": {"id": "c2", "cpuPercent": 3.0},
        }
    )
    sensor = DockerTotalCpuSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    attrs = sensor.extra_state_attributes
    assert attrs["container_count"] == 2


def test_docker_total_memory_percent_sensor_init() -> None:
    """Test DockerTotalMemoryPercentSensor initialization."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager()
    sensor = DockerTotalMemoryPercentSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    assert sensor._attr_translation_key == "docker_total_memory_percent"
    assert sensor._attr_native_unit_of_measurement == "%"
    assert sensor._attr_state_class == SensorStateClass.MEASUREMENT
    assert sensor.unique_id == "test-uuid_docker_total_memory_pct"


def test_docker_total_memory_percent_sensor_value() -> None:
    """Test DockerTotalMemoryPercentSensor sums container memory percentages."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager(
        stats={
            "c1": {"id": "c1", "memPercent": 15.2},
            "c2": {"id": "c2", "memPercent": 8.5},
            "c3": {"id": "c3", "memPercent": 3.1},
        }
    )
    sensor = DockerTotalMemoryPercentSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    assert sensor.native_value == 26.8


def test_docker_total_memory_percent_sensor_empty_stats() -> None:
    """Test DockerTotalMemoryPercentSensor returns None when no stats."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager()
    sensor = DockerTotalMemoryPercentSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    assert sensor.native_value is None


def test_docker_total_memory_percent_sensor_some_none() -> None:
    """Test DockerTotalMemoryPercentSensor skips containers with None memPercent."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager(
        stats={
            "c1": {"id": "c1", "memPercent": 12.0},
            "c2": {"id": "c2", "memPercent": None},
        }
    )
    sensor = DockerTotalMemoryPercentSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    assert sensor.native_value == 12.0


def test_docker_total_memory_percent_sensor_extra_attributes() -> None:
    """Test DockerTotalMemoryPercentSensor extra attributes include container count."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    ws = _make_ws_manager(
        stats={
            "c1": {"id": "c1", "memPercent": 5.0},
            "c2": {"id": "c2", "memPercent": 3.0},
            "c3": {"id": "c3", "memPercent": 2.0},
        }
    )
    sensor = DockerTotalMemoryPercentSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ws_manager=ws,
    )
    attrs = sensor.extra_state_attributes
    assert attrs["container_count"] == 3


# =============================================================================
# RAM Buffer/Cache Sensor Tests
# =============================================================================


def test_rambuffcachesensor_creation() -> None:
    """Test RAM buffer/cache sensor is created with correct attributes."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(memory_buffcache=2000000000)

    sensor = RAMBuffCacheSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_ram_buffcache"
    assert sensor.device_class == SensorDeviceClass.DATA_SIZE
    assert sensor.native_unit_of_measurement == "B"
    assert sensor.suggested_unit_of_measurement == "GiB"
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.entity_registry_enabled_default is False


def test_rambuffcachesensor_state() -> None:
    """Test RAM buffer/cache sensor returns correct bytes value."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(memory_buffcache=3221225472)

    sensor = RAMBuffCacheSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 3221225472


def test_rambuffcachesensor_none_data() -> None:
    """Test RAM buffer/cache sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = RAMBuffCacheSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_rambuffcachesensor_none_value() -> None:
    """Test RAM buffer/cache sensor returns None when buffcache is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(memory_buffcache=None)

    sensor = RAMBuffCacheSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# RAM Active Sensor Tests
# =============================================================================


def test_ramactivesensor_creation() -> None:
    """Test RAM active sensor is created with correct attributes."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(memory_active=4000000000)

    sensor = RAMActiveSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_ram_active"
    assert sensor.device_class == SensorDeviceClass.DATA_SIZE
    assert sensor.native_unit_of_measurement == "B"
    assert sensor.suggested_unit_of_measurement == "GiB"
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.entity_registry_enabled_default is False


def test_ramactivesensor_state() -> None:
    """Test RAM active sensor returns correct bytes value."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(memory_active=2147483648)

    sensor = RAMActiveSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 2147483648


def test_ramactivesensor_none_data() -> None:
    """Test RAM active sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = RAMActiveSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# Swap Free Sensor Tests
# =============================================================================


def test_swapfreesensor_creation() -> None:
    """Test swap free sensor is created with correct attributes."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(swap_free=1000000000)

    sensor = SwapFreeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_swap_free"
    assert sensor.device_class == SensorDeviceClass.DATA_SIZE
    assert sensor.native_unit_of_measurement == "B"
    assert sensor.suggested_unit_of_measurement == "GiB"
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.entity_registry_enabled_default is False


def test_swapfreesensor_state() -> None:
    """Test swap free sensor returns correct bytes value."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(swap_free=4294967296)

    sensor = SwapFreeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 4294967296


def test_swapfreesensor_none_data() -> None:
    """Test swap free sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = SwapFreeSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


# =============================================================================
# System Temperature Sensor Tests
# =============================================================================


def _make_temp_sensor(
    sensor_id: str = "mb_temp1",
    name: str = "Motherboard Temp",
    sensor_type: SensorType | str | None = SensorType.MOTHERBOARD,
    location: str | None = "Socket 0",
    temperature: float = 42.0,
    warning: float | None = 85.0,
    critical: float | None = 95.0,
    status: TemperatureStatus = TemperatureStatus.NORMAL,
) -> TemperatureSensorModel:
    """Create a TemperatureSensor model for testing."""
    return TemperatureSensorModel(
        id=sensor_id,
        name=name,
        type=sensor_type,
        location=location,
        current=TemperatureReading(value=temperature, unit="CELSIUS", status=status),
        min=TemperatureReading(value=35.0, unit="CELSIUS"),
        max=TemperatureReading(value=55.0, unit="CELSIUS"),
        warning=warning,
        critical=critical,
        history=[],
    )


def _make_temp_metrics(
    sensors: list[TemperatureSensorModel] | None = None,
    average: float | None = 45.0,
    warning_count: int | None = 0,
    critical_count: int | None = 0,
) -> TemperatureMetrics:
    """Create a TemperatureMetrics model for testing."""
    if sensors is None:
        sensors = [_make_temp_sensor()]
    return TemperatureMetrics(
        id="temp_metrics",
        summary=TemperatureSummary(
            average=average,
            warningCount=warning_count,
            criticalCount=critical_count,
            hottest=TemperatureSensorSummary(
                name=sensors[0].name if sensors else None,
                current=TemperatureReading(value=55.0, unit="CELSIUS"),
            )
            if sensors
            else None,
            coolest=TemperatureSensorSummary(
                name=sensors[-1].name if sensors else None,
                current=TemperatureReading(value=35.0, unit="CELSIUS"),
            )
            if sensors
            else None,
        ),
        sensors=sensors,
    )


def test_systemtemperaturesensor_creation() -> None:
    """Test system temperature sensor is created with correct attributes."""
    temp_sensor = _make_temp_sensor()
    temp_metrics = _make_temp_metrics(sensors=[temp_sensor])
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=temp_metrics)

    sensor = SystemTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        sensor=temp_sensor,
    )

    assert sensor.unique_id == "test-uuid_temp_mb_temp1"
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.native_unit_of_measurement == "°C"
    assert sensor.state_class == SensorStateClass.MEASUREMENT


def test_systemtemperaturesensor_value() -> None:
    """Test system temperature sensor returns correct temperature."""
    temp_sensor = _make_temp_sensor(temperature=52.5)
    temp_metrics = _make_temp_metrics(sensors=[temp_sensor])
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=temp_metrics)

    sensor = SystemTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        sensor=temp_sensor,
    )

    assert sensor.native_value == 52.5


def test_systemtemperaturesensor_none_data() -> None:
    """Test system temperature sensor returns None when coordinator data is None."""
    temp_sensor = _make_temp_sensor()
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = SystemTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        sensor=temp_sensor,
    )

    assert sensor.native_value is None


def test_systemtemperaturesensor_none_temperature() -> None:
    """Test system temperature sensor returns None when temperature metrics absent."""
    temp_sensor = _make_temp_sensor()
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=None)

    sensor = SystemTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        sensor=temp_sensor,
    )

    assert sensor.native_value is None


def test_systemtemperaturesensor_sensor_not_found() -> None:
    """Test system temperature sensor returns None when sensor removed from data."""
    temp_sensor = _make_temp_sensor(sensor_id="removed_sensor")
    other_sensor = _make_temp_sensor(sensor_id="different_sensor")
    temp_metrics = _make_temp_metrics(sensors=[other_sensor])
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=temp_metrics)

    sensor = SystemTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        sensor=temp_sensor,
    )

    assert sensor.native_value is None


def test_systemtemperaturesensor_extra_attributes() -> None:
    """Test system temperature sensor returns correct extra state attributes."""
    temp_sensor = _make_temp_sensor(
        sensor_type=SensorType.CHIPSET,
        location="PCH",
        warning=80.0,
        critical=100.0,
        status=TemperatureStatus.NORMAL,
    )
    temp_metrics = _make_temp_metrics(sensors=[temp_sensor])
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=temp_metrics)

    sensor = SystemTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        sensor=temp_sensor,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["sensor_type"] == "CHIPSET"
    assert attrs["location"] == "PCH"
    assert attrs["warning_threshold"] == 80.0
    assert attrs["critical_threshold"] == 100.0
    assert attrs["status"] == "NORMAL"
    assert attrs["min_recorded"] == 35.0
    assert attrs["max_recorded"] == 55.0


def test_systemtemperaturesensor_extra_attributes_none() -> None:
    """Test system temperature sensor returns empty dict when data is None."""
    temp_sensor = _make_temp_sensor()
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = SystemTemperatureSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        sensor=temp_sensor,
    )

    assert sensor.extra_state_attributes == {}


def test_systemtemperaturesensor_translation_key() -> None:
    """Test system temperature sensor translation key matches sensor type."""
    for stype in [
        SensorType.MOTHERBOARD,
        SensorType.CHIPSET,
        SensorType.AMBIENT,
        SensorType.GPU,
        SensorType.VRM,
    ]:
        temp_sensor = _make_temp_sensor(sensor_type=stype)
        coordinator = MagicMock(spec=UnraidSystemCoordinator)
        coordinator.data = make_system_data()

        sensor = SystemTemperatureSensor(
            coordinator=coordinator,
            server_uuid="test-uuid",
            server_name="test-server",
            sensor=temp_sensor,
        )

        expected_key = f"temperature_{str(stype).lower()}"
        assert sensor.translation_key == expected_key


# =============================================================================
# Temperature Average Sensor Tests
# =============================================================================


def test_temperatureaveragesensor_creation() -> None:
    """Test temperature average sensor is created with correct attributes."""
    temp_metrics = _make_temp_metrics(average=48.5)
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=temp_metrics)

    sensor = TemperatureAverageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.unique_id == "test-uuid_temperature_average"
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.native_unit_of_measurement == "°C"
    assert sensor.state_class == SensorStateClass.MEASUREMENT


def test_temperatureaveragesensor_value() -> None:
    """Test temperature average sensor computes average from valid sensors."""
    sensors = [
        _make_temp_sensor(sensor_id="s1", temperature=50.0),
        _make_temp_sensor(sensor_id="s2", temperature=54.6),
    ]
    temp_metrics = _make_temp_metrics(sensors=sensors, average=530830.3)
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=temp_metrics)

    sensor = TemperatureAverageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 52.3


def test_temperatureaveragesensor_none_data() -> None:
    """Test temperature average sensor returns None when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = TemperatureAverageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_temperatureaveragesensor_none_temperature() -> None:
    """Test temperature average sensor returns None when no temperature data."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=None)

    sensor = TemperatureAverageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value is None


def test_temperatureaveragesensor_none_summary() -> None:
    """Test temperature average sensor does not require summary when sensors exist."""
    sensors = [_make_temp_sensor(sensor_id="s1", temperature=47.0)]
    temp_metrics = TemperatureMetrics(id="temp", summary=None, sensors=sensors)
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=temp_metrics)

    sensor = TemperatureAverageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.native_value == 47.0


def test_is_valid_system_temp_sensor_rejects_auxtin_and_in_channels() -> None:
    """Test bogus motherboard AUXTIN/inX channels are filtered out."""
    assert (
        _is_valid_system_temp_sensor(
            _make_temp_sensor(name="nct6793-isa-0290 AUXTIN0", temperature=36.0)
        )
        is False
    )
    assert (
        _is_valid_system_temp_sensor(
            _make_temp_sensor(name="nct6793-isa-0290 in7", temperature=3.4)
        )
        is False
    )


def test_is_valid_system_temp_sensor_rejects_out_of_range_temps() -> None:
    """Test extreme/near-zero values are filtered."""
    assert (
        _is_valid_system_temp_sensor(
            _make_temp_sensor(name="SYSTIN", temperature=115.0)
        )
        is False
    )
    assert (
        _is_valid_system_temp_sensor(_make_temp_sensor(name="in5", temperature=0.1))
        is False
    )


def test_temperatureaveragesensor_extra_attributes() -> None:
    """Test temperature average sensor returns correct extra attributes."""
    sensors = [
        _make_temp_sensor(
            sensor_id="s1",
            name="Sensor 1",
            temperature=55.0,
            status=TemperatureStatus.WARNING,
        ),
        _make_temp_sensor(sensor_id="s2", name="Sensor 2", temperature=42.0),
        _make_temp_sensor(sensor_id="s3", name="Sensor 3", temperature=35.0),
    ]
    temp_metrics = _make_temp_metrics(
        sensors=sensors, warning_count=1, critical_count=0
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(temperature=temp_metrics)

    sensor = TemperatureAverageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = sensor.extra_state_attributes
    assert attrs["sensor_count"] == 3
    assert attrs["warning_count"] == 1
    assert attrs["critical_count"] == 0
    assert attrs["hottest_sensor"] == "Sensor 1"
    assert attrs["coolest_sensor"] == "Sensor 3"


def test_temperatureaveragesensor_extra_attributes_none() -> None:
    """Test temperature average sensor returns empty dict when no data."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = TemperatureAverageSensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert sensor.extra_state_attributes == {}
