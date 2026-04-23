from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.core.event_types import (
    INTERMEDIATE_POSITIVE_EVENT_TYPES,
    POSITIVE_EVENT_TYPES,
    TERMINAL_POSITIVE_EVENT_TYPES,
    VIEW_EVENT_TYPES,
)


@dataclass(slots=True)
class FeatureBuilderConfig:
    positive_event_types: set[str]
    view_event_types: set[str]

    @classmethod
    def default(cls) -> "FeatureBuilderConfig":
        return cls(
            positive_event_types=POSITIVE_EVENT_TYPES,
            view_event_types=VIEW_EVENT_TYPES,
        )


class FeatureBuilder:
    """
    Builds ML-ready user-level features from raw event rows.

    Expected input columns:
    - user_id
    - event_type
    - timestamp
    - feature_key (optional but recommended)

    Optional:
    - properties
    """

    def __init__(self, config: FeatureBuilderConfig | None = None) -> None:
        self.config = config or FeatureBuilderConfig.default()

    def build_from_dataframe(
        self,
        df: pd.DataFrame,
        *,
        reference_timestamp: Any | None = None,
    ) -> pd.DataFrame:
        self._validate_columns(df)

        work_df = df.copy()
        work_df["timestamp"] = pd.to_datetime(work_df["timestamp"], errors="coerce", utc=True)
        work_df = work_df.dropna(subset=["user_id", "event_type", "timestamp"])

        work_df["event_type"] = work_df["event_type"].astype(str)
        work_df["user_id"] = work_df["user_id"].astype(str)

        if "feature_key" not in work_df.columns:
            work_df["feature_key"] = "unknown"

        work_df["is_positive"] = work_df["event_type"].isin(self.config.positive_event_types).astype(int)
        work_df["is_view"] = work_df["event_type"].isin(self.config.view_event_types).astype(int)
        work_df["is_terminal_positive"] = work_df["event_type"].isin(TERMINAL_POSITIVE_EVENT_TYPES).astype(int)
        work_df["is_intermediate_positive"] = work_df["event_type"].isin(INTERMEDIATE_POSITIVE_EVENT_TYPES).astype(int)

        work_df["event_date"] = work_df["timestamp"].dt.date
        work_df["hour"] = work_df["timestamp"].dt.hour
        work_df["day_of_week"] = work_df["timestamp"].dt.dayofweek

        max_timestamp = self._resolve_reference_timestamp(
            reference_timestamp=reference_timestamp,
            fallback_timestamp=work_df["timestamp"].max(),
        )

        agg = (
            work_df.groupby("user_id")
            .agg(
                total_events=("event_type", "count"),
                positive_events=("is_positive", "sum"),
                view_events=("is_view", "sum"),
                cart_events=("is_intermediate_positive", "sum"),
                purchase_events=("is_terminal_positive", "sum"),
                unique_features=("feature_key", "nunique"),
                active_days=("event_date", "nunique"),
                avg_hour=("hour", "mean"),
                avg_day_of_week=("day_of_week", "mean"),
                last_seen=("timestamp", "max"),
            )
            .reset_index()
        )

        agg["hours_since_last_event"] = (
            (max_timestamp - agg["last_seen"]).dt.total_seconds() / 3600.0
        ).clip(lower=0)
        agg["events_per_day"] = agg["total_events"] / agg["active_days"].clip(lower=1)
        agg["positive_rate"] = agg["positive_events"] / agg["total_events"].clip(lower=1)

        # Binary target for MVP:
        # 1 if the user had at least one positive event, else 0
        agg["target"] = (agg["positive_events"] > 0).astype(int)

        agg = agg.drop(columns=["last_seen"])
        agg = agg.fillna(0)

        return agg

    def build_prediction_frame(
        self,
        *,
        total_events: int,
        view_events: int,
        cart_events: int,
        purchase_events: int,
        positive_events: int,
        unique_features: int,
        active_days: int,
        avg_hour: float,
        avg_day_of_week: float,
        hours_since_last_event: float,
    ) -> pd.DataFrame:
        events_per_day = total_events / max(active_days, 1)
        positive_rate = positive_events / max(total_events, 1)

        return pd.DataFrame(
            [
                {
                    "total_events": total_events,
                    "positive_events": positive_events,
                    "view_events": view_events,
                    "cart_events": cart_events,
                    "purchase_events": purchase_events,
                    "unique_features": unique_features,
                    "active_days": active_days,
                    "avg_hour": avg_hour,
                    "avg_day_of_week": avg_day_of_week,
                    "hours_since_last_event": hours_since_last_event,
                    "events_per_day": events_per_day,
                    "positive_rate": positive_rate,
                }
            ]
        )

    @staticmethod
    def model_feature_columns() -> list[str]:
        return [
            "total_events",
            "positive_events",
            "view_events",
            "cart_events",
            "purchase_events",
            "unique_features",
            "active_days",
            "avg_hour",
            "avg_day_of_week",
            "hours_since_last_event",
            "events_per_day",
            "positive_rate",
        ]

    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> None:
        required_columns = {"user_id", "event_type", "timestamp"}
        missing = required_columns.difference(df.columns)
        if missing:
            raise ValueError(
                f"Missing required columns for feature building: {sorted(missing)}"
            )

    @staticmethod
    def _resolve_reference_timestamp(
        *,
        reference_timestamp: Any | None,
        fallback_timestamp: pd.Timestamp,
    ) -> pd.Timestamp:
        if reference_timestamp is None:
            return fallback_timestamp

        parsed_reference = pd.to_datetime(reference_timestamp, errors="coerce", utc=True)
        if pd.isna(parsed_reference):
            return fallback_timestamp

        return max(parsed_reference, fallback_timestamp)