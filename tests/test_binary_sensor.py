"""Tests for Unraid binary sensor platform."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from unraid_api.models import (
    ArrayDisk,
    Cloud,
    CloudResponse,
    DockerContainer,
    ParityCheck,
    RemoteAccess,
    Service,
    ServiceUptime,
    UnraidArray,
    UPSBattery,
    UPSDevice,
    Vars,
)

from custom_components.unraid import UnraidRuntimeData
from custom_components.unraid.binary_sensor import (
    ArrayStartedBinarySensor,
    CloudConnectedBinarySensor,
    ConfigValidBinarySensor,
    ContainerUpdateAvailableBinarySensor,
    DiskHealthBinarySensor,
    DisksDisabledBinarySensor,
    DisksInvalidBinarySensor,
    DisksMissingBinarySensor,
    FilesystemsUnmountableBinarySensor,
    MoverActiveBinarySensor,
    ParityCheckRunningBinarySensor,
    ParityStatusBinarySensor,
    ParityValidBinarySensor,
    RemoteAccessBinarySensor,
    SafeModeBinarySensor,
    ServiceBinarySensor,
    UPSConnectedBinarySensor,
    async_setup_entry,
)
from custom_components.unraid.coordinator import (
    UnraidStorageData,
    UnraidSystemCoordinator,
)
from tests.conftest import make_infra_data, make_system_data

# =============================================================================
# Helper Functions
# =============================================================================


def make_array(**kwargs: Any) -> UnraidArray:
    """Create an UnraidArray model for testing."""
    defaults = {
        "state": "STARTED",
        "disks": [],
        "parities": [],
        "caches": [],
    }
    defaults.update(kwargs)
    return UnraidArray(**defaults)


def make_storage_data(
    array_state: str | None = "STARTED",
    disks: list[ArrayDisk] | None = None,
    parities: list[ArrayDisk] | None = None,
    caches: list[ArrayDisk] | None = None,
    parity_status: ParityCheck | None = None,
    **kwargs: Any,
) -> UnraidStorageData:
    """
    Create UnraidStorageData with convenience parameters.

    This helper accepts the old-style parameters and creates the new structure.
    """
    array_kwargs = {
        "state": array_state,
        "disks": disks or [],
        "parities": parities or [],
        "caches": caches or [],
        **kwargs,
    }
    # Only set parityCheckStatus if explicitly provided (model has its own default)
    if parity_status is not None:
        array_kwargs["parityCheckStatus"] = parity_status
    array = make_array(**array_kwargs)
    return UnraidStorageData(array=array)


def make_disk(**kwargs: Any) -> ArrayDisk:
    """Create an ArrayDisk model for testing."""
    defaults = {
        "id": "disk:1",
        "idx": 1,
        "device": "sda",
        "name": "Disk 1",
        "type": "DATA",
        "status": "DISK_OK",
        "temp": 35,
        "isSpinning": True,
        "smartStatus": "PASSED",
        "fsType": "XFS",
    }
    defaults.update(kwargs)
    return ArrayDisk(**defaults)


def make_ups(**kwargs: Any) -> UPSDevice:
    """Create a UPSDevice model for testing."""
    defaults = {
        "id": "ups:1",
        "name": "APC Smart-UPS",
        "status": "Online",
        "battery": UPSBattery(chargeLevel=95, estimatedRuntime=1200),
    }
    defaults.update(kwargs)
    return UPSDevice(**defaults)


def make_service(**kwargs: Any) -> Service:
    """Create a Service model for testing."""
    defaults = {
        "id": "smb",
        "name": "SMB",
        "online": True,
        "uptime": ServiceUptime(timestamp="2025-12-01T10:00:00Z"),
        "version": "4.21.4",
    }
    defaults.update(kwargs)
    return Service(**defaults)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_storage_coordinator():
    """Create a mock storage coordinator."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    return coordinator


@pytest.fixture
def mock_system_coordinator():
    """Create a mock system coordinator."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    return coordinator


@pytest.fixture
def mock_infra_coordinator():
    """Create a mock infrastructure coordinator."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    return coordinator


@pytest.fixture
def mock_disk():
    """Create a mock disk."""
    return make_disk()


@pytest.fixture
def mock_ups():
    """Create a mock UPS device."""
    return make_ups()


# =============================================================================
# DiskHealthBinarySensor Tests
# =============================================================================


def test_disk_health_init(mock_storage_coordinator, mock_disk):
    """Test DiskHealthBinarySensor initialization."""
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=mock_disk,
    )
    assert sensor._attr_unique_id == "test-uuid_disk_health_disk:1"
    assert sensor._attr_translation_key == "disk_health"
    assert sensor._attr_translation_placeholders == {"name": "Disk 1"}
    assert sensor._attr_device_class == BinarySensorDeviceClass.PROBLEM


