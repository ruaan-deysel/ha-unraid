"""Tests for Unraid switch entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError
from unraid_api.models import ArrayDisk, DockerContainer, ParityCheck, VmDomain

from custom_components.unraid import UnraidRuntimeData
from custom_components.unraid.coordinator import (
    UnraidStorageCoordinator,
    UnraidSystemCoordinator,
)
from custom_components.unraid.switch import (
    ArraySwitch,
    DiskSpinSwitch,
    DockerContainerSwitch,
    ParityCheckSwitch,
    VirtualMachineSwitch,
    async_setup_entry,
)
from tests.conftest import make_storage_data, make_system_data

# =============================================================================
# DockerContainerSwitch Tests
# =============================================================================


def test_container_switch_creation() -> None:
    """Test Docker container switch creation."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        image="nginx:latest",
        webUiUrl="https://tower/apps/web",
        iconUrl="https://cdn/icons/web.png",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    # unique_id uses container NAME (stable) not ID (ephemeral)
    assert switch.unique_id == "test-uuid_container_switch_web"
    assert switch._attr_translation_key == "docker_container"
    assert switch._attr_translation_placeholders == {"name": "web"}
    assert switch.device_info is not None


def test_container_switch_is_on_when_running() -> None:
    """Test container switch is on when running."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    assert switch.is_on is True


def test_container_switch_is_off_when_stopped() -> None:
    """Test container switch is off when stopped."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="EXITED",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    assert switch.is_on is False


def test_container_switch_attributes() -> None:
    """Test container switch extra attributes."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
        image="nginx:latest",
        imageId="sha256:abc123",
        autoStart=True,
        webUiUrl="https://tower/apps/web",
        iconUrl="https://cdn/icons/web.png",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    attrs = switch.extra_state_attributes
    assert attrs["status"] == "RUNNING"
    assert attrs["image"] == "nginx:latest"
    assert attrs["image_id"] == "sha256:abc123"
    assert attrs["auto_start"] is True
    assert attrs["web_ui_url"] == "https://tower/apps/web"
    assert attrs["icon_url"] == "https://cdn/icons/web.png"


def test_container_switch_attributes_filters_none() -> None:
    """Test container switch filters out None values from attributes."""
    container = DockerContainer(
        id="ct:1",
        name="/minimal",
        state="RUNNING",
        # All optional fields are None by default
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    attrs = switch.extra_state_attributes
    # Only status should be present (always set)
    assert attrs == {"status": "RUNNING"}
    assert "image" not in attrs
    assert "web_ui_url" not in attrs
    assert "icon_url" not in attrs


def test_container_switch_no_data() -> None:
    """Test container switch when coordinator has no data."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None
    api_client = MagicMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    assert switch.is_on is False
    assert switch.extra_state_attributes == {}


def test_container_switch_container_not_found() -> None:
    """Test container switch when container not found in coordinator data."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[])  # Empty containers
    api_client = MagicMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    assert switch.is_on is False


@pytest.mark.asyncio
async def test_container_turn_on_success() -> None:
    """Test successfully starting a container."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="EXITED",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()
    api_client.start_container = AsyncMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    await switch.async_turn_on()
    api_client.start_container.assert_called_once_with("ct:1")


@pytest.mark.asyncio
async def test_container_turn_on_failure() -> None:
    """Test container start failure raises HomeAssistantError."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="EXITED",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()
    api_client.start_container = AsyncMock(side_effect=Exception("Connection failed"))

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_on()
    assert exc_info.value.translation_key == "container_start_failed"


@pytest.mark.asyncio
async def test_container_turn_off_success() -> None:
    """Test successfully stopping a container."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()
    api_client.stop_container = AsyncMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    await switch.async_turn_off()
    api_client.stop_container.assert_called_once_with("ct:1")


