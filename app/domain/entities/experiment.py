from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Experiment:
    id: int | None
    name: str
    feature_key: str
    primary_metric_event: str
    min_samples_per_variant: int
    min_lift: float
    enabled: bool
    created_at: datetime
    updated_at: datetime