def test_disk_health_is_on_disk_ok(mock_storage_coordinator, mock_disk):
    """Test is_on returns False when disk is healthy."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[mock_disk],
    )
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=mock_disk,
    )
    assert sensor.is_on is False  # No problem


def test_disk_health_is_on_disk_error(mock_storage_coordinator):
    """Test is_on returns True when disk has problem."""
    disk = make_disk(status="DISK_DISABLED")
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[disk],
    )
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=disk,
    )
    assert sensor.is_on is True  # Problem detected


def test_disk_health_is_on_no_data(mock_storage_coordinator, mock_disk):
    """Test is_on returns None when no data."""
    mock_storage_coordinator.data = None
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=mock_disk,
    )
    assert sensor.is_on is None


def test_disk_health_is_on_disk_not_found(mock_storage_coordinator, mock_disk):
    """Test is_on returns None when disk not found in data."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[],  # Empty disks list
    )
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=mock_disk,
    )
    assert sensor.is_on is None


def test_disk_health_is_on_status_none(mock_storage_coordinator):
    """Test is_on returns None when disk status is None."""
    disk = make_disk(status=None)
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[disk],
    )
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=disk,
    )
    assert sensor.is_on is None


def test_disk_health_extra_state_attributes(mock_storage_coordinator, mock_disk):
    """Test extra state attributes."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[mock_disk],
    )
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=mock_disk,
    )
    attrs = sensor.extra_state_attributes
    assert attrs["status"] == "DISK_OK"
    assert attrs["device"] == "sda"
    assert attrs["filesystem"] == "XFS"
    assert attrs["temperature"] == 35
    assert attrs["smart_status"] == "PASSED"
    assert attrs["standby"] is False
    assert attrs["spinning"] is True


def test_disk_health_extra_state_attributes_minimal(mock_storage_coordinator):
    """Test extra_state_attributes with minimal disk data (no optional fields)."""
    minimal_disk = ArrayDisk(
        id="disk:1",
        name="Disk 1",
        type="DATA",
        status="DISK_OK",
        device="sda",
        # No fsType, temp, smartStatus, isSpinning - all optional fields missing
    )
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[minimal_disk],
    )
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=minimal_disk,
    )
    attrs = sensor.extra_state_attributes
    # Only required fields should be present
    assert attrs["status"] == "DISK_OK"
    assert attrs["device"] == "sda"
    # Optional fields should not be present
    assert "filesystem" not in attrs
    assert "temperature" not in attrs
    assert "smart_status" not in attrs
    assert "standby" not in attrs
    assert "spinning" not in attrs


def test_disk_health_extra_state_attributes_no_data(
    mock_storage_coordinator, mock_disk
):
    """Test extra_state_attributes returns empty dict when no data."""
    mock_storage_coordinator.data = None
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=mock_disk,
    )
    assert sensor.extra_state_attributes == {}


def test_disk_health_get_disk_from_parities(mock_storage_coordinator):
    """Test _get_disk finds disk in parities list."""
    parity_disk = make_disk(id="parity:1", name="Parity", status="DISK_OK")
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[],
        parities=[parity_disk],
    )
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=parity_disk,
    )
    assert sensor.is_on is False


def test_disk_health_get_disk_from_caches(mock_storage_coordinator):
    """Test _get_disk finds disk in caches list."""
    cache_disk = make_disk(id="cache:1", name="Cache", status="DISK_OK")
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[],
        caches=[cache_disk],
    )
    sensor = DiskHealthBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        disk=cache_disk,
    )
    assert sensor.is_on is False


# =============================================================================
# ParityStatusBinarySensor Tests
# =============================================================================


def test_parity_status_init(mock_storage_coordinator):
    """Test ParityStatusBinarySensor initialization."""
    sensor = ParityStatusBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_parity_status"
    assert sensor._attr_translation_key == "parity_status"
    assert sensor._attr_device_class == BinarySensorDeviceClass.PROBLEM


def test_parity_status_is_on_running(mock_storage_coordinator):
    """Test is_on returns True when parity check running."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="RUNNING", progress=50, errors=0),
    )
    sensor = ParityStatusBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True


def test_parity_status_is_on_paused(mock_storage_coordinator):
    """Test is_on returns True when parity check paused."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="PAUSED", progress=50, errors=0),
    )
    sensor = ParityStatusBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True


def test_parity_status_is_on_completed(mock_storage_coordinator):
    """Test is_on returns False when parity check completed."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="COMPLETED", progress=100, errors=0),
    )
    sensor = ParityStatusBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is False


