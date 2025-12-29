"""Coordinator tests for the Unraid integration."""

from __future__ import annotations

import builtins
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.unraid.coordinator import (
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = MagicMock()
    client.query = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_system_coordinator_initialization(hass, mock_api_client):
    """Test UnraidSystemCoordinator initializes with 30s interval."""
    coordinator = UnraidSystemCoordinator(
        hass=hass,
        api_client=mock_api_client,
        server_name="tower",
    )

    assert coordinator.name == "tower System"
    assert coordinator.update_interval == timedelta(seconds=30)
    assert coordinator.api_client == mock_api_client


@pytest.mark.asyncio
async def test_storage_coordinator_initialization(hass, mock_api_client):
    """Test UnraidStorageCoordinator initializes with 5min interval."""
    coordinator = UnraidStorageCoordinator(
        hass=hass,
        api_client=mock_api_client,
        server_name="tower",
    )

    assert coordinator.name == "tower Storage"
    assert coordinator.update_interval == timedelta(seconds=300)
    assert coordinator.api_client == mock_api_client


@pytest.mark.asyncio
async def test_system_coordinator_fetch_success(hass, mock_api_client):
    """Test system coordinator successfully fetches data."""
    mock_api_client.query.return_value = {
        "info": {
            "time": "2025-12-23T10:30:00Z",
            "system": {"uuid": "abc-123"},
            "cpu": {"brand": "AMD Ryzen", "packages": {"temp": [45.2]}},
            "os": {"hostname": "tower"},
            "versions": {"core": {"unraid": "7.2.0", "api": "4.29.2"}},
        },
        "metrics": {
            "cpu": {"percentTotal": 25.5},
            "memory": {"total": 17179869184, "used": 8589934592, "percentTotal": 50.0},
        },
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert data is not None
    # Now returns UnraidSystemData dataclass instead of dict
    assert data.info is not None
    assert data.metrics is not None
    assert data.info.system.uuid == "abc-123"
    assert data.metrics.cpu.percentTotal == 25.5
    assert mock_api_client.query.call_count >= 1


@pytest.mark.asyncio
async def test_storage_coordinator_fetch_success(hass, mock_api_client):
    """Test storage coordinator successfully fetches data."""
    mock_api_client.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": {
                "kilobytes": {"total": 1000000, "used": 400000, "free": 600000}
            },
            "disks": [],
            "parities": [],
            "caches": [],
        },
        "disks": [],
        "shares": [],
    }

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert data is not None
    # Now returns UnraidStorageData dataclass instead of dict
    assert data.array_state == "STARTED"
    assert data.capacity is not None
    assert data.capacity.kilobytes.total == 1000000
    assert mock_api_client.query.call_count >= 1


@pytest.mark.asyncio
async def test_coordinator_network_error_handling(hass, mock_api_client):
    """Test coordinator handles network errors with UpdateFailed."""
    from aiohttp import ClientError

    mock_api_client.query.side_effect = ClientError("Connection refused")

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="Connection refused"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_authentication_error_handling(hass, mock_api_client):
    """Test coordinator handles authentication errors with UpdateFailed."""
    from aiohttp import ClientResponseError

    mock_api_client.query.side_effect = ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=401,
        message="Unauthorized",
    )

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="Authentication failed"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_graphql_error_handling(hass, mock_api_client):
    """Test coordinator handles GraphQL errors with UpdateFailed."""
    mock_api_client.query.side_effect = Exception("GraphQL errors: Field not found")

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="GraphQL errors"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_timeout_error_handling(hass, mock_api_client):
    """Test coordinator handles timeout errors with UpdateFailed."""
    mock_api_client.query.side_effect = builtins.TimeoutError("Request timeout")

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="timeout"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_system_coordinator_queries_all_endpoints(hass, mock_api_client):
    """Test system coordinator queries all required endpoints."""
    mock_response = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }
    mock_api_client.query.return_value = mock_response

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    await coordinator._async_update_data()

    # Verify query was called (may be combined into one or multiple queries)
    assert mock_api_client.query.called
    call_args = mock_api_client.query.call_args[0][0]

    # Check that query includes key fields
    assert "info" in call_args.lower() or "metrics" in call_args.lower()


