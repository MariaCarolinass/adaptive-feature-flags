from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

ScalarValue = str | int | float | bool | None
CanonicalEvent = dict[str, Any]
RowMapper = Callable[[pd.Series], Any]
PropertiesBuilder = Callable[[pd.Series], dict[str, ScalarValue]]


@dataclass(slots=True)
class CSVAdapterConfig:
    source: str
    field_mapping: dict[str, str | RowMapper]
    properties_builder: PropertiesBuilder | None = None
    default_properties: dict[str, ScalarValue] = field(default_factory=dict)
    required_fields: tuple[str, ...] = ("user_id", "feature_key", "event_type", "timestamp")


class EventCSVAdapter(ABC):
    def __init__(self, config: CSVAdapterConfig) -> None:
        self.config = config

    @abstractmethod
    def iter_events(self, csv_path: str, *, chunk_size: int = 50000, limit: int | None = None) -> Iterable[CanonicalEvent]:
        raise NotImplementedError

    @staticmethod
    def parse_timestamp(value: Any) -> datetime:
        parsed = pd.to_datetime(value, errors="coerce", utc=True)
        if pd.isna(parsed):
            raise ValueError(f"Invalid timestamp value: {value!r}")
        return parsed.to_pydatetime()
