from __future__ import annotations

import csv
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.models import Base
from app.infrastructure.integrations.retailrocket_adapter import RetailrocketCSVAdapter
from scripts.import_retailrocket import _insert_batch


def _write_retailrocket_csv(csv_path, rows: list[dict]) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "visitorid", "event", "itemid", "transactionid"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_retailrocket_adapter_maps_to_canonical_schema(tmp_path) -> None:
    csv_path = tmp_path / "events.csv"
    _write_retailrocket_csv(
        csv_path,
        [
            {"timestamp": 1713780000000, "visitorid": "u1", "event": "view", "itemid": 10, "transactionid": ""},
        ],
    )

    adapter = RetailrocketCSVAdapter(feature_key_mode="item")
    events = list(adapter.iter_events(str(csv_path)))

    assert len(events) == 1
    event = events[0]
    assert event["source"] == "retailrocket"
    assert event["user_id"] == "u1"
    assert event["event_type"] == "view"
    assert event["feature_key"] == "item_10"
    assert isinstance(event["timestamp"], datetime)
    assert event["timestamp"].tzinfo == timezone.utc
    assert event["properties"]["raw_itemid"] == "10"


def test_retailrocket_adapter_respects_limit(tmp_path) -> None:
    csv_path = tmp_path / "events.csv"
    _write_retailrocket_csv(
        csv_path,
        [
            {"timestamp": 1, "visitorid": "u1", "event": "view", "itemid": 1, "transactionid": ""},
            {"timestamp": 2, "visitorid": "u2", "event": "view", "itemid": 2, "transactionid": ""},
            {"timestamp": 3, "visitorid": "u3", "event": "view", "itemid": 3, "transactionid": ""},
        ],
    )

    adapter = RetailrocketCSVAdapter(feature_key_mode="item")
    events = list(adapter.iter_events(str(csv_path), chunk_size=2, limit=2))
    assert len(events) == 2


def test_insert_batch_persists_rows_with_properties() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    inserted = _insert_batch(
        test_session_factory,
        [
            {
                "source": "retailrocket",
                "user_id": "u1",
                "feature_key": "item_10",
                "event_type": "view",
                "timestamp": datetime.now(timezone.utc),
                "properties": {"source": "retailrocket", "raw_itemid": "10"},
            }
        ],
    )

    assert inserted == 1
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM events")).scalar_one()
        assert count == 1
