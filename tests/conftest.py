"""Shared pytest fixtures for Unraid integration tests."""

from __future__ import annotations

import json
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion
from unraid_api.models import (
    ArrayCapacity,
    ArrayDisk,
    CapacityKilobytes,
    DockerContainer,
    NotificationOverview,
    NotificationOverviewCounts,
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


# =============================================================================
# Snapshot Testing Fixture
# =============================================================================


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


# Fixtures directory path
FIXTURES = Path(__file__).parent / "fixtures"


def load_json(name: str) -> dict[str, Any]:
    """Load JSON fixture from fixtures directory."""
    return json.loads((FIXTURES / name).read_text())


# =============================================================================
# Server Info Factory
# =============================================================================


def make_server_info(**kwargs: Any) -> ServerInfo:
    """Create a ServerInfo model for testing."""
    defaults = {
        "uuid": "test-uuid-123",
        "hostname": "tower",
        "sw_version": "7.2.0",
        "api_version": "4.29.2",
        "manufacturer": "Lime Technology",
        "serial_number": "12345",
        "hw_manufacturer": "ASUS",
        "hw_model": "Pro WS",
        "os_distro": "Unraid",
        "os_release": "7.2.0",
        "os_arch": "x86_64",
        "license_type": "Pro",
        "cpu_brand": "AMD Ryzen 7",
        "cpu_cores": 8,
        "cpu_threads": 16,
    }
    defaults.update(kwargs)
    return ServerInfo(**defaults)


# =============================================================================
# System Data Factory
# =============================================================================


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


# =============================================================================
# Unified Mock Client Fixture (HA Core Pattern)
# =============================================================================


def create_mock_unraid_client(
    server_info: ServerInfo | None = None,
    system_metrics: SystemMetrics | None = None,
    notification_overview: NotificationOverview | None = None,
    containers: list[DockerContainer] | None = None,
    vms: list[VmDomain] | None = None,
    ups_devices: list[UPSDevice] | None = None,
    array: UnraidArray | None = None,
    shares: list[Share] | None = None,
) -> MagicMock:
    """
    Create a mock UnraidClient with configurable responses.

    This follows the HA Core pattern for mock API clients, returning
    library typed models for all methods.
    """
    client = MagicMock()

    # Connection methods
    client.test_connection = AsyncMock(return_value=True)
    client.close = AsyncMock()

    # Server info (returns ServerInfo model)
    client.get_server_info = AsyncMock(return_value=server_info or make_server_info())

    # Version (returns dict)
    client.get_version = AsyncMock(
        return_value={
            "api": server_info.api_version if server_info else "4.29.2",
            "unraid": server_info.sw_version if server_info else "7.2.0",
        }
    )

    # System metrics (returns SystemMetrics model)
    default_metrics = SystemMetrics(
        cpu_percent=25.5,
        memory_percent=50.0,
        memory_total=17179869184,
        memory_used=8589934592,
        uptime=86400,
    )
    client.get_system_metrics = AsyncMock(
        return_value=system_metrics or default_metrics
    )

    # Notifications (returns NotificationOverview model)
    default_notifications = NotificationOverview(
        unread=NotificationOverviewCounts(total=0)
    )
    client.get_notification_overview = AsyncMock(
        return_value=notification_overview or default_notifications
    )

    # Docker containers (returns list of DockerContainer models)
    client.get_docker_containers = AsyncMock(return_value=containers or [])

    # VMs (returns list of VmDomain models)
    client.get_vms = AsyncMock(return_value=vms or [])

    # UPS devices (returns list of UPSDevice models)
    client.get_ups_info = AsyncMock(return_value=ups_devices or [])

    # Array data (returns UnraidArray model)
    default_array = UnraidArray(
        state="STARTED",
        capacity=ArrayCapacity(
            kilobytes=CapacityKilobytes(total=1000000, used=500000, free=500000)
        ),
        parityCheckStatus=ParityCheck(),
        disks=[],
        parities=[],
        caches=[],
        boot=None,
    )
    client.get_array = AsyncMock(return_value=array or default_array)

    # Shares (returns list of Share models)
    client.get_shares = AsyncMock(return_value=shares or [])

    return client


@pytest.fixture
def mock_unraid_client() -> Generator[MagicMock]:
    """
    Return a mocked UnraidClient with both modules patched.

    This unified fixture patches both the main module and config_flow
    to ensure consistent mocking throughout tests.
    """
    with (
        patch("custom_components.unraid.UnraidClient") as mock_client_class,
        patch(
            "custom_components.unraid.config_flow.UnraidClient",
            new=mock_client_class,
        ),
    ):
        client = create_mock_unraid_client()
        mock_client_class.return_value = client
        yield client


@pytest.fixture
def mock_unraid_client_factory() -> Generator[type]:
    """
    Return the mock client class for custom configuration.

    Use this when you need to customize the client behavior.
    """
    with (
        patch("custom_components.unraid.UnraidClient") as mock_client_class,
        patch(
            "custom_components.unraid.config_flow.UnraidClient",
            new=mock_client_class,
        ),
    ):
        yield mock_client_class


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Provide a mock config entry for coordinator tests."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.title = "Unraid Tower"
    entry.data = {
        "host": "192.168.1.100",
        "api_key": "test-api-key",
    }
    entry.options = {}
    return entry