def test_parity_status_is_on_no_data(mock_storage_coordinator):
    """Test is_on returns None when no data."""
    mock_storage_coordinator.data = None
    sensor = ParityStatusBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_parity_status_is_on_no_parity_status(mock_storage_coordinator):
    """Test is_on returns None when no parity status."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=None,
    )
    sensor = ParityStatusBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_parity_status_is_on_status_none(mock_storage_coordinator):
    """Test is_on returns None when status is None."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status=None),
    )
    sensor = ParityStatusBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_parity_status_extra_state_attributes(mock_storage_coordinator):
    """Test extra state attributes."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="COMPLETED", progress=100, errors=0),
    )
    sensor = ParityStatusBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert attrs["status"] == "completed"
    assert attrs["progress"] == 100
    assert attrs["errors"] == 0


def test_parity_status_extra_state_attributes_no_data(mock_storage_coordinator):
    """Test extra_state_attributes returns empty dict when no data."""
    mock_storage_coordinator.data = None
    sensor = ParityStatusBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# ArrayStartedBinarySensor Tests
# =============================================================================


def test_array_started_init(mock_storage_coordinator):
    """Test ArrayStartedBinarySensor initialization."""
    sensor = ArrayStartedBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_array_started"
    assert sensor._attr_translation_key == "array_started"
    assert sensor._attr_device_class == BinarySensorDeviceClass.RUNNING


def test_array_started_is_on_started(mock_storage_coordinator):
    """Test is_on returns True when array started."""
    mock_storage_coordinator.data = make_storage_data(array_state="STARTED")
    sensor = ArrayStartedBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True


def test_array_started_is_on_stopped(mock_storage_coordinator):
    """Test is_on returns False when array stopped."""
    mock_storage_coordinator.data = make_storage_data(array_state="STOPPED")
    sensor = ArrayStartedBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is False


def test_array_started_is_on_no_data(mock_storage_coordinator):
    """Test is_on returns None when no data."""
    mock_storage_coordinator.data = None
    sensor = ArrayStartedBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_array_started_is_on_array_state_none(mock_storage_coordinator):
    """Test is_on returns None when array_state is None."""
    mock_storage_coordinator.data = make_storage_data(array_state=None)
    sensor = ArrayStartedBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


# =============================================================================
# ParityCheckRunningBinarySensor Tests
# =============================================================================


def test_parity_check_running_init(mock_storage_coordinator):
    """Test ParityCheckRunningBinarySensor initialization."""
    sensor = ParityCheckRunningBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_parity_check_running"
    assert sensor._attr_translation_key == "parity_check_running"
    assert sensor._attr_device_class == BinarySensorDeviceClass.RUNNING


def test_parity_check_running_is_on_running(mock_storage_coordinator):
    """Test is_on returns True when parity check running."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="RUNNING", progress=50),
    )
    sensor = ParityCheckRunningBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True


def test_parity_check_running_is_on_paused(mock_storage_coordinator):
    """Test is_on returns True when parity check paused."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="PAUSED", progress=50),
    )
    sensor = ParityCheckRunningBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True


def test_parity_check_running_is_on_completed(mock_storage_coordinator):
    """Test is_on returns False when parity check completed."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="COMPLETED", progress=100),
    )
    sensor = ParityCheckRunningBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is False


def test_parity_check_running_is_on_no_data(mock_storage_coordinator):
    """Test is_on returns None when no data."""
    mock_storage_coordinator.data = None
    sensor = ParityCheckRunningBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_parity_check_running_is_on_no_parity_status(mock_storage_coordinator):
    """Test is_on returns None when no parity status."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=None,
    )
    sensor = ParityCheckRunningBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_parity_check_running_is_on_status_none(mock_storage_coordinator):
    """Test is_on returns None when status is None."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status=None),
    )
    sensor = ParityCheckRunningBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_parity_check_running_extra_state_attributes(mock_storage_coordinator):
    """Test extra state attributes."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="RUNNING", progress=50),
    )
    sensor = ParityCheckRunningBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert attrs["status"] == "running"
    assert attrs["progress"] == 50


def test_parity_check_running_extra_state_attributes_no_data(mock_storage_coordinator):
    """Test extra_state_attributes returns empty dict when no data."""
    mock_storage_coordinator.data = None
    sensor = ParityCheckRunningBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# ParityValidBinarySensor Tests
# =============================================================================


def test_parity_valid_init(mock_storage_coordinator):
    """Test ParityValidBinarySensor initialization."""
    sensor = ParityValidBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_parity_valid"
    assert sensor._attr_translation_key == "parity_valid"
    assert sensor._attr_device_class == BinarySensorDeviceClass.PROBLEM


def test_parity_valid_is_on_failed(mock_storage_coordinator):
    """Test is_on returns True when parity failed."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="FAILED", errors=0),
    )
    sensor = ParityValidBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True  # Problem detected


def test_parity_valid_is_on_with_errors(mock_storage_coordinator):
    """Test is_on returns True when parity has errors."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="COMPLETED", errors=5),
    )
    sensor = ParityValidBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True  # Problem detected


def test_parity_valid_is_on_valid(mock_storage_coordinator):
    """Test is_on returns False when parity is valid."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="COMPLETED", errors=0),
    )
    sensor = ParityValidBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is False  # No problem


def test_parity_valid_is_on_no_data(mock_storage_coordinator):
    """Test is_on returns None when no data."""
    mock_storage_coordinator.data = None
    sensor = ParityValidBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_parity_valid_extra_state_attributes(mock_storage_coordinator):
    """Test extra state attributes."""
    mock_storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        parity_status=ParityCheck(status="COMPLETED", errors=0),
    )
    sensor = ParityValidBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert attrs["status"] == "completed"
    assert attrs["errors"] == 0


def test_parity_valid_extra_state_attributes_no_data(mock_storage_coordinator):
    """Test extra_state_attributes returns empty dict when no data."""
    mock_storage_coordinator.data = None
    sensor = ParityValidBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# UPSConnectedBinarySensor Tests
# =============================================================================


def test_ups_connected_init(mock_system_coordinator, mock_ups):
    """Test UPSConnectedBinarySensor initialization."""
    sensor = UPSConnectedBinarySensor(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=mock_ups,
    )
    assert sensor._attr_unique_id == "test-uuid_ups_ups:1_connected"
    assert sensor._attr_translation_key == "ups_connected"
    assert sensor._attr_translation_placeholders == {"name": "APC Smart-UPS"}
    assert sensor._attr_device_class == BinarySensorDeviceClass.CONNECTIVITY


