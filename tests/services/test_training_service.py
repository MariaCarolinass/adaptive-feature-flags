from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.core.exceptions import ValidationError
from app.domain.entities.event import Event
from app.domain.entities.model_metadata import ModelMetadata
from app.domain.services.training_service import TrainingService


class _EventRepo:
    def __init__(self, events: list[Event]) -> None:
        self._events = events

    def list(self, user_id: str | None = None, feature_key: str | None = None, event_type: str | None = None) -> list[Event]:
        return self._events


class _ModelRepo:
    def __init__(self) -> None:
        self.saved: ModelMetadata | None = None

    def save_status(self, metadata: ModelMetadata) -> ModelMetadata:
        self.saved = metadata
        return metadata

    def get_status(self) -> ModelMetadata:
        return ModelMetadata(
            status="idle",
            model_name=None,
            model_version=None,
            trained_at=None,
            metrics=None,
            artifact_path=None,
        )

    def append_training_run(self, *, model_version: str, trained_at, status: str, snapshot: dict) -> None:
        return

    def list_training_runs(self, limit: int = 20) -> list[dict]:
        return []


def _event(event_type: str) -> Event:
    return Event(
        id=1,
        source="test",
        user_id="u1",
        feature_key="f1",
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        properties={},
    )


def test_training_service_requires_events() -> None:
    service = TrainingService(event_repository=_EventRepo([]), model_repository=_ModelRepo())
    with pytest.raises(ValidationError, match="at least one event"):
        service.train()


def test_training_service_wraps_trainer_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    service = TrainingService(event_repository=_EventRepo([_event("view")]), model_repository=_ModelRepo())

    def _raise(_: list) -> dict:
        raise ValueError("Training requires examples from at least two classes.")

    monkeypatch.setattr("app.domain.services.training_service.train_from_events", _raise)

    with pytest.raises(ValidationError, match="two classes"):
        service.train()


def test_training_service_returns_process_details(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _ModelRepo()
    service = TrainingService(
        event_repository=_EventRepo([_event("view"), _event("transaction"), _event("view")]),
        model_repository=repo,
    )

    def _ok(_: list) -> dict:
        return {
            "model_name": "random_forest",
            "model_version": "v1",
            "trained_at": datetime.now(timezone.utc),
            "metrics": {
                "accuracy": 0.8,
                "precision": 0.76,
                "recall": 0.72,
                "f1_score": 0.7,
                "roc_auc": 0.81,
                "confusion_matrix": {
                    "true_negative": 10,
                    "false_positive": 2,
                    "false_negative": 3,
                    "true_positive": 7,
                },
            },
            "artifact_path": "storage/models/v1.joblib",
            "feature_columns": ["total_events", "positive_events"],
            "benchmark": [{"model_name": "random_forest", "f1_score": 0.7}],
            "dataset_profile": {"rows": 3, "train_rows": 2, "test_rows": 1, "positive_rate": 0.33},
        }

    monkeypatch.setattr("app.domain.services.training_service.train_from_events", _ok)

    result = service.train()

    assert result["status"] == "ready"
    assert result["model_name"] == "random_forest"
    assert result["artifact_path"] == "storage/models/v1.joblib"
    assert result["process"]["total_events"] == 3
    assert result["process"]["unique_users"] == 1
    assert result["process"]["positive_events"] == 1
    assert result["process"]["feature_columns"] == ["total_events", "positive_events"]
    assert result["process"]["benchmark"] == [{"model_name": "random_forest", "f1_score": 0.7}]
    assert result["process"]["dataset_profile"]["rows"] == 3
    assert isinstance(result["process"]["duration_ms"], int)
