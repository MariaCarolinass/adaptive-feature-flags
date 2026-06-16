from __future__ import annotations

import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.event_types import POSITIVE_EVENT_TYPES
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

    seed_demo.main([])

    feature_repo = SqliteFeatureRepository(test_session_factory)
    event_repo = SqliteEventRepository(test_session_factory)

    first_features = feature_repo.list()
    first_events = event_repo.list()

    seed_demo.main([])

    second_features = feature_repo.list()
    second_events = event_repo.list()
    default_catalogs = [
        seed_demo._load_seed_catalog(path)
        for path in seed_demo._resolve_catalog_paths(None, False)
    ]
    expected_exposure_events = {
        journey["exposure_event"]
        for catalog in default_catalogs
        for journey in catalog.journeys.values()
    }
    expected_feature_count = len({spec.key for catalog in default_catalogs for spec in catalog.features})
    expected_user_count = len(default_catalogs) * seed_demo.USERS_PER_CATALOG

    users = {event.user_id for event in second_events}
    feature_keys = {event.feature_key for event in second_events}
    event_types = {event.event_type for event in second_events}
    positive_events = [event for event in second_events if event.event_type in POSITIVE_EVENT_TYPES]
    seeded_events = [event for event in second_events if event.properties.get("seed_source") == "seed_demo"]
    timestamps = sorted(event.timestamp for event in second_events)

    assert len(first_features) == len(second_features)
    assert len(first_events) == len(second_events)
    assert len(second_features) == expected_feature_count
    assert len(users) == expected_user_count
    assert len(second_events) >= len(default_catalogs) * 120
    assert len(feature_keys) >= expected_feature_count
    assert "view" in event_types
    assert any(event_type in event_types for event_type in expected_exposure_events)
    assert any(event_type in event_types for event_type in POSITIVE_EVENT_TYPES)
    assert len(positive_events) >= 20
    assert len(seeded_events) == len(second_events)
    assert (timestamps[-1] - timestamps[0]).days >= 10


def test_seed_demo_can_import_a_single_json_catalog(monkeypatch, tmp_path: Path) -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    monkeypatch.setattr(seed_demo, "SessionLocal", test_session_factory)
    monkeypatch.setattr(seed_demo, "init_db", lambda: Base.metadata.create_all(bind=engine))

    default_catalog_path = Path(seed_demo.DEFAULT_SEED_DATA_PATH)
    catalog_a = tmp_path / "seed_demo_a.json"
    catalog_b = tmp_path / "seed_demo_b.json"

    base_catalog = json.loads(default_catalog_path.read_text(encoding="utf-8"))
    first_catalog = dict(base_catalog)
    second_catalog = dict(base_catalog)
    first_catalog["user_prefix"] = "demo_a_user"
    second_catalog["user_prefix"] = "demo_b_user"
    second_catalog["seed_version"] = "v3"

    catalog_a.write_text(json.dumps(first_catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    catalog_b.write_text(json.dumps(second_catalog, ensure_ascii=False, indent=2), encoding="utf-8")

    seed_demo.main(["--catalog", str(catalog_a)])

    event_repo = SqliteEventRepository(test_session_factory)
    events = event_repo.list()
    users = {event.user_id for event in events}

    assert len(users) == 50
    assert any(user.startswith("demo_a_user_") for user in users)
    assert not any(user.startswith("demo_b_user_") for user in users)
    assert len(events) >= 120


def test_seed_demo_can_import_all_json_catalogs_from_custom_directory(monkeypatch, tmp_path: Path) -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    monkeypatch.setattr(seed_demo, "SessionLocal", test_session_factory)
    monkeypatch.setattr(seed_demo, "init_db", lambda: Base.metadata.create_all(bind=engine))

    default_catalog_path = Path(seed_demo.DEFAULT_SEED_DATA_PATH)
    catalog_a = tmp_path / "seed_demo_a.json"
    catalog_b = tmp_path / "seed_demo_b.json"

    base_catalog = json.loads(default_catalog_path.read_text(encoding="utf-8"))
    first_catalog = dict(base_catalog)
    second_catalog = dict(base_catalog)
    first_catalog["user_prefix"] = "demo_a_user"
    second_catalog["user_prefix"] = "demo_b_user"
    second_catalog["seed_version"] = "v3"

    catalog_a.write_text(json.dumps(first_catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    catalog_b.write_text(json.dumps(second_catalog, ensure_ascii=False, indent=2), encoding="utf-8")

    seed_demo.main(["--catalog", str(catalog_a), "--all-json"])

    event_repo = SqliteEventRepository(test_session_factory)
    events = event_repo.list()
    users = {event.user_id for event in events}

    assert len(users) == 100
    assert any(user.startswith("demo_a_user_") for user in users)
    assert any(user.startswith("demo_b_user_") for user in users)
    assert len(events) >= 2 * 120
