from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import NotFoundError
from app.domain.entities.feature import Feature
from app.domain.repositories.feature_repository import FeatureRepository
from app.infrastructure.db.models import FeatureModel


class SqliteFeatureRepository(FeatureRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def create(self, feature: Feature) -> Feature:
        with self._session_factory() as session:
            row = FeatureModel(
                name=feature.name,
                key=feature.key,
                description=feature.description,
                enabled=feature.enabled,
                rollout_percentage=feature.rollout_percentage,
                ml_enabled=feature.ml_enabled,
                created_at=feature.created_at,
                updated_at=feature.updated_at,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            feature.id = row.id
        return feature

    def list(self) -> list[Feature]:
        with self._session_factory() as session:
            rows = session.execute(select(FeatureModel).order_by(FeatureModel.created_at.asc())).scalars().all()
            return [self._to_entity(r) for r in rows]

    def get_by_id(self, feature_id: int) -> Feature | None:
        with self._session_factory() as session:
            row = session.get(FeatureModel, feature_id)
            return self._to_entity(row) if row is not None else None

    def get_by_key(self, key: str) -> Feature | None:
        with self._session_factory() as session:
            row = session.execute(select(FeatureModel).where(FeatureModel.key == key)).scalars().first()
            return self._to_entity(row) if row is not None else None

    def update(self, feature: Feature) -> Feature:
        with self._session_factory() as session:
            if feature.id is None:
                raise NotFoundError("Feature not found.")
            row = session.get(FeatureModel, feature.id)
            if row is None:
                raise NotFoundError("Feature not found.")

            row.name = feature.name
            row.key = feature.key
            row.description = feature.description
            row.enabled = feature.enabled
            row.rollout_percentage = feature.rollout_percentage
            row.ml_enabled = feature.ml_enabled
            row.updated_at = feature.updated_at
            session.commit()
        return feature

    def delete(self, feature_id: int) -> bool:
        with self._session_factory() as session:
            row = session.get(FeatureModel, feature_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    @staticmethod
    def _to_entity(row: FeatureModel) -> Feature:
        return Feature(
            id=row.id,
            name=row.name,
            key=row.key,
            description=row.description,
            enabled=row.enabled,
            rollout_percentage=row.rollout_percentage,
            ml_enabled=row.ml_enabled,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

