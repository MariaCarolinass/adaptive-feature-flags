from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import NotFoundError
from app.domain.entities.activity import Activity
from app.domain.repositories.activity_repository import ActivityRepository
from app.infrastructure.db.models import ActivityModel


class SqliteActivityRepository(ActivityRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def create(self, activity: Activity) -> Activity:
        with self._session_factory() as session:
            row = ActivityModel(
                key=activity.key,
                name=activity.name,
                description=activity.description,
                enabled=activity.enabled,
                created_at=activity.created_at,
                updated_at=activity.updated_at,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            activity.id = row.id
        return activity

    def list(self) -> list[Activity]:
        with self._session_factory() as session:
            rows = session.execute(select(ActivityModel).order_by(ActivityModel.created_at.asc())).scalars().all()
            return [self._to_entity(row) for row in rows]

    def get_by_id(self, activity_id: int) -> Activity | None:
        with self._session_factory() as session:
            row = session.get(ActivityModel, activity_id)
            return self._to_entity(row) if row is not None else None

    def get_by_key(self, key: str) -> Activity | None:
        with self._session_factory() as session:
            row = session.execute(select(ActivityModel).where(ActivityModel.key == key)).scalars().first()
            return self._to_entity(row) if row is not None else None

    def update(self, activity: Activity) -> Activity:
        with self._session_factory() as session:
            if activity.id is None:
                raise NotFoundError("Activity not found.")
            row = session.get(ActivityModel, activity.id)
            if row is None:
                raise NotFoundError("Activity not found.")

            row.key = activity.key
            row.name = activity.name
            row.description = activity.description
            row.enabled = activity.enabled
            row.updated_at = activity.updated_at
            session.commit()
        return activity

    def delete(self, activity_id: int) -> bool:
        with self._session_factory() as session:
            row = session.get(ActivityModel, activity_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    @staticmethod
    def _to_entity(row: ActivityModel) -> Activity:
        return Activity(
            id=row.id,
            key=row.key,
            name=row.name,
            description=row.description,
            enabled=row.enabled,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