def test_ups_connected_is_on_online(mock_system_coordinator, mock_ups):
    """Test is_on returns True when UPS online."""
    mock_system_coordinator.data = MagicMock()
    mock_system_coordinator.data.ups_devices = [mock_ups]
    sensor = UPSConnectedBinarySensor(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=mock_ups,
    )
    assert sensor.is_on is True


def test_ups_connected_is_on_offline(mock_system_coordinator):
    """Test is_on returns False when UPS offline."""
    ups = make_ups(status="Offline")
    mock_system_coordinator.data = MagicMock()
    mock_system_coordinator.data.ups_devices = [ups]
    sensor = UPSConnectedBinarySensor(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=ups,
    )
    assert sensor.is_on is False


def test_ups_connected_is_on_status_none(mock_system_coordinator):
    """Test is_on returns False when UPS status is None."""
    ups = make_ups(status=None)
    mock_system_coordinator.data = MagicMock()
    mock_system_coordinator.data.ups_devices = [ups]
    sensor = UPSConnectedBinarySensor(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=ups,
    )
    assert sensor.is_on is False


def test_ups_connected_is_on_ups_not_found(mock_system_coordinator, mock_ups):
    """Test is_on returns False when UPS not found."""
    mock_system_coordinator.data = MagicMock()
    mock_system_coordinator.data.ups_devices = []
    sensor = UPSConnectedBinarySensor(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=mock_ups,
    )
    assert sensor.is_on is False


def test_ups_connected_is_on_no_data(mock_system_coordinator, mock_ups):
    """Test is_on returns False when no data."""
    mock_system_coordinator.data = None
    sensor = UPSConnectedBinarySensor(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=mock_ups,
    )
    assert sensor.is_on is False


def test_ups_connected_extra_state_attributes(mock_system_coordinator, mock_ups):
    """Test extra state attributes."""
    mock_system_coordinator.data = MagicMock()
    mock_system_coordinator.data.ups_devices = [mock_ups]
    sensor = UPSConnectedBinarySensor(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=mock_ups,
    )
    attrs = sensor.extra_state_attributes
    assert attrs["model"] == "APC Smart-UPS"
    assert attrs["status"] == "Online"
    assert attrs["battery_level"] == 95


def test_ups_connected_extra_state_attributes_no_data(
    mock_system_coordinator, mock_ups
):
    """Test extra_state_attributes returns empty dict when no UPS."""
    mock_system_coordinator.data = None
    sensor = UPSConnectedBinarySensor(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=mock_ups,
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# Binary Sensor Availability Tests
# =============================================================================


def test_binary_sensor_available_true(mock_storage_coordinator):
    """Test sensor is available when coordinator succeeds."""
    mock_storage_coordinator.last_update_success = True
    sensor = ArrayStartedBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.available is True


def test_binary_sensor_available_false(mock_storage_coordinator):
    """Test sensor is not available when coordinator fails."""
    mock_storage_coordinator.last_update_success = False
    sensor = ArrayStartedBinarySensor(
        coordinator=mock_storage_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.available is False


# =============================================================================
# async_setup_entry Tests
# =============================================================================


@pytest.mark.asyncio
async def test_setup_entry_creates_entities(hass):
    """Test async_setup_entry creates expected entities."""
    mock_disk = make_disk()
    mock_ups_device = make_ups()

    # Setup mock coordinators
    storage_coordinator = MagicMock()
    storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[mock_disk],
    )

    system_coordinator = MagicMock()
    system_data = MagicMock()
    system_data.ups_devices = [mock_ups_device]
    system_coordinator.data = system_data

    # Create mock config entry
    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
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
    )

    # Track added entities
    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Verify expected entities were created
    assert len(added_entities) > 0

    # Check for expected sensor types
    entity_types = [type(e).__name__ for e in added_entities]
    assert "ArrayStartedBinarySensor" in entity_types
    assert "ParityCheckRunningBinarySensor" in entity_types
    assert "ParityValidBinarySensor" in entity_types
    assert "ParityStatusBinarySensor" in entity_types
    assert "DiskHealthBinarySensor" in entity_types
    assert "UPSConnectedBinarySensor" in entity_types


@pytest.mark.asyncio
async def test_setup_entry_no_ups(hass):
    """Test async_setup_entry works without UPS."""
    mock_disk = make_disk()

    storage_coordinator = MagicMock()
    storage_coordinator.data = make_storage_data(
        array_state="STARTED",
        disks=[mock_disk],
    )

    system_coordinator = MagicMock()
    system_coordinator.data = None  # No system data

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        infra_coordinator=MagicMock(),
        server_info={
            "uuid": "test-uuid",
            "name": "tower",
        },
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Verify no UPS sensors created
    entity_types = [type(e).__name__ for e in added_entities]
    assert "UPSConnectedBinarySensor" not in entity_types


@pytest.mark.asyncio
async def test_setup_entry_no_storage_data(hass):
    """Test async_setup_entry works without storage data."""
    storage_coordinator = MagicMock()
    storage_coordinator.data = None

    system_coordinator = MagicMock()
    system_coordinator.data = None

    mock_entry = MagicMock()
    mock_entry.data = {"host": "192.168.1.100"}
    mock_entry.runtime_data = UnraidRuntimeData(
        api_client=MagicMock(),
        system_coordinator=system_coordinator,
        storage_coordinator=storage_coordinator,
        infra_coordinator=MagicMock(),
        server_info={
            "uuid": "test-uuid",
            "name": "tower",
        },
    )

    added_entities = []

    def mock_add_entities(entities) -> None:
        added_entities.extend(entities)

    await async_setup_entry(hass, mock_entry, mock_add_entities)

    # Still creates array sensors (just no disk sensors)
    assert (
        len(added_entities) >= 4
    )  # ArrayStarted, ParityCheck, ParityValid, ParityStatus


# =============================================================================
# ServiceBinarySensor Tests
# =============================================================================


def test_service_init(mock_infra_coordinator):
    """Test ServiceBinarySensor initialization."""
    service = make_service(name="SMB")
    sensor = ServiceBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        service=service,
    )
    assert sensor._attr_unique_id == "test-uuid_service_SMB"
    assert sensor._attr_translation_key == "service"
    assert sensor._attr_device_class == BinarySensorDeviceClass.CONNECTIVITY
    assert sensor._attr_entity_registry_enabled_default is False
    assert sensor._attr_translation_placeholders == {"name": "SMB"}


def test_service_is_on_online(mock_infra_coordinator):
    """Test is_on returns True when service is online."""
    service = make_service(name="SMB", online=True)
    mock_infra_coordinator.data = make_infra_data(services=[service])
    sensor = ServiceBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        service=service,
    )
    assert sensor.is_on is True


def test_service_is_on_offline(mock_infra_coordinator):
    """Test is_on returns False when service is offline."""
    service = make_service(name="Nginx", online=False)
    mock_infra_coordinator.data = make_infra_data(services=[service])
    sensor = ServiceBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        service=service,
    )
    assert sensor.is_on is False


def test_service_is_on_no_data(mock_infra_coordinator):
    """Test is_on returns None when no coordinator data."""
    service = make_service(name="SMB")
    mock_infra_coordinator.data = None
    sensor = ServiceBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        service=service,
    )
    assert sensor.is_on is None


def test_service_is_on_service_not_found(mock_infra_coordinator):
    """Test is_on returns None when service not found in data."""
    service = make_service(name="SMB")
    other_service = make_service(id="nfs", name="NFS")
    mock_infra_coordinator.data = make_infra_data(services=[other_service])
    sensor = ServiceBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        service=service,
    )
    assert sensor.is_on is None


def test_service_extra_state_attributes(mock_infra_coordinator):
    """Test extra state attributes with version and uptime."""
    service = make_service(
        name="SMB",
        version="4.21.4",
        uptime=ServiceUptime(timestamp="2025-12-01T10:00:00Z"),
    )
    mock_infra_coordinator.data = make_infra_data(services=[service])
    sensor = ServiceBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        service=service,
    )
    attrs = sensor.extra_state_attributes
    assert attrs["version"] == "4.21.4"
    assert attrs["uptime"] == "2025-12-01T10:00:00Z"


def test_service_extra_state_attributes_minimal(mock_infra_coordinator):
    """Test extra state attributes with no version or uptime."""
    service = make_service(name="CustomSvc", version=None, uptime=None)
    mock_infra_coordinator.data = make_infra_data(services=[service])
    sensor = ServiceBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        service=service,
    )
    attrs = sensor.extra_state_attributes
    assert attrs == {}


def test_service_extra_state_attributes_no_data(mock_infra_coordinator):
    """Test extra state attributes when no coordinator data."""
    service = make_service(name="SMB")
    mock_infra_coordinator.data = None
    sensor = ServiceBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        service=service,
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# CloudConnectedBinarySensor Tests
# =============================================================================


def test_cloud_connected_init(mock_infra_coordinator):
    """Test CloudConnectedBinarySensor initialization."""
    sensor = CloudConnectedBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_cloud_connected"
    assert sensor._attr_translation_key == "cloud_connected"
    assert sensor._attr_device_class == BinarySensorDeviceClass.CONNECTIVITY
    assert sensor._attr_entity_registry_enabled_default is False


def test_cloud_connected_is_on_connected(mock_infra_coordinator):
    """Test is_on returns True when cloud is connected."""
    cloud = Cloud(cloud=CloudResponse(status="connected", ip="1.2.3.4"))
    mock_infra_coordinator.data = make_infra_data(cloud=cloud)
    sensor = CloudConnectedBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True


def test_cloud_connected_is_on_disconnected(mock_infra_coordinator):
    """Test is_on returns False when cloud is not connected."""
    cloud = Cloud(cloud=CloudResponse(status="disconnected"))
    mock_infra_coordinator.data = make_infra_data(cloud=cloud)
    sensor = CloudConnectedBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is False


