from datetime import datetime

from app.core.exceptions import NotFoundError
from app.domain.entities.event import Event
from app.domain.repositories.event_repository import EventRepository


class EventService:
    def __init__(self, event_repository: EventRepository) -> None:
        self.event_repository = event_repository

    def create_event(
        self,
        user_id: str,
        feature_key: str,
        event_type: str,
        timestamp: datetime,
        properties: dict[str, str | int | float | bool | None],
        source: str | None = None,
    ) -> Event:
        merged_properties = dict(properties)
        if source:
            merged_properties["source"] = source
        elif "source" in merged_properties and merged_properties["source"] is not None:
            source = str(merged_properties["source"])

        event = Event(
            id=None,
            source=source,
            user_id=user_id,
            feature_key=feature_key,
            event_type=event_type,
            timestamp=timestamp,
            properties=merged_properties,
        )
        return self.event_repository.create(event)

    def list_events(
        self,
        user_id: str | None = None,
        feature_key: str | None = None,
        event_type: str | None = None,
    ) -> list[Event]:
        return self.event_repository.list(
            user_id=user_id,
            feature_key=feature_key,
            event_type=event_type,
        )

    def get_event_by_id(self, event_id: int) -> Event | None:
        return self.event_repository.get_by_id(event_id)

    def update_event(
        self,
        event_id: int,
        user_id: str,
        feature_key: str,
        event_type: str,
        timestamp: datetime,
        properties: dict[str, str | int | float | bool | None],
        source: str | None = None,
    ) -> Event:
        existing = self.event_repository.get_by_id(event_id)
        if existing is None:
            raise NotFoundError("Event not found.")

        merged_properties = dict(properties)
        if source:
            merged_properties["source"] = source
        elif "source" in merged_properties and merged_properties["source"] is not None:
            source = str(merged_properties["source"])

        updated = Event(
            id=existing.id,
            source=source,
            user_id=user_id,
            feature_key=feature_key,
            event_type=event_type,
            timestamp=timestamp,
            properties=merged_properties,
        )
        return self.event_repository.update(updated)

    def delete_event(self, event_id: int) -> None:
        deleted = self.event_repository.delete(event_id)
        if not deleted:
            raise NotFoundError("Event not found.")
