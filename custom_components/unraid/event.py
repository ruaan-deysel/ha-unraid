"""Event entities for Unraid integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import NOTIFICATION_EVENT_TYPE_CREATED, UnraidNotificationEventData
from .entity import UnraidBaseEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import UnraidConfigEntry
    from .coordinator import UnraidSystemCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class UnraidEventEntityDescription(EventEntityDescription):
    """Unraid EventEntity description."""


NOTIFICATION_EVENT_DESCRIPTION = UnraidEventEntityDescription(
    key="notifications",
    translation_key="notifications",
    event_types=[NOTIFICATION_EVENT_TYPE_CREATED],
)


class UnraidNotificationsEventEntity(UnraidBaseEntity, EventEntity):
    """Event entity that emits newly-discovered Unraid unread notifications."""

    entity_description: UnraidEventEntityDescription = NOTIFICATION_EVENT_DESCRIPTION

    def __init__(
        self,
        coordinator: UnraidSystemCoordinator,
        server_uuid: str,
        server_name: str,
        server_info: dict | None = None,
    ) -> None:
        """Initialize the notifications event entity."""
        super().__init__(
            coordinator=coordinator,
            server_uuid=server_uuid,
            server_name=server_name,
            resource_id=self.entity_description.key,
            name=None,
            server_info=server_info,
        )
        self._attr_translation_key = self.entity_description.translation_key
        self._attr_event_types = self.entity_description.event_types

    async def async_added_to_hass(self) -> None:
        """Register coordinator event listener when added to Home Assistant."""
        await super().async_added_to_hass()

        def _handle_notification_event(event_data: UnraidNotificationEventData) -> None:
            self._trigger_event(
                event_data.event_type,
                {
                    "notification_id": event_data.notification_id,
                    "title": event_data.title,
                    "subject": event_data.subject,
                    "description": event_data.description,
                    "timestamp": event_data.timestamp,
                    "formatted_timestamp": event_data.formatted_timestamp,
                    "importance": event_data.importance,
                    "link": event_data.link,
                    "notification_type": event_data.notification_type,
                },
            )
            self.async_write_ha_state()

        unsubscribe = self.coordinator.async_add_event_listener(
            _handle_notification_event,
            NOTIFICATION_EVENT_TYPE_CREATED,
        )
        self.async_on_remove(unsubscribe)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Unraid event entities."""
    runtime_data = entry.runtime_data
    server_info = runtime_data.server_info
    server_uuid = server_info.get("uuid", entry.entry_id)
    server_name = server_info.get("name", entry.title)

    _LOGGER.debug("Setting up notifications event entity for %s", server_name)
    async_add_entities(
        [
            UnraidNotificationsEventEntity(
                coordinator=runtime_data.system_coordinator,
                server_uuid=server_uuid,
                server_name=server_name,
                server_info=server_info,
            )
        ]
    )
