from __future__ import annotations

from app.core.exceptions import ValidationError
from app.domain.services.event_service import EventService


class IngestService:
    def __init__(self, event_service: EventService) -> None:
        self._event_service = event_service

    def ingest_events(self, *, source: str, events: list[dict]) -> dict[str, int]:
        if not source.strip():
            raise ValidationError("source must not be empty.")
        if not events:
            raise ValidationError("events must contain at least one item.")

        saved = 0
        for event in events:
            self._event_service.create_event(
                source=source,
                user_id=event["user_id"],
                feature_key=event["feature_key"],
                event_type=event["event_type"],
                timestamp=event["timestamp"],
                properties=event["properties"],
            )
            saved += 1
        return {"saved_events": saved}