def test_cloud_connected_is_on_no_data(mock_infra_coordinator):
    """Test is_on returns None when no coordinator data."""
    mock_infra_coordinator.data = None
    sensor = CloudConnectedBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_cloud_connected_is_on_no_cloud(mock_infra_coordinator):
    """Test is_on returns None when cloud data is None."""
    mock_infra_coordinator.data = make_infra_data(cloud=None)
    sensor = CloudConnectedBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_cloud_connected_is_on_no_cloud_response(mock_infra_coordinator):
    """Test is_on returns None when cloud.cloud is None."""
    cloud = Cloud()
    mock_infra_coordinator.data = make_infra_data(cloud=cloud)
    sensor = CloudConnectedBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_cloud_connected_extra_attributes(mock_infra_coordinator):
    """Test extra state attributes with full cloud data."""
    from unraid_api.models import MinigraphqlResponse, RelayResponse

    cloud = Cloud(
        cloud=CloudResponse(status="connected", ip="1.2.3.4"),
        relay=RelayResponse(status="connected"),
        minigraphql=MinigraphqlResponse(status="CONNECTED"),
    )
    mock_infra_coordinator.data = make_infra_data(cloud=cloud)
    sensor = CloudConnectedBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert attrs["status"] == "connected"
    assert attrs["ip"] == "1.2.3.4"
    assert attrs["relay_status"] == "connected"
    assert attrs["minigraphql_status"] == "CONNECTED"


def test_cloud_connected_extra_attributes_no_data(mock_infra_coordinator):
    """Test extra state attributes when no data."""
    mock_infra_coordinator.data = None
    sensor = CloudConnectedBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


def test_cloud_connected_extra_attributes_no_cloud(mock_infra_coordinator):
    """Test extra state attributes when cloud is None."""
    mock_infra_coordinator.data = make_infra_data(cloud=None)
    sensor = CloudConnectedBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# RemoteAccessBinarySensor Tests
# =============================================================================


def test_remote_access_init(mock_infra_coordinator):
    """Test RemoteAccessBinarySensor initialization."""
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor._attr_unique_id == "test-uuid_remote_access"
    assert sensor._attr_translation_key == "remote_access"
    assert sensor._attr_device_class == BinarySensorDeviceClass.CONNECTIVITY
    assert sensor._attr_entity_registry_enabled_default is False


def test_remote_access_is_on_dynamic(mock_infra_coordinator):
    """Test is_on returns True when access type is DYNAMIC."""
    ra = RemoteAccess(accessType="DYNAMIC", forwardType="UPNP", port=443)
    mock_infra_coordinator.data = make_infra_data(remote_access=ra)
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True


def test_remote_access_is_on_always(mock_infra_coordinator):
    """Test is_on returns True when access type is ALWAYS."""
    ra = RemoteAccess(accessType="ALWAYS", port=443)
    mock_infra_coordinator.data = make_infra_data(remote_access=ra)
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is True


def test_remote_access_is_on_disabled(mock_infra_coordinator):
    """Test is_on returns False when access type is DISABLED."""
    ra = RemoteAccess(accessType="DISABLED")
    mock_infra_coordinator.data = make_infra_data(remote_access=ra)
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is False


def test_remote_access_is_on_no_data(mock_infra_coordinator):
    """Test is_on returns None when no data."""
    mock_infra_coordinator.data = None
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_remote_access_is_on_no_remote_access(mock_infra_coordinator):
    """Test is_on returns None when remote_access is None."""
    mock_infra_coordinator.data = make_infra_data(remote_access=None)
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_remote_access_is_on_no_access_type(mock_infra_coordinator):
    """Test is_on returns None when accessType is None."""
    ra = RemoteAccess()
    mock_infra_coordinator.data = make_infra_data(remote_access=ra)
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.is_on is None


def test_remote_access_extra_attributes(mock_infra_coordinator):
    """Test extra state attributes with remote access data."""
    ra = RemoteAccess(accessType="DYNAMIC", forwardType="UPNP", port=443)
    mock_infra_coordinator.data = make_infra_data(remote_access=ra)
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    attrs = sensor.extra_state_attributes
    assert attrs["access_type"] == "DYNAMIC"
    assert attrs["forward_type"] == "UPNP"
    assert attrs["port"] == 443


def test_remote_access_extra_attributes_no_data(mock_infra_coordinator):
    """Test extra state attributes when no data."""
    mock_infra_coordinator.data = None
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


def test_remote_access_extra_attributes_minimal(mock_infra_coordinator):
    """Test extra state attributes with minimal remote access data."""
    ra = RemoteAccess()
    mock_infra_coordinator.data = make_infra_data(remote_access=ra)
    sensor = RemoteAccessBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )
    assert sensor.extra_state_attributes == {}


# =============================================================================
# ContainerUpdateAvailableBinarySensor Tests
# =============================================================================


def test_container_update_available_init():
    """Test ContainerUpdateAvailableBinarySensor initialization."""
    container = DockerContainer(
        id="ct:1", name="/nginx", state="RUNNING", isUpdateAvailable=True
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])

    sensor = ContainerUpdateAvailableBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        container=container,
    )

    assert sensor._attr_unique_id == "test-uuid_container_nginx_update"
    assert sensor._attr_translation_key == "container_update_available"
    assert sensor._attr_translation_placeholders == {"name": "nginx"}
    assert sensor._attr_device_class == BinarySensorDeviceClass.UPDATE


def test_container_update_available_is_on():
    """Test is_on returns True when update is available."""
    container = DockerContainer(
        id="ct:1", name="/nginx", state="RUNNING", isUpdateAvailable=True
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])

    sensor = ContainerUpdateAvailableBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        container=container,
    )

    assert sensor.is_on is True


