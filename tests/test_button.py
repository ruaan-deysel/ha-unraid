"""Tests for button entities."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.unraid.button import (
    ArrayStartButton,
    ArrayStopButton,
    DiskSpinDownButton,
    DiskSpinUpButton,
    ParityCheckPauseButton,
    ParityCheckResumeButton,
    ParityCheckStartButton,
    ParityCheckStartCorrectionButton,
    ParityCheckStopButton,
)
from custom_components.unraid.models import ArrayDisk


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = MagicMock()
    client.start_array = AsyncMock(return_value={"array": {"state": "STARTED"}})
    client.stop_array = AsyncMock(return_value={"array": {"state": "STOPPED"}})
    client.start_parity_check = AsyncMock(return_value={"parityCheck": {"start": True}})
    client.pause_parity_check = AsyncMock(return_value={"parityCheck": {"pause": True}})
    client.resume_parity_check = AsyncMock(
        return_value={"parityCheck": {"resume": True}}
    )
    client.cancel_parity_check = AsyncMock(
        return_value={"parityCheck": {"cancel": True}}
    )
    client.spin_up_disk = AsyncMock(
        return_value={"array": {"mountArrayDisk": {"isSpinning": True}}}
    )
    client.spin_down_disk = AsyncMock(
        return_value={"array": {"unmountArrayDisk": {"isSpinning": False}}}
    )
    return client


@pytest.fixture
def mock_storage_coordinator():
    """Create a mock storage coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_disk():
    """Create a mock disk."""
    return ArrayDisk(
        id="disk:1",
        idx=1,
        name="Disk 1",
        device="sda",
        type="DATA",
    )


class TestArrayStartButton:
    """Test ArrayStartButton."""

    def test_button_creation(self, mock_api_client):
        """Test array start button is created correctly."""
        button = ArrayStartButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        assert button.name == "Start Array"
        assert button.unique_id == "test-uuid_array_start"
        assert button.translation_key == "array_start"

    @pytest.mark.asyncio
    async def test_button_press(self, mock_api_client):
        """Test pressing array start button calls API."""
        button = ArrayStartButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        await button.async_press()
        mock_api_client.start_array.assert_called_once()


class TestArrayStopButton:
    """Test ArrayStopButton."""

    def test_button_creation(self, mock_api_client):
        """Test array stop button is created correctly."""
        button = ArrayStopButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        assert button.name == "Stop Array"
        assert button.unique_id == "test-uuid_array_stop"
        assert button.translation_key == "array_stop"

    @pytest.mark.asyncio
    async def test_button_press(self, mock_api_client):
        """Test pressing array stop button calls API."""
        button = ArrayStopButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        await button.async_press()
        mock_api_client.stop_array.assert_called_once()


class TestParityCheckStartButton:
    """Test ParityCheckStartButton."""

    def test_button_creation(self, mock_api_client):
        """Test parity check start button is created correctly."""
        button = ParityCheckStartButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        assert button.name == "Start Parity Check"
        assert button.unique_id == "test-uuid_parity_check_start"
        assert button.translation_key == "parity_check_start"

    @pytest.mark.asyncio
    async def test_button_press(self, mock_api_client):
        """Test pressing parity check start button calls API with correct=False."""
        button = ParityCheckStartButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        await button.async_press()
        mock_api_client.start_parity_check.assert_called_once_with(correct=False)


class TestParityCheckStartCorrectionButton:
    """Test ParityCheckStartCorrectionButton."""

    def test_button_creation(self, mock_api_client):
        """Test parity check correction button is created correctly."""
        button = ParityCheckStartCorrectionButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        assert button.name == "Start Parity Check (Correcting)"
        assert button.unique_id == "test-uuid_parity_check_start_correct"

    @pytest.mark.asyncio
    async def test_button_press(self, mock_api_client):
        """Test pressing correction button calls API with correct=True."""
        button = ParityCheckStartCorrectionButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        await button.async_press()
        mock_api_client.start_parity_check.assert_called_once_with(correct=True)


