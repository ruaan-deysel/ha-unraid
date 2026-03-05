"""Button entities for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from unraid_api.exceptions import UnraidAPIError

from .const import DOMAIN
from .entity import UnraidBaseEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from unraid_api.models import DockerContainer, VmDomain

    from . import UnraidConfigEntry
    from .coordinator import UnraidStorageCoordinator, UnraidSystemCoordinator

_LOGGER = logging.getLogger(__name__)

# Buttons make API calls (restart, force stop, parity operations, etc.).
# Limit to one concurrent call to avoid overloading the Unraid server.
PARALLEL_UPDATES = 1


class UnraidButtonEntity(ButtonEntity, UnraidBaseEntity):
    """
    Base class for Unraid button entities.

    Buttons are action-only entities and invoke actions via coordinator wrappers.
    Uses UnraidBaseEntity for consistent device info, unique ID, and availability.
    """

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator | UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        resource_id: str,
        name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize button entity."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=resource_id,
            name=name,
            server_info=server_info,
        )


# =============================================================================
# Parity Check Control Buttons
# =============================================================================
# Note: Start/Stop parity check is handled by ParityCheckSwitch in switch.py
# These buttons provide additional parity control not possible with a switch:
# - Start with corrections (write mode)
# - Pause/Resume (for long-running checks)


class ParityCheckStartCorrectionButton(UnraidButtonEntity):
    """
    Button to start a parity check with corrections enabled.

    This button starts a parity check that will WRITE corrections to the
    parity disk if errors are found. Use with caution.

    Note: For read-only parity checks, use the Parity Check switch instead.
    """

    _attr_translation_key = "parity_check_start_correct"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize parity check with corrections button."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_check_start_correct",
            name="Parity Check (Correcting)",
            server_info=server_info,
        )

    async def async_press(self) -> None:
        """Handle button press to start parity check with corrections."""
        _LOGGER.info("Starting correcting parity check on %s", self._server_name)
        try:
            # Start with corrections enabled (correct=True)
            await self.coordinator.async_start_parity_check(correct=True)
            _LOGGER.debug("Correcting parity check start command sent successfully")
        except UnraidAPIError as err:
            _LOGGER.error("Failed to start correcting parity check: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="parity_check_start_failed",
                translation_placeholders={"error": str(err)},
            ) from err


class ParityCheckPauseButton(UnraidButtonEntity):
    """
    Button to pause a running parity check.

    Pausing preserves progress and allows resuming later.
    """

    _attr_translation_key = "parity_check_pause"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize parity check pause button."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_check_pause",
            name="Pause Parity Check",
            server_info=server_info,
        )

    async def async_press(self) -> None:
        """Handle button press to pause parity check."""
        _LOGGER.info("Pausing parity check on %s", self._server_name)
        try:
            await self.coordinator.async_pause_parity_check()
            _LOGGER.debug("Parity check pause command sent successfully")
        except UnraidAPIError as err:
            _LOGGER.error("Failed to pause parity check: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="parity_check_pause_failed",
                translation_placeholders={"error": str(err)},
            ) from err


class ParityCheckResumeButton(UnraidButtonEntity):
    """
    Button to resume a paused parity check.

    Resumes from the last paused position.
    """

    _attr_translation_key = "parity_check_resume"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidStorageCoordinator,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize parity check resume button."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="parity_check_resume",
            name="Resume Parity Check",
            server_info=server_info,
        )

    async def async_press(self) -> None:
        """Handle button press to resume parity check."""
        _LOGGER.info("Resuming parity check on %s", self._server_name)
        try:
            await self.coordinator.async_resume_parity_check()
            _LOGGER.debug("Parity check resume command sent successfully")
        except UnraidAPIError as err:
            _LOGGER.error("Failed to resume parity check: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="parity_check_resume_failed",
                translation_placeholders={"error": str(err)},
            ) from err


# =============================================================================
# Docker Container Control Buttons
# =============================================================================


class DockerContainerRestartButton(UnraidButtonEntity):
    """
    Button to restart a Docker container.

    Performs a stop + start sequence since Unraid's GraphQL API
    does not have a native restart mutation.

    Disabled by default - users can enable per-container as needed.
    """

    _attr_translation_key = "docker_container_restart"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        container: DockerContainer,
        server_info: dict | None = None,
    ) -> None:
        """Initialize Docker container restart button."""
        # Container IDs are ephemeral - use NAME for stable unique_id
        self._container_name = container.name.lstrip("/")
        self._container_id = container.id
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"container_restart_{self._container_name}",
            name=f"Restart Container {self._container_name}",
            server_info=server_info,
        )
        self._attr_translation_placeholders = {"name": self._container_name}

    async def async_press(self) -> None:
        """Handle button press to restart container."""
        _LOGGER.info(
            "Restarting Docker container '%s' on %s",
            self._container_name,
            self._server_name,
        )
        try:
            await self.coordinator.async_restart_container(self._container_id)
            _LOGGER.debug(
                "Container '%s' restart completed successfully", self._container_name
            )
        except UnraidAPIError as err:
            _LOGGER.error(
                "Failed to restart Docker container '%s': %s", self._container_name, err
            )
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="container_restart_failed",
                translation_placeholders={
                    "name": self._container_name,
                    "error": str(err),
                },
            ) from err


# =============================================================================
# Virtual Machine Control Buttons
# =============================================================================


class VMButtonBase(UnraidButtonEntity):
    """
    Base class for per-VM button entities.

    All VM buttons are disabled by default and categorized as CONFIG.
    Subclasses implement specific VM actions via async_press().
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        action: str,
        server_info: dict | None = None,
    ) -> None:
        """
        Initialize VM button.

        Args:
            coordinator: Unraid system coordinator
            server_uuid: Server UUID for unique_id
            server_name: Server name for device info
            vm: VM model from coordinator data
            action: Action identifier (e.g., "force_stop", "reboot")
            server_info: Optional server info dict for device registration

        """
        self._vm_name = vm.name
        self._vm_id = vm.id
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=f"vm_{action}_{self._vm_name}",
            name=f"{action.replace('_', ' ').title()} VM {vm.name}",
            server_info=server_info,
        )
        self._attr_translation_placeholders = {"name": self._vm_name}


