from __future__ import annotations

from datetime import datetime, timezone

from app.domain.entities.event import Event
from app.domain.entities.feature import Feature
from app.domain.entities.model_metadata import ModelMetadata
from app.domain.services.evaluation_service import EvaluationService


class _FeatureRepo:
    def __init__(self, feature: Feature | None) -> None:
        self._feature = feature

    def get_by_key(self, key: str) -> Feature | None:
        if self._feature is None:
            return None
        return self._feature if self._feature.key == key else None


class _EventRepo:
    def __init__(self, events: list[Event]) -> None:
        self._events = events

    def list(self, user_id: str | None = None, feature_key: str | None = None, event_type: str | None = None) -> list[Event]:
        events = self._events
        if user_id is not None:
            events = [e for e in events if e.user_id == user_id]
        if feature_key is not None:
            events = [e for e in events if e.feature_key == feature_key]
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        return events


class _ModelRepo:
    def __init__(self, metadata: ModelMetadata) -> None:
        self._metadata = metadata

    def get_status(self) -> ModelMetadata:
        return self._metadata


class _ExperimentService:
    def maybe_build_context(self, *, feature_key: str, user_id: str) -> dict | None:
        return {
            "experiment_id": 1,
            "experiment_name": "Checkout A/B",
            "variant": "A",
        }


def _feature(*, enabled: bool = True, ml_enabled: bool = True) -> Feature:
    now = datetime.now(timezone.utc)
    return Feature(
        id=1,
        name="Feature A",
        key="feature_a",
        description=None,
        enabled=enabled,
        rollout_percentage=20,
        ml_enabled=ml_enabled,
        ml_threshold_mode="fixed",
        ml_threshold_value=0.1,
        created_at=now,
        updated_at=now,
    )


def _event(user_id: str, event_type: str) -> Event:
    return Event(
        id=1,
        source="test",
        user_id=user_id,
        feature_key="feature_a",
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        properties={},
    )


def test_evaluate_uses_ml_score_when_model_is_ready(monkeypatch) -> None:
    class _Serializer:
        def load_feature_columns(self, _artifact_path: str) -> list[str]:
            return [
                "unique_features",
                "active_days",
                "avg_hour",
                "events_per_day",
                "hours_since_last_event",
            ]

    class _Predictor:
        def __init__(self, _: str) -> None:
            pass

        def predict_score(self, payload: dict) -> float:
            assert payload["unique_features"] == 1
            assert payload["active_days"] == 1
            assert payload["hours_since_last_event"] == 24.0
            return 0.91

    monkeypatch.setattr("app.domain.services.evaluation_service.ModelSerializer", _Serializer)
    monkeypatch.setattr("app.domain.services.evaluation_service.ModelPredictor", _Predictor)

    service = EvaluationService(
        feature_repository=_FeatureRepo(_feature()),
        event_repository=_EventRepo(
            [
                Event(
                    id=1,
                    source="test",
                    user_id="u1",
                    feature_key="feature_a",
                    event_type="view",
                    timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    properties={},
                ),
                Event(
                    id=2,
                    source="test",
                    user_id="u1",
                    feature_key="feature_a",
                    event_type="transaction",
                    timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    properties={},
                ),
            ]
        ),
        model_repository=_ModelRepo(
            ModelMetadata(
                status="ready",
                model_name="random_forest",
                model_version="v1",
                trained_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                metrics={"accuracy": 0.8},
                artifact_path="/tmp/model.joblib",
            )
        ),
        experiment_service=_ExperimentService(),
    )

    result = service.evaluate("feature_a", {"user_id": "u1"})

    assert result["decision_source"] == "ml"
    assert result["enabled"] is True
    assert result["score"] == 0.91
    assert result["threshold"] == 0.1
    assert result["threshold_mode"] == "fixed"
    assert result["model_version"] == "v1"


def test_evaluate_falls_back_to_rollout_when_prediction_fails(monkeypatch) -> None:
    class _Serializer:
        def load_feature_columns(self, _artifact_path: str) -> list[str]:
            return ["unique_features", "active_days"]

    class _BrokenPredictor:
        def __init__(self, _: str) -> None:
            pass

        def predict_score(self, payload: dict) -> float:
            raise RuntimeError("boom")

    monkeypatch.setattr("app.domain.services.evaluation_service.ModelSerializer", _Serializer)
    monkeypatch.setattr("app.domain.services.evaluation_service.ModelPredictor", _BrokenPredictor)

    service = EvaluationService(
        feature_repository=_FeatureRepo(_feature(enabled=True, ml_enabled=True)),
        event_repository=_EventRepo([]),
        model_repository=_ModelRepo(
            ModelMetadata(
                status="ready",
                model_name="random_forest",
                model_version="v1",
                trained_at=datetime.now(timezone.utc),
                metrics={"accuracy": 0.8},
                artifact_path="/tmp/model.joblib",
            )
        ),
        experiment_service=_ExperimentService(),
    )

    result = service.evaluate("feature_a", {"user_id": "u1"})

    assert result["decision_source"] == "rollout"
    assert result["score"] is None
    assert result["threshold"] is None
    assert result["threshold_mode"] is None


def test_evaluate_uses_match_rollout_threshold(monkeypatch) -> None:
    class _Serializer:
        def load_feature_columns(self, _artifact_path: str) -> list[str]:
            return ["unique_features", "active_days"]

    class _Predictor:
        def __init__(self, _: str) -> None:
            pass

        def predict_score(self, payload: dict) -> float:
            return 0.75

    monkeypatch.setattr("app.domain.services.evaluation_service.ModelSerializer", _Serializer)
    monkeypatch.setattr("app.domain.services.evaluation_service.ModelPredictor", _Predictor)

    feature = _feature(enabled=True, ml_enabled=True)
    feature.rollout_percentage = 20
    feature.ml_threshold_mode = "match_rollout"
    feature.ml_threshold_value = 0.2

    service = EvaluationService(
        feature_repository=_FeatureRepo(feature),
        event_repository=_EventRepo([_event("u1", "transaction")]),
        model_repository=_ModelRepo(
            ModelMetadata(
                status="ready",
                model_name="random_forest",
                model_version="v1",
                trained_at=datetime.now(timezone.utc),
                metrics={"accuracy": 0.8},
                artifact_path="/tmp/model.joblib",
            )
        ),
        experiment_service=_ExperimentService(),
    )

    result = service.evaluate("feature_a", {"user_id": "u1"})

    assert result["decision_source"] == "ml"
    assert result["threshold_mode"] == "match_rollout"
    assert result["threshold"] == 0.8
    assert result["enabled"] is False
    assert result["experiment"]["variant"] == "A"