@pytest.mark.asyncio
async def test_container_turn_off_failure() -> None:
    """Test container stop failure raises HomeAssistantError."""
    container = DockerContainer(
        id="ct:1",
        name="/web",
        state="RUNNING",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()
    api_client.stop_container = AsyncMock(side_effect=Exception("Timeout"))

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_off()
    assert exc_info.value.translation_key == "container_stop_failed"


# =============================================================================
# VirtualMachineSwitch Tests
# =============================================================================


def test_vm_switch_creation() -> None:
    """Test VM switch creation."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="RUNNING",
        memory=4096,
        vcpu=4,
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    assert switch.unique_id == "test-uuid_vm_switch_Ubuntu"
    assert switch._attr_translation_key == "virtual_machine"
    assert switch._attr_translation_placeholders == {"name": "Ubuntu"}


def test_vm_switch_is_on_when_running() -> None:
    """Test VM switch is on when running."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="RUNNING",
        memory=4096,
        vcpu=4,
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    assert switch.is_on is True


def test_vm_switch_is_on_when_idle() -> None:
    """Test VM switch is on when idle."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="IDLE",
        memory=4096,
        vcpu=4,
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    assert switch.is_on is True


def test_vm_switch_is_off_when_shut_down() -> None:
    """Test VM switch is off when shut down."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="SHUT_DOWN",
        memory=4096,
        vcpu=4,
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    assert switch.is_on is False


def test_vm_switch_attributes() -> None:
    """Test VM switch extra attributes."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="RUNNING",
        memory=4096,
        vcpu=4,
        autostart=True,
        primaryGpu="NVIDIA GeForce RTX 3080",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    attrs = switch.extra_state_attributes
    assert attrs["state"] == "RUNNING"
    assert attrs["memory"] == 4096
    assert attrs["vcpu"] == 4
    assert attrs["auto_start"] is True
    assert attrs["primary_gpu"] == "NVIDIA GeForce RTX 3080"


def test_vm_switch_attributes_filters_none() -> None:
    """Test VM switch filters out None values from attributes."""
    vm = VmDomain(
        id="vm:1",
        name="Minimal",
        state="RUNNING",
        # memory and vcpu are None by default
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    attrs = switch.extra_state_attributes
    # Only state should be present (always set)
    assert attrs == {"state": "RUNNING"}
    assert "memory" not in attrs
    assert "vcpu" not in attrs


def test_vm_switch_no_data() -> None:
    """Test VM switch when coordinator has no data."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="RUNNING",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = None
    api_client = MagicMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    assert switch.is_on is False
    assert switch.extra_state_attributes == {}


def test_vm_switch_vm_not_found() -> None:
    """Test VM switch when VM not found in coordinator data."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="RUNNING",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[])  # Empty VMs
    api_client = MagicMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    assert switch.is_on is False


@pytest.mark.asyncio
async def test_vm_turn_on_success() -> None:
    """Test successfully starting a VM."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="SHUTOFF",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()
    api_client.start_vm = AsyncMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    await switch.async_turn_on()
    api_client.start_vm.assert_called_once_with("vm:1")


@pytest.mark.asyncio
async def test_vm_turn_on_failure() -> None:
    """Test VM start failure raises HomeAssistantError."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="SHUTOFF",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()
    api_client.start_vm = AsyncMock(side_effect=Exception("Connection failed"))

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_on()
    assert exc_info.value.translation_key == "vm_start_failed"


@pytest.mark.asyncio
async def test_vm_turn_off_success() -> None:
    """Test successfully stopping a VM."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="RUNNING",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()
    api_client.stop_vm = AsyncMock()

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    await switch.async_turn_off()
    api_client.stop_vm.assert_called_once_with("vm:1")


@pytest.mark.asyncio
async def test_vm_turn_off_failure() -> None:
    """Test VM stop failure raises HomeAssistantError."""
    vm = VmDomain(
        id="vm:1",
        name="Ubuntu",
        state="RUNNING",
    )
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(vms=[vm])
    api_client = MagicMock()
    api_client.stop_vm = AsyncMock(side_effect=Exception("Permission denied"))

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_off()
    assert exc_info.value.translation_key == "vm_stop_failed"


# =============================================================================
# ArraySwitch Tests
# =============================================================================


def test_array_switch_creation() -> None:
    """Test array switch creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STARTED")
    api_client = MagicMock()

    switch = ArraySwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert switch.unique_id == "test-uuid_array_switch"
    assert switch._attr_translation_key == "array"
    assert switch.entity_registry_enabled_default is False


def test_array_switch_is_on_when_started() -> None:
    """Test array switch is on when array is started."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STARTED")
    api_client = MagicMock()

    switch = ArraySwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert switch.is_on is True


