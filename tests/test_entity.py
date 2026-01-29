"""Tests for base entity classes."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.unraid.const import DOMAIN
from custom_components.unraid.coordinator import (
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)
from custom_components.unraid.entity import (
    UnraidBaseEntity,
    UnraidEntity,
    UnraidEntityDescription,
)
from tests.conftest import make_storage_data, make_system_data

# =============================================================================
# UnraidEntityDescription Tests
# =============================================================================


def test_entity_description_defaults() -> None:
    """Test entity description has sensible defaults."""
    description = UnraidEntityDescription(
        key="test_entity",
    )

    assert description.key == "test_entity"
    # Default functions should return True
    assert description.available_fn(None) is True
    assert description.supported_fn(None) is True


def test_entity_description_custom_available_fn() -> None:
    """Test entity description with custom available function."""

    # Custom function that checks for specific data
    def custom_available(data) -> bool:
        if data is None:
            return False
        return hasattr(data, "metrics") and data.metrics is not None

    description = UnraidEntityDescription(
        key="test_entity",
        available_fn=custom_available,
    )

    # Test with None data
    assert description.available_fn(None) is False

    # Test with valid data
    data = make_system_data(cpu_percent=50.0)
    assert description.available_fn(data) is True


def test_entity_description_custom_supported_fn() -> None:
    """Test entity description with custom supported function."""

    # Custom function that checks for UPS support
    def ups_supported(data) -> bool:
        return data is not None and len(data.ups_devices) > 0

    description = UnraidEntityDescription(
        key="ups_sensor",
        supported_fn=ups_supported,
    )

    # Test with no UPS devices
    data = make_system_data()
    assert description.supported_fn(data) is False


# =============================================================================
# UnraidBaseEntity Tests
# =============================================================================


def test_base_entity_creation() -> None:
    """Test base entity creation with all parameters."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True

    entity = UnraidBaseEntity(
        coordinator=coordinator,
        server_uuid="test-uuid-123",
        server_name="tower",
        resource_id="cpu_usage",
        name="CPU Usage",
        server_info={
            "manufacturer": "Lime Technology",
            "model": "Unraid 7.2.0",
            "serial_number": "ABC123",
            "sw_version": "7.2.0",
            "hw_version": "1.0",
            "configuration_url": "https://tower.local",
        },
    )

    assert entity.unique_id == "test-uuid-123_cpu_usage"
    assert entity.name == "CPU Usage"
    assert entity._attr_has_entity_name is True

    # Check device info
    device_info = entity.device_info
    assert device_info["identifiers"] == {(DOMAIN, "test-uuid-123")}
    assert device_info["name"] == "tower"
    assert device_info["manufacturer"] == "Lime Technology"
    assert device_info["model"] == "Unraid 7.2.0"
    assert device_info["serial_number"] == "ABC123"
    assert device_info["sw_version"] == "7.2.0"
    assert device_info["hw_version"] == "1.0"
    assert device_info["configuration_url"] == "https://tower.local"


def test_base_entity_creation_without_server_info() -> None:
    """Test base entity creation without server_info."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True

    entity = UnraidBaseEntity(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        resource_id="sensor",
        name="Test Sensor",
        server_info=None,
    )

    # Device info should have None for optional fields
    device_info = entity.device_info
    assert device_info["identifiers"] == {(DOMAIN, "test-uuid")}
    assert device_info["name"] == "tower"
    assert device_info["manufacturer"] is None
    assert device_info["model"] is None


def test_base_entity_availability_success() -> None:
    """Test entity availability when coordinator update succeeds."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True

    entity = UnraidBaseEntity(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        resource_id="sensor",
        name="Test",
    )

    assert entity.available is True


