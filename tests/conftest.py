"""Shared pytest fixtures for Unraid integration tests."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from unraid_api.models import (
    ArrayCapacity,
    ArrayDisk,
    CapacityKilobytes,
    DockerContainer,
    ParityCheck,
    ServerInfo,
    Share,
    SystemMetrics,
    UnraidArray,
    UPSDevice,
    VmDomain,
)

from custom_components.unraid.coordinator import UnraidStorageData, UnraidSystemData

# Import pytest_homeassistant_custom_component's autouse fixtures
pytest_plugins = "pytest_homeassistant_custom_component"

# Fixtures directory path
FIXTURES = Path(__file__).parent / "fixtures"


def load_json(name: str) -> dict[str, Any]:
    """Load JSON fixture from fixtures directory."""
    return json.loads((FIXTURES / name).read_text())


def make_system_data(
    cpu_percent: float | None = None,
    memory_used: int | None = None,
    memory_total: int | None = None,
    memory_percent: float | None = None,
    memory_free: int | None = None,
    memory_available: int | None = None,
    cpu_temps: list[float] | None = None,
    cpu_power: float | None = None,
    uptime: str | datetime | None = None,  # ISO format string or datetime
    ups_devices: list[UPSDevice] | None = None,
    containers: list[DockerContainer] | None = None,
    vms: list[VmDomain] | None = None,
    notifications_unread: int = 0,
) -> UnraidSystemData:
    """Create a UnraidSystemData instance for testing."""
    from datetime import datetime

    uptime_dt = None
    if uptime:
        if isinstance(uptime, str):
            uptime_dt = datetime.fromisoformat(uptime)
        else:
            uptime_dt = uptime

    return UnraidSystemData(
        info=ServerInfo(
            uuid="test-uuid",
            hostname="tower",
            manufacturer="Lime Technology",
        ),
        metrics=SystemMetrics(
            cpu_percent=cpu_percent,
            cpu_temperature=cpu_temps[0] if cpu_temps else None,
            cpu_temperatures=cpu_temps or [],
            cpu_power=cpu_power,
            memory_percent=memory_percent,
            memory_total=memory_total,
            memory_used=memory_used,
            memory_free=memory_free,
            memory_available=memory_available,
            uptime=uptime_dt,
        ),
        ups_devices=ups_devices or [],
        containers=containers or [],
        vms=vms or [],
        notifications_unread=notifications_unread,
    )


# Sentinel value for explicitly unset optional params
_UNSET = object()


def make_storage_data(
    array_state: str | None = None,
    capacity: ArrayCapacity | None | object = _UNSET,
    parity_status: ParityCheck | None = None,
    disks: list[ArrayDisk] | None = None,
    parities: list[ArrayDisk] | None = None,
    caches: list[ArrayDisk] | None = None,
    shares: list[Share] | None = None,
    boot: ArrayDisk | None = None,
) -> UnraidStorageData:
    """Create a UnraidStorageData instance for testing."""
    # Provide default capacity only if not explicitly set
    if capacity is _UNSET:
        capacity = ArrayCapacity(
            kilobytes=CapacityKilobytes(total=1000, used=500, free=500)
        )
    if parity_status is None:
        parity_status = ParityCheck()

    # Create UnraidArray and wrap in UnraidStorageData
    array = UnraidArray(
        state=array_state,
        capacity=capacity,
        parityCheckStatus=parity_status,
        disks=disks or [],
        parities=parities or [],
        caches=caches or [],
        boot=boot,
    )
    return UnraidStorageData(
        array=array,
        shares=shares or [],
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """
    Enable custom integrations for all tests.

    This fixture uses the enable_custom_integrations fixture from
    pytest-homeassistant-custom-component to allow Home Assistant
    to load custom components from the custom_components directory.
    """
    return


@pytest.fixture
def mock_api_client():
    """Provide a mocked Unraid API client."""
    client = MagicMock()
    client.query.return_value = {}
    return client


@pytest.fixture
def hass_simple():
    """Provide a minimal HomeAssistant mock without Frame helper requirement."""
    hass = MagicMock()
    hass.data = {}
    hass.loop = None
    hass.config_entries = MagicMock()

    # Mock the frame helper to avoid "Frame helper not set up" error
    with patch("homeassistant.helpers.frame._hass.hass", hass):
        yield hass


@pytest.fixture
def mock_api():
    """Provide a mock API client with async methods."""
    client = MagicMock()
    client.query = AsyncMock()
    client.close = AsyncMock()
    return client
