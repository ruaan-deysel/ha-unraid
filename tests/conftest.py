"""Shared pytest fixtures for Unraid integration tests."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.unraid.coordinator import UnraidStorageData, UnraidSystemData
from custom_components.unraid.models import (
    ArrayCapacity,
    ArrayDisk,
    CapacityKilobytes,
    CpuPackages,
    CpuUtilization,
    DockerContainer,
    InfoCpu,
    InfoOs,
    MemoryUtilization,
    Metrics,
    ParityCheck,
    Share,
    SystemInfo,
    UPSDevice,
    VmDomain,
)

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
    cpu_temps: list[float] | None = None,
    cpu_power: float | None = None,
    uptime: datetime | None = None,
    ups_devices: list[UPSDevice] | None = None,
    containers: list[DockerContainer] | None = None,
    vms: list[VmDomain] | None = None,
    notifications_unread: int = 0,
) -> UnraidSystemData:
    """Create a UnraidSystemData instance for testing."""
    return UnraidSystemData(
        info=SystemInfo(
            cpu=InfoCpu(
                packages=CpuPackages(temp=cpu_temps or [], totalPower=cpu_power)
            ),
            os=InfoOs(uptime=uptime),
        ),
        metrics=Metrics(
            cpu=CpuUtilization(percentTotal=cpu_percent),
            memory=MemoryUtilization(
                total=memory_total,
                used=memory_used,
                percentTotal=memory_percent,
            ),
        ),
        ups_devices=ups_devices or [],
        containers=containers or [],
        vms=vms or [],
        notifications_unread=notifications_unread,
    )


def make_storage_data(
    array_state: str | None = None,
    capacity: ArrayCapacity | None = None,
    parity_status: ParityCheck | None = None,
    disks: list[ArrayDisk] | None = None,
    parities: list[ArrayDisk] | None = None,
    caches: list[ArrayDisk] | None = None,
    shares: list[Share] | None = None,
    boot: ArrayDisk | None = None,
) -> UnraidStorageData:
    """Create a UnraidStorageData instance for testing."""
    # Provide default capacity if not specified and array_state is set
    if capacity is None and array_state is not None:
        capacity = ArrayCapacity(
            kilobytes=CapacityKilobytes(total=1000, used=500, free=500)
        )
    return UnraidStorageData(
        array_state=array_state,
        capacity=capacity,
        parity_status=parity_status,
        disks=disks or [],
        parities=parities or [],
        caches=caches or [],
        shares=shares or [],
        boot=boot,
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