def test_base_entity_availability_failure() -> None:
    """Test entity availability when coordinator update fails."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = False

    entity = UnraidBaseEntity(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        resource_id="sensor",
        name="Test",
    )

    assert entity.available is False


# =============================================================================
# UnraidEntity Tests (with EntityDescription)
# =============================================================================


def test_unraid_entity_creation() -> None:
    """Test UnraidEntity creation with description."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True
    coordinator.data = make_system_data(cpu_percent=50.0)

    description = UnraidEntityDescription(
        key="cpu_usage",
        name="CPU Usage",
    )

    entity = UnraidEntity(
        coordinator=coordinator,
        entity_description=description,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert entity.unique_id == "test-uuid_cpu_usage"
    assert entity.name == "CPU Usage"
    assert entity.entity_description == description


def test_unraid_entity_uses_key_as_name_fallback() -> None:
    """Test UnraidEntity correctly handles description.name being UNDEFINED."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True
    coordinator.data = make_system_data()

    # When name is explicitly set to None, it falls back to key
    description = UnraidEntityDescription(
        key="some_sensor_key",
        name=None,  # Explicitly set to None to test fallback
    )

    entity = UnraidEntity(
        coordinator=coordinator,
        entity_description=description,
        server_uuid="test-uuid",
        server_name="tower",
    )

    # When name is None, the code falls back to using the key
    assert entity._attr_name == "some_sensor_key"


def test_unraid_entity_availability_with_custom_fn() -> None:
    """Test UnraidEntity availability with custom available_fn."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True
    coordinator.data = make_system_data(cpu_percent=50.0)

    # Custom available function that checks for metrics
    def check_metrics(data) -> bool:
        return data is not None and data.metrics is not None

    description = UnraidEntityDescription(
        key="cpu_usage",
        available_fn=check_metrics,
    )

    entity = UnraidEntity(
        coordinator=coordinator,
        entity_description=description,
        server_uuid="test-uuid",
        server_name="tower",
    )

    # Should be available
    assert entity.available is True

    # Make data None - should be unavailable
    coordinator.data = None
    assert entity.available is False


def test_unraid_entity_unavailable_when_coordinator_fails() -> None:
    """Test UnraidEntity unavailable when coordinator update fails."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = False  # Coordinator failed
    coordinator.data = make_system_data()

    description = UnraidEntityDescription(key="test")

    entity = UnraidEntity(
        coordinator=coordinator,
        entity_description=description,
        server_uuid="test-uuid",
        server_name="tower",
    )

    # Should be unavailable because coordinator failed
    assert entity.available is False


def test_unraid_entity_unavailable_when_data_none() -> None:
    """Test UnraidEntity unavailable when coordinator data is None."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True
    coordinator.data = None  # No data

    description = UnraidEntityDescription(key="test")

    entity = UnraidEntity(
        coordinator=coordinator,
        entity_description=description,
        server_uuid="test-uuid",
        server_name="tower",
    )

    # Should be unavailable because data is None
    assert entity.available is False


def test_unraid_entity_with_server_info() -> None:
    """Test UnraidEntity with server_info passed through."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True
    coordinator.data = make_system_data()

    description = UnraidEntityDescription(key="test")

    server_info = {
        "manufacturer": "Test Manufacturer",
        "model": "Test Model",
    }

    entity = UnraidEntity(
        coordinator=coordinator,
        entity_description=description,
        server_uuid="test-uuid",
        server_name="tower",
        server_info=server_info,
    )

    assert entity.device_info["manufacturer"] == "Test Manufacturer"
    assert entity.device_info["model"] == "Test Model"


# =============================================================================
# Edge Cases
# =============================================================================


def test_entity_with_storage_coordinator() -> None:
    """Test entity works with storage coordinator."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.last_update_success = True
    coordinator.data = make_storage_data(array_state="STARTED")

    entity = UnraidBaseEntity(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        resource_id="array_state",
        name="Array State",
    )

    assert entity.available is True
    assert entity.unique_id == "test-uuid_array_state"


def test_entity_description_available_fn_with_storage_data() -> None:
    """Test entity description available_fn with storage data."""

    def array_started(data) -> bool:
        if data is None or data.array is None:
            return False
        return data.array.state == "STARTED"

    description = UnraidEntityDescription(
        key="array_sensor",
        available_fn=array_started,
    )

    # Test with started array
    data = make_storage_data(array_state="STARTED")
    assert description.available_fn(data) is True

    # Test with stopped array
    data = make_storage_data(array_state="STOPPED")
    assert description.available_fn(data) is False


def test_entity_unique_id_special_characters() -> None:
    """Test entity unique_id handles special characters in resource_id."""
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True

    # Resource ID with underscores and numbers
    entity = UnraidBaseEntity(
        coordinator=coordinator,
        server_uuid="uuid-123-abc",
        server_name="tower",
        resource_id="disk_1_temperature",
        name="Disk 1 Temperature",
    )

    assert entity.unique_id == "uuid-123-abc_disk_1_temperature"


def test_entity_description_supported_fn_filters_entities() -> None:
    """Test supported_fn can be used to filter entities during setup."""
    # This tests the pattern used in async_setup_entry

    def has_ups(data) -> bool:
        """Check if UPS devices are available."""
        return data is not None and len(data.ups_devices) > 0

    description = UnraidEntityDescription(
        key="ups_battery",
        supported_fn=has_ups,
    )

    # Without UPS devices - should not be supported
    data = make_system_data()
    assert description.supported_fn(data) is False

    # With UPS devices - should be supported
    from unraid_api.models import UPSBattery, UPSDevice

    ups = UPSDevice(
        id="ups:1",
        name="APC UPS",
        status="Online",
        battery=UPSBattery(chargeLevel=100, estimatedRuntime=3600),
    )
    data = make_system_data(ups_devices=[ups])
    assert description.supported_fn(data) is True
