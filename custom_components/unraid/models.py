"""Pydantic models for Unraid GraphQL responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Python's fromisoformat doesn't handle trailing Z, normalize first
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        return datetime.fromisoformat(normalized)
    return None


class UnraidBaseModel(BaseModel):
    """Base model that ignores unknown fields for forward compatibility."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# System Info models


class InfoSystem(UnraidBaseModel):
    """System information model (manufacturer, model, version, serial, UUID)."""

    uuid: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    version: str | None = None
    serial: str | None = None


class CpuPackages(UnraidBaseModel):
    """CPU package information (temperature, power consumption)."""

    temp: list[float] = []
    totalPower: float | None = None


class InfoCpu(UnraidBaseModel):
    """CPU information model (brand, threads, cores, temperature, power)."""

    brand: str | None = None
    threads: int | None = None
    cores: int | None = None
    packages: CpuPackages = CpuPackages()


class InfoOs(UnraidBaseModel):
    """Operating system information (hostname, uptime, kernel)."""

    hostname: str | None = None
    uptime: datetime | None = None
    kernel: str | None = None

    @field_validator("uptime", mode="before")
    @classmethod
    def parse_uptime(cls, value: str | datetime | None) -> datetime | None:
        return _parse_datetime(value)


class CoreVersions(UnraidBaseModel):
    unraid: str | None = None
    api: str | None = None
    kernel: str | None = None


class InfoVersions(UnraidBaseModel):
    core: CoreVersions = CoreVersions()


class SystemInfo(UnraidBaseModel):
    time: datetime | None = None
    system: InfoSystem = InfoSystem()
    cpu: InfoCpu = InfoCpu()
    os: InfoOs = InfoOs()
    versions: InfoVersions = InfoVersions()

    @field_validator("time", mode="before")
    @classmethod
    def parse_time(cls, value: str | datetime | None) -> datetime | None:
        return _parse_datetime(value)


# Metrics models


class CpuUtilization(UnraidBaseModel):
    percentTotal: float | None = None


class MemoryUtilization(UnraidBaseModel):
    total: int | None = None
    used: int | None = None
    free: int | None = None
    available: int | None = None
    percentTotal: float | None = None
    swapTotal: int | None = None
    swapUsed: int | None = None
    percentSwapTotal: float | None = None


class Metrics(UnraidBaseModel):
    cpu: CpuUtilization = CpuUtilization()
    memory: MemoryUtilization = MemoryUtilization()


# Array models


class CapacityKilobytes(UnraidBaseModel):
    total: int
    used: int
    free: int


class ArrayCapacity(UnraidBaseModel):
    kilobytes: CapacityKilobytes

    @property
    def total_bytes(self) -> int:
        return self.kilobytes.total * 1024

    @property
    def used_bytes(self) -> int:
        return self.kilobytes.used * 1024

    @property
    def free_bytes(self) -> int:
        return self.kilobytes.free * 1024

    @property
    def usage_percent(self) -> float:
        return (
            (self.kilobytes.used / self.kilobytes.total * 100)
            if self.kilobytes.total
            else 0.0
        )


class ParityCheck(UnraidBaseModel):
    status: str | None = None
    progress: int | None = None
    errors: int | None = None


class ArrayDisk(UnraidBaseModel):
    id: str
    idx: int | None = None  # Optional - boot device doesn't have idx
    device: str | None = None
    name: str | None = None
    type: str | None = None
    size: int | None = None
    fsSize: int | None = None
    fsUsed: int | None = None
    fsFree: int | None = None
    fsType: str | None = None  # Filesystem type (XFS, BTRFS, vfat, etc.)
    temp: int | None = None
    status: str | None = None
    isSpinning: bool | None = None
    # SMART data (enriched from physical disks query)
    smartStatus: str | None = None

    @property
    def size_bytes(self) -> int | None:
        return self.size * 1024 if self.size is not None else None

    @property
    def fs_size_bytes(self) -> int | None:
        return self.fsSize * 1024 if self.fsSize is not None else None

    @property
    def fs_used_bytes(self) -> int | None:
        return self.fsUsed * 1024 if self.fsUsed is not None else None

    @property
    def fs_free_bytes(self) -> int | None:
        return self.fsFree * 1024 if self.fsFree is not None else None

    @property
    def usage_percent(self) -> float | None:
        if self.fsSize is None or self.fsSize == 0 or self.fsUsed is None:
            return None
        return (self.fsUsed / self.fsSize) * 100


class UnraidArray(UnraidBaseModel):
    state: str | None = None
    capacity: ArrayCapacity
    parityCheckStatus: ParityCheck = ParityCheck()
    disks: list[ArrayDisk] = []
    parities: list[ArrayDisk] = []
    caches: list[ArrayDisk] = []


# Docker models


class ContainerPort(UnraidBaseModel):
    privatePort: int | None = None
    publicPort: int | None = None
    type: str | None = None


class DockerContainer(UnraidBaseModel):
    id: str
    name: str
    state: str | None = None
    image: str | None = None
    webUiUrl: str | None = None
    iconUrl: str | None = None
    ports: list[ContainerPort] = []


# VM models


class VmDomain(UnraidBaseModel):
    id: str
    name: str
    state: str | None = None
    memory: int | None = None
    vcpu: int | None = None


# UPS models


class UPSBattery(UnraidBaseModel):
    chargeLevel: int | None = None
    estimatedRuntime: int | None = None


class UPSPower(UnraidBaseModel):
    inputVoltage: float | None = None
    outputVoltage: float | None = None
    loadPercentage: float | None = None


class UPSDevice(UnraidBaseModel):
    id: str
    name: str
    status: str | None = None
    battery: UPSBattery = UPSBattery()
    power: UPSPower = UPSPower()


# Share models


class Share(UnraidBaseModel):
    """User share information."""

    id: str
    name: str
    size: int | None = None  # Size in KB (often returns 0, use used+free instead)
    used: int | None = None  # Used in KB
    free: int | None = None  # Free in KB

    @property
    def size_bytes(self) -> int | None:
        """Return share size in bytes (calculates from used+free if size=0)."""
        # If size is provided and non-zero, use it
        if self.size is not None and self.size > 0:
            return self.size * 1024
        # Otherwise calculate from used + free
        if self.used is not None and self.free is not None:
            return (self.used + self.free) * 1024
        return None

    @property
    def used_bytes(self) -> int | None:
        """Return used space in bytes."""
        return self.used * 1024 if self.used is not None else None

    @property
    def free_bytes(self) -> int | None:
        """Return free space in bytes."""
        return self.free * 1024 if self.free is not None else None

    @property
    def usage_percent(self) -> float | None:
        """Return share usage percentage."""
        size = self.size_bytes
        used = self.used_bytes
        if size is None or size == 0 or used is None:
            return None
        return (used / size) * 100
