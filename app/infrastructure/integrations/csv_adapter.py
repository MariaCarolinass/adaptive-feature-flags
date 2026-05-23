from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from app.infrastructure.integrations.base import CSVAdapterConfig, EventCSVAdapter, RowMapper


class GenericCSVAdapter(EventCSVAdapter):
    """
    Generic CSV -> canonical event adapter.
    """

    def __init__(self, config: CSVAdapterConfig) -> None:
        super().__init__(config)
        self._validate_config()

    def iter_events(self, csv_path: str, *, chunk_size: int = 50000, limit: int | None = None) -> Iterable[dict[str, Any]]:
        processed = 0
        for frame in pd.read_csv(csv_path, chunksize=chunk_size):
            for _, row in frame.iterrows():
                if limit is not None and processed >= limit:
                    return
                normalized = self._map_row(row)
                if normalized is None:
                    continue
                processed += 1
                yield normalized

    def _map_row(self, row: pd.Series) -> dict[str, Any] | None:
        event: dict[str, Any] = {}
        for field in self.config.required_fields:
            mapped = self.config.field_mapping[field]
            value = self._resolve_value(row, mapped)
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            event[field] = value

        event["timestamp"] = self.parse_timestamp(event["timestamp"])
        properties = dict(self.config.default_properties)
        if self.config.properties_builder is not None:
            properties.update(self.config.properties_builder(row))

        event["source"] = self.config.source
        event["properties"] = properties
        return event

    @staticmethod
    def _resolve_value(row: pd.Series, mapped: str | RowMapper) -> Any:
        if callable(mapped):
            return mapped(row)
        if mapped not in row:
            return None
        value = row[mapped]
        if pd.isna(value):
            return None
        return value

    def _validate_config(self) -> None:
        missing = [field for field in self.config.required_fields if field not in self.config.field_mapping]
        if missing:
            raise ValueError(f"Missing required mapping fields: {missing}")
