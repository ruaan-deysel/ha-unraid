"""Tests for Unraid event entities."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from custom_components.unraid.coordinator import UnraidNotificationEventData
from custom_components.unraid.event import UnraidNotificationsEventEntity


@pytest.fixture
def mock_system_coordinator() -> MagicMock:
    """Create a mock system coordinator."""
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = MagicMock()
    return coordinator


@pytest.fixture
def mock_server_info() -> dict[str, str]:
    """Create test server info payload."""
    return {"manufacturer": "Lime Technology", "model": "Unraid 7.2.0"}


@pytest.mark.asyncio
async def test_notifications_event_entity_subscribes_and_unsubscribes(
    mock_system_coordinator, mock_server_info
) -> None:
    """Test event entity registers and unregisters coordinator callback."""
    mock_system_coordinator.async_add_event_listener = MagicMock(
        return_value=MagicMock()
    )

    entity = UnraidNotificationsEventEntity(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        server_info=mock_server_info,
    )

    entity.async_on_remove = MagicMock()

    await entity.async_added_to_hass()

    mock_system_coordinator.async_add_event_listener.assert_called_once()
    entity.async_on_remove.assert_called_once()


@pytest.mark.asyncio
async def test_notifications_event_entity_triggers_event_on_callback(
    mock_system_coordinator, mock_server_info
) -> None:
    """Test coordinator notification callback triggers HA event + state write."""
    captured_callback = None

    def _capture_callback(
        callback: Callable[[UnraidNotificationEventData], None],
        _target_event_id: str,
    ) -> Callable[[], None]:
        nonlocal captured_callback
        captured_callback = callback
        return lambda: None

    mock_system_coordinator.async_add_event_listener = _capture_callback

    entity = UnraidNotificationsEventEntity(
        coordinator=mock_system_coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        server_info=mock_server_info,
    )
    entity._trigger_event = MagicMock()
    entity.async_write_ha_state = MagicMock()

    await entity.async_added_to_hass()

    assert captured_callback is not None
    captured_callback(
        UnraidNotificationEventData(
            event_type="notification_created",
            notification_id="notif-1",
            title="Photo Backup",
            subject="Backup Successful",
            description="All photo backups completed successfully.",
            timestamp="2026-04-24T08:01:04.000Z",
            formatted_timestamp="Friday, 24-04-2026 10:01",
            importance="INFO",
            link="",
            notification_type="UNREAD",
        )
    )

    entity._trigger_event.assert_called_once_with(
        "notification_created",
        {
            "notification_id": "notif-1",
            "title": "Photo Backup",
            "subject": "Backup Successful",
            "description": "All photo backups completed successfully.",
            "timestamp": "2026-04-24T08:01:04.000Z",
            "formatted_timestamp": "Friday, 24-04-2026 10:01",
            "importance": "INFO",
            "link": "",
            "notification_type": "UNREAD",
        },
    )
    entity.async_write_ha_state.assert_called_once()
