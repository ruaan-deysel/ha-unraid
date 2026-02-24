"""Binary sensor entities for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ARRAY_STATE_STARTED
from .entity import UnraidBaseEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from unraid_api.models import ArrayDisk, DockerContainer, Service, UPSDevice

    from . import UnraidConfigEntry
    from .coordinator import (
        UnraidInfraCoordinator,
        UnraidInfraData,
        UnraidStorageCoordinator,
        UnraidStorageData,
        UnraidSystemCoordinator,
        UnraidSystemData,
    )

_LOGGER = logging.getLogger(__name__)

# Coordinator handles all data updates, no parallel entity updates needed
PARALLEL_UPDATES = 0


class UnraidBinarySensorEntity(UnraidBaseEntity, BinarySensorEntity):
    """Base class for Unraid binary sensor entities."""

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator
        | UnraidSystemCoordinator
        | UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
        resource_id: str,
        name: str,
        server_info: dict | None = None,
    ) -> None:
        """
        Initialize binary sensor entity.

        Args:
            coordinator: Data coordinator
            server_uuid: Unraid server UUID
            server_name: Friendly server name
            resource_id: Resource identifier for unique_id
            name: Entity name
            server_info: Optional dict with manufacturer, model, sw_version, etc.

        """
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=resource_id,
            name=name,
            server_info=server_info,
        )


class DiskHealthBinarySensor(UnraidBinarySensorEntity):
    """Disk health binary sensor."""

    _attr_translation_key = "disk_health"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        disk: ArrayDisk,
    ) -> None:
        """Initialize disk health binary sensor."""
        self._disk_id = disk.id
        self._disk_name = disk.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"disk_health_{self._disk_id}",
            name=f"Disk {self._disk_name} Health",
        )
        self._attr_translation_placeholders = {"name": self._disk_name}

    def _get_disk(self) -> ArrayDisk | None:
        """Get current disk from coordinator data."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None:
            return None
        all_disks = data.disks + data.parities + data.caches
        for disk in all_disks:
            if disk.id == self._disk_id:
                return disk
        return None

    @property
    def is_on(self) -> bool | None:
        """Return True if disk has a problem (status != DISK_OK)."""
        disk = self._get_disk()
        if disk is None:
            return None
        if disk.status is None:
            return None
        return not disk.is_healthy

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return disk details including temperature and standby as attributes."""
        disk = self._get_disk()
        if disk is None:
            return {}
        attrs: dict[str, Any] = {
            "status": disk.status,
            "device": disk.device,
        }
        # Add filesystem type if available
        if disk.fsType:
            attrs["filesystem"] = disk.fsType
        if disk.temp is not None:
            attrs["temperature"] = disk.temp
        if disk.smartStatus:
            attrs["smart_status"] = disk.smartStatus
        if disk.isSpinning is not None:
            attrs["standby"] = not disk.isSpinning
            attrs["spinning"] = disk.isSpinning
        return attrs


class ParityStatusBinarySensor(UnraidBinarySensorEntity):
    """
    Parity check status binary sensor.

    ON = Parity check is running or has issues (RUNNING, PAUSED, FAILED)
    OFF = Parity check completed or never run (COMPLETED, NEVER_RUN, CANCELLED)
    """

    _attr_translation_key = "parity_status"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize parity status binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_status",
            name="Parity Status",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if parity check is in progress or has issues."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return None
        parity = data.parity_status
        if parity.status is None:
            return None
        return parity.is_running or parity.has_problem

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return parity check details as attributes."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return {}
        parity = data.parity_status
        return {
            "status": parity.status.lower() if parity.status else None,
            "progress": parity.progress,
            "errors": parity.errors,
        }


class ArrayStartedBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if the array is started.

    ON = Array is started/running
    OFF = Array is stopped
    """

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "array_started"

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize array started binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="array_started",
            name="Array Started",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if array is started."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.array_state is None:
            return None
        return data.array_state.upper() == ARRAY_STATE_STARTED


class ParityCheckRunningBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if a parity check is currently running.

    ON = Parity check in progress (RUNNING or PAUSED)
    OFF = No parity check in progress
    """

    _attr_translation_key = "parity_check_running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize parity check running binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_check_running",
            name="Parity Check Running",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if parity check is running."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return None
        if data.parity_status.status is None:
            return None
        return data.parity_status.is_running

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return parity check details as attributes."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return {}
        parity = data.parity_status
        return {
            "status": parity.status.lower() if parity.status else None,
            "progress": parity.progress,
        }


class ParityValidBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if parity is valid.

    Uses device_class=PROBLEM, so:
    ON = Parity is INVALID (problem detected)
    OFF = Parity is valid (no problem)

    Parity is considered invalid if:
    - Status is FAILED
    - Errors count > 0
    - Status is unknown/unavailable
    """

    _attr_translation_key = "parity_valid"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize parity valid binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_valid",
            name="Parity Valid",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if parity is INVALID (problem detected)."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return None
        return data.parity_status.has_problem

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return parity details as attributes."""
        data: UnraidStorageData | None = self.coordinator.data
        if data is None or data.parity_status is None:
            return {}
        parity = data.parity_status
        return {
            "status": parity.status.lower() if parity.status else None,
            "errors": parity.errors,
        }


# =============================================================================
# System Binary Sensors (use UnraidSystemBinarySensor base class)
# =============================================================================


class UnraidSystemBinarySensor(UnraidBinarySensorEntity):
    """Base class for Unraid system binary sensor entities."""

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        resource_id: str,
        name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize system binary sensor entity."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=resource_id,
            name=name,
            server_info=server_info,
        )


class UPSConnectedBinarySensor(UnraidSystemBinarySensor):
    """
    Binary sensor indicating if UPS is connected.

    ON = UPS is connected and online
    OFF = UPS is not connected or offline
    """

    _attr_translation_key = "ups_connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        ups: UPSDevice,
    ) -> None:
        """Initialize UPS connected binary sensor."""
        self._ups_id = ups.id
        self._ups_name = ups.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"ups_{ups.id}_connected",
            name="UPS Connected",
        )
        self._attr_translation_placeholders = {"name": self._ups_name}

    def _get_ups(self) -> UPSDevice | None:
        """Get current UPS from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for ups in data.ups_devices:
            if ups.id == self._ups_id:
                return ups
        return None

    @property
    def is_on(self) -> bool | None:
        """Return True if UPS is connected and online."""
        ups = self._get_ups()
        if ups is None:
            return False  # UPS not found = not connected
        return ups.is_connected

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return UPS details as attributes."""
        ups = self._get_ups()
        if ups is None:
            return {}
        return {
            "model": self._ups_name,
            "status": ups.status,
            "battery_level": ups.battery.chargeLevel if ups.battery else None,
        }


class ServiceBinarySensor(UnraidBinarySensorEntity):
    """Binary sensor for an Unraid system service (SMB, NFS, SSH, etc.)."""

    _attr_translation_key = "service"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
        service: Service,
    ) -> None:
        """Initialize service binary sensor."""
        self._service_name = service.name
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"service_{self._service_name}",
            name=f"Service {self._service_name}",
        )
        self._attr_translation_placeholders = {"name": self._service_name}

    def _get_service(self) -> Service | None:
        """Get current service from coordinator data."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None:
            return None
        for service in data.services:
            if service.name == self._service_name:
                return service
        return None

    @property
    def is_on(self) -> bool | None:
        """Return True if service is online."""
        service = self._get_service()
        if service is None:
            return None
        return service.online

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return service details as attributes."""
        service = self._get_service()
        if service is None:
            return {}
        attrs: dict[str, Any] = {}
        if service.version:
            attrs["version"] = service.version
        if service.uptime and service.uptime.timestamp:
            attrs["uptime"] = service.uptime.timestamp
        return attrs


class CloudConnectedBinarySensor(UnraidBinarySensorEntity):
    """Binary sensor for Unraid cloud connection status."""

    _attr_translation_key = "cloud_connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize cloud connected binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="cloud_connected",
            name="Cloud Connected",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if cloud is connected."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.cloud is None or data.cloud.cloud is None:
            return None
        return data.cloud.cloud.status.lower() == "connected"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return cloud connection details as attributes."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.cloud is None:
            return {}
        attrs: dict[str, Any] = {}
        cloud = data.cloud
        if cloud.error is not None:
            attrs["error"] = cloud.error
        if cloud.cloud is not None:
            attrs["status"] = cloud.cloud.status
            if cloud.cloud.ip is not None:
                attrs["ip"] = cloud.cloud.ip
            if cloud.cloud.error is not None:
                attrs["cloud_error"] = cloud.cloud.error
        if cloud.relay is not None:
            attrs["relay_status"] = cloud.relay.status
        if cloud.minigraphql is not None and cloud.minigraphql.status is not None:
            attrs["minigraphql_status"] = cloud.minigraphql.status
        return attrs


class RemoteAccessBinarySensor(UnraidBinarySensorEntity):
    """Binary sensor for Unraid remote access status."""

    _attr_translation_key = "remote_access"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize remote access binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="remote_access",
            name="Remote Access",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if remote access is enabled (not DISABLED)."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.remote_access is None:
            return None
        access_type = data.remote_access.accessType
        if access_type is None:
            return None
        return access_type.upper() != "DISABLED"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return remote access details as attributes."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.remote_access is None:
            return {}
        ra = data.remote_access
        attrs: dict[str, Any] = {}
        if ra.accessType is not None:
            attrs["access_type"] = ra.accessType
        if ra.forwardType is not None:
            attrs["forward_type"] = ra.forwardType
        if ra.port is not None:
            attrs["port"] = ra.port
        return attrs


# =============================================================================
# Container Binary Sensors
# =============================================================================


class ContainerUpdateAvailableBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if a container has an update available.

    ON = Update is available
    OFF = Container is up to date
    """

    _attr_translation_key = "container_update_available"
    _attr_device_class = BinarySensorDeviceClass.UPDATE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        container: DockerContainer,
    ) -> None:
        """Initialize container update available binary sensor."""
        self._container_name = container.name.lstrip("/")
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_{self._container_name}_update",
            name=f"Container {self._container_name} Update",
        )
        self._attr_translation_placeholders = {"name": self._container_name}

    def _get_container(self) -> DockerContainer | None:
        """Get current container from coordinator data."""
        data: UnraidSystemData | None = self.coordinator.data
        if data is None:
            return None
        for c in data.containers:
            if c.name.lstrip("/") == self._container_name:
                return c
        return None

    @property
    def is_on(self) -> bool | None:
        """Return True if container has an update available."""
        container = self._get_container()
        if container is None:
            return None
        # Treat None (unknown) as False — no update detected
        return container.isUpdateAvailable or False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return container details as attributes."""
        container = self._get_container()
        if container is None:
            return {}
        attrs: dict[str, Any] = {}
        if container.image is not None:
            attrs["image"] = container.image
        if container.state is not None:
            attrs["state"] = container.state
        return attrs


# =============================================================================
# System Health Binary Sensors (from Vars via InfraCoordinator)
# =============================================================================


class MoverActiveBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if the mover is currently active.

    ON = Mover is running
    OFF = Mover is idle
    """

    _attr_translation_key = "mover_active"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize mover active binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="mover_active",
            name="Mover Active",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if mover is active."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return None
        return data.vars.share_mover_active


class DisksDisabledBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if any disks are disabled.

    ON = One or more disks are disabled (problem)
    OFF = All disks are healthy
    """

    _attr_translation_key = "disks_disabled"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize disks disabled binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="disks_disabled",
            name="Disks Disabled",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if any disks are disabled."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return None
        count = data.vars.md_num_disabled
        if count is None:
            return None
        return count > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return disabled disk count."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return {}
        return {"count": data.vars.md_num_disabled}


class DisksMissingBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if any disks are missing.

    ON = One or more disks are missing (problem)
    OFF = All disks are present
    """

    _attr_translation_key = "disks_missing"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize disks missing binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="disks_missing",
            name="Disks Missing",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if any disks are missing."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return None
        count = data.vars.md_num_missing
        if count is None:
            return None
        return count > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return missing disk count."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return {}
        return {"count": data.vars.md_num_missing}


class DisksInvalidBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if any disks are invalid.

    ON = One or more disks are invalid (problem)
    OFF = All disks are valid
    """

    _attr_translation_key = "disks_invalid"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize disks invalid binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="disks_invalid",
            name="Disks Invalid",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if any disks are invalid."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return None
        count = data.vars.md_num_invalid
        if count is None:
            return None
        return count > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return invalid disk count."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return {}
        return {"count": data.vars.md_num_invalid}


class SafeModeBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if the server is in safe mode.

    ON = Server is in safe mode (problem — plugins/Docker disabled)
    OFF = Server is running normally
    """

    _attr_translation_key = "safe_mode"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize safe mode binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="safe_mode",
            name="Safe Mode",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if server is in safe mode."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return None
        return data.vars.safe_mode


class ConfigValidBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if the configuration is invalid.

    Uses device_class=PROBLEM, so:
    ON = Configuration is INVALID (problem detected)
    OFF = Configuration is valid
    """

    _attr_translation_key = "config_valid"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize config valid binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="config_valid",
            name="Config Valid",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if config is INVALID (problem)."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return None
        valid = data.vars.config_valid
        if valid is None:
            return None
        # Invert: config_valid=True means no problem, so is_on=False
        return not valid


class FilesystemsUnmountableBinarySensor(UnraidBinarySensorEntity):
    """
    Binary sensor indicating if any filesystems are unmountable.

    ON = One or more filesystems cannot be mounted (problem)
    OFF = All filesystems are mountable
    """

    _attr_translation_key = "filesystems_unmountable"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UnraidInfraCoordinator,
        server_uuid: str,
        server_name: str,
    ) -> None:
        """Initialize filesystems unmountable binary sensor."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="filesystems_unmountable",
            name="Filesystems Unmountable",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if any filesystems are unmountable."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return None
        count = data.vars.fs_num_unmountable
        if count is None:
            return None
        return count > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return unmountable filesystem count."""
        data: UnraidInfraData | None = self.coordinator.data
        if data is None or data.vars is None:
            return {}
        return {"count": data.vars.fs_num_unmountable}


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    _LOGGER.debug("Setting up Unraid binary_sensor platform")

    # Get coordinators from runtime_data (HA 2024.4+ pattern)
    runtime_data = entry.runtime_data
    system_coordinator = runtime_data.system_coordinator
    storage_coordinator = runtime_data.storage_coordinator
    infra_coordinator = runtime_data.infra_coordinator
    server_info = runtime_data.server_info

    # Server info is now a flat dict with uuid, name, manufacturer, etc.
    server_uuid = server_info.get("uuid", "unknown")
    server_name = server_info.get("name", entry.data.get("host", "Unraid"))

    entities: list[BinarySensorEntity] = []

    # Array binary sensors
    entities.append(
        ArrayStartedBinarySensor(storage_coordinator, server_uuid, server_name)
    )
    entities.append(
        ParityCheckRunningBinarySensor(storage_coordinator, server_uuid, server_name)
    )
    entities.append(
        ParityValidBinarySensor(storage_coordinator, server_uuid, server_name)
    )

    # Legacy parity status binary sensor (for backwards compatibility)
    entities.append(
        ParityStatusBinarySensor(storage_coordinator, server_uuid, server_name)
    )

    # Add disk sensors using typed coordinator data
    coordinator_data = storage_coordinator.data
    if coordinator_data:
        # Add disk health sensors for all disk types
        all_disks = (
            coordinator_data.disks + coordinator_data.parities + coordinator_data.caches
        )
        for disk in all_disks:
            # Disk health binary sensor (includes standby state in attributes)
            entities.append(
                DiskHealthBinarySensor(
                    storage_coordinator, server_uuid, server_name, disk
                )
            )

    # UPS binary sensors (only created when UPS devices are connected)
    system_data = system_coordinator.data
    if system_data and system_data.ups_devices:
        _LOGGER.debug(
            "Found %d UPS device(s), creating binary sensors",
            len(system_data.ups_devices),
        )
        for ups in system_data.ups_devices:
            entities.append(
                UPSConnectedBinarySensor(
                    system_coordinator, server_uuid, server_name, ups
                )
            )
    else:
        _LOGGER.debug("No UPS devices connected, skipping UPS binary sensors")

    # Container update available binary sensors (enabled by default)
    if system_data and system_data.containers:
        for container in system_data.containers:
            entities.append(
                ContainerUpdateAvailableBinarySensor(
                    system_coordinator, server_uuid, server_name, container
                )
            )

    # Service binary sensors from infrastructure coordinator
    infra_data = infra_coordinator.data
    if infra_data and infra_data.services:
        _LOGGER.debug(
            "Found %d service(s), creating binary sensors",
            len(infra_data.services),
        )
        for service in infra_data.services:
            entities.append(
                ServiceBinarySensor(
                    infra_coordinator, server_uuid, server_name, service
                )
            )
    else:
        _LOGGER.debug("No services data available, skipping service binary sensors")

    # Cloud and remote access binary sensors from infrastructure coordinator
    entities.append(
        CloudConnectedBinarySensor(infra_coordinator, server_uuid, server_name)
    )
    entities.append(
        RemoteAccessBinarySensor(infra_coordinator, server_uuid, server_name)
    )

    # System health binary sensors from Vars (via infrastructure coordinator)
    entities.extend(
        [
            MoverActiveBinarySensor(infra_coordinator, server_uuid, server_name),
            DisksDisabledBinarySensor(infra_coordinator, server_uuid, server_name),
            DisksMissingBinarySensor(infra_coordinator, server_uuid, server_name),
            DisksInvalidBinarySensor(infra_coordinator, server_uuid, server_name),
            SafeModeBinarySensor(infra_coordinator, server_uuid, server_name),
            ConfigValidBinarySensor(infra_coordinator, server_uuid, server_name),
            FilesystemsUnmountableBinarySensor(
                infra_coordinator, server_uuid, server_name
            ),
        ]
    )

    _LOGGER.debug("Adding %d binary_sensor entities", len(entities))
    async_add_entities(entities)
