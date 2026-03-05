"""Tests for button entities."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError
from unraid_api.exceptions import UnraidAPIError

from custom_components.unraid.button import (
    ArchiveAllNotificationsButton,
    DeleteAllArchivedNotificationsButton,
    DockerContainerRestartButton,
    ParityCheckPauseButton,
    ParityCheckResumeButton,
    ParityCheckStartCorrectionButton,
    VMForceStopButton,
    VMPauseButton,
    VMRebootButton,
    VMResetButton,
    VMResumeButton,
    async_setup_entry,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with action wrappers."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.async_start_parity_check = AsyncMock(
        return_value={"parityCheck": {"start": True}}
    )
    coordinator.async_pause_parity_check = AsyncMock(
        return_value={"parityCheck": {"pause": True}}
    )
    coordinator.async_resume_parity_check = AsyncMock(
        return_value={"parityCheck": {"resume": True}}
    )
    coordinator.async_restart_container = AsyncMock()
    coordinator.async_force_stop_vm = AsyncMock()
    coordinator.async_reboot_vm = AsyncMock()
    coordinator.async_pause_vm = AsyncMock()
    coordinator.async_resume_vm = AsyncMock()
    coordinator.async_reset_vm = AsyncMock()
    coordinator.async_archive_all_notifications = AsyncMock()
    coordinator.async_delete_all_notifications = AsyncMock()
    return coordinator


@pytest.fixture
def mock_server_info():
    """Create mock server info."""
    return {
        "uuid": "test-uuid",
        "name": "Test Server",
        "manufacturer": "Test",
        "model": "Server",
    }


# =============================================================================
# ParityCheckStartCorrectionButton Tests
# =============================================================================


def test_parity_check_correction_button_creation(mock_coordinator, mock_server_info):
    """Test parity check correction button is created correctly."""
    button = ParityCheckStartCorrectionButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    assert button._attr_translation_key == "parity_check_start_correct"
    assert button.unique_id == "test-uuid_parity_check_start_correct"
    # Disabled by default - users enable if needed
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_parity_check_correction_button_press(mock_coordinator, mock_server_info):
    """Test pressing correction button calls API with correct=True."""
    button = ParityCheckStartCorrectionButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_coordinator.async_start_parity_check.assert_called_once_with(correct=True)


@pytest.mark.asyncio
async def test_parity_check_correction_button_error(mock_coordinator, mock_server_info):
    """Test parity check correction button raises HomeAssistantError."""
    mock_coordinator.async_start_parity_check = AsyncMock(
        side_effect=UnraidAPIError("API Error")
    )
    button = ParityCheckStartCorrectionButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "parity_check_start_failed"


# =============================================================================
# ParityCheckPauseButton Tests
# =============================================================================


def test_parity_check_pause_button_creation(mock_coordinator, mock_server_info):
    """Test parity check pause button is created correctly."""
    button = ParityCheckPauseButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    assert button._attr_translation_key == "parity_check_pause"
    # Disabled by default - users enable if needed
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_parity_check_pause_button_press(mock_coordinator, mock_server_info):
    """Test pressing pause button calls API."""
    button = ParityCheckPauseButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_coordinator.async_pause_parity_check.assert_called_once()


@pytest.mark.asyncio
async def test_parity_check_pause_button_error(mock_coordinator, mock_server_info):
    """Test parity check pause button raises HomeAssistantError on failure."""
    mock_coordinator.async_pause_parity_check = AsyncMock(
        side_effect=UnraidAPIError("API Error")
    )
    button = ParityCheckPauseButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "parity_check_pause_failed"


# =============================================================================
# ParityCheckResumeButton Tests
# =============================================================================


def test_parity_check_resume_button_creation(mock_coordinator, mock_server_info):
    """Test parity check resume button is created correctly."""
    button = ParityCheckResumeButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    assert button._attr_translation_key == "parity_check_resume"
    # Disabled by default - users enable if needed
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_parity_check_resume_button_press(mock_coordinator, mock_server_info):
    """Test pressing resume button calls API."""
    button = ParityCheckResumeButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_coordinator.async_resume_parity_check.assert_called_once()


@pytest.mark.asyncio
async def test_parity_check_resume_button_error(mock_coordinator, mock_server_info):
    """Test parity check resume button raises HomeAssistantError on failure."""
    mock_coordinator.async_resume_parity_check = AsyncMock(
        side_effect=UnraidAPIError("API Error")
    )
    button = ParityCheckResumeButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "parity_check_resume_failed"


# =============================================================================
# async_setup_entry Tests
# =============================================================================


@pytest.mark.asyncio
async def test_setup_entry_creates_parity_buttons(hass):
    """Test that setup creates parity control buttons."""
    mock_api = MagicMock()

    runtime_data = MagicMock()
    runtime_data.api_client = mock_api
    runtime_data.server_info = {
        "uuid": "test-uuid",
        "name": "Test Server",
        "manufacturer": "Test",
        "model": "Server",
    }
    runtime_data.system_coordinator = MagicMock()
    runtime_data.system_coordinator.data = None  # No containers

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # Should have 3 parity + 2 notification buttons
    assert len(entities) == 5
    entity_types = [type(e).__name__ for e in entities]
    assert "ParityCheckStartCorrectionButton" in entity_types
    assert "ParityCheckPauseButton" in entity_types
    assert "ParityCheckResumeButton" in entity_types
    assert "ArchiveAllNotificationsButton" in entity_types
    assert "DeleteAllArchivedNotificationsButton" in entity_types


@pytest.mark.asyncio
async def test_setup_entry_with_missing_server_uuid(hass):
    """Test setup with missing server UUID uses 'unknown'."""
    mock_api = MagicMock()

    runtime_data = MagicMock()
    runtime_data.api_client = mock_api
    runtime_data.server_info = {}  # No uuid
    runtime_data.system_coordinator = MagicMock()
    runtime_data.system_coordinator.data = None  # No containers

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # Check that entities were created with "unknown" uuid
    assert len(entities) == 5
    assert entities[0].unique_id.startswith("unknown_")


@pytest.mark.asyncio
async def test_setup_entry_uses_host_as_fallback_name(hass):
    """Test setup uses host as fallback when server name is missing."""
    mock_api = MagicMock()

    runtime_data = MagicMock()
    runtime_data.api_client = mock_api
    runtime_data.server_info = {"uuid": "test-uuid"}  # No name
    runtime_data.system_coordinator = MagicMock()
    runtime_data.system_coordinator.data = None  # No containers

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # Should still create 3 parity + 2 notification buttons
    assert len(entities) == 5


# =============================================================================
# DockerContainerRestartButton Tests
# =============================================================================


@pytest.fixture
def mock_container():
    """Create a mock Docker container."""
    container = MagicMock()
    container.name = "/plex"
    container.id = "abc123"
    return container


def test_docker_restart_button_creation(
    mock_coordinator, mock_server_info, mock_container
):
    """Test Docker container restart button is created correctly."""
    button = DockerContainerRestartButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        container=mock_container,
        server_info=mock_server_info,
    )
    assert button.unique_id == "test-uuid_container_restart_plex"
    assert button.translation_key == "docker_container_restart"
    # Disabled by default - users enable if needed
    assert button.entity_registry_enabled_default is False
    # Check translation placeholders
    assert button.translation_placeholders == {"name": "plex"}


@pytest.mark.asyncio
async def test_docker_restart_button_press(
    mock_coordinator, mock_server_info, mock_container
):
    """Test pressing restart button calls restart_container."""
    button = DockerContainerRestartButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        container=mock_container,
        server_info=mock_server_info,
    )

    await button.async_press()

    mock_coordinator.async_restart_container.assert_called_once_with("abc123")


@pytest.mark.asyncio
async def test_docker_restart_button_error_on_stop(
    mock_coordinator, mock_server_info, mock_container
):
    """Test restart button raises HomeAssistantError if restart fails."""
    mock_coordinator.async_restart_container = AsyncMock(
        side_effect=UnraidAPIError("Restart failed")
    )

    button = DockerContainerRestartButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        container=mock_container,
        server_info=mock_server_info,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()

    assert exc_info.value.translation_key == "container_restart_failed"


@pytest.mark.asyncio
async def test_docker_restart_button_error_on_start(
    mock_coordinator, mock_server_info, mock_container
):
    """Test restart button raises HomeAssistantError if library restart raises."""
    mock_coordinator.async_restart_container = AsyncMock(
        side_effect=UnraidAPIError("Start failed")
    )

    button = DockerContainerRestartButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        container=mock_container,
        server_info=mock_server_info,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()

    assert exc_info.value.translation_key == "container_restart_failed"


@pytest.mark.asyncio
async def test_setup_entry_creates_container_restart_buttons(hass):
    """Test that setup creates restart buttons for Docker containers."""
    mock_api = MagicMock()

    # Create mock containers
    container1 = MagicMock()
    container1.name = "/plex"
    container1.id = "abc123"
    container2 = MagicMock()
    container2.name = "/sonarr"
    container2.id = "def456"

    system_coordinator = MagicMock()
    system_coordinator.data = MagicMock()
    system_coordinator.data.containers = [container1, container2]
    system_coordinator.data.vms = []

    runtime_data = MagicMock()
    runtime_data.api_client = mock_api
    runtime_data.server_info = {
        "uuid": "test-uuid",
        "name": "Test Server",
        "manufacturer": "Test",
        "model": "Server",
    }
    runtime_data.system_coordinator = system_coordinator

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # Should have 3 parity + 2 notification + 2 container restart = 7
    assert len(entities) == 7
    entity_types = [type(e).__name__ for e in entities]
    assert entity_types.count("DockerContainerRestartButton") == 2


@pytest.mark.asyncio
async def test_setup_entry_no_containers(hass):
    """Test that setup handles no containers gracefully."""
    mock_api = MagicMock()

    system_coordinator = MagicMock()
    system_coordinator.data = MagicMock()
    system_coordinator.data.containers = []  # Empty list
    system_coordinator.data.vms = []  # No VMs either

    runtime_data = MagicMock()
    runtime_data.api_client = mock_api
    runtime_data.server_info = {"uuid": "test-uuid", "name": "Test Server"}
    runtime_data.system_coordinator = system_coordinator

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # Should only have 3 parity + 2 notification buttons, no container buttons
    assert len(entities) == 5


# =============================================================================
# VM Button Fixture
# =============================================================================


@pytest.fixture
def mock_vm():
    """Create a mock VM."""
    vm = MagicMock()
    vm.name = "Windows 11"
    vm.id = "vm-uuid-001"
    return vm


# =============================================================================
# VMForceStopButton Tests
# =============================================================================


def test_vm_force_stop_button_creation(mock_coordinator, mock_server_info, mock_vm):
    """Test VM force stop button is created correctly."""
    button = VMForceStopButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    assert button.unique_id == "test-uuid_vm_force_stop_Windows 11"
    assert button.translation_key == "vm_force_stop"
    assert button.entity_registry_enabled_default is False
    assert button.translation_placeholders == {"name": "Windows 11"}


@pytest.mark.asyncio
async def test_vm_force_stop_button_press(mock_coordinator, mock_server_info, mock_vm):
    """Test pressing force stop button calls API."""
    button = VMForceStopButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_coordinator.async_force_stop_vm.assert_called_once_with("vm-uuid-001")


@pytest.mark.asyncio
async def test_vm_force_stop_button_error(mock_coordinator, mock_server_info, mock_vm):
    """Test force stop button raises HomeAssistantError on failure."""
    mock_coordinator.async_force_stop_vm = AsyncMock(
        side_effect=UnraidAPIError("API Error")
    )
    button = VMForceStopButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "vm_force_stop_failed"


# =============================================================================
# VMRebootButton Tests
# =============================================================================


def test_vm_reboot_button_creation(mock_coordinator, mock_server_info, mock_vm):
    """Test VM reboot button is created correctly."""
    button = VMRebootButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    assert button.unique_id == "test-uuid_vm_reboot_Windows 11"
    assert button.translation_key == "vm_reboot"
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_vm_reboot_button_press(mock_coordinator, mock_server_info, mock_vm):
    """Test pressing reboot button calls API."""
    button = VMRebootButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_coordinator.async_reboot_vm.assert_called_once_with("vm-uuid-001")


@pytest.mark.asyncio
async def test_vm_reboot_button_error(mock_coordinator, mock_server_info, mock_vm):
    """Test reboot button raises HomeAssistantError on failure."""
    mock_coordinator.async_reboot_vm = AsyncMock(
        side_effect=UnraidAPIError("API Error")
    )
    button = VMRebootButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "vm_reboot_failed"


# =============================================================================
# VMPauseButton Tests
# =============================================================================


def test_vm_pause_button_creation(mock_coordinator, mock_server_info, mock_vm):
    """Test VM pause button is created correctly."""
    button = VMPauseButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    assert button.unique_id == "test-uuid_vm_pause_Windows 11"
    assert button.translation_key == "vm_pause"
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_vm_pause_button_press(mock_coordinator, mock_server_info, mock_vm):
    """Test pressing pause button calls API."""
    button = VMPauseButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_coordinator.async_pause_vm.assert_called_once_with("vm-uuid-001")


@pytest.mark.asyncio
async def test_vm_pause_button_error(mock_coordinator, mock_server_info, mock_vm):
    """Test pause button raises HomeAssistantError on failure."""
    mock_coordinator.async_pause_vm = AsyncMock(side_effect=UnraidAPIError("API Error"))
    button = VMPauseButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "vm_pause_failed"


# =============================================================================
# VMResumeButton Tests
# =============================================================================


def test_vm_resume_button_creation(mock_coordinator, mock_server_info, mock_vm):
    """Test VM resume button is created correctly."""
    button = VMResumeButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    assert button.unique_id == "test-uuid_vm_resume_Windows 11"
    assert button.translation_key == "vm_resume"
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_vm_resume_button_press(mock_coordinator, mock_server_info, mock_vm):
    """Test pressing resume button calls API."""
    button = VMResumeButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_coordinator.async_resume_vm.assert_called_once_with("vm-uuid-001")


@pytest.mark.asyncio
async def test_vm_resume_button_error(mock_coordinator, mock_server_info, mock_vm):
    """Test resume button raises HomeAssistantError on failure."""
    mock_coordinator.async_resume_vm = AsyncMock(
        side_effect=UnraidAPIError("API Error")
    )
    button = VMResumeButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "vm_resume_failed"


# =============================================================================
# VMResetButton Tests
# =============================================================================


def test_vm_reset_button_creation(mock_coordinator, mock_server_info, mock_vm):
    """Test VM reset button is created correctly."""
    button = VMResetButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    assert button.unique_id == "test-uuid_vm_reset_Windows 11"
    assert button.translation_key == "vm_reset"
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_vm_reset_button_press(mock_coordinator, mock_server_info, mock_vm):
    """Test pressing reset button calls API."""
    button = VMResetButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_coordinator.async_reset_vm.assert_called_once_with("vm-uuid-001")


@pytest.mark.asyncio
async def test_vm_reset_button_error(mock_coordinator, mock_server_info, mock_vm):
    """Test reset button raises HomeAssistantError on failure."""
    mock_coordinator.async_reset_vm = AsyncMock(side_effect=UnraidAPIError("API Error"))
    button = VMResetButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        vm=mock_vm,
        server_info=mock_server_info,
    )
    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "vm_reset_failed"


# =============================================================================
# VM Setup Entry Tests
# =============================================================================


@pytest.mark.asyncio
async def test_setup_entry_creates_vm_buttons(hass):
    """Test that setup creates VM control buttons for each VM."""
    mock_api = MagicMock()

    vm1 = MagicMock()
    vm1.name = "Windows 11"
    vm1.id = "vm-001"
    vm2 = MagicMock()
    vm2.name = "Ubuntu"
    vm2.id = "vm-002"

    system_coordinator = MagicMock()
    system_coordinator.data = MagicMock()
    system_coordinator.data.containers = []
    system_coordinator.data.vms = [vm1, vm2]

    runtime_data = MagicMock()
    runtime_data.api_client = mock_api
    runtime_data.server_info = {
        "uuid": "test-uuid",
        "name": "Test Server",
        "manufacturer": "Test",
        "model": "Server",
    }
    runtime_data.system_coordinator = system_coordinator

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # 3 parity + 2 notification + 2 VMs * 5 buttons each = 15
    assert len(entities) == 15
    entity_types = [type(e).__name__ for e in entities]
    assert entity_types.count("VMForceStopButton") == 2
    assert entity_types.count("VMRebootButton") == 2
    assert entity_types.count("VMPauseButton") == 2
    assert entity_types.count("VMResumeButton") == 2
    assert entity_types.count("VMResetButton") == 2


@pytest.mark.asyncio
async def test_setup_entry_creates_container_and_vm_buttons(hass):
    """Test that setup creates both container and VM buttons."""
    mock_api = MagicMock()

    container = MagicMock()
    container.name = "/plex"
    container.id = "ct-001"

    vm = MagicMock()
    vm.name = "Windows 11"
    vm.id = "vm-001"

    system_coordinator = MagicMock()
    system_coordinator.data = MagicMock()
    system_coordinator.data.containers = [container]
    system_coordinator.data.vms = [vm]

    runtime_data = MagicMock()
    runtime_data.api_client = mock_api
    runtime_data.server_info = {
        "uuid": "test-uuid",
        "name": "Test Server",
    }
    runtime_data.system_coordinator = system_coordinator

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # 3 parity + 2 notification + 1 container restart + 1 VM * 5 buttons = 11
    assert len(entities) == 11
    entity_types = [type(e).__name__ for e in entities]
    assert entity_types.count("DockerContainerRestartButton") == 1
    assert entity_types.count("VMForceStopButton") == 1
    assert entity_types.count("VMRebootButton") == 1
    assert entity_types.count("VMPauseButton") == 1
    assert entity_types.count("VMResumeButton") == 1
    assert entity_types.count("VMResetButton") == 1


# =============================================================================
# ArchiveAllNotificationsButton Tests
# =============================================================================


def test_archive_all_notifications_button_creation(mock_coordinator, mock_server_info):
    """Test archive all notifications button is created correctly."""
    button = ArchiveAllNotificationsButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    assert button.unique_id == "test-uuid_archive_all_notifications"
    assert button.translation_key == "archive_all_notifications"
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_archive_all_notifications_button_press(
    mock_coordinator, mock_server_info
):
    """Test pressing archive all notifications button."""
    button = ArchiveAllNotificationsButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )

    await button.async_press()

    mock_coordinator.async_archive_all_notifications.assert_called_once()


@pytest.mark.asyncio
async def test_archive_all_notifications_button_error(
    mock_coordinator, mock_server_info
):
    """Test archive all notifications button raises error on failure."""
    mock_coordinator.async_archive_all_notifications = AsyncMock(
        side_effect=UnraidAPIError("Archive failed")
    )

    button = ArchiveAllNotificationsButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "archive_all_notifications_failed"


# =============================================================================
# DeleteAllArchivedNotificationsButton Tests
# =============================================================================


def test_delete_all_archived_notifications_button_creation(
    mock_coordinator, mock_server_info
):
    """Test delete all archived notifications button is created correctly."""
    button = DeleteAllArchivedNotificationsButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    assert button.unique_id == "test-uuid_delete_all_archived_notifications"
    assert button.translation_key == "delete_all_archived_notifications"
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_delete_all_archived_notifications_button_press(
    mock_coordinator, mock_server_info
):
    """Test pressing delete all archived notifications button."""
    button = DeleteAllArchivedNotificationsButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )

    await button.async_press()

    mock_coordinator.async_delete_all_notifications.assert_called_once()


@pytest.mark.asyncio
async def test_delete_all_archived_notifications_button_error(
    mock_coordinator, mock_server_info
):
    """Test delete all archived button raises error on failure."""
    mock_coordinator.async_delete_all_notifications = AsyncMock(
        side_effect=UnraidAPIError("Delete failed")
    )

    button = DeleteAllArchivedNotificationsButton(
        coordinator=mock_coordinator,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )

    with pytest.raises(HomeAssistantError) as exc_info:
        await button.async_press()
    assert exc_info.value.translation_key == "delete_all_archived_notifications_failed"
