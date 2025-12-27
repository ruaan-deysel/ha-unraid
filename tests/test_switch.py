"""Tests for Unraid switch entities."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.unraid.coordinator import UnraidSystemCoordinator
from custom_components.unraid.models import DockerContainer, VmDomain
from custom_components.unraid.switch import DockerContainerSwitch, VirtualMachineSwitch
from tests.conftest import make_system_data


class TestDockerContainerSwitch:
    """Test Docker container switch."""

    def test_container_switch_creation(self) -> None:
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

        assert switch.unique_id == "test-uuid_container_switch_ct:1"
        assert (
            switch.name == "Container web"
        )  # Should strip leading / and prefix with Container
        assert switch.device_info is not None

    def test_container_switch_is_on_when_running(self) -> None:
        """Test container switch is on when running."""
        container = DockerContainer(
            id="ct:1",
            name="/web",
            state="RUNNING",
            image="nginx:latest",
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

    def test_container_switch_is_off_when_stopped(self) -> None:
        """Test container switch is off when stopped."""
        container = DockerContainer(
            id="ct:1",
            name="/web",
            state="EXITED",
            image="nginx:latest",
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

    def test_container_switch_attributes(self) -> None:
        """Test container switch extra attributes."""
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

        attrs = switch.extra_state_attributes
        assert attrs["image"] == "nginx:latest"
        assert attrs["status"] == "RUNNING"
        assert attrs["web_ui_url"] == "https://tower/apps/web"
        assert attrs["icon_url"] == "https://cdn/icons/web.png"

    def test_container_switch_attributes_filters_none(self) -> None:
        """Test container switch filters out None values from attributes."""
        container = DockerContainer(
            id="ct:1",
            name="/minimal",
            state="RUNNING",
            # image, webUiUrl, iconUrl are all None by default
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


class TestVirtualMachineSwitch:
    """Test VM switch."""

    def test_vm_switch_creation(self) -> None:
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

        assert switch.unique_id == "test-uuid_vm_switch_vm:1"
        assert switch.name == "VM Ubuntu"  # Should prefix with VM

    def test_vm_switch_is_on_when_running(self) -> None:
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

    def test_vm_switch_is_on_when_idle(self) -> None:
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

    def test_vm_switch_is_off_when_shut_down(self) -> None:
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

    def test_vm_switch_attributes(self) -> None:
        """Test VM switch extra attributes."""
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

        attrs = switch.extra_state_attributes
        assert attrs["state"] == "RUNNING"
        assert attrs["memory"] == 4096
        assert attrs["vcpu"] == 4

    def test_vm_switch_attributes_filters_none(self) -> None:
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
