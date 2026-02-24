"""Button entities for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from unraid_api import UnraidClient
    from unraid_api.models import DockerContainer, VmDomain

    from . import UnraidConfigEntry

_LOGGER = logging.getLogger(__name__)

# Buttons make API calls, limit to one at a time to avoid overloading server
PARALLEL_UPDATES = 1


class UnraidButtonEntity(ButtonEntity):
    """
    Base class for Unraid button entities.

    Buttons are action-only entities that don't track state from a coordinator.
    They use the API client directly for mutations.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        resource_id: str,
        name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize button entity."""
        self.api_client = api_client
        self._server_uuid = server_uuid
        self._server_name = server_name
        self._attr_unique_id = f"{server_uuid}_{resource_id}"
        # Only set _attr_name if no translation_key handles the naming
        if not getattr(self, "_attr_translation_key", None):
            self._attr_name = name
        # Use DeviceInfo for consistent device registration
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, server_uuid)},
            name=server_name,
            manufacturer=server_info.get("manufacturer") if server_info else None,
            model=server_info.get("model") if server_info else None,
            serial_number=server_info.get("serial_number") if server_info else None,
            sw_version=server_info.get("sw_version") if server_info else None,
            hw_version=server_info.get("hw_version") if server_info else None,
            configuration_url=(
                server_info.get("configuration_url") if server_info else None
            ),
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
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize parity check with corrections button."""
        super().__init__(
            api_client=api_client,
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
            await self.api_client.start_parity_check(correct=True)
            _LOGGER.debug("Correcting parity check start command sent successfully")
        except Exception as err:
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
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize parity check pause button."""
        super().__init__(
            api_client=api_client,
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
            await self.api_client.pause_parity_check()
            _LOGGER.debug("Parity check pause command sent successfully")
        except Exception as err:
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
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize parity check resume button."""
        super().__init__(
            api_client=api_client,
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
            await self.api_client.resume_parity_check()
            _LOGGER.debug("Parity check resume command sent successfully")
        except Exception as err:
            _LOGGER.error("Failed to resume parity check: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="parity_check_resume_failed",
                translation_placeholders={"error": str(err)},
            ) from err


# =============================================================================
# Docker Container Control Buttons
# =============================================================================


class DockerContainerRestartButton(ButtonEntity):
    """
    Button to restart a Docker container.

    Performs a stop + start sequence since Unraid's GraphQL API
    does not have a native restart mutation.

    Disabled by default - users can enable per-container as needed.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "docker_container_restart"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        container: DockerContainer,
        server_info: dict | None = None,
    ) -> None:
        """Initialize Docker container restart button."""
        self.api_client = api_client
        self._server_uuid = server_uuid
        self._server_name = server_name
        # Container IDs are ephemeral - use NAME for stable unique_id
        self._container_name = container.name.lstrip("/")
        self._container_id = container.id
        self._attr_unique_id = f"{server_uuid}_container_restart_{self._container_name}"
        self._attr_translation_placeholders = {"name": self._container_name}
        # Use DeviceInfo for consistent device registration
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, server_uuid)},
            name=server_name,
            manufacturer=server_info.get("manufacturer") if server_info else None,
            model=server_info.get("model") if server_info else None,
            serial_number=server_info.get("serial_number") if server_info else None,
            sw_version=server_info.get("sw_version") if server_info else None,
            hw_version=server_info.get("hw_version") if server_info else None,
            configuration_url=(
                server_info.get("configuration_url") if server_info else None
            ),
        )

    async def async_press(self) -> None:
        """Handle button press to restart container."""
        _LOGGER.info(
            "Restarting Docker container '%s' on %s",
            self._container_name,
            self._server_name,
        )
        try:
            # Use the library's restart_container() which encapsulates
            # the stop/wait/start sequence (available since unraid-api 1.5.0)
            await self.api_client.restart_container(self._container_id)
            _LOGGER.debug(
                "Container '%s' restart completed successfully", self._container_name
            )
        except Exception as err:
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


class VMButtonBase(ButtonEntity):
    """
    Base class for per-VM button entities.

    All VM buttons are disabled by default and categorized as CONFIG.
    Subclasses implement specific VM actions via async_press().
    """

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        action: str,
        server_info: dict | None = None,
    ) -> None:
        """
        Initialize VM button.

        Args:
            api_client: Unraid API client
            server_uuid: Server UUID for unique_id
            server_name: Server name for device info
            vm: VM model from coordinator data
            action: Action identifier (e.g., "force_stop", "reboot")
            server_info: Optional server info dict for device registration

        """
        self.api_client = api_client
        self._server_uuid = server_uuid
        self._server_name = server_name
        self._vm_name = vm.name
        self._vm_id = vm.id
        self._attr_unique_id = f"{server_uuid}_vm_{action}_{self._vm_name}"
        self._attr_translation_placeholders = {"name": self._vm_name}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, server_uuid)},
            name=server_name,
            manufacturer=server_info.get("manufacturer") if server_info else None,
            model=server_info.get("model") if server_info else None,
            serial_number=server_info.get("serial_number") if server_info else None,
            sw_version=server_info.get("sw_version") if server_info else None,
            hw_version=server_info.get("hw_version") if server_info else None,
            configuration_url=(
                server_info.get("configuration_url") if server_info else None
            ),
        )


class VMForceStopButton(VMButtonBase):
    """Button to force stop a virtual machine."""

    _attr_translation_key = "vm_force_stop"

    def __init__(
        self,
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM force stop button."""
        super().__init__(
            api_client, server_uuid, server_name, vm, "force_stop", server_info
        )

    async def async_press(self) -> None:
        """Handle button press to force stop VM."""
        try:
            await self.api_client.force_stop_vm(self._vm_id)
            _LOGGER.debug("Force stopped VM '%s'", self._vm_name)
        except Exception as err:
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
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM reboot button."""
        super().__init__(
            api_client, server_uuid, server_name, vm, "reboot", server_info
        )

    async def async_press(self) -> None:
        """Handle button press to reboot VM."""
        try:
            await self.api_client.reboot_vm(self._vm_id)
            _LOGGER.debug("Rebooted VM '%s'", self._vm_name)
        except Exception as err:
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
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM pause button."""
        super().__init__(api_client, server_uuid, server_name, vm, "pause", server_info)

    async def async_press(self) -> None:
        """Handle button press to pause VM."""
        try:
            await self.api_client.pause_vm(self._vm_id)
            _LOGGER.debug("Paused VM '%s'", self._vm_name)
        except Exception as err:
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
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM resume button."""
        super().__init__(
            api_client, server_uuid, server_name, vm, "resume", server_info
        )

    async def async_press(self) -> None:
        """Handle button press to resume VM."""
        try:
            await self.api_client.resume_vm(self._vm_id)
            _LOGGER.debug("Resumed VM '%s'", self._vm_name)
        except Exception as err:
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
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        vm: VmDomain,
        server_info: dict | None = None,
    ) -> None:
        """Initialize VM reset button."""
        super().__init__(api_client, server_uuid, server_name, vm, "reset", server_info)

    async def async_press(self) -> None:
        """Handle button press to reset VM."""
        try:
            await self.api_client.reset_vm(self._vm_id)
            _LOGGER.debug("Reset VM '%s'", self._vm_name)
        except Exception as err:
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
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize archive all notifications button."""
        super().__init__(
            api_client=api_client,
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
            await self.api_client.archive_all_notifications()
            _LOGGER.debug("Archive all notifications command sent successfully")
        except Exception as err:
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
        api_client: UnraidClient,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize delete all archived notifications button."""
        super().__init__(
            api_client=api_client,
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
            await self.api_client.delete_all_notifications()
            _LOGGER.debug("Delete all archived notifications command sent successfully")
        except Exception as err:
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

    # Get API client and coordinators from runtime_data (HA 2024.4+ pattern)
    runtime_data = entry.runtime_data
    api_client = runtime_data.api_client
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
            api_client, server_uuid, server_name, server_info
        )
    )
    entities.append(
        ParityCheckPauseButton(api_client, server_uuid, server_name, server_info)
    )
    entities.append(
        ParityCheckResumeButton(api_client, server_uuid, server_name, server_info)
    )

    # Notification management buttons (disabled by default)
    entities.append(
        ArchiveAllNotificationsButton(api_client, server_uuid, server_name, server_info)
    )
    entities.append(
        DeleteAllArchivedNotificationsButton(
            api_client, server_uuid, server_name, server_info
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
                    api_client, server_uuid, server_name, container, server_info
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
                        api_client, server_uuid, server_name, vm, server_info
                    ),
                    VMRebootButton(
                        api_client, server_uuid, server_name, vm, server_info
                    ),
                    VMPauseButton(
                        api_client, server_uuid, server_name, vm, server_info
                    ),
                    VMResumeButton(
                        api_client, server_uuid, server_name, vm, server_info
                    ),
                    VMResetButton(
                        api_client, server_uuid, server_name, vm, server_info
                    ),
                ]
            )

    _LOGGER.debug("Adding %d button entities", len(entities))
    async_add_entities(entities)
