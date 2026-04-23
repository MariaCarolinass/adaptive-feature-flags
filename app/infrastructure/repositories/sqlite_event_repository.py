from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import NotFoundError
from app.domain.entities.event import Event
from app.domain.repositories.event_repository import EventRepository
from app.infrastructure.db.models import EventModel


class SqliteEventRepository(EventRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def create(self, event: Event) -> Event:
        with self._session_factory() as session:
            row = EventModel(
                user_id=event.user_id,
                feature_key=event.feature_key,
                event_type=event.event_type,
                timestamp=event.timestamp,
                properties=event.properties,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            event.id = row.id
        return event

    def list(
        self,
        user_id: str | None = None,
        feature_key: str | None = None,
        event_type: str | None = None,
    ) -> list[Event]:
        stmt = select(EventModel)
        if user_id is not None:
            stmt = stmt.where(EventModel.user_id == user_id)
        if feature_key is not None:
            stmt = stmt.where(EventModel.feature_key == feature_key)
        if event_type is not None:
            stmt = stmt.where(EventModel.event_type == event_type)
        stmt = stmt.order_by(EventModel.timestamp.asc())

        with self._session_factory() as session:
            rows = session.execute(stmt).scalars().all()
            return [self._to_entity(r) for r in rows]

    def get_by_id(self, event_id: int) -> Event | None:
        with self._session_factory() as session:
            row = session.get(EventModel, event_id)
            return self._to_entity(row) if row is not None else None

    def update(self, event: Event) -> Event:
        with self._session_factory() as session:
            if event.id is None:
                raise NotFoundError("Event not found.")
            row = session.get(EventModel, event.id)
            if row is None:
                raise NotFoundError("Event not found.")

            row.user_id = event.user_id
            row.feature_key = event.feature_key
            row.event_type = event.event_type
            row.timestamp = event.timestamp
            row.properties = event.properties
            session.commit()
        return event

    def delete(self, event_id: int) -> bool:
        with self._session_factory() as session:
            row = session.get(EventModel, event_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    @staticmethod
    def _to_entity(row: EventModel) -> Event:
        return Event(
            id=row.id,
            user_id=row.user_id,
            feature_key=row.feature_key,
            event_type=row.event_type,
            timestamp=row.timestamp,
            properties=row.properties or {},
        )