class VMForceStopButton(VMButtonBase):
    """Button to force stop a virtual machine."""

    _attr_translation_key = "vm_force_stop"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM force stop button."""
        super().__init__(
            coordinator, server_uuid, server_name, vm, "force_stop", server_info
        )

    async def async_press(self) -> None:
        """Handle button press to force stop VM."""
        try:
            await self.coordinator.async_force_stop_vm(self._vm_id)
            _LOGGER.debug("Force stopped VM '%s'", self._vm_name)
        except UnraidAPIError as err:
            _LOGGER.error("Failed to force stop VM '%s': %s", self._vm_name, err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="vm_force_stop_failed",
                translation_placeholders={
                    "name": self._vm_name,
                    "error": str(err),
                },
            ) from err


class VMRebootButton(VMButtonBase):
    """Button to reboot a virtual machine."""

    _attr_translation_key = "vm_reboot"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM reboot button."""
        super().__init__(
            coordinator, server_uuid, server_name, vm, "reboot", server_info
        )

    async def async_press(self) -> None:
        """Handle button press to reboot VM."""
        try:
            await self.coordinator.async_reboot_vm(self._vm_id)
            _LOGGER.debug("Rebooted VM '%s'", self._vm_name)
        except UnraidAPIError as err:
            _LOGGER.error("Failed to reboot VM '%s': %s", self._vm_name, err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="vm_reboot_failed",
                translation_placeholders={
                    "name": self._vm_name,
                    "error": str(err),
                },
            ) from err


class VMPauseButton(VMButtonBase):
    """Button to pause a virtual machine."""

    _attr_translation_key = "vm_pause"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM pause button."""
        super().__init__(
            coordinator, server_uuid, server_name, vm, "pause", server_info
        )

    async def async_press(self) -> None:
        """Handle button press to pause VM."""
        try:
            await self.coordinator.async_pause_vm(self._vm_id)
            _LOGGER.debug("Paused VM '%s'", self._vm_name)
        except UnraidAPIError as err:
            _LOGGER.error("Failed to pause VM '%s': %s", self._vm_name, err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="vm_pause_failed",
                translation_placeholders={
                    "name": self._vm_name,
                    "error": str(err),
                },
            ) from err


class VMResumeButton(VMButtonBase):
    """Button to resume a paused virtual machine."""

    _attr_translation_key = "vm_resume"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM resume button."""
        super().__init__(
            coordinator, server_uuid, server_name, vm, "resume", server_info
        )

    async def async_press(self) -> None:
        """Handle button press to resume VM."""
        try:
            await self.coordinator.async_resume_vm(self._vm_id)
            _LOGGER.debug("Resumed VM '%s'", self._vm_name)
        except UnraidAPIError as err:
            _LOGGER.error("Failed to resume VM '%s': %s", self._vm_name, err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="vm_resume_failed",
                translation_placeholders={
                    "name": self._vm_name,
                    "error": str(err),
                },
            ) from err


