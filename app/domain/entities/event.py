from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Event:
    id: int | None
    source: str | None
    user_id: str
    feature_key: str
    event_type: str
    timestamp: datetime
    properties: dict[str, str | int | float | bool | None]
