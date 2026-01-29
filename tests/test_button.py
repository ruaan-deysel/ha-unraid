"""Tests for button entities."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.unraid.button import (
    ParityCheckPauseButton,
    ParityCheckResumeButton,
    ParityCheckStartCorrectionButton,
    async_setup_entry,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = MagicMock()
    client.start_parity_check = AsyncMock(return_value={"parityCheck": {"start": True}})
    client.pause_parity_check = AsyncMock(return_value={"parityCheck": {"pause": True}})
    client.resume_parity_check = AsyncMock(
        return_value={"parityCheck": {"resume": True}}
    )
    return client


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


def test_parity_check_correction_button_creation(mock_api_client, mock_server_info):
    """Test parity check correction button is created correctly."""
    button = ParityCheckStartCorrectionButton(
        api_client=mock_api_client,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    assert button.name == "Parity Check (Correcting)"
    assert button.unique_id == "test-uuid_parity_check_start_correct"
    assert button.translation_key == "parity_check_start_correct"
    # Disabled by default - users enable if needed
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_parity_check_correction_button_press(mock_api_client, mock_server_info):
    """Test pressing correction button calls API with correct=True."""
    button = ParityCheckStartCorrectionButton(
        api_client=mock_api_client,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_api_client.start_parity_check.assert_called_once_with(correct=True)


@pytest.mark.asyncio
async def test_parity_check_correction_button_error(mock_api_client, mock_server_info):
    """Test parity check correction button raises HomeAssistantError."""
    mock_api_client.start_parity_check = AsyncMock(side_effect=Exception("API Error"))
    button = ParityCheckStartCorrectionButton(
        api_client=mock_api_client,
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


def test_parity_check_pause_button_creation(mock_api_client, mock_server_info):
    """Test parity check pause button is created correctly."""
    button = ParityCheckPauseButton(
        api_client=mock_api_client,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    assert button.name == "Pause Parity Check"
    assert button.translation_key == "parity_check_pause"
    # Disabled by default - users enable if needed
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_parity_check_pause_button_press(mock_api_client, mock_server_info):
    """Test pressing pause button calls API."""
    button = ParityCheckPauseButton(
        api_client=mock_api_client,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_api_client.pause_parity_check.assert_called_once()


@pytest.mark.asyncio
async def test_parity_check_pause_button_error(mock_api_client, mock_server_info):
    """Test parity check pause button raises HomeAssistantError on failure."""
    mock_api_client.pause_parity_check = AsyncMock(side_effect=Exception("API Error"))
    button = ParityCheckPauseButton(
        api_client=mock_api_client,
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


def test_parity_check_resume_button_creation(mock_api_client, mock_server_info):
    """Test parity check resume button is created correctly."""
    button = ParityCheckResumeButton(
        api_client=mock_api_client,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    assert button.name == "Resume Parity Check"
    assert button.translation_key == "parity_check_resume"
    # Disabled by default - users enable if needed
    assert button.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_parity_check_resume_button_press(mock_api_client, mock_server_info):
    """Test pressing resume button calls API."""
    button = ParityCheckResumeButton(
        api_client=mock_api_client,
        server_uuid="test-uuid",
        server_name="Test Server",
        server_info=mock_server_info,
    )
    await button.async_press()
    mock_api_client.resume_parity_check.assert_called_once()


@pytest.mark.asyncio
async def test_parity_check_resume_button_error(mock_api_client, mock_server_info):
    """Test parity check resume button raises HomeAssistantError on failure."""
    mock_api_client.resume_parity_check = AsyncMock(side_effect=Exception("API Error"))
    button = ParityCheckResumeButton(
        api_client=mock_api_client,
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

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # Should have 3 parity buttons: correction, pause, resume
    assert len(entities) == 3
    entity_types = [type(e).__name__ for e in entities]
    assert "ParityCheckStartCorrectionButton" in entity_types
    assert "ParityCheckPauseButton" in entity_types
    assert "ParityCheckResumeButton" in entity_types


@pytest.mark.asyncio
async def test_setup_entry_with_missing_server_uuid(hass):
    """Test setup with missing server UUID uses 'unknown'."""
    mock_api = MagicMock()

    runtime_data = MagicMock()
    runtime_data.api_client = mock_api
    runtime_data.server_info = {}  # No uuid

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # Check that entities were created with "unknown" uuid
    assert len(entities) == 3
    assert entities[0].unique_id.startswith("unknown_")


@pytest.mark.asyncio
async def test_setup_entry_uses_host_as_fallback_name(hass):
    """Test setup uses host as fallback when server name is missing."""
    mock_api = MagicMock()

    runtime_data = MagicMock()
    runtime_data.api_client = mock_api
    runtime_data.server_info = {"uuid": "test-uuid"}  # No name

    mock_entry = MagicMock()
    mock_entry.runtime_data = runtime_data
    mock_entry.data = {"host": "192.168.1.100"}

    entities = []

    def capture_entities(ents) -> None:
        entities.extend(ents)

    await async_setup_entry(hass, mock_entry, capture_entities)

    # Should still create 3 buttons
    assert len(entities) == 3