def test_array_switch_is_off_when_stopped() -> None:
    """Test array switch is off when array is stopped."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STOPPED")
    api_client = MagicMock()

    switch = ArraySwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert switch.is_on is False


def test_array_switch_is_none_when_no_data() -> None:
    """Test array switch returns None when no data."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None
    api_client = MagicMock()

    switch = ArraySwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert switch.is_on is None


def test_array_switch_attributes() -> None:
    """Test array switch extra attributes."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STARTED")
    api_client = MagicMock()

    switch = ArraySwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = switch.extra_state_attributes
    assert attrs["state"] == "STARTED"


@pytest.mark.asyncio
async def test_array_turn_on_success() -> None:
    """Test successfully starting the array."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STOPPED")
    coordinator.async_request_refresh = AsyncMock()
    api_client = MagicMock()
    api_client.start_array = AsyncMock()

    switch = ArraySwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    await switch.async_turn_on()
    api_client.start_array.assert_called_once()
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_array_turn_on_failure() -> None:
    """Test array start failure raises HomeAssistantError."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STOPPED")
    api_client = MagicMock()
    api_client.start_array = AsyncMock(side_effect=Exception("Array start failed"))

    switch = ArraySwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_on()
    assert exc_info.value.translation_key == "array_start_failed"


@pytest.mark.asyncio
async def test_array_turn_off_success() -> None:
    """Test successfully stopping the array."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STARTED")
    coordinator.async_request_refresh = AsyncMock()
    api_client = MagicMock()
    api_client.stop_array = AsyncMock()

    switch = ArraySwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    await switch.async_turn_off()
    api_client.stop_array.assert_called_once()
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_array_turn_off_failure() -> None:
    """Test array stop failure raises HomeAssistantError."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(array_state="STARTED")
    api_client = MagicMock()
    api_client.stop_array = AsyncMock(side_effect=Exception("Array stop failed"))

    switch = ArraySwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_off()
    assert exc_info.value.translation_key == "array_stop_failed"


# =============================================================================
# ParityCheckSwitch Tests
# =============================================================================


def test_parity_check_switch_creation() -> None:
    """Test parity check switch creation."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(status="IDLE"))
    api_client = MagicMock()

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert switch.unique_id == "test-uuid_parity_check_switch"
    assert switch._attr_translation_key == "parity_check"
    assert switch.entity_registry_enabled_default is False


def test_parity_check_switch_is_on_when_running() -> None:
    """Test parity check switch is on when check is running."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(status="RUNNING"))
    api_client = MagicMock()

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert switch.is_on is True


def test_parity_check_switch_is_on_when_paused() -> None:
    """Test parity check switch is on when check is paused."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(status="PAUSED"))
    api_client = MagicMock()

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert switch.is_on is True


def test_parity_check_switch_is_off_when_idle() -> None:
    """Test parity check switch is off when idle."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(status="IDLE"))
    api_client = MagicMock()

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert switch.is_on is False


def test_parity_check_switch_is_none_when_no_data() -> None:
    """Test parity check switch returns None when no data."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None
    api_client = MagicMock()

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    assert switch.is_on is None


