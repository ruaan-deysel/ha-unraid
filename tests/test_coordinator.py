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