@pytest.mark.asyncio
async def test_storage_coordinator_queries_all_endpoints(hass, mock_api_client):
    """Test storage coordinator queries all required endpoints."""
    mock_response = {
        "array": {
            "state": "STARTED",
            "capacity": {
                "kilobytes": {"total": 1000000, "used": 400000, "free": 600000}
            },
            "disks": [],
        },
        "disks": [],
    }
    mock_api_client.query.return_value = mock_response

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")
    await coordinator._async_update_data()

    # Verify query was called
    assert mock_api_client.query.called
    call_args = mock_api_client.query.call_args[0][0]

    # Check that query includes array/disks fields
    assert "array" in call_args.lower() or "disks" in call_args.lower()


@pytest.mark.asyncio
async def test_coordinator_custom_interval(hass, mock_api_client):
    """Test coordinators can use custom intervals."""
    coordinator = UnraidSystemCoordinator(
        hass, mock_api_client, "tower", update_interval=60
    )

    assert coordinator.update_interval == timedelta(seconds=60)


@pytest.mark.asyncio
async def test_coordinator_data_refresh_cycle(hass, mock_api_client):
    """Test coordinator handles multiple refresh cycles."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")

    # First refresh
    data1 = await coordinator._async_update_data()
    assert data1 is not None
    assert data1.metrics.cpu.percentTotal == 25.5

    # Second refresh
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 35.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }
    data2 = await coordinator._async_update_data()
    assert data2 is not None
    assert data2.metrics.cpu.percentTotal == 35.5


# =============================================================================
# Storage Coordinator Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_storage_coordinator_network_error_handling(hass, mock_api_client):
    """Test storage coordinator handles network errors with UpdateFailed."""
    from aiohttp import ClientError

    mock_api_client.query.side_effect = ClientError("Connection refused")

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_storage_coordinator_authentication_error_handling(hass, mock_api_client):
    """Test storage coordinator handles authentication errors with UpdateFailed."""
    from aiohttp import ClientResponseError

    mock_api_client.query.side_effect = ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=403,
        message="Forbidden",
    )

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="Authentication failed"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_storage_coordinator_http_error_handling(hass, mock_api_client):
    """Test storage coordinator handles HTTP errors with UpdateFailed."""
    from aiohttp import ClientResponseError

    mock_api_client.query.side_effect = ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=500,
        message="Internal Server Error",
    )

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="HTTP error 500"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_storage_coordinator_timeout_error_handling(hass, mock_api_client):
    """Test storage coordinator handles timeout errors with UpdateFailed."""
    import builtins

    mock_api_client.query.side_effect = builtins.TimeoutError("Timeout")

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="timeout"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_storage_coordinator_unexpected_error_handling(hass, mock_api_client):
    """Test storage coordinator handles unexpected errors with UpdateFailed."""
    mock_api_client.query.side_effect = ValueError("Unexpected error")

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="Unexpected error"):
        await coordinator._async_update_data()


# =============================================================================
# System Coordinator HTTP Error Tests
# =============================================================================


@pytest.mark.asyncio
async def test_system_coordinator_http_error_handling(hass, mock_api_client):
    """Test system coordinator handles non-auth HTTP errors."""
    from aiohttp import ClientResponseError

    mock_api_client.query.side_effect = ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=500,
        message="Server Error",
    )

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed, match="HTTP error 500"):
        await coordinator._async_update_data()


# =============================================================================
# Connection Recovery Tests
# =============================================================================


@pytest.mark.asyncio
async def test_system_coordinator_connection_recovery(hass, mock_api_client, caplog):
    """Test system coordinator logs connection recovery."""
    from aiohttp import ClientError

    # First call fails
    mock_api_client.query.side_effect = ClientError("Connection refused")
    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    # Now simulate recovery
    mock_api_client.query.side_effect = None
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    data = await coordinator._async_update_data()
    assert data is not None
    assert "Connection restored" in caplog.text


@pytest.mark.asyncio
async def test_storage_coordinator_connection_recovery(hass, mock_api_client, caplog):
    """Test storage coordinator logs connection recovery."""
    from aiohttp import ClientError

    # First call fails
    mock_api_client.query.side_effect = ClientError("Connection refused")
    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    # Now simulate recovery
    mock_api_client.query.side_effect = None
    mock_api_client.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": {"kilobytes": {"total": 1000, "used": 500, "free": 500}},
            "disks": [],
            "parities": [],
            "caches": [],
        },
        "shares": [],
    }

    data = await coordinator._async_update_data()
    assert data is not None
    assert "Connection restored" in caplog.text


# =============================================================================
# Parsing Tests
# =============================================================================


@pytest.mark.asyncio
async def test_system_coordinator_parses_docker_containers(hass, mock_api_client):
    """Test system coordinator correctly parses Docker containers."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {
            "containers": [
                {
                    "id": "ct:1",
                    "names": ["/plex"],
                    "state": "RUNNING",
                    "image": "plexinc/pms-docker",
                    "ports": [
                        {"privatePort": 32400, "publicPort": 32400, "type": "tcp"}
                    ],
                }
            ]
        },
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert len(data.containers) == 1
    assert data.containers[0].name == "plex"  # Should strip leading /
    assert data.containers[0].state == "RUNNING"


