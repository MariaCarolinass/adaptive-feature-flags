from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class EvaluationRecord:
    id: int | None
    feature_key: str
    user_id: str
    enabled: bool
    decision_source: str
    score: float | None
    threshold: float | None
    threshold_mode: str | None
    experiment: dict | None
    model_version: str | None
    created_at: datetime
