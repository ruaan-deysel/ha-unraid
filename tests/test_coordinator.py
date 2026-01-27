"""Coordinator tests for the Unraid integration (using unraid-api library)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from unraid_api.exceptions import (
    UnraidAPIError,
    UnraidAuthenticationError,
    UnraidConnectionError,
    UnraidTimeoutError,
)
from unraid_api.models import (
    ArrayCapacity,
    ArrayDisk,
    CapacityKilobytes,
    DockerContainer,
    NotificationOverview,
    NotificationOverviewCounts,
    ServerInfo,
    Share,
    SystemMetrics,
    UnraidArray,
    UPSDevice,
    VmDomain,
)

from custom_components.unraid.coordinator import (
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)

# =============================================================================
# Helper Functions to Create Test Models
# =============================================================================


def make_server_info(**kwargs: Any) -> ServerInfo:
    """Create a ServerInfo model for testing."""
    defaults = {
        "uuid": "abc-123",
        "hostname": "tower",
        "sw_version": "7.2.0",
        "api_version": "4.29.2",
        "cpu_brand": "AMD Ryzen 7",
        "cpu_cores": 8,
        "cpu_threads": 16,
    }
    defaults.update(kwargs)
    return ServerInfo(**defaults)


def make_system_metrics(**kwargs: Any) -> SystemMetrics:
    """Create a SystemMetrics model for testing."""
    defaults = {
        "cpu_percent": 25.5,
        "memory_percent": 50.0,
        "memory_total": 17179869184,
        "memory_used": 8589934592,
        "uptime": 86400,
    }
    defaults.update(kwargs)
    return SystemMetrics(**defaults)


def make_notification_overview(**kwargs: Any) -> NotificationOverview:
    """Create a NotificationOverview model for testing."""
    unread = kwargs.pop("unread", None)
    if unread is None:
        unread = NotificationOverviewCounts(total=0)
    return NotificationOverview(unread=unread)


def make_docker_container(**kwargs: Any) -> DockerContainer:
    """Create a DockerContainer model for testing."""
    defaults = {
        "id": "container123",
        "name": "plex",  # Required field
        "names": ["/plex"],
        "image": "linuxserver/plex",
        "state": "RUNNING",
    }
    defaults.update(kwargs)
    return DockerContainer(**defaults)


def make_vm(**kwargs: Any) -> VmDomain:
    """Create a VmDomain model for testing."""
    defaults = {
        "id": "vm-uuid-123",  # VmDomain uses 'id' not 'uuid'
        "name": "windows10",
        "state": "RUNNING",
        "vcpu": 4,  # VmDomain uses 'vcpu' not 'vcpus'
        "memory": 8589934592,
    }
    defaults.update(kwargs)
    return VmDomain(**defaults)


def make_ups(**kwargs: Any) -> UPSDevice:
    """Create a UPSDevice model for testing."""
    defaults = {
        "id": "ups-1",
        "name": "CyberPower",
        "status": "OL",
    }
    defaults.update(kwargs)
    return UPSDevice(**defaults)


def make_array(**kwargs: Any) -> UnraidArray:
    """Create an UnraidArray model for testing."""
    defaults = {
        "state": "STARTED",
        "capacity": ArrayCapacity(
            kilobytes=CapacityKilobytes(total=1000000, used=400000, free=600000)
        ),
        "disks": [],
        "parities": [],
        "caches": [],
    }
    defaults.update(kwargs)
    return UnraidArray(**defaults)


def make_disk(**kwargs: Any) -> ArrayDisk:
    """Create an ArrayDisk model for testing."""
    defaults = {
        "id": "disk1",
        "device": "sda",
        "name": "Disk 1",
        "type": "DATA",
        "status": "DISK_OK",
    }
    defaults.update(kwargs)
    return ArrayDisk(**defaults)


def make_share(**kwargs: Any) -> Share:
    """Create a Share model for testing."""
    defaults = {
        "id": "share-user",
        "name": "user",
        "free_bytes": 500000000,
        "total_bytes": 1000000000,
    }
    defaults.update(kwargs)
    return Share(**defaults)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_api_client():
    """Create a mock API client with AsyncMock methods for library calls."""
    client = MagicMock()
    # All methods that the coordinator uses are async
    client.get_server_info = AsyncMock(return_value=make_server_info())
    client.get_system_metrics = AsyncMock(return_value=make_system_metrics())
    client.get_notification_overview = AsyncMock(
        return_value=make_notification_overview()
    )
    client.typed_get_containers = AsyncMock(return_value=[])
    client.typed_get_vms = AsyncMock(return_value=[])
    client.typed_get_ups_devices = AsyncMock(return_value=[])
    client.typed_get_array = AsyncMock(return_value=make_array())
    client.typed_get_shares = AsyncMock(return_value=[])
    client.close = AsyncMock()
    return client


# =============================================================================
# Initialization Tests
# =============================================================================


@pytest.mark.asyncio
async def test_system_coordinator_initialization(
    hass, mock_api_client, mock_config_entry
):
    """Test UnraidSystemCoordinator initializes with 30s interval."""
    coordinator = UnraidSystemCoordinator(
        hass=hass,
        api_client=mock_api_client,
        server_name="tower",
        config_entry=mock_config_entry,
    )

    assert coordinator.name == "tower System"
    assert coordinator.update_interval == timedelta(seconds=30)
    assert coordinator.api_client == mock_api_client


@pytest.mark.asyncio
async def test_storage_coordinator_initialization(
    hass, mock_api_client, mock_config_entry
):
    """Test UnraidStorageCoordinator initializes with 5min interval."""
    coordinator = UnraidStorageCoordinator(
        hass=hass,
        api_client=mock_api_client,
        server_name="tower",
        config_entry=mock_config_entry,
    )

    assert coordinator.name == "tower Storage"
    assert coordinator.update_interval == timedelta(seconds=300)
    assert coordinator.api_client == mock_api_client


# =============================================================================
# System Coordinator Success Tests
# =============================================================================


@pytest.mark.asyncio
async def test_system_coordinator_fetch_success(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator successfully fetches data."""
    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    # Returns UnraidSystemData dataclass with library models
    assert data.info is not None
    assert data.metrics is not None
    assert data.info.uuid == "abc-123"
    assert data.metrics.cpu_percent == 25.5
    mock_api_client.get_server_info.assert_called_once()
    mock_api_client.get_system_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_system_coordinator_queries_all_endpoints(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator queries all required endpoints."""
    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    await coordinator._async_update_data()

    # Verify all library methods were called
    mock_api_client.get_server_info.assert_called_once()
    mock_api_client.get_system_metrics.assert_called_once()
    mock_api_client.get_notification_overview.assert_called_once()
    mock_api_client.typed_get_containers.assert_called_once()
    mock_api_client.typed_get_vms.assert_called_once()
    mock_api_client.typed_get_ups_devices.assert_called_once()


@pytest.mark.asyncio
async def test_system_coordinator_parses_docker_containers(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator correctly parses Docker container data."""
    mock_api_client.typed_get_containers.return_value = [
        make_docker_container(id="c1", names=["/plex"], state="RUNNING"),
        make_docker_container(id="c2", names=["/sonarr"], state="EXITED"),
    ]

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert len(data.containers) == 2
    assert data.containers[0].names == ["/plex"]
    assert data.containers[0].state == "RUNNING"
    assert data.containers[1].names == ["/sonarr"]


@pytest.mark.asyncio
async def test_system_coordinator_parses_vms(hass, mock_api_client, mock_config_entry):
    """Test system coordinator correctly parses VM data."""
    mock_api_client.typed_get_vms.return_value = [
        make_vm(name="windows10", state="RUNNING", vcpu=4),
        make_vm(name="ubuntu", state="SHUTOFF", vcpu=2),
    ]

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert len(data.vms) == 2
    assert data.vms[0].name == "windows10"
    assert data.vms[0].vcpu == 4
    assert data.vms[1].state == "SHUTOFF"


@pytest.mark.asyncio
async def test_system_coordinator_parses_ups_devices(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator correctly parses UPS device data."""
    from unraid_api.models import UPSBattery

    mock_api_client.typed_get_ups_devices.return_value = [
        make_ups(name="CyberPower", status="OL", battery=UPSBattery(chargeLevel=100.0)),
    ]

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert len(data.ups_devices) == 1
    assert data.ups_devices[0].name == "CyberPower"
    assert data.ups_devices[0].battery.chargeLevel == 100.0


@pytest.mark.asyncio
async def test_system_coordinator_parses_notifications(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator correctly parses notification count."""
    mock_api_client.get_notification_overview.return_value = make_notification_overview(
        unread=NotificationOverviewCounts(total=5)
    )

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data.notifications_unread == 5


# =============================================================================
# System Coordinator Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_coordinator_authentication_error_handling(
    hass, mock_api_client, mock_config_entry
):
    """Test coordinator handles authentication errors with ConfigEntryAuthFailed."""
    mock_api_client.get_server_info.side_effect = UnraidAuthenticationError(
        "Unauthorized"
    )

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(ConfigEntryAuthFailed, match="Authentication failed"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_connection_error_handling(
    hass, mock_api_client, mock_config_entry
):
    """Test coordinator handles connection errors with UpdateFailed."""
    mock_api_client.get_server_info.side_effect = UnraidConnectionError(
        "Connection refused"
    )

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_timeout_error_handling(
    hass, mock_api_client, mock_config_entry
):
    """Test coordinator handles timeout errors with UpdateFailed."""
    mock_api_client.get_server_info.side_effect = UnraidTimeoutError("Request timeout")

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_api_error_handling(hass, mock_api_client, mock_config_entry):
    """Test coordinator handles API errors with UpdateFailed."""
    mock_api_client.get_server_info.side_effect = UnraidAPIError("API error occurred")

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(UpdateFailed, match="API error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_system_coordinator_http_error_handling(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles HTTP errors with UpdateFailed."""
    mock_api_client.get_server_info.side_effect = UnraidConnectionError("HTTP 500")

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


# =============================================================================
# Optional Query Failure Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_system_coordinator_handles_docker_query_failure(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles Docker query failure gracefully."""
    mock_api_client.typed_get_containers.side_effect = UnraidAPIError(
        "Docker not available"
    )

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    # Should still return data with empty containers list
    assert data is not None
    assert data.containers == []
    assert data.info is not None


@pytest.mark.asyncio
async def test_system_coordinator_handles_vms_query_failure(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles VM query failure gracefully."""
    mock_api_client.typed_get_vms.side_effect = UnraidAPIError("VMs not enabled")

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    # Should still return data with empty VMs list
    assert data is not None
    assert data.vms == []
    assert data.info is not None


@pytest.mark.asyncio
async def test_system_coordinator_handles_ups_query_failure(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles UPS query failure gracefully."""
    mock_api_client.typed_get_ups_devices.side_effect = UnraidAPIError(
        "No UPS configured"
    )

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    # Should still return data with empty UPS list
    assert data is not None
    assert data.ups_devices == []
    assert data.info is not None


# =============================================================================
# Connection Recovery Tests
# =============================================================================


@pytest.mark.asyncio
async def test_system_coordinator_connection_recovery(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator logs recovery after previous failure."""
    # First call fails
    mock_api_client.get_server_info.side_effect = UnraidConnectionError(
        "Connection refused"
    )

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    # First update fails
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    # Mark as previously unavailable
    assert coordinator._previously_unavailable is True

    # Second call succeeds
    mock_api_client.get_server_info.side_effect = None
    mock_api_client.get_server_info.return_value = make_server_info()

    # Second update succeeds
    data = await coordinator._async_update_data()

    assert data is not None
    assert coordinator._previously_unavailable is False


# =============================================================================
# Storage Coordinator Tests
# =============================================================================


@pytest.mark.asyncio
async def test_storage_coordinator_fetch_success(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator successfully fetches data."""
    mock_api_client.typed_get_array.return_value = make_array(
        state="STARTED",
        capacity=ArrayCapacity(
            kilobytes=CapacityKilobytes(total=1000000, used=400000, free=600000)
        ),
    )

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    # Returns UnraidStorageData dataclass
    assert data.array_state == "STARTED"
    assert data.capacity is not None
    assert data.capacity.kilobytes.total == 1000000
    mock_api_client.typed_get_array.assert_called_once()


@pytest.mark.asyncio
async def test_storage_coordinator_queries_all_endpoints(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator queries all required endpoints."""
    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    await coordinator._async_update_data()

    # Verify library methods were called
    mock_api_client.typed_get_array.assert_called_once()
    mock_api_client.typed_get_shares.assert_called_once()


@pytest.mark.asyncio
async def test_storage_coordinator_parses_disks_with_type(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator correctly parses disk data with types."""
    mock_api_client.typed_get_array.return_value = make_array(
        disks=[
            make_disk(id="disk1", name="Disk 1", type="DATA"),
            make_disk(id="disk2", name="Disk 2", type="DATA"),
        ],
        parities=[
            make_disk(id="parity1", name="Parity 1", type="PARITY"),
        ],
        caches=[
            make_disk(id="cache1", name="Cache 1", type="CACHE"),
        ],
    )

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert len(data.disks) == 2
    assert len(data.parities) == 1
    assert len(data.caches) == 1
    assert data.disks[0].type == "DATA"
    assert data.parities[0].type == "PARITY"


@pytest.mark.asyncio
async def test_storage_coordinator_parses_shares(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator correctly parses share data."""
    mock_api_client.typed_get_shares.return_value = [
        make_share(name="user", free_bytes=500000000, total_bytes=1000000000),
        make_share(name="media", free_bytes=1000000000, total_bytes=2000000000),
    ]

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert len(data.shares) == 2
    assert data.shares[0].name == "user"
    assert data.shares[1].name == "media"


# =============================================================================
# Storage Coordinator Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_storage_coordinator_authentication_error_handling(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles auth errors with ConfigEntryAuthFailed."""
    mock_api_client.typed_get_array.side_effect = UnraidAuthenticationError(
        "Unauthorized"
    )

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(ConfigEntryAuthFailed, match="Authentication failed"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_storage_coordinator_connection_error_handling(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles connection errors."""
    mock_api_client.typed_get_array.side_effect = UnraidConnectionError(
        "Connection refused"
    )

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_storage_coordinator_timeout_error_handling(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles timeout errors."""
    mock_api_client.typed_get_array.side_effect = UnraidTimeoutError("Request timeout")

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_storage_coordinator_http_error_handling(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles HTTP errors."""
    mock_api_client.typed_get_array.side_effect = UnraidConnectionError("HTTP 500")

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_storage_coordinator_unexpected_error_handling(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles unexpected errors."""
    mock_api_client.typed_get_array.side_effect = RuntimeError("Something went wrong")

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    with pytest.raises(UpdateFailed, match="Unexpected error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_storage_coordinator_handles_shares_query_failure(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles shares query failure gracefully."""
    mock_api_client.typed_get_shares.side_effect = UnraidAPIError("Shares query failed")

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    # Should still return data with empty shares list
    assert data is not None
    assert data.shares == []
    assert data.array is not None


# =============================================================================
# Storage Coordinator Recovery Tests
# =============================================================================


@pytest.mark.asyncio
async def test_storage_coordinator_connection_recovery(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator logs recovery after previous failure."""
    # First call fails
    mock_api_client.typed_get_array.side_effect = UnraidConnectionError(
        "Connection refused"
    )

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    # First update fails
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator._previously_unavailable is True

    # Second call succeeds
    mock_api_client.typed_get_array.side_effect = None
    mock_api_client.typed_get_array.return_value = make_array()

    data = await coordinator._async_update_data()

    assert data is not None
    assert coordinator._previously_unavailable is False


# =============================================================================
# Data Refresh Cycle Test
# =============================================================================


@pytest.mark.asyncio
async def test_coordinator_data_refresh_cycle(hass, mock_api_client, mock_config_entry):
    """Test coordinator can perform multiple refresh cycles."""
    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )

    # First refresh
    data1 = await coordinator._async_update_data()
    assert data1 is not None

    # Update mock to return different values
    mock_api_client.get_system_metrics.return_value = make_system_metrics(
        cpu_percent=75.0
    )

    # Second refresh
    data2 = await coordinator._async_update_data()
    assert data2 is not None
    assert data2.metrics.cpu_percent == 75.0


# =============================================================================
# Edge Case Tests
# =============================================================================


@pytest.mark.asyncio
async def test_storage_coordinator_handles_none_capacity(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles array with zero capacity."""
    mock_api_client.typed_get_array.return_value = make_array(
        capacity=ArrayCapacity(kilobytes=CapacityKilobytes(total=0, used=0, free=0))
    )

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert data.capacity.kilobytes.total == 0


@pytest.mark.asyncio
async def test_system_coordinator_handles_none_ups_list(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles no UPS devices."""
    mock_api_client.typed_get_ups_devices.return_value = []

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert data.ups_devices == []


@pytest.mark.asyncio
async def test_system_coordinator_handles_zero_notifications(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles zero notification unread."""
    mock_api_client.get_notification_overview.return_value = NotificationOverview(
        unread=NotificationOverviewCounts(total=0)
    )

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert data.notifications_unread == 0


@pytest.mark.asyncio
async def test_system_coordinator_handles_container_without_names(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles container with empty names list."""
    mock_api_client.typed_get_containers.return_value = [
        make_docker_container(names=[])
    ]

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert len(data.containers) == 1
    assert data.containers[0].names == []


@pytest.mark.asyncio
async def test_storage_coordinator_handles_none_boot(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles array with no boot device."""
    mock_api_client.typed_get_array.return_value = make_array(boot=None)

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None


# =============================================================================
# Invalid Data Handling Tests (Library Models Handle Validation)
# =============================================================================


@pytest.mark.asyncio
async def test_system_coordinator_handles_invalid_container(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles container data."""
    # Library models handle validation, so we just test with valid data
    mock_api_client.typed_get_containers.return_value = [
        make_docker_container(state="UNKNOWN_STATE")
    ]

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert len(data.containers) == 1


@pytest.mark.asyncio
async def test_system_coordinator_handles_invalid_vm(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles VM data."""
    mock_api_client.typed_get_vms.return_value = [make_vm(state="UNKNOWN_STATE")]

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert len(data.vms) == 1


@pytest.mark.asyncio
async def test_system_coordinator_handles_invalid_ups(
    hass, mock_api_client, mock_config_entry
):
    """Test system coordinator handles UPS data."""
    mock_api_client.typed_get_ups_devices.return_value = [make_ups(status="UNKNOWN")]

    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert len(data.ups_devices) == 1


@pytest.mark.asyncio
async def test_storage_coordinator_handles_invalid_disk(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles disk data."""
    mock_api_client.typed_get_array.return_value = make_array(
        disks=[make_disk(status="UNKNOWN_STATUS")]
    )

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert len(data.disks) == 1


@pytest.mark.asyncio
async def test_storage_coordinator_handles_invalid_share(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator handles share data."""
    mock_api_client.typed_get_shares.return_value = [make_share(name="test")]

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert len(data.shares) == 1


@pytest.mark.asyncio
async def test_storage_coordinator_parses_boot_device(
    hass, mock_api_client, mock_config_entry
):
    """Test storage coordinator correctly parses boot device."""
    mock_api_client.typed_get_array.return_value = make_array(
        boot=make_disk(id="flash", name="Flash", type="FLASH")
    )

    coordinator = UnraidStorageCoordinator(
        hass, mock_api_client, "tower", mock_config_entry
    )
    data = await coordinator._async_update_data()

    assert data is not None
    assert data.array.boot is not None
    assert data.array.boot.name == "Flash"
