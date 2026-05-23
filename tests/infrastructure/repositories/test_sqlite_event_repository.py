from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from app.core.exceptions import NotFoundError
from app.domain.entities.event import Event
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository


def _event(
    *,
    user_id: str = "u1",
    feature_key: str = "feature_a",
    event_type: str = "click",
    timestamp: datetime | None = None,
) -> Event:
    ts = timestamp or datetime.now(timezone.utc)
    return Event(
        id=None,
        source="test",
        user_id=user_id,
        feature_key=feature_key,
        event_type=event_type,
        timestamp=ts,
        properties={"source": "test"},
    )


def test_create_and_get_event(session_factory) -> None:
    repo = SqliteEventRepository(session_factory)
    event = _event()
    repo.create(event)

    assert isinstance(event.id, int)
    loaded = repo.get_by_id(event.id)

    assert loaded is not None
    assert loaded.id == event.id
    assert loaded.properties["source"] == "test"


def test_list_event_applies_filters(session_factory) -> None:
    repo = SqliteEventRepository(session_factory)
    repo.create(_event(user_id="u1", feature_key="f1", event_type="view"))
    repo.create(_event(user_id="u2", feature_key="f1", event_type="click"))
    repo.create(_event(user_id="u2", feature_key="f2", event_type="view"))

    only_u2 = repo.list(user_id="u2")
    only_f1 = repo.list(feature_key="f1")
    only_view = repo.list(event_type="view")

    assert len(only_u2) == 2
    assert len(only_f1) == 2
    assert len(only_view) == 2


def test_update_event_persists_changes(session_factory) -> None:
    repo = SqliteEventRepository(session_factory)
    event = _event()
    repo.create(event)

    event.event_type = "purchase"
    event.properties = {"amount": 99.9}
    event.timestamp = datetime.now(timezone.utc) + timedelta(minutes=1)
    repo.update(event)

    loaded = repo.get_by_id(event.id)

    assert loaded is not None
    assert loaded.event_type == "purchase"
    assert loaded.properties["amount"] == 99.9


def test_delete_event_removes_record(session_factory) -> None:
    repo = SqliteEventRepository(session_factory)
    event = _event()
    repo.create(event)

    deleted = repo.delete(event.id)
    loaded = repo.get_by_id(event.id)

    assert deleted is True
    assert loaded is None
    assert repo.delete(event.id) is False


def test_update_event_requires_existing_id(session_factory) -> None:
    repo = SqliteEventRepository(session_factory)
    event = _event()

    with pytest.raises(NotFoundError, match="Event not found"):
        repo.update(event)
