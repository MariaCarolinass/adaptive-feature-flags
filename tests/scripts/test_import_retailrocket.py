from __future__ import annotations

from datetime import datetime, timezone
import csv

import pandas as pd
from sqlalchemy import create_engine, text

from scripts.import_retailrocket import ensure_events_table, insert_events, load_csv_chunks, sync_features


def test_insert_events_persists_rows_with_json_properties() -> None:
    engine = create_engine("sqlite:///:memory:")
    ensure_events_table(engine)

    df = pd.DataFrame(
        [
            {
                "user_id": "u1",
                "feature_key": "item_1",
                "event_type": "view",
                "timestamp": datetime.now(timezone.utc),
                "properties": {"source": "retailrocket"},
            }
        ]
    )

    inserted = insert_events(engine, df)
    assert inserted == 1

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM events")).scalar_one()
        assert count == 1


def test_sync_features_creates_missing_feature_rows() -> None:
    engine = create_engine("sqlite:///:memory:")
    ensure_events_table(engine)

    created = sync_features(
        engine,
        {"item_1", "item_2"},
        rollout_percentage=15,
        ml_enabled=True,
    )
    assert created == 2

    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT key, rollout_percentage, ml_enabled, enabled FROM features ORDER BY key ASC")
        ).fetchall()

    assert len(rows) == 2
    assert rows[0][0] == "item_1"
    assert rows[0][1] == 15
    assert rows[0][2] == 1
    assert rows[0][3] == 1


def test_sync_features_is_idempotent() -> None:
    engine = create_engine("sqlite:///:memory:")
    ensure_events_table(engine)

    first = sync_features(engine, {"item_1"}, rollout_percentage=10, ml_enabled=True)
    second = sync_features(engine, {"item_1"}, rollout_percentage=10, ml_enabled=True)

    assert first == 1
    assert second == 0


def test_load_csv_chunks_respects_limit(tmp_path) -> None:
    csv_path = tmp_path / "events.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "visitorid", "event", "itemid"])
        writer.writeheader()
        writer.writerow({"timestamp": 1, "visitorid": "u1", "event": "view", "itemid": 1})
        writer.writerow({"timestamp": 2, "visitorid": "u2", "event": "view", "itemid": 2})
        writer.writerow({"timestamp": 3, "visitorid": "u3", "event": "view", "itemid": 3})

    chunks = list(load_csv_chunks(str(csv_path), chunk_size=2, limit=2))
    assert len(chunks) == 1
    assert len(chunks[0]) == 2