def test_parity_check_switch_attributes() -> None:
    """Test parity check switch extra attributes."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    parity = ParityCheck(status="RUNNING", progress=50.0, errors=0)
    coordinator.data = make_storage_data(parity_status=parity)
    api_client = MagicMock()

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    attrs = switch.extra_state_attributes
    assert attrs["status"] == "running"
    assert attrs["progress"] == 50.0
    assert attrs["errors"] == 0


@pytest.mark.asyncio
async def test_parity_check_turn_on_success() -> None:
    """Test successfully starting parity check."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(status="IDLE"))
    coordinator.async_request_refresh = AsyncMock()
    api_client = MagicMock()
    api_client.start_parity_check = AsyncMock()

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    await switch.async_turn_on()
    api_client.start_parity_check.assert_called_once_with(correct=False)
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_parity_check_turn_on_failure() -> None:
    """Test parity check start failure raises HomeAssistantError."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(status="IDLE"))
    api_client = MagicMock()
    api_client.start_parity_check = AsyncMock(side_effect=Exception("Check failed"))

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_on()
    assert exc_info.value.translation_key == "parity_check_start_failed"


@pytest.mark.asyncio
async def test_parity_check_turn_off_success() -> None:
    """Test successfully stopping parity check."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(status="RUNNING"))
    coordinator.async_request_refresh = AsyncMock()
    api_client = MagicMock()
    api_client.cancel_parity_check = AsyncMock()

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    await switch.async_turn_off()
    api_client.cancel_parity_check.assert_called_once()
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_parity_check_turn_off_failure() -> None:
    """Test parity check stop failure raises HomeAssistantError."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(status="RUNNING"))
    api_client = MagicMock()
    api_client.cancel_parity_check = AsyncMock(side_effect=Exception("Cancel failed"))

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_off()
    assert exc_info.value.translation_key == "parity_check_stop_failed"


# =============================================================================
# DiskSpinSwitch Tests
# =============================================================================


def test_disk_spin_switch_creation() -> None:
    """Test disk spin switch creation."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    api_client = MagicMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert switch.unique_id == "test-uuid_disk_spin_disk1"
    assert switch._attr_translation_key == "disk_spin"
    assert switch._attr_translation_placeholders == {"name": "Disk 1"}
    assert switch.entity_registry_enabled_default is False


def test_disk_spin_switch_is_on_when_spinning() -> None:
    """Test disk spin switch is on when disk is spinning."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    api_client = MagicMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert switch.is_on is True


def test_disk_spin_switch_is_off_when_not_spinning() -> None:
    """Test disk spin switch is off when disk is spun down."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=False,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    api_client = MagicMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert switch.is_on is False


def test_disk_spin_switch_is_none_when_no_data() -> None:
    """Test disk spin switch returns None when no data."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None
    api_client = MagicMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert switch.is_on is None


def test_disk_spin_switch_disk_not_found() -> None:
    """Test disk spin switch returns None when disk not found."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[])  # Empty disks
    api_client = MagicMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    assert switch.is_on is None


def test_disk_spin_switch_attributes() -> None:
    """Test disk spin switch extra attributes."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=True,
        temp=35,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    api_client = MagicMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    attrs = switch.extra_state_attributes
    assert attrs["device"] == "/dev/sdb"
    assert attrs["type"] == "DATA"
    assert attrs["status"] == "DISK_OK"
    assert attrs["temperature"] == 35


def test_disk_spin_switch_attributes_filters_none() -> None:
    """Test disk spin switch filters out None values from attributes."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=True,
        # temp is None by default
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    api_client = MagicMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    attrs = switch.extra_state_attributes
    assert "temperature" not in attrs


def test_disk_spin_switch_finds_parity_disk() -> None:
    """Test disk spin switch can find parity disks."""
    parity_disk = ArrayDisk(
        id="parity1",
        name="Parity",
        device="/dev/sda",
        type="PARITY",
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parities=[parity_disk])
    api_client = MagicMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=parity_disk,
    )

    assert switch.is_on is True


def test_disk_spin_switch_finds_cache_disk() -> None:
    """Test disk spin switch can find cache disks."""
    cache_disk = ArrayDisk(
        id="cache1",
        name="Cache",
        device="/dev/sdc",
        type="CACHE",
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(caches=[cache_disk])
    api_client = MagicMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=cache_disk,
    )

    assert switch.is_on is True


