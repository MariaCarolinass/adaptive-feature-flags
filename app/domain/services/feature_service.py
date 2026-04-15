from datetime import datetime, timezone
from uuid import uuid4, UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.entities.feature import Feature
from app.domain.repositories.feature_repository import FeatureRepository


class FeatureService:
    def __init__(self, feature_repository: FeatureRepository) -> None:
        self.feature_repository = feature_repository

    def create_feature(
        self,
        name: str,
        key: str,
        description: str | None,
        enabled: bool,
        rollout_percentage: int,
        ml_enabled: bool,
    ) -> Feature:
        existing = self.feature_repository.get_by_key(key)
        if existing is not None:
            raise ConflictError(f"Feature with key '{key}' already exists.")

        now = datetime.now(timezone.utc)

        feature = Feature(
            id=uuid4(),
            name=name,
            key=key,
            description=description,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            ml_enabled=ml_enabled,
            created_at=now,
            updated_at=now,
        )

        return self.feature_repository.create(feature)

    def list_features(self) -> list[Feature]:
        return self.feature_repository.list()

    def get_feature_by_id(self, feature_id: UUID) -> Feature | None:
        return self.feature_repository.get_by_id(feature_id)

    def update_feature(
        self,
        feature_id: UUID,
        name: str,
        key: str,
        description: str | None,
        enabled: bool,
        rollout_percentage: int,
        ml_enabled: bool,
    ) -> Feature:
        existing = self.feature_repository.get_by_id(feature_id)
        if existing is None:
            raise NotFoundError("Feature not found.")

        duplicate_key_feature = self.feature_repository.get_by_key(key)
        if duplicate_key_feature is not None and duplicate_key_feature.id != feature_id:
            raise ConflictError(f"Feature with key '{key}' already exists.")

        updated = Feature(
            id=existing.id,
            name=name,
            key=key,
            description=description,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            ml_enabled=ml_enabled,
            created_at=existing.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        return self.feature_repository.update(updated)

    def delete_feature(self, feature_id: UUID) -> None:
        deleted = self.feature_repository.delete(feature_id)
        if not deleted:
            raise NotFoundError("Feature not found.")