from __future__ import annotations

from datetime import datetime, timezone

from app.domain.entities.event import Event
from app.domain.entities.feature import Feature
from app.domain.entities.model_metadata import ModelMetadata
from app.domain.services.recommendation_service import RecommendationService


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
    def get_status(self) -> ModelMetadata:
        return ModelMetadata(
            status="ready",
            model_name="random_forest",
            model_version="v1",
            trained_at=datetime.now(timezone.utc),
            metrics={"accuracy": 0.8},
            artifact_path="storage/models/v1.joblib",
        )


def _feature() -> Feature:
    now = datetime.now(timezone.utc)
    return Feature(
        id=1,
        name="Checkout",
        key="new_checkout",
        description=None,
        enabled=True,
        rollout_percentage=10,
        ml_enabled=True,
        created_at=now,
        updated_at=now,
    )


def _event(user_id: str, event_type: str) -> Event:
    return Event(
        id=1,
        source="test",
        user_id=user_id,
        feature_key="new_checkout",
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        properties={},
    )


def test_recommendation_increase_rollout_when_uplift_is_high(monkeypatch) -> None:
    service = RecommendationService(
        feature_repository=_FeatureRepo(_feature()),
        event_repository=_EventRepo(
            [
                _event("u1", "transaction"),
                _event("u2", "view"),
                _event("u3", "view"),
                _event("u4", "view"),
            ]
        ),
        model_repository=_ModelRepo(),
    )

    monkeypatch.setattr(
        RecommendationService,
        "_ml_selected_users",
        lambda self, _events, _artifact: ["u1", "u2"],
    )
    monkeypatch.setattr(
        RecommendationService,
        "_stable_percentage",
        staticmethod(lambda user_id, _feature_key: 0 if user_id in {"u2", "u3"} else 99),
    )

    result = service.get_recommendation("new_checkout")

    assert result["recommendation"] == "increase_rollout"
    assert result["suggested_rollout"] == 30
    assert "higher engagement" in result["reason"]
    assert result["metrics"]["ml_engagement"] == 0.5
    assert result["metrics"]["rollout_engagement"] == 0.0
    assert result["metrics"]["uplift"] == 0.5


def test_recommendation_maintains_rollout_when_no_events() -> None:
    service = RecommendationService(
        feature_repository=_FeatureRepo(_feature()),
        event_repository=_EventRepo([]),
        model_repository=_ModelRepo(),
    )

    result = service.get_recommendation("new_checkout")

    assert result["recommendation"] == "maintain_rollout"
    assert result["suggested_rollout"] == 10
    assert result["metrics"]["uplift"] == 0.0
