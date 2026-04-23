from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.infrastructure.ml import trainer


@dataclass
class _Event:
    user_id: str
    event_type: str
    timestamp: datetime
    feature_key: str


class _FakeSerializer:
    def __init__(self) -> None:
        self.saved = None

    def save(self, *, model, model_version: str, metadata: dict, feature_columns: list[str]) -> str:
        self.saved = {
            "model": model,
            "model_version": model_version,
            "metadata": metadata,
            "feature_columns": feature_columns,
        }
        return "/tmp/test-model.joblib"


def test_train_from_events_requires_non_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one event"):
        trainer.train_from_events([])


def test_train_from_events_requires_two_classes() -> None:
    events = [
        _Event("u1", "view", datetime.now(timezone.utc), "f1"),
        _Event("u1", "view", datetime.now(timezone.utc), "f1"),
        _Event("u2", "view", datetime.now(timezone.utc), "f1"),
    ]
    with pytest.raises(ValueError, match="two classes"):
        trainer.train_from_events(events)


def test_train_from_events_saves_model_and_returns_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_serializer = _FakeSerializer()
    monkeypatch.setattr(trainer, "ModelSerializer", lambda: fake_serializer)

    events = [
        _Event("u1", "view", datetime.now(timezone.utc), "f1"),
        _Event("u1", "addtocart", datetime.now(timezone.utc), "f1"),
        _Event("u2", "view", datetime.now(timezone.utc), "f1"),
        _Event("u2", "view", datetime.now(timezone.utc), "f1"),
        _Event("u3", "transaction", datetime.now(timezone.utc), "f1"),
        _Event("u4", "view", datetime.now(timezone.utc), "f1"),
    ]

    result = trainer.train_from_events(events)

    assert result["model_name"] == "random_forest"
    assert result["model_version"] == "v1"
    assert result["artifact_path"] == "/tmp/test-model.joblib"
    assert "accuracy" in result["metrics"]
    assert "f1_score" in result["metrics"]
