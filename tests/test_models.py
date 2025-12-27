"""Model tests for the Unraid integration."""

import pytest

from custom_components.unraid import models
from tests.conftest import load_json


def test_base_model_ignores_unknown_fields():
    class SampleModel(models.UnraidBaseModel):
        required: str

    data = {"required": "ok", "unexpected": "ignored"}
    parsed = SampleModel.model_validate(data)
    assert parsed.required == "ok"
    assert not hasattr(parsed, "unexpected")


def test_system_info_parses_core_sections():
    payload = load_json("system_info.json")
    info = models.SystemInfo.model_validate(payload)

    assert info.time.isoformat() == "2025-12-23T10:30:00+00:00"
    assert info.system.uuid == "abc-123"
    assert info.cpu.brand == "AMD Ryzen"
    assert info.cpu.threads == 16
    assert info.cpu.cores == 8
    assert info.cpu.packages.temp == [45.2]
    assert info.cpu.packages.totalPower == 65.5
    assert info.os.hostname == "tower"
    assert info.versions.core.unraid == "7.2.0"
    assert info.versions.core.api == "4.29.2"


def test_metrics_parses_cpu_and_memory():
    payload = load_json("metrics.json")
    metrics = models.Metrics.model_validate(payload)

    assert metrics.cpu.percentTotal == pytest.approx(23.5)
    assert metrics.memory.total == 17179869184
    assert metrics.memory.used == 8589934592
    assert metrics.memory.free == 8589934592
    assert metrics.memory.percentTotal == pytest.approx(50.0)
    assert metrics.memory.percentSwapTotal == pytest.approx(0.0)


def test_array_parses_capacity_and_disks():
    payload = load_json("array.json")
    array = models.UnraidArray.model_validate(payload)

    assert array.state == "STARTED"
    assert array.capacity.total_bytes == 1000 * 1024
    assert array.capacity.used_bytes == 400 * 1024
    assert array.capacity.free_bytes == 600 * 1024
    assert array.capacity.usage_percent == pytest.approx(40.0)

    disk = array.disks[0]
    assert disk.id == "disk:1"
    assert disk.idx == 1
    assert disk.device == "sda"
    assert disk.name == "Disk 1"
    assert disk.type == "DATA"
    assert disk.size_bytes == 500000 * 1024  # size field is in KB
    assert disk.fs_size_bytes == 400000 * 1024  # fsSize field is in KB
    assert disk.fs_used_bytes == 200000 * 1024  # fsUsed field is in KB
    assert disk.fs_free_bytes == 200000 * 1024  # fsFree field is in KB
    assert disk.usage_percent == pytest.approx(50.0)
    assert disk.temp == 35
    assert disk.status == "DISK_OK"

    assert array.parityCheckStatus.status == "COMPLETED"
    assert array.parityCheckStatus.progress == 100
    assert array.parityCheckStatus.errors == 0


def test_docker_container_parses_ports_and_state():
    payload = load_json("docker.json")
    container = models.DockerContainer.model_validate(payload)

    assert container.id == "ct:1"
    assert container.name == "web"
    assert container.state == "RUNNING"
    assert container.image == "nginx:latest"
    assert container.webUiUrl == "https://tower/apps/web"
    assert container.iconUrl == "https://cdn/icons/web.png"
    assert container.ports[0].privatePort == 80
    assert container.ports[0].publicPort == 8080
    assert container.ports[0].type == "tcp"


def test_vm_domain_parses_state_and_ids():
    payload = load_json("vms.json")
    domain = models.VmDomain.model_validate(payload)

    assert domain.id == "vm:1"
    assert domain.name == "Ubuntu"
    assert domain.state == "RUNNING"
    assert domain.memory == 2147483648
    assert domain.vcpu == 4


def test_ups_device_parses_battery_and_power():
    payload = load_json("ups.json")
    ups = models.UPSDevice.model_validate(payload)

    assert ups.id == "ups:1"
    assert ups.name == "APC"
    assert ups.status == "Online"
    assert ups.battery.chargeLevel == 95
    assert ups.battery.estimatedRuntime == 1200
    assert ups.power.inputVoltage == pytest.approx(120.0)
    assert ups.power.outputVoltage == pytest.approx(118.5)
    assert ups.power.loadPercentage == pytest.approx(20.5)
