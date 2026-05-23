from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, select

from app.infrastructure.db.models import EventModel
from app.infrastructure.ml.feature_builder import FeatureBuilder


def load_event_chunks(database_url: str, chunk_size: int):
    engine = create_engine(database_url)
    stmt = select(
        EventModel.user_id,
        EventModel.event_type,
        EventModel.timestamp,
        EventModel.feature_key,
    )
    with engine.connect() as conn:
        yield from pd.read_sql(stmt, conn, chunksize=chunk_size)


def build_features_from_chunks(chunks) -> pd.DataFrame:
    builder = FeatureBuilder()
    stats_by_user: dict[str, dict] = {}
    global_max_timestamp = None
    total_rows = 0

    for chunk_idx, chunk in enumerate(chunks, start=1):
        if chunk.empty:
            continue

        total_rows += len(chunk)
        chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], errors="coerce", utc=True)
        chunk = chunk.dropna(subset=["user_id", "event_type", "timestamp"])
        if chunk.empty:
            continue

        chunk["user_id"] = chunk["user_id"].astype(str)
        chunk["event_type"] = chunk["event_type"].astype(str)
        chunk["feature_key"] = chunk["feature_key"].fillna("unknown").astype(str)
        chunk["event_date"] = chunk["timestamp"].dt.date
        chunk_features = builder.build_from_dataframe(
            chunk[["user_id", "event_type", "timestamp", "feature_key"]]
        )

        chunk_max = chunk["timestamp"].max()
        if global_max_timestamp is None or chunk_max > global_max_timestamp:
            global_max_timestamp = chunk_max

        raw_by_user = chunk.groupby("user_id")
        feature_by_user = chunk_features.set_index("user_id")

        for user_id, user_chunk in raw_by_user:
            feature_row = feature_by_user.loc[user_id]
            stats = stats_by_user.setdefault(
                user_id,
                {
                    "total_events": 0,
                    "positive_events": 0,
                    "view_events": 0,
                    "cart_events": 0,
                    "purchase_events": 0,
                    "feature_keys": set(),
                    "active_days": set(),
                    "hour_sum": 0.0,
                    "day_of_week_sum": 0.0,
                    "last_seen": None,
                },
            )

            row_total_events = int(feature_row["total_events"])
            stats["total_events"] += row_total_events
            stats["positive_events"] += int(feature_row["positive_events"])
            stats["view_events"] += int(feature_row["view_events"])
            stats["cart_events"] += int(feature_row["cart_events"])
            stats["purchase_events"] += int(feature_row["purchase_events"])
            stats["feature_keys"].update(user_chunk["feature_key"].unique().tolist())
            stats["active_days"].update(user_chunk["event_date"].unique().tolist())
            stats["hour_sum"] += float(feature_row["avg_hour"]) * row_total_events
            stats["day_of_week_sum"] += float(feature_row["avg_day_of_week"]) * row_total_events

            user_last_seen = user_chunk["timestamp"].max()
            if stats["last_seen"] is None or user_last_seen > stats["last_seen"]:
                stats["last_seen"] = user_last_seen

        print(f"Processed chunk {chunk_idx}: rows={len(chunk)} users_so_far={len(stats_by_user)}")

    if total_rows == 0 or not stats_by_user:
        raise ValueError("No events found. Import events before building features.")

    rows = []
    for user_id, stats in stats_by_user.items():
        total_events = stats["total_events"]
        active_days_count = max(len(stats["active_days"]), 1)
        last_seen = stats["last_seen"]

        if global_max_timestamp is not None and last_seen is not None:
            hours_since_last_event = (global_max_timestamp - last_seen).total_seconds() / 3600.0
        else:
            hours_since_last_event = 0.0

        rows.append(
            {
                "user_id": user_id,
                "total_events": total_events,
                "positive_events": stats["positive_events"],
                "view_events": stats["view_events"],
                "cart_events": stats["cart_events"],
                "purchase_events": stats["purchase_events"],
                "unique_features": len(stats["feature_keys"]),
                "active_days": len(stats["active_days"]),
                "avg_hour": stats["hour_sum"] / max(total_events, 1),
                "avg_day_of_week": stats["day_of_week_sum"] / max(total_events, 1),
                "hours_since_last_event": hours_since_last_event,
                "events_per_day": total_events / active_days_count,
                "positive_rate": stats["positive_events"] / max(total_events, 1),
                "target": int(stats["positive_events"] > 0),
            }
        )

    return pd.DataFrame(rows)


def save_features(df: pd.DataFrame, database_url: str, output_table: str, if_exists: str) -> None:
    engine = create_engine(database_url)

    df.to_sql(
        output_table,
        engine,
        if_exists=if_exists,
        index=False,
    )
