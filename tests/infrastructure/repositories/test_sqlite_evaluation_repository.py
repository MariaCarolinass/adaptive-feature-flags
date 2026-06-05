from __future__ import annotations

from datetime import datetime, timezone, timedelta

from app.domain.entities.evaluation import EvaluationRecord
from app.infrastructure.repositories.sqlite_evaluation_repository import SqliteEvaluationRepository


def _evaluation(
    *,
    user_id: str = "u1",
    feature_key: str = "feature_a",
    created_at: datetime | None = None,
) -> EvaluationRecord:
    ts = created_at or datetime.now(timezone.utc)
    return EvaluationRecord(
        id=None,
        feature_key=feature_key,
        user_id=user_id,
        enabled=True,
        decision_source="rollout",
        score=0.42,
        threshold=0.1,
        threshold_mode="fixed",
        experiment={"experiment_id": 1, "variant": "A"},
        model_version="v1",
        created_at=ts,
    )


def test_create_and_list_evaluations(session_factory) -> None:
    repo = SqliteEvaluationRepository(session_factory)
    first = repo.create(_evaluation(user_id="u1", created_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
    second = repo.create(_evaluation(user_id="u2"))

    result = repo.list(limit=10)

    assert first.id is not None
    assert second.id is not None
    assert len(result) == 2
    assert result[0].id == second.id
    assert result[1].id == first.id


def test_delete_all_evaluations_removes_rows(session_factory) -> None:
    repo = SqliteEvaluationRepository(session_factory)
    repo.create(_evaluation())
    repo.create(_evaluation(user_id="u2"))

    deleted = repo.delete_all()

    assert deleted == 2
    assert repo.list(limit=10) == []
