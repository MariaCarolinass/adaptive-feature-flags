from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.models import Base
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository
from scripts import seed_demo


def test_seed_demo_creates_sufficient_data_and_is_idempotent(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    monkeypatch.setattr(seed_demo, "SessionLocal", test_session_factory)
    monkeypatch.setattr(seed_demo, "init_db", lambda: Base.metadata.create_all(bind=engine))

    seed_demo.main()
    seed_demo.main()

    feature_repo = SqliteFeatureRepository(test_session_factory)
    event_repo = SqliteEventRepository(test_session_factory)

    features = feature_repo.list()
    events = event_repo.list()
    users = {event.user_id for event in events}
    positive_events = [event for event in events if event.event_type in {"addtocart", "transaction"}]

    assert len(features) >= 3
    assert len(users) >= 10
    assert len(events) >= 30
    assert len(positive_events) >= 6
