from datetime import datetime, timezone

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.entities.activity import Activity
from app.domain.repositories.activity_repository import ActivityRepository


class ActivityService:
    def __init__(self, activity_repository: ActivityRepository) -> None:
        self.activity_repository = activity_repository

    def create_activity(
        self,
        key: str,
        name: str,
        description: str | None,
        enabled: bool,
    ) -> Activity:
        existing = self.activity_repository.get_by_key(key)
        if existing is not None:
            raise ConflictError(f"Activity with key '{key}' already exists.")

        now = datetime.now(timezone.utc)
        activity = Activity(
            id=None,
            key=key,
            name=name,
            description=description,
            enabled=enabled,
            created_at=now,
            updated_at=now,
        )
        return self.activity_repository.create(activity)

    def list_activities(self) -> list[Activity]:
        return self.activity_repository.list()

    def get_activity_by_id(self, activity_id: int) -> Activity | None:
        return self.activity_repository.get_by_id(activity_id)

    def update_activity(
        self,
        activity_id: int,
        key: str,
        name: str,
        description: str | None,
        enabled: bool,
    ) -> Activity:
        existing = self.activity_repository.get_by_id(activity_id)
        if existing is None:
            raise NotFoundError("Activity not found.")

        duplicate = self.activity_repository.get_by_key(key)
        if duplicate is not None and duplicate.id != activity_id:
            raise ConflictError(f"Activity with key '{key}' already exists.")

        updated = Activity(
            id=existing.id,
            key=key,
            name=name,
            description=description,
            enabled=enabled,
            created_at=existing.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        return self.activity_repository.update(updated)

    def delete_activity(self, activity_id: int) -> None:
        deleted = self.activity_repository.delete(activity_id)
        if not deleted:
            raise NotFoundError("Activity not found.")