class VMResetButton(VMButtonBase):
    """Button to reset a virtual machine."""

    _attr_translation_key = "vm_reset"

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM reset button."""
        super().__init__(
            coordinator, server_uuid, server_name, vm, "reset", server_info
        )

    async def async_press(self) -> None:
        """Handle button press to reset VM."""
        try:
            await self.coordinator.async_reset_vm(self._vm_id)
            _LOGGER.debug("Reset VM '%s'", self._vm_name)
        except UnraidAPIError as err:
            _LOGGER.error("Failed to reset VM '%s': %s", self._vm_name, err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="vm_reset_failed",
                translation_placeholders={
                    "name": self._vm_name,
                    "error": str(err),
                },
            ) from err


# =============================================================================
# Notification Management Buttons
# =============================================================================


class ArchiveAllNotificationsButton(UnraidButtonEntity):
    """
    Button to archive all unread notifications.

    Archives all current unread notifications on the Unraid server.
    Disabled by default - users enable when needed.
    """

    _attr_translation_key = "archive_all_notifications"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize archive all notifications button."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="archive_all_notifications",
            name="Archive All Notifications",
            server_info=server_info,
        )

    async def async_press(self) -> None:
        """Handle button press to archive all notifications."""
        _LOGGER.info("Archiving all notifications on %s", self._server_name)
        try:
            await self.coordinator.async_archive_all_notifications()
            _LOGGER.debug("Archive all notifications command sent successfully")
        except UnraidAPIError as err:
            _LOGGER.error("Failed to archive all notifications: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="archive_all_notifications_failed",
                translation_placeholders={"error": str(err)},
            ) from err


class DeleteAllArchivedNotificationsButton(UnraidButtonEntity):
    """
    Button to delete all archived notifications.

    Permanently deletes all archived notifications on the Unraid server.
    Disabled by default - users enable when needed.
    """

    _attr_translation_key = "delete_all_archived_notifications"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize delete all archived notifications button."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id="delete_all_archived_notifications",
            name="Delete All Archived Notifications",
            server_info=server_info,
        )

    async def async_press(self) -> None:
        """Handle button press to delete all archived notifications."""
        _LOGGER.info("Deleting all archived notifications on %s", self._server_name)
        try:
            await self.coordinator.async_delete_all_notifications()
            _LOGGER.debug("Delete all archived notifications command sent successfully")
        except UnraidAPIError as err:
            _LOGGER.error("Failed to delete all archived notifications: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="delete_all_archived_notifications_failed",
                translation_placeholders={"error": str(err)},
            ) from err


# =============================================================================
# Platform Setup
# =============================================================================


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    _LOGGER.debug("Setting up Unraid button platform")

    # Get coordinators from runtime_data (HA 2024.4+ pattern)
    runtime_data = entry.runtime_data
    storage_coordinator = runtime_data.storage_coordinator
    server_info = runtime_data.server_info
    system_coordinator = runtime_data.system_coordinator

    # Server info is now a flat dict with uuid, name, manufacturer, etc.
    server_uuid = server_info.get("uuid", "unknown")
    server_name = server_info.get("name", entry.data.get("host", "Unraid"))

    entities: list[ButtonEntity] = []

    # Parity check control buttons (disabled by default)
    # Note: Array start/stop and disk spin up/down are now switches
    # These buttons provide parity operations not possible with a simple switch:
    # - Correcting mode (writes to parity)
    # - Pause/Resume (for long checks)
    entities.append(
        ParityCheckStartCorrectionButton(
            storage_coordinator, server_uuid, server_name, server_info
        )
    )
    entities.append(
        ParityCheckPauseButton(
            storage_coordinator, server_uuid, server_name, server_info
        )
    )
    entities.append(
        ParityCheckResumeButton(
            storage_coordinator, server_uuid, server_name, server_info
        )
    )

    # Notification management buttons (disabled by default)
    entities.append(
        ArchiveAllNotificationsButton(
            system_coordinator, server_uuid, server_name, server_info
        )
    )
    entities.append(
        DeleteAllArchivedNotificationsButton(
            system_coordinator, server_uuid, server_name, server_info
        )
    )

    # Docker container restart buttons (disabled by default)
    # Users can enable per-container as needed for automation workflows
    if system_coordinator.data and system_coordinator.data.containers:
        _LOGGER.debug(
            "Creating restart buttons for %d Docker container(s)",
            len(system_coordinator.data.containers),
        )
        for container in system_coordinator.data.containers:
            entities.append(
                DockerContainerRestartButton(
                    system_coordinator,
                    server_uuid,
                    server_name,
                    container,
                    server_info,
                )
            )

    # ==========================================================================
    # VM Control Buttons (disabled by default)
    # ==========================================================================
    # These provide actions not available through the VM on/off switch:
    # - Force Stop: immediate power off (vs graceful shutdown)
    # - Reboot: restart without full stop/start cycle
    # - Pause/Resume: freeze/unfreeze VM state
    # - Reset: hard reset (equivalent to power cycle)
    if system_coordinator.data and system_coordinator.data.vms:
        _LOGGER.debug(
            "Creating control buttons for %d VM(s)",
            len(system_coordinator.data.vms),
        )
        for vm in system_coordinator.data.vms:
            entities.extend(
                [
                    VMForceStopButton(
                        system_coordinator, server_uuid, server_name, vm, server_info
                    ),
                    VMRebootButton(
                        system_coordinator, server_uuid, server_name, vm, server_info
                    ),
                    VMPauseButton(
                        system_coordinator, server_uuid, server_name, vm, server_info
                    ),
                    VMResumeButton(
                        system_coordinator, server_uuid, server_name, vm, server_info
                    ),
                    VMResetButton(
                        system_coordinator, server_uuid, server_name, vm, server_info
                    ),
                ]
            )

    _LOGGER.debug("Adding %d button entities", len(entities))
    async_add_entities(entities)