class TestParityCheckPauseButton:
    """Test ParityCheckPauseButton."""

    def test_button_creation(self, mock_api_client):
        """Test parity check pause button is created correctly."""
        button = ParityCheckPauseButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        assert button.name == "Pause Parity Check"
        assert button.translation_key == "parity_check_pause"

    @pytest.mark.asyncio
    async def test_button_press(self, mock_api_client):
        """Test pressing pause button calls API."""
        button = ParityCheckPauseButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        await button.async_press()
        mock_api_client.pause_parity_check.assert_called_once()


class TestParityCheckResumeButton:
    """Test ParityCheckResumeButton."""

    def test_button_creation(self, mock_api_client):
        """Test parity check resume button is created correctly."""
        button = ParityCheckResumeButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        assert button.name == "Resume Parity Check"
        assert button.translation_key == "parity_check_resume"

    @pytest.mark.asyncio
    async def test_button_press(self, mock_api_client):
        """Test pressing resume button calls API."""
        button = ParityCheckResumeButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        await button.async_press()
        mock_api_client.resume_parity_check.assert_called_once()


class TestParityCheckStopButton:
    """Test ParityCheckStopButton."""

    def test_button_creation(self, mock_api_client):
        """Test parity check stop button is created correctly."""
        button = ParityCheckStopButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        assert button.name == "Stop Parity Check"
        assert button.translation_key == "parity_check_stop"

    @pytest.mark.asyncio
    async def test_button_press(self, mock_api_client):
        """Test pressing stop button calls API."""
        button = ParityCheckStopButton(
            api_client=mock_api_client,
            server_uuid="test-uuid",
            server_name="Test Server",
        )
        await button.async_press()
        mock_api_client.cancel_parity_check.assert_called_once()


class TestDiskSpinUpButton:
    """Test DiskSpinUpButton."""

    def test_button_creation(
        self, mock_api_client, mock_storage_coordinator, mock_disk
    ):
        """Test disk spin up button is created correctly."""
        button = DiskSpinUpButton(
            api_client=mock_api_client,
            coordinator=mock_storage_coordinator,
            server_uuid="test-uuid",
            server_name="Test Server",
            disk=mock_disk,
        )
        assert button.name == "Spin Up Disk 1"
        assert button.unique_id == "test-uuid_disk_spin_up_disk:1"
        assert button.translation_key == "disk_spin_up"

    @pytest.mark.asyncio
    async def test_button_press(
        self, mock_api_client, mock_storage_coordinator, mock_disk
    ):
        """Test pressing spin up button calls API and refreshes coordinator."""
        button = DiskSpinUpButton(
            api_client=mock_api_client,
            coordinator=mock_storage_coordinator,
            server_uuid="test-uuid",
            server_name="Test Server",
            disk=mock_disk,
        )
        await button.async_press()
        mock_api_client.spin_up_disk.assert_called_once_with("disk:1")
        mock_storage_coordinator.async_request_refresh.assert_called_once()


class TestDiskSpinDownButton:
    """Test DiskSpinDownButton."""

    def test_button_creation(
        self, mock_api_client, mock_storage_coordinator, mock_disk
    ):
        """Test disk spin down button is created correctly."""
        button = DiskSpinDownButton(
            api_client=mock_api_client,
            coordinator=mock_storage_coordinator,
            server_uuid="test-uuid",
            server_name="Test Server",
            disk=mock_disk,
        )
        assert button.name == "Spin Down Disk 1"
        assert button.unique_id == "test-uuid_disk_spin_down_disk:1"
        assert button.translation_key == "disk_spin_down"

    @pytest.mark.asyncio
    async def test_button_press(
        self, mock_api_client, mock_storage_coordinator, mock_disk
    ):
        """Test pressing spin down button calls API and refreshes coordinator."""
        button = DiskSpinDownButton(
            api_client=mock_api_client,
            coordinator=mock_storage_coordinator,
            server_uuid="test-uuid",
            server_name="Test Server",
            disk=mock_disk,
        )
        await button.async_press()
        mock_api_client.spin_down_disk.assert_called_once_with("disk:1")
        mock_storage_coordinator.async_request_refresh.assert_called_once()
