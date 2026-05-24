from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.domain.entities.experiment import Experiment
from app.domain.repositories.experiment_repository import ExperimentRepository
from app.infrastructure.db.models import ExperimentModel


class SqliteExperimentRepository(ExperimentRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def create(self, experiment: Experiment) -> Experiment:
        with self._session_factory() as session:
            row = ExperimentModel(
                name=experiment.name,
                feature_key=experiment.feature_key,
                primary_metric_event=experiment.primary_metric_event,
                min_samples_per_variant=experiment.min_samples_per_variant,
                min_lift=experiment.min_lift,
                enabled=experiment.enabled,
                created_at=experiment.created_at,
                updated_at=experiment.updated_at,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            experiment.id = row.id
            return experiment

    def list(self) -> list[Experiment]:
        with self._session_factory() as session:
            rows = session.execute(
                select(ExperimentModel).order_by(ExperimentModel.created_at.desc())
            ).scalars().all()
            return [self._to_entity(row) for row in rows]

    def get_active_by_feature_key(self, feature_key: str) -> Experiment | None:
        with self._session_factory() as session:
            row = session.execute(
                select(ExperimentModel).where(
                    ExperimentModel.feature_key == feature_key,
                    ExperimentModel.enabled.is_(True),
                )
            ).scalars().first()
            return self._to_entity(row) if row else None

    @staticmethod
    def _to_entity(row: ExperimentModel) -> Experiment:
        return Experiment(
            id=row.id,
            name=row.name,
            feature_key=row.feature_key,
            primary_metric_event=row.primary_metric_event,
            min_samples_per_variant=row.min_samples_per_variant,
            min_lift=row.min_lift,
            enabled=row.enabled,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
