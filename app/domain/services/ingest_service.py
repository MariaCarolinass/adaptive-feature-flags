from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import ValidationError
from app.domain.services.experiment_service import ExperimentService
from app.domain.services.event_service import EventService
from app.infrastructure.observability.metrics import MetricsSink, NoopMetricsSink


class IngestService:
    def __init__(
        self,
        event_service: EventService,
        experiment_service: ExperimentService | None = None,
        metrics: MetricsSink | None = None,
    ) -> None:
        self._event_service = event_service
        self._experiment_service = experiment_service
        self.metrics = metrics or NoopMetricsSink()

    def ingest_events(self, *, source: str, events: list[dict]) -> dict[str, int]:
        if not source.strip():
            raise ValidationError("source must not be empty.")
        if not events:
            raise ValidationError("events must contain at least one item.")

        saved = 0
        rejected = 0
        now = datetime.now(timezone.utc)
        for event in events:
            if not self._is_valid_event(event, now):
                rejected += 1
                self.metrics.increment("ingest.rejected.count")
                continue
            if self._experiment_service is not None:
                context = self._experiment_service.maybe_build_context(
                    feature_key=str(event["feature_key"]),
                    user_id=str(event["user_id"]),
                )
                if context is not None:
                    event_properties = dict(event["properties"])
                    event_properties["ab_variant"] = context["variant"]
                    event["properties"] = event_properties
            self._event_service.create_event(
                source=source,
                user_id=event["user_id"],
                feature_key=event["feature_key"],
                event_type=event["event_type"],
                timestamp=event["timestamp"],
                properties=event["properties"],
            )
            saved += 1
            self.metrics.increment("ingest.saved.count")
        self.metrics.gauge("ingest.rejection_rate", rejected / max(len(events), 1))
        return {"saved_events": saved, "rejected": rejected}

    @staticmethod
    def _is_valid_event(event: dict, now: datetime) -> bool:
        required = ("user_id", "feature_key", "event_type", "timestamp", "properties")
        if any(key not in event for key in required):
            return False
        if not str(event["user_id"]).strip():
            return False
        if not str(event["feature_key"]).strip():
            return False
        if not str(event["event_type"]).strip():
            return False
        if not isinstance(event["properties"], dict):
            return False

        timestamp = event["timestamp"]
        if not isinstance(timestamp, datetime):
            return False
        if timestamp.tzinfo is None:
            return False
        if timestamp > now:
            return False
        if not IngestService._has_valid_operational_metrics(event["properties"]):
            return False

        return True

    @staticmethod
    def _has_valid_operational_metrics(properties: dict) -> bool:
        validators = {
            "latency_ms": lambda v: isinstance(v, (int, float)) and 0 <= float(v) <= 120000,
            "error_rate": lambda v: isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0,
            "cpu_pct": lambda v: isinstance(v, (int, float)) and 0.0 <= float(v) <= 100.0,
            "mem_pct": lambda v: isinstance(v, (int, float)) and 0.0 <= float(v) <= 100.0,
        }
        for key, check in validators.items():
            if key in properties and not check(properties[key]):
                return False
        return True