def test_container_update_available_is_off():
    """Test is_on returns False when no update available."""
    container = DockerContainer(
        id="ct:1", name="/nginx", state="RUNNING", isUpdateAvailable=False
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])

    sensor = ContainerUpdateAvailableBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        container=container,
    )

    assert sensor.is_on is False


def test_container_update_available_none_data():
    """Test is_on returns None when coordinator data is None."""
    container = DockerContainer(id="ct:1", name="/nginx", state="RUNNING")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None

    sensor = ContainerUpdateAvailableBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        container=container,
    )

    assert sensor.is_on is None
    assert sensor.extra_state_attributes == {}


def test_container_update_available_not_found():
    """Test is_on returns None when container not in coordinator data."""
    container = DockerContainer(id="ct:1", name="/nginx", state="RUNNING")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[])

    sensor = ContainerUpdateAvailableBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        container=container,
    )

    assert sensor.is_on is None


def test_container_update_available_none_treated_as_false():
    """Test is_on returns False when isUpdateAvailable is None (unknown)."""
    container = DockerContainer(
        id="ct:1", name="/nginx", state="RUNNING", isUpdateAvailable=None
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])

    sensor = ContainerUpdateAvailableBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        container=container,
    )

    # None from API is treated as False (no update detected)
    assert sensor.is_on is False


def test_container_update_available_attributes():
    """Test extra_state_attributes includes image and state."""
    container = DockerContainer(
        id="ct:1",
        name="/nginx",
        state="RUNNING",
        image="nginx:latest",
        isUpdateAvailable=True,
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])

    sensor = ContainerUpdateAvailableBinarySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        container=container,
    )

    attrs = sensor.extra_state_attributes
    assert attrs["image"] == "nginx:latest"
    assert attrs["state"] == "RUNNING"


# =============================================================================
# MoverActiveBinarySensor Tests
# =============================================================================


def test_mover_active_init(mock_infra_coordinator):
    """Test MoverActiveBinarySensor initialization."""
    mock_infra_coordinator.data = make_infra_data(
        vars_data=Vars(share_mover_active=False)
    )

    sensor = MoverActiveBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor._attr_unique_id == "test-uuid_mover_active"
    assert sensor._attr_translation_key == "mover_active"
    assert sensor._attr_device_class == BinarySensorDeviceClass.RUNNING


def test_mover_active_is_on(mock_infra_coordinator):
    """Test is_on returns True when mover is active."""
    mock_infra_coordinator.data = make_infra_data(
        vars_data=Vars(share_mover_active=True)
    )

    sensor = MoverActiveBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is True


def test_mover_active_is_off(mock_infra_coordinator):
    """Test is_on returns False when mover is idle."""
    mock_infra_coordinator.data = make_infra_data(
        vars_data=Vars(share_mover_active=False)
    )

    sensor = MoverActiveBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is False


def test_mover_active_none_data(mock_infra_coordinator):
    """Test is_on returns None when coordinator data is None."""
    mock_infra_coordinator.data = None

    sensor = MoverActiveBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None


def test_mover_active_no_vars(mock_infra_coordinator):
    """Test is_on returns None when vars is None."""
    mock_infra_coordinator.data = make_infra_data(vars_data=None)

    sensor = MoverActiveBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None


# =============================================================================
# DisksDisabledBinarySensor Tests
# =============================================================================


def test_disks_disabled_init(mock_infra_coordinator):
    """Test DisksDisabledBinarySensor initialization."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(md_num_disabled=0))

    sensor = DisksDisabledBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor._attr_unique_id == "test-uuid_disks_disabled"
    assert sensor._attr_translation_key == "disks_disabled"
    assert sensor._attr_device_class == BinarySensorDeviceClass.PROBLEM


def test_disks_disabled_is_on_when_count_gt_zero(mock_infra_coordinator):
    """Test is_on returns True when disabled disk count > 0."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(md_num_disabled=2))

    sensor = DisksDisabledBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is True


def test_disks_disabled_is_off_when_count_zero(mock_infra_coordinator):
    """Test is_on returns False when disabled disk count is 0."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(md_num_disabled=0))

    sensor = DisksDisabledBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is False


def test_disks_disabled_none_data(mock_infra_coordinator):
    """Test is_on returns None when coordinator data is None."""
    mock_infra_coordinator.data = None

    sensor = DisksDisabledBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None
    assert sensor.extra_state_attributes == {}


def test_disks_disabled_none_count(mock_infra_coordinator):
    """Test is_on returns None when md_num_disabled is None."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(md_num_disabled=None))

    sensor = DisksDisabledBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None


def test_disks_disabled_attributes(mock_infra_coordinator):
    """Test extra_state_attributes includes count."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(md_num_disabled=3))

    sensor = DisksDisabledBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.extra_state_attributes == {"count": 3}


# =============================================================================
# DisksMissingBinarySensor Tests
# =============================================================================


def test_disks_missing_is_on_when_count_gt_zero(mock_infra_coordinator):
    """Test is_on returns True when missing disk count > 0."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(md_num_missing=1))

    sensor = DisksMissingBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is True
    assert sensor.extra_state_attributes == {"count": 1}


