from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ModelMetadata:
    status: str
    model_name: str | None
    model_version: str | None
    trained_at: datetime | None
    metrics: dict[str, float] | None