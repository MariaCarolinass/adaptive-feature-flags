from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.core.exceptions import NotFoundError
from app.domain.services.event_service import EventService
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository


def test_create_and_list_events_with_filters(session_factory) -> None:
    repo = SqliteEventRepository(session_factory)
    service = EventService(repo)
    now = datetime.now(timezone.utc)

    service.create_event(
        user_id="u1",
        feature_key="f1",
        event_type="view",
        timestamp=now,
        properties={"a": 1},
    )
    service.create_event(
        user_id="u2",
        feature_key="f1",
        event_type="click",
        timestamp=now,
        properties={"b": 2},
    )

    events_u2 = service.list_events(user_id="u2")
    events_f1 = service.list_events(feature_key="f1")

    assert len(events_u2) == 1
    assert len(events_f1) == 2


def test_update_and_delete_event(session_factory) -> None:
    repo = SqliteEventRepository(session_factory)
    service = EventService(repo)
    created = service.create_event(
        user_id="u1",
        feature_key="f1",
        event_type="view",
        timestamp=datetime.now(timezone.utc),
        properties={"step": 1},
    )

    updated = service.update_event(
        event_id=created.id,
        user_id="u1",
        feature_key="f2",
        event_type="click",
        timestamp=datetime.now(timezone.utc),
        properties={"step": 2},
    )
    assert updated.feature_key == "f2"
    assert updated.event_type == "click"

    service.delete_event(created.id)
    assert service.get_event_by_id(created.id) is None


def test_update_event_requires_existing_id(session_factory) -> None:
    repo = SqliteEventRepository(session_factory)
    service = EventService(repo)

    with pytest.raises(NotFoundError, match="Event not found"):
        service.update_event(
            event_id=999999,
            user_id="u1",
            feature_key="f1",
            event_type="view",
            timestamp=datetime.now(timezone.utc),
            properties={},
        )

