from __future__ import annotations

from typing import Any

import pandas as pd

from app.infrastructure.integrations.base import CSVAdapterConfig
from app.infrastructure.integrations.csv_adapter import GenericCSVAdapter


class EcommerceCSVAdapter(GenericCSVAdapter):
    def __init__(self, *, feature_key_mode: str = "item") -> None:
        if feature_key_mode not in {"item", "single"}:
            raise ValueError("feature_key_mode must be either 'item' or 'single'.")

        def map_feature_key(row: pd.Series) -> str:
            if feature_key_mode == "single":
                return "dataset_import"
            return f"item_{int(row['itemid'])}"

        def build_properties(row: pd.Series) -> dict[str, str | int | float | bool | None]:
            transaction_id: Any = row.get("transactionid")
            return {
                "raw_itemid": str(row["itemid"]),
                "raw_event": str(row["event"]),
                "transactionid": None if pd.isna(transaction_id) else str(int(transaction_id)),
            }

        config = CSVAdapterConfig(
            source="ecommerce_dataset",
            field_mapping={
                "user_id": "visitorid",
                "feature_key": map_feature_key,
                "event_type": "event",
                "timestamp": "timestamp",
            },
            properties_builder=build_properties,
        )
        super().__init__(config)

    @staticmethod
    def parse_timestamp(value: Any):
        parsed = pd.to_datetime(value, unit="ms", utc=True, errors="coerce")
        if pd.isna(parsed):
            raise ValueError(f"Invalid ecommerce_dataset timestamp: {value!r}")
        return parsed.to_pydatetime()