@pytest.mark.asyncio
async def test_system_coordinator_parses_vms(hass, mock_api_client):
    """Test system coordinator correctly parses VMs."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {
            "domains": [
                {"id": "vm:1", "name": "Ubuntu", "state": "RUNNING"},
                {"id": "vm:2", "name": "Windows", "state": "SHUTOFF"},
            ]
        },
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert len(data.vms) == 2
    assert data.vms[0].name == "Ubuntu"
    assert data.vms[1].state == "SHUTOFF"


@pytest.mark.asyncio
async def test_system_coordinator_parses_ups_devices(hass, mock_api_client):
    """Test system coordinator correctly parses UPS devices."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [
            {
                "id": "ups:1",
                "name": "APC UPS",
                "status": "Online",
                "battery": {"chargeLevel": 100, "estimatedRuntime": 1800},
                "power": {"loadPercentage": 25.5},
            }
        ],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert len(data.ups_devices) == 1
    assert data.ups_devices[0].name == "APC UPS"
    assert data.ups_devices[0].battery.chargeLevel == 100


@pytest.mark.asyncio
async def test_system_coordinator_parses_notifications(hass, mock_api_client):
    """Test system coordinator correctly parses notifications."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 5}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert data.notifications_unread == 5


@pytest.mark.asyncio
async def test_system_coordinator_handles_invalid_container(
    hass, mock_api_client, caplog
):
    """Test system coordinator skips invalid containers."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {
            "containers": [
                {"id": "ct:1", "names": ["/good"], "state": "RUNNING"},
                {"invalid": "data"},  # Missing required fields
            ]
        },
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert len(data.containers) == 1
    assert "Failed to parse container" in caplog.text


@pytest.mark.asyncio
async def test_system_coordinator_handles_invalid_vm(hass, mock_api_client, caplog):
    """Test system coordinator skips invalid VMs."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {
            "domains": [
                {"id": "vm:1", "name": "Good", "state": "RUNNING"},
                {"invalid": "vm_data"},  # Missing required fields
            ]
        },
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert len(data.vms) == 1
    assert "Failed to parse VM" in caplog.text


@pytest.mark.asyncio
async def test_system_coordinator_handles_invalid_ups(hass, mock_api_client, caplog):
    """Test system coordinator skips invalid UPS devices."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [
            {"id": "ups:1", "name": "Good UPS", "status": "Online"},
            {"invalid": "ups_data"},  # Missing required fields
        ],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert len(data.ups_devices) == 1
    assert "Failed to parse UPS" in caplog.text


@pytest.mark.asyncio
async def test_storage_coordinator_parses_disks_with_type(hass, mock_api_client):
    """Test storage coordinator sets default disk types."""
    mock_api_client.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": {"kilobytes": {"total": 1000, "used": 500, "free": 500}},
            "disks": [
                {"id": "disk:1", "idx": 1, "name": "Disk 1"},  # No type
            ],
            "parities": [
                {"id": "parity:1", "idx": 0, "name": "Parity"},  # No type
            ],
            "caches": [
                {"id": "cache:1", "idx": 0, "name": "Cache"},  # No type
            ],
        },
        "shares": [],
    }

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert data.disks[0].type == "DATA"
    assert data.parities[0].type == "PARITY"
    assert data.caches[0].type == "CACHE"


