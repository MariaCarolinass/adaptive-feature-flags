from __future__ import annotations

from datetime import datetime, timezone

from app.domain.services.event_service import EventService
from app.domain.services.ingest_service import IngestService
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository
from app.domain.services.feature_service import FeatureService


def test_ingest_service_saves_events_in_batch(session_factory) -> None:
    event_repo = SqliteEventRepository(session_factory)
    feature_repo = SqliteFeatureRepository(session_factory)
    feature_service = FeatureService(feature_repo)
    event_service = EventService(event_repo)
    ingest_service = IngestService(event_service)

    feature_service.create_feature(
        name="New Checkout",
        key="new_checkout",
        description="test",
        enabled=True,
        rollout_percentage=10,
        ml_enabled=True,
    )

    result = ingest_service.ingest_events(
        source="web_app",
        events=[
            {
                "user_id": "u123",
                "feature_key": "new_checkout",
                "event_type": "clicked",
                "timestamp": datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc),
                "properties": {"device": "mobile"},
            },
            {
                "user_id": "u124",
                "feature_key": "new_checkout",
                "event_type": "viewed_feature",
                "timestamp": datetime(2026, 4, 22, 10, 1, tzinfo=timezone.utc),
                "properties": {"device": "desktop"},
            },
        ],
    )

    assert result["saved_events"] == 2
    saved = event_service.list_events(feature_key="new_checkout")
    assert len(saved) == 2
    assert all(event.source == "web_app" for event in saved)