@pytest.mark.asyncio
async def test_disk_spin_turn_on_success() -> None:
    """Test successfully spinning up a disk."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=False,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    coordinator.async_request_refresh = AsyncMock()
    api_client = MagicMock()
    api_client.spin_up_disk = AsyncMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    await switch.async_turn_on()
    api_client.spin_up_disk.assert_called_once_with("disk1")
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_disk_spin_turn_on_failure() -> None:
    """Test disk spin up failure raises HomeAssistantError."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=False,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    api_client = MagicMock()
    api_client.spin_up_disk = AsyncMock(side_effect=Exception("Spin up failed"))

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_on()
    assert exc_info.value.translation_key == "disk_spin_up_failed"


@pytest.mark.asyncio
async def test_disk_spin_turn_off_success() -> None:
    """Test successfully spinning down a disk."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    coordinator.async_request_refresh = AsyncMock()
    api_client = MagicMock()
    api_client.spin_down_disk = AsyncMock()

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    await switch.async_turn_off()
    api_client.spin_down_disk.assert_called_once_with("disk1")
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_disk_spin_turn_off_failure() -> None:
    """Test disk spin down failure raises HomeAssistantError."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=True,
    )
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])
    api_client = MagicMock()
    api_client.spin_down_disk = AsyncMock(side_effect=Exception("Spin down failed"))

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await switch.async_turn_off()
    assert exc_info.value.translation_key == "disk_spin_down_failed"


# =============================================================================
# Switch Availability Tests
# =============================================================================


def test_switch_available_true() -> None:
    """Test switch is available when coordinator succeeds."""
    container = DockerContainer(id="ct:1", name="/web", state="RUNNING")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = True
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    assert switch.available is True


def test_switch_available_false() -> None:
    """Test switch is not available when coordinator fails."""
    container = DockerContainer(id="ct:1", name="/web", state="RUNNING")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.last_update_success = False
    coordinator.data = make_system_data(containers=[container])
    api_client = MagicMock()

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        api_client=api_client,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
    )

    assert switch.available is False


# =============================================================================
# async_setup_entry Tests
# =============================================================================


@pytest.mark.asyncio
async def test_setup_creates_control_switches(hass) -> None:
    """Test setup creates array and parity check control switches."""
    disk = ArrayDisk(
        id="disk1",
        name="Disk 1",
        device="/dev/sdb",
        type="DATA",
        status="DISK_OK",
        isSpinning=True,
    )

    storage_coordinator = MagicMock()
    storage_coordinator.data = make_storage_data(array_state="STARTED", disks=[disk])

    system_coordinator = MagicMock()
    system_coordinator.data = make_system_data()

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

    # Should have: ArraySwitch, ParityCheckSwitch, DiskSpinSwitch
    assert len(added_entities) == 3
    assert any(isinstance(e, ArraySwitch) for e in added_entities)
    assert any(isinstance(e, ParityCheckSwitch) for e in added_entities)
    assert any(isinstance(e, DiskSpinSwitch) for e in added_entities)


@pytest.mark.asyncio
async def test_setup_creates_container_switches(hass) -> None:
    """Test setup creates Docker container switches."""
    container = DockerContainer(id="ct:1", name="/web", state="RUNNING")

    system_coordinator = MagicMock()
    system_coordinator.data = make_system_data(containers=[container])

    storage_coordinator = MagicMock()
    storage_coordinator.data = make_storage_data(array_state="STARTED")

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

    # Should have: ArraySwitch, ParityCheckSwitch, DockerContainerSwitch
    assert len(added_entities) == 3
    assert any(isinstance(e, DockerContainerSwitch) for e in added_entities)


@pytest.mark.asyncio
async def test_setup_creates_vm_switches(hass) -> None:
    """Test setup creates VM switches."""
    vm = VmDomain(id="vm:1", name="Ubuntu", state="RUNNING")

    system_coordinator = MagicMock()
    system_coordinator.data = make_system_data(vms=[vm])

    storage_coordinator = MagicMock()
    storage_coordinator.data = make_storage_data(array_state="STARTED")

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

    # Should have: ArraySwitch, ParityCheckSwitch, VirtualMachineSwitch
    assert len(added_entities) == 3
    assert any(isinstance(e, VirtualMachineSwitch) for e in added_entities)


