from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.core.exceptions import ValidationError
from app.domain.services.event_service import EventService
from app.domain.services.ingest_service import IngestService
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository
from app.domain.services.feature_service import FeatureService


class _ExperimentService:
    def maybe_build_context(self, *, feature_key: str, user_id: str) -> dict | None:
        if feature_key == "new_checkout":
            return {"experiment_id": 1, "experiment_name": "Checkout A/B", "variant": "B"}
        return None


def test_ingest_service_saves_events_in_batch(session_factory) -> None:
    event_repo = SqliteEventRepository(session_factory)
    feature_repo = SqliteFeatureRepository(session_factory)
    feature_service = FeatureService(feature_repo)
    event_service = EventService(event_repo)
    ingest_service = IngestService(event_service, experiment_service=_ExperimentService())

    feature_service.create_feature(
        name="New Checkout",
        key="new_checkout",
        description="test",
        enabled=True,
        rollout_percentage=10,
        ml_enabled=True,
        ml_threshold_mode="fixed",
        ml_threshold_value=0.1,
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
                "event_type": "checkout_upsell_shown",
                "timestamp": datetime(2026, 4, 22, 10, 1, tzinfo=timezone.utc),
                "properties": {"device": "desktop"},
            },
        ],
    )

    assert result["saved_events"] == 2
    assert result["rejected"] == 0
    saved = event_service.list_events(feature_key="new_checkout")
    assert len(saved) == 2
    assert all(event.source == "web_app" for event in saved)
    assert all(event.properties.get("ab_variant") == "B" for event in saved)


def test_ingest_service_rejects_future_events(session_factory) -> None:
    event_repo = SqliteEventRepository(session_factory)
    feature_repo = SqliteFeatureRepository(session_factory)
    feature_service = FeatureService(feature_repo)
    event_service = EventService(event_repo)
    ingest_service = IngestService(event_service, experiment_service=_ExperimentService())

    feature_service.create_feature(
        name="New Checkout",
        key="new_checkout",
        description="test",
        enabled=True,
        rollout_percentage=10,
        ml_enabled=True,
        ml_threshold_mode="fixed",
        ml_threshold_value=0.1,
    )

    result = ingest_service.ingest_events(
        source="web_app",
        events=[
            {
                "user_id": "u123",
                "feature_key": "new_checkout",
                "event_type": "clicked",
                "timestamp": datetime(2099, 1, 1, tzinfo=timezone.utc),
                "properties": {"device": "mobile"},
            }
        ],
    )

    assert result["saved_events"] == 0
    assert result["rejected"] == 1


def test_ingest_service_rejects_invalid_latency_metric(session_factory) -> None:
    event_repo = SqliteEventRepository(session_factory)
    event_service = EventService(event_repo)
    ingest_service = IngestService(event_service, experiment_service=_ExperimentService())

    result = ingest_service.ingest_events(
        source="web_app",
        events=[
            {
                "user_id": "u123",
                "feature_key": "new_checkout",
                "event_type": "clicked",
                "timestamp": datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc),
                "properties": {"latency_ms": 130000},
            }
        ],
    )
    assert result["saved_events"] == 0
    assert result["rejected"] == 1


def test_ingest_service_rejects_batches_above_limit(session_factory) -> None:
    event_repo = SqliteEventRepository(session_factory)
    event_service = EventService(event_repo)
    ingest_service = IngestService(event_service)

    payload = [
        {
            "user_id": f"u{i}",
            "feature_key": "new_checkout",
            "event_type": "clicked",
            "timestamp": datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc),
            "properties": {"device": "mobile"},
        }
        for i in range(1001)
    ]

    with pytest.raises(ValidationError, match="must not exceed 1000 items"):
        ingest_service.ingest_events(source="web_app", events=payload)


def test_ingest_service_rate_limits_repeated_small_requests(session_factory) -> None:
    event_repo = SqliteEventRepository(session_factory)
    event_service = EventService(event_repo)
    ingest_service = IngestService(
        event_service,
        rate_limit_max_events=2,
        rate_limit_window_seconds=60,
    )
    event = {
        "user_id": "u1",
        "feature_key": "new_checkout",
        "event_type": "clicked",
        "timestamp": datetime(2026, 4, 22, 10, 0, tzinfo=timezone.utc),
        "properties": {"device": "mobile"},
    }

    first = ingest_service.ingest_events(source="web_app", events=[event], client_id="1.2.3.4")
    second = ingest_service.ingest_events(source="web_app", events=[event], client_id="1.2.3.4")
    third = ingest_service.ingest_events(source="web_app", events=[event], client_id="1.2.3.4")

    assert first["saved_events"] == 1
    assert second["saved_events"] == 1
    assert third["saved_events"] == 0
    assert third["rejected"] == 1
