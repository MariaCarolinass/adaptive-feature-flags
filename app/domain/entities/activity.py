from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Activity:
    id: int | None
    key: str
    name: str
    description: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime
