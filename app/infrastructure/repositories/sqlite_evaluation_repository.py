from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from app.domain.entities.evaluation import EvaluationRecord
from app.domain.repositories.evaluation_repository import EvaluationRepository
from app.infrastructure.db.models import EvaluationModel


class SqliteEvaluationRepository(EvaluationRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def create(self, evaluation: EvaluationRecord) -> EvaluationRecord:
        with self._session_factory() as session:
            row = EvaluationModel(
                feature_key=evaluation.feature_key,
                user_id=evaluation.user_id,
                activity=evaluation.activity,
                enabled=evaluation.enabled,
                decision_source=evaluation.decision_source,
                score=evaluation.score,
                threshold=evaluation.threshold,
                threshold_mode=evaluation.threshold_mode,
                experiment=evaluation.experiment,
                model_version=evaluation.model_version,
                created_at=evaluation.created_at,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            evaluation.id = row.id
        return evaluation

    def list(self, limit: int = 50) -> list[EvaluationRecord]:
        stmt = select(EvaluationModel).order_by(EvaluationModel.created_at.desc(), EvaluationModel.id.desc()).limit(max(1, limit))
        with self._session_factory() as session:
            rows = session.execute(stmt).scalars().all()
            return [self._to_entity(row) for row in rows]

    def delete_all(self) -> int:
        with self._session_factory() as session:
            result = session.execute(delete(EvaluationModel))
            session.commit()
            return int(result.rowcount or 0)

    @staticmethod
    def _to_entity(row: EvaluationModel) -> EvaluationRecord:
        return EvaluationRecord(
            id=row.id,
            feature_key=row.feature_key,
            user_id=row.user_id,
            activity=row.activity,
            enabled=row.enabled,
            decision_source=row.decision_source,
            score=row.score,
            threshold=row.threshold,
            threshold_mode=row.threshold_mode,
            experiment=row.experiment,
            model_version=row.model_version,
            created_at=row.created_at,
        )