@pytest.mark.asyncio
async def test_storage_coordinator_parses_boot_device(hass, mock_api_client):
    """Test storage coordinator parses boot device."""
    mock_api_client.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": {"kilobytes": {"total": 1000, "used": 500, "free": 500}},
            "boot": {
                "id": "boot:1",
                "name": "Flash",
                "device": "sde",
                "fsSize": 32000,
                "fsUsed": 8000,
                "fsFree": 24000,
            },
            "disks": [],
            "parities": [],
            "caches": [],
        },
        "shares": [],
    }

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert data.boot is not None
    assert data.boot.name == "Flash"
    assert data.boot.type == "FLASH"  # Default type set


@pytest.mark.asyncio
async def test_storage_coordinator_parses_shares(hass, mock_api_client):
    """Test storage coordinator parses shares."""
    mock_api_client.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": {"kilobytes": {"total": 1000, "used": 500, "free": 500}},
            "disks": [],
            "parities": [],
            "caches": [],
        },
        "shares": [
            {
                "id": "share:1",
                "name": "appdata",
                "size": 100000,
                "used": 50000,
                "free": 50000,
            },
            {
                "id": "share:2",
                "name": "media",
                "size": 500000,
                "used": 400000,
                "free": 100000,
            },
        ],
    }

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert len(data.shares) == 2
    assert data.shares[0].name == "appdata"
    assert data.shares[1].name == "media"


@pytest.mark.asyncio
async def test_storage_coordinator_handles_invalid_disk(hass, mock_api_client, caplog):
    """Test storage coordinator skips invalid disks."""
    mock_api_client.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": {"kilobytes": {"total": 1000, "used": 500, "free": 500}},
            "disks": [
                {"id": "disk:1", "idx": 1, "name": "Good Disk"},
                {"invalid": "disk_data"},  # Missing required id field
            ],
            "parities": [],
            "caches": [],
        },
        "shares": [],
    }

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert len(data.disks) == 1
    assert "Failed to parse disk" in caplog.text


@pytest.mark.asyncio
async def test_storage_coordinator_handles_invalid_share(hass, mock_api_client, caplog):
    """Test storage coordinator skips invalid shares."""
    mock_api_client.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": {"kilobytes": {"total": 1000, "used": 500, "free": 500}},
            "disks": [],
            "parities": [],
            "caches": [],
        },
        "shares": [
            {"id": "share:1", "name": "good"},
            {"invalid": "share_data"},  # Missing required fields
        ],
    }

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert len(data.shares) == 1
    assert "Failed to parse share" in caplog.text


@pytest.mark.asyncio
async def test_storage_coordinator_handles_none_boot(hass, mock_api_client):
    """Test storage coordinator handles missing boot device."""
    mock_api_client.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": {"kilobytes": {"total": 1000, "used": 500, "free": 500}},
            "boot": None,
            "disks": [],
            "parities": [],
            "caches": [],
        },
        "shares": [],
    }

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert data.boot is None


@pytest.mark.asyncio
async def test_storage_coordinator_handles_none_capacity(hass, mock_api_client):
    """Test storage coordinator handles missing capacity."""
    mock_api_client.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": None,
            "disks": [],
            "parities": [],
            "caches": [],
        },
        "shares": [],
    }

    coordinator = UnraidStorageCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert data.capacity is None


@pytest.mark.asyncio
async def test_system_coordinator_handles_none_ups_list(hass, mock_api_client):
    """Test system coordinator handles None upsDevices list."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": None,  # Can be None instead of empty list
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert data.ups_devices == []


@pytest.mark.asyncio
async def test_system_coordinator_handles_none_notifications(hass, mock_api_client):
    """Test system coordinator handles missing notifications count."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": None}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    assert data.notifications_unread == 0


@pytest.mark.asyncio
async def test_system_coordinator_handles_container_without_names(
    hass, mock_api_client, caplog
):
    """Test system coordinator handles container without names list."""
    mock_api_client.query.return_value = {
        "info": {"system": {"uuid": "abc-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {
            "containers": [
                {"id": "ct:1", "names": [], "state": "RUNNING"},  # Empty names list
            ]
        },
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass, mock_api_client, "tower")
    data = await coordinator._async_update_data()

    # Container without name is skipped due to validation error
    assert len(data.containers) == 0
    assert "Failed to parse container" in caplog.text