def test_disks_missing_is_off_when_count_zero(mock_infra_coordinator):
    """Test is_on returns False when missing disk count is 0."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(md_num_missing=0))

    sensor = DisksMissingBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is False


def test_disks_missing_none_data(mock_infra_coordinator):
    """Test is_on returns None when coordinator data is None."""
    mock_infra_coordinator.data = None

    sensor = DisksMissingBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None


# =============================================================================
# DisksInvalidBinarySensor Tests
# =============================================================================


def test_disks_invalid_is_on_when_count_gt_zero(mock_infra_coordinator):
    """Test is_on returns True when invalid disk count > 0."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(md_num_invalid=1))

    sensor = DisksInvalidBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is True
    assert sensor.extra_state_attributes == {"count": 1}


def test_disks_invalid_is_off_when_count_zero(mock_infra_coordinator):
    """Test is_on returns False when invalid disk count is 0."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(md_num_invalid=0))

    sensor = DisksInvalidBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is False


def test_disks_invalid_none_data(mock_infra_coordinator):
    """Test is_on returns None when coordinator data is None."""
    mock_infra_coordinator.data = None

    sensor = DisksInvalidBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None


# =============================================================================
# SafeModeBinarySensor Tests
# =============================================================================


def test_safe_mode_init(mock_infra_coordinator):
    """Test SafeModeBinarySensor initialization."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(safe_mode=False))

    sensor = SafeModeBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor._attr_unique_id == "test-uuid_safe_mode"
    assert sensor._attr_translation_key == "safe_mode"
    assert sensor._attr_device_class == BinarySensorDeviceClass.PROBLEM


def test_safe_mode_is_on(mock_infra_coordinator):
    """Test is_on returns True when server is in safe mode."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(safe_mode=True))

    sensor = SafeModeBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is True


def test_safe_mode_is_off(mock_infra_coordinator):
    """Test is_on returns False when server is not in safe mode."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(safe_mode=False))

    sensor = SafeModeBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is False


def test_safe_mode_none_data(mock_infra_coordinator):
    """Test is_on returns None when coordinator data is None."""
    mock_infra_coordinator.data = None

    sensor = SafeModeBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None


# =============================================================================
# ConfigValidBinarySensor Tests
# =============================================================================


def test_config_valid_init(mock_infra_coordinator):
    """Test ConfigValidBinarySensor initialization."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(config_valid=True))

    sensor = ConfigValidBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor._attr_unique_id == "test-uuid_config_valid"
    assert sensor._attr_translation_key == "config_valid"
    assert sensor._attr_device_class == BinarySensorDeviceClass.PROBLEM


def test_config_valid_is_off_when_valid(mock_infra_coordinator):
    """Test is_on returns False when config is valid (no problem)."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(config_valid=True))

    sensor = ConfigValidBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    # config_valid=True means no problem, so is_on=False
    assert sensor.is_on is False


def test_config_valid_is_on_when_invalid(mock_infra_coordinator):
    """Test is_on returns True when config is invalid (problem)."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(config_valid=False))

    sensor = ConfigValidBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    # config_valid=False means problem, so is_on=True
    assert sensor.is_on is True


def test_config_valid_none_data(mock_infra_coordinator):
    """Test is_on returns None when coordinator data is None."""
    mock_infra_coordinator.data = None

    sensor = ConfigValidBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None


def test_config_valid_none_value(mock_infra_coordinator):
    """Test is_on returns None when config_valid is None."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(config_valid=None))

    sensor = ConfigValidBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None


# =============================================================================
# FilesystemsUnmountableBinarySensor Tests
# =============================================================================


def test_filesystems_unmountable_init(mock_infra_coordinator):
    """Test FilesystemsUnmountableBinarySensor initialization."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(fs_num_unmountable=0))

    sensor = FilesystemsUnmountableBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor._attr_unique_id == "test-uuid_filesystems_unmountable"
    assert sensor._attr_translation_key == "filesystems_unmountable"
    assert sensor._attr_device_class == BinarySensorDeviceClass.PROBLEM


def test_filesystems_unmountable_is_on(mock_infra_coordinator):
    """Test is_on returns True when unmountable count > 0."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(fs_num_unmountable=2))

    sensor = FilesystemsUnmountableBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is True
    assert sensor.extra_state_attributes == {"count": 2}


def test_filesystems_unmountable_is_off(mock_infra_coordinator):
    """Test is_on returns False when unmountable count is 0."""
    mock_infra_coordinator.data = make_infra_data(vars_data=Vars(fs_num_unmountable=0))

    sensor = FilesystemsUnmountableBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is False


def test_filesystems_unmountable_none_data(mock_infra_coordinator):
    """Test is_on returns None when coordinator data is None."""
    mock_infra_coordinator.data = None

    sensor = FilesystemsUnmountableBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None
    assert sensor.extra_state_attributes == {}


def test_filesystems_unmountable_none_count(mock_infra_coordinator):
    """Test is_on returns None when fs_num_unmountable is None."""
    mock_infra_coordinator.data = make_infra_data(
        vars_data=Vars(fs_num_unmountable=None)
    )

    sensor = FilesystemsUnmountableBinarySensor(
        coordinator=mock_infra_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
    )

    assert sensor.is_on is None
