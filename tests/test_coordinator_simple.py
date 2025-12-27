"""Simple coordinator tests without full HA setup."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import ClientError, ClientResponseError
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.unraid.coordinator import (
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_system_coordinator_basic_attributes(mock_report, hass_simple, mock_api):
    """Test system coordinator has correct attributes."""
    coordinator = UnraidSystemCoordinator(hass_simple, mock_api, "tower")

    assert coordinator.name == "tower System"
    assert coordinator.update_interval == timedelta(seconds=30)


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_storage_coordinator_basic_attributes(mock_report, hass_simple, mock_api):
    """Test storage coordinator has correct attributes."""
    coordinator = UnraidStorageCoordinator(hass_simple, mock_api, "tower")

    assert coordinator.name == "tower Storage"
    assert coordinator.update_interval == timedelta(seconds=300)


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_system_coordinator_successful_data_fetch(
    mock_report, hass_simple, mock_api
):
    """Test system coordinator fetches and returns data."""
    mock_api.query.return_value = {
        "info": {"system": {"uuid": "test-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
        "vms": {"domains": []},
        "upsDevices": [],
        "notifications": {"overview": {"unread": {"total": 0}}},
    }

    coordinator = UnraidSystemCoordinator(hass_simple, mock_api, "tower")
    data = await coordinator._async_update_data()

    assert data is not None
    # Now returns UnraidSystemData dataclass instead of dict
    assert data.info is not None
    assert data.metrics is not None
    assert data.info.system.uuid == "test-123"
    assert data.metrics.cpu.percentTotal == 25.5


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_storage_coordinator_successful_data_fetch(
    mock_report, hass_simple, mock_api
):
    """Test storage coordinator fetches and returns data."""
    mock_api.query.return_value = {
        "array": {
            "state": "STARTED",
            "capacity": {"kilobytes": {"total": 1000, "used": 400, "free": 600}},
        },
        "disks": [],
        "shares": [],
    }

    coordinator = UnraidStorageCoordinator(hass_simple, mock_api, "tower")
    data = await coordinator._async_update_data()

    assert data is not None
    # Now returns UnraidStorageData dataclass instead of dict
    assert data.array_state == "STARTED"
    assert data.capacity is not None
    assert data.capacity.kilobytes.total == 1000


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_handles_network_error(mock_report, hass_simple, mock_api):
    """Test coordinator raises UpdateFailed on network error."""
    mock_api.query.side_effect = ClientError("Connection failed")

    coordinator = UnraidSystemCoordinator(hass_simple, mock_api, "tower")

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_handles_auth_error(mock_report, hass_simple, mock_api):
    """Test coordinator raises UpdateFailed on authentication error."""
    mock_api.query.side_effect = ClientResponseError(
        request_info=MagicMock(),
        history=(),
        status=401,
        message="Unauthorized",
    )

    coordinator = UnraidSystemCoordinator(hass_simple, mock_api, "tower")

    with pytest.raises(UpdateFailed, match="Authentication failed"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_handles_timeout(mock_report, hass_simple, mock_api):
    """Test coordinator raises UpdateFailed on timeout."""
    mock_api.query.side_effect = TimeoutError("Request timeout")

    coordinator = UnraidSystemCoordinator(hass_simple, mock_api, "tower")

    with pytest.raises(UpdateFailed, match="Request timeout"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_handles_generic_error(mock_report, hass_simple, mock_api):
    """Test coordinator raises UpdateFailed on unexpected error."""
    mock_api.query.side_effect = Exception("Something went wrong")

    coordinator = UnraidSystemCoordinator(hass_simple, mock_api, "tower")

    with pytest.raises(UpdateFailed, match="Unexpected error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_custom_update_interval(mock_report, hass_simple, mock_api):
    """Test coordinator accepts custom update interval."""
    coordinator = UnraidSystemCoordinator(
        hass_simple, mock_api, "tower", update_interval=60
    )

    assert coordinator.update_interval == timedelta(seconds=60)


@pytest.mark.asyncio
@patch("homeassistant.helpers.frame.report_usage")
async def test_coordinator_multiple_fetches(mock_report, hass_simple, mock_api):
    """Test coordinator handles multiple data fetches."""
    mock_api.query.return_value = {
        "info": {"system": {"uuid": "test-123"}},
        "metrics": {"cpu": {"percentTotal": 25.5}},
        "docker": {"containers": []},
    }

    coordinator = UnraidSystemCoordinator(hass_simple, mock_api, "tower")

    # First fetch
    data1 = await coordinator._async_update_data()
    assert data1 is not None

    # Second fetch
    data2 = await coordinator._async_update_data()
    assert data2 is not None

    # Verify called twice
    assert mock_api.query.call_count == 2
