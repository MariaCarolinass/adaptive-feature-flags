from __future__ import annotations

import argparse
from pathlib import Path
import sys
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.infrastructure.db.models import Base, EventModel

settings = Settings()
REQUIRED_COLUMNS = {"timestamp", "visitorid", "event", "itemid"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Retailrocket events.csv into the SmartFeatureFlagsAPI events table."
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to Retailrocket events.csv file.",
    )
    parser.add_argument(
        "--database-url",
        default=settings.database_url,
        help="SQLAlchemy database URL. Default: " + settings.database_url,
    )
    parser.add_argument(
        "--feature-key-mode",
        choices=["single", "item"],
        default="item",
        help=(
            "How to map feature_key. "
            "'item' -> feature_key becomes item_<itemid>. "
            "'single' -> feature_key becomes 'retailrocket_import'."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional row limit for quick local tests.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=200000,
        help="Number of CSV rows processed per chunk.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10000,
        help="Number of ORM rows inserted per transaction batch.",
    )
    parser.add_argument(
        "--sync-features",
        action="store_true",
        help="When enabled, auto-create missing rows in features table from imported feature_key values.",
    )
    parser.add_argument(
        "--feature-rollout-percentage",
        type=int,
        default=10,
        help="Default rollout percentage for auto-created features (0-100).",
    )
    parser.add_argument(
        "--feature-ml-enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether auto-created features should have ml_enabled=true.",
    )
    return parser.parse_args()


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
    work_df = df.copy()

    work_df["timestamp"] = pd.to_datetime(work_df["timestamp"], unit="ms", utc=True, errors="coerce")
    work_df = work_df.dropna(subset=["timestamp", "visitorid", "event", "itemid"])

    work_df["user_id"] = work_df["visitorid"].astype(str)
    work_df["event_type"] = work_df["event"].astype(str)

    if feature_key_mode == "item":
        work_df["feature_key"] = work_df["itemid"].apply(lambda value: f"item_{value}")
    else:
        work_df["feature_key"] = "retailrocket_import"

    work_df["properties"] = work_df.apply(
        lambda row: {
            "source": "retailrocket",
            "raw_itemid": str(row["itemid"]),
            "raw_event": str(row["event"]),
            "transactionid": (
                None
                if "transactionid" not in row or pd.isna(row.get("transactionid"))
                else str(int(row["transactionid"]))
            ),
        },
        axis=1,
    )

    return work_df[["user_id", "feature_key", "event_type", "timestamp", "properties"]].copy()


def ensure_events_table(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)


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


def insert_events(engine: Engine, df: pd.DataFrame, batch_size: int = 10000) -> int:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    inserted = 0
    with SessionLocal() as session:
        for offset in range(0, len(df), batch_size):
            frame = df.iloc[offset : offset + batch_size]
            batch = [
                EventModel(
                    user_id=row["user_id"],
                    feature_key=row["feature_key"],
                    event_type=row["event_type"],
                    timestamp=row["timestamp"],
                    properties=row["properties"],
                )
                for _, row in frame.iterrows()
            ]
            session.add_all(batch)
            session.commit()
            inserted += len(batch)
    return inserted


def main() -> None:
    args = parse_args()
    if not (0 <= args.feature_rollout_percentage <= 100):
        raise ValueError("--feature-rollout-percentage must be between 0 and 100.")

    print("Connecting to database...")
    engine = create_engine(args.database_url)

    print("Ensuring events table exists...")
    ensure_events_table(engine)

    total_raw_rows = 0
    total_normalized_rows = 0
    total_inserted_rows = 0
    imported_feature_keys: set[str] = set()

    print("Loading, normalizing and inserting in chunks...")
    for index, raw_chunk in enumerate(
        load_csv_chunks(args.csv, chunk_size=args.chunk_size, limit=args.limit),
        start=1,
    ):
        total_raw_rows += len(raw_chunk)
        normalized_chunk = normalize_events(raw_chunk, feature_key_mode=args.feature_key_mode)
        total_normalized_rows += len(normalized_chunk)
        imported_feature_keys.update(normalized_chunk["feature_key"].astype(str).unique().tolist())
        inserted = insert_events(engine, normalized_chunk, batch_size=args.batch_size)
        total_inserted_rows += inserted
        print(
            f"Chunk {index}: raw={len(raw_chunk)} normalized={len(normalized_chunk)} inserted={inserted}"
        )

    synced_features = 0
    if args.sync_features:
        print("Syncing feature registry from imported feature keys...")
        synced_features = sync_features(
            engine,
            imported_feature_keys,
            rollout_percentage=args.feature_rollout_percentage,
            ml_enabled=args.feature_ml_enabled,
        )

    print("Done.")
    print(f"Raw rows processed: {total_raw_rows}")
    print(f"Normalized rows: {total_normalized_rows}")
    print(f"Inserted rows: {total_inserted_rows}")
    if args.sync_features:
        print(f"Features auto-created: {synced_features}")
    print(f"Database URL: {args.database_url}")


if __name__ == "__main__":
    main()