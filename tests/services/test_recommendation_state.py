from __future__ import annotations

from datetime import datetime, timezone

from app.domain.services.event_service import EventService
from app.domain.services.feature_service import FeatureService
from app.domain.services.recommendation_service import RecommendationService
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository
from app.infrastructure.repositories.sqlite_model_repository import SqliteModelRepository


def test_recommendation_returns_without_mutating_feature_state(session_factory) -> None:
    event_repo = SqliteEventRepository(session_factory)
    feature_repo = SqliteFeatureRepository(session_factory)
    model_repo = SqliteModelRepository(session_factory)

    event_service = EventService(event_repo)
    feature_service = FeatureService(feature_repo)
    recommendation_service = RecommendationService(feature_repo, event_repo, model_repo)

    created = feature_service.create_feature(
        name="New Checkout",
        key="new_checkout",
        description="test",
        enabled=True,
        rollout_percentage=10,
        ml_enabled=False,
    )
    event_service.create_event(
        user_id="u1",
        feature_key="new_checkout",
        event_type="viewed_feature",
        timestamp=datetime.now(timezone.utc),
        properties={},
        source="test",
    )

    response = recommendation_service.get_recommendation("new_checkout")
    loaded = feature_repo.get_by_id(created.id)

    assert response["feature_key"] == "new_checkout"
    assert response["recommendation"] in {"maintain_rollout", "increase_rollout", "pause_rollout"}
    assert loaded is not None
    assert loaded.rollout_percentage == 10