@pytest.mark.asyncio
async def test_setup_no_containers_or_vms(hass) -> None:
    """Test setup handles no containers or VMs but still creates control switches."""
    system_coordinator = MagicMock()
    system_coordinator.data = make_system_data()  # Empty data

    storage_coordinator = MagicMock()
    storage_coordinator.data = make_storage_data(array_state="STARTED")

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

    # Should still have ArraySwitch and ParityCheckSwitch
    assert len(added_entities) == 2
    assert any(isinstance(e, ArraySwitch) for e in added_entities)
    assert any(isinstance(e, ParityCheckSwitch) for e in added_entities)


@pytest.mark.asyncio
async def test_setup_no_coordinator_data(hass) -> None:
    """Test setup handles None coordinator data."""
    system_coordinator = MagicMock()
    system_coordinator.data = None

    storage_coordinator = MagicMock()
    storage_coordinator.data = None

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

    # Should still have ArraySwitch and ParityCheckSwitch (always created)
    assert len(added_entities) == 2
    assert any(isinstance(e, ArraySwitch) for e in added_entities)
    assert any(isinstance(e, ParityCheckSwitch) for e in added_entities)


# =============================================================================
# Cache Hit Tests
# =============================================================================


def test_containerswitch_cache_hit() -> None:
    """Test container switch uses cached value when data object is same."""
    container = DockerContainer(id="abc123", name="/plex", state="RUNNING")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    data = make_system_data(containers=[container])
    coordinator.data = data

    switch = DockerContainerSwitch(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        container=container,
        api_client=MagicMock(),
    )

    # First call populates cache
    result1 = switch._get_container()
    assert result1 is not None
    assert result1.name == "/plex"

    # Second call with SAME data object should hit cache (line 120)
    result2 = switch._get_container()
    assert result2 is not None
    # Verify cache was used (returned same cached object)
    assert result2 is switch._cached_container


def test_vmswitch_cache_hit() -> None:
    """Test VM switch uses cached value when data object is same."""
    vm = VmDomain(id="vm:1", name="Windows 11", state="RUNNING")
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    data = make_system_data(vms=[vm])
    coordinator.data = data

    switch = VirtualMachineSwitch(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        vm=vm,
        api_client=MagicMock(),
    )

    # First call populates cache
    result1 = switch._get_vm()
    assert result1 is not None
    assert result1.name == "Windows 11"

    # Second call with SAME data object should hit cache (line 240)
    result2 = switch._get_vm()
    assert result2 is not None
    # Verify cache was used (returned same cached object)
    assert result2 is switch._cached_vm


def test_arrayswitch_extra_attributes_none_data() -> None:
    """Test array switch extra_state_attributes returns empty when data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    switch = ArraySwitch(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        api_client=MagicMock(),
    )

    assert switch.extra_state_attributes == {}


def test_paritycheckswitch_is_on_none_data() -> None:
    """Test parity check switch is_on returns None when data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        api_client=MagicMock(),
    )

    assert switch.is_on is None


def test_paritycheckswitch_extra_attributes_none_data() -> None:
    """Test parity check extra_state_attributes returns empty when data is None."""
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = None

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        api_client=MagicMock(),
    )

    assert switch.extra_state_attributes == {}


def test_paritycheckswitch_is_on_returns_false_when_status_none() -> None:
    """Test parity check is_on returns False when parity status value is None."""
    parity = ParityCheck(status=None, progress=None, errors=0)
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=parity)

    switch = ParityCheckSwitch(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        api_client=MagicMock(),
    )

    # Line 440: status is None so returns False (not running)
    assert switch.is_on is False


def test_diskspinswitch_returns_none_when_disk_missing() -> None:
    """Test disk spin switch returns None when disk is missing from data."""
    disk = ArrayDisk(id="disk:1", name="Disk 1", type="DATA", status="DISK_OK")
    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(disks=[disk])

    switch = DiskSpinSwitch(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="test-server",
        disk=disk,
        api_client=MagicMock(),
    )

    # Remove disk from data
    coordinator.data = make_storage_data(disks=[])

    assert switch.is_on is None
    assert switch.extra_state_attributes == {}
