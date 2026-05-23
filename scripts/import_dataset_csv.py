from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.infrastructure.db.db import SessionLocal, init_db
from app.infrastructure.db.models import Base, EventModel
from app.infrastructure.integrations.ecommerce_adapter import EcommerceCSVAdapter

REQUIRED_COLUMNS = {"timestamp", "visitorid", "event", "itemid"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import e-commerce dataset events.csv into canonical events schema."
    )
    parser.add_argument("--csv", required=True, help="Path to e-commerce dataset events.csv file.")
    parser.add_argument(
        "--feature-key-mode",
        choices=["single", "item"],
        default="item",
        help="'item' -> feature_key=item_<itemid>, 'single' -> feature_key=dataset_import.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of events to import.")
    parser.add_argument("--chunk-size", type=int, default=200000, help="CSV rows processed per chunk.")
    parser.add_argument("--batch-size", type=int, default=10000, help="DB rows inserted per transaction.")
    return parser.parse_args()


def _insert_batch(session_factory: sessionmaker, batch: list[dict]) -> int:
    if not batch:
        return 0
    with session_factory() as session:
        rows = [
            EventModel(
                user_id=str(event["user_id"]),
                feature_key=str(event["feature_key"]),
                event_type=str(event["event_type"]),
                timestamp=event["timestamp"],
                properties=event["properties"],
            )
            for event in batch
        ]
        session.add_all(rows)
        session.commit()
    return len(batch)


def _validate_columns(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")


def load_csv_chunks(csv_path: str, chunk_size: int, limit: int | None = None):
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    processed_rows = 0
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        _validate_columns(chunk)
        if limit is not None:
            remaining = limit - processed_rows
            if remaining <= 0:
                break
            if len(chunk) > remaining:
                chunk = chunk.head(remaining)
        processed_rows += len(chunk)
        yield chunk


def normalize_events(df: pd.DataFrame, feature_key_mode: str) -> pd.DataFrame:
    adapter = EcommerceCSVAdapter(feature_key_mode=feature_key_mode)
    events = []
    for _, row in df.iterrows():
        mapped = adapter._map_row(row)  # reuse adapter mapping to canonical schema
        if mapped is None:
            continue
        events.append(
            {
                "user_id": str(mapped["user_id"]),
                "feature_key": str(mapped["feature_key"]),
                "event_type": str(mapped["event_type"]),
                "timestamp": mapped["timestamp"],
                "properties": mapped["properties"],
            }
        )
    return pd.DataFrame(events, columns=["user_id", "feature_key", "event_type", "timestamp", "properties"])


def ensure_events_table(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)


def insert_events(engine: Engine, df: pd.DataFrame, batch_size: int = 10000) -> int:
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    inserted = 0
    batch: list[dict] = []
    for _, row in df.iterrows():
        batch.append(
            {
                "user_id": row["user_id"],
                "feature_key": row["feature_key"],
                "event_type": row["event_type"],
                "timestamp": row["timestamp"],
                "properties": row["properties"],
            }
        )
        if len(batch) >= batch_size:
            inserted += _insert_batch(local_session, batch)
            batch = []
    inserted += _insert_batch(local_session, batch)
    return inserted


def sync_features(
    engine: Engine,
    feature_keys: set[str],
    *,
    rollout_percentage: int,
    ml_enabled: bool,
) -> int:
    if not feature_keys:
        return 0

    now_iso = datetime.now(timezone.utc).isoformat()
    insert_sql = text(
        """
        INSERT OR IGNORE INTO features
        (name, key, description, enabled, rollout_percentage, ml_enabled, created_at, updated_at)
        VALUES
        (:name, :key, :description, :enabled, :rollout_percentage, :ml_enabled, :created_at, :updated_at)
        """
    )
    count_sql = text("SELECT COUNT(*) FROM features")
    rows = [
        {
            "name": f"Imported {feature_key}",
            "key": feature_key,
            "description": "Auto-created from imported events.",
            "enabled": True,
            "rollout_percentage": rollout_percentage,
            "ml_enabled": ml_enabled,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        for feature_key in sorted(feature_keys)
    ]

    with engine.begin() as conn:
        before = conn.execute(count_sql).scalar_one()
        conn.execute(insert_sql, rows)
        after = conn.execute(count_sql).scalar_one()
    return int(after - before)


def main() -> None:
    args = parse_args()
    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit must be greater than zero.")
    if args.chunk_size <= 0:
        raise ValueError("--chunk-size must be greater than zero.")
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be greater than zero.")

    init_db()
    adapter = EcommerceCSVAdapter(feature_key_mode=args.feature_key_mode)

    saved = 0
    processed = 0
    batch: list[dict] = []

    for event in adapter.iter_events(
        args.csv,
        chunk_size=args.chunk_size,
        limit=args.limit,
    ):
        processed += 1
        raw_item = event["properties"].get("raw_itemid")
        if raw_item is not None:
            event["properties"]["context_itemid"] = raw_item

        batch.append(event)
        if len(batch) >= args.batch_size:
            saved += _insert_batch(SessionLocal, batch)
            batch = []

    saved += _insert_batch(SessionLocal, batch)

    print("e-commerce dataset import completed.")
    print("Source: ecommerce_dataset")
    print(f"CSV file: {args.csv}")
    print(f"Feature key mode: {args.feature_key_mode}")
    print(f"Events processed: {processed}")
    print(f"Events saved: {saved}")
    print(f"Limit: {args.limit if args.limit is not None else 'none'}")
    print(f"Batch size: {args.batch_size}")


if __name__ == "__main__":
    main()
