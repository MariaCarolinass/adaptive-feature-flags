from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.core.exceptions import ValidationError
from app.domain.services.experiment_service import ExperimentService
from app.domain.services.event_service import EventService
from app.schemas.event_ingest import MAX_INGEST_BATCH_SIZE
from app.infrastructure.observability.metrics import MetricsSink, NoopMetricsSink

DEFAULT_INGEST_RATE_LIMIT_EVENTS = 5000
DEFAULT_INGEST_RATE_LIMIT_WINDOW_SECONDS = 60


class _SlidingWindowRateLimiter:
    def __init__(self, max_events: int, window_seconds: int) -> None:
        self._max_events = max_events
        self._window = timedelta(seconds=window_seconds)
        self._events: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, now: datetime) -> bool:
        with self._lock:
            queue = self._events[key]
            cutoff = now - self._window
            while queue and queue[0] <= cutoff:
                queue.popleft()
            if len(queue) >= self._max_events:
                return False
            queue.append(now)
            return True


class IngestService:
    def __init__(
        self,
        event_service: EventService,
        experiment_service: ExperimentService | None = None,
        metrics: MetricsSink | None = None,
        rate_limit_max_events: int = DEFAULT_INGEST_RATE_LIMIT_EVENTS,
        rate_limit_window_seconds: int = DEFAULT_INGEST_RATE_LIMIT_WINDOW_SECONDS,
    ) -> None:
        self._event_service = event_service
        self._experiment_service = experiment_service
        self.metrics = metrics or NoopMetricsSink()
        self._rate_limiter = _SlidingWindowRateLimiter(rate_limit_max_events, rate_limit_window_seconds)

    def ingest_events(self, *, source: str, events: list[dict], client_id: str = "unknown") -> dict[str, int]:
        if not source.strip():
            raise ValidationError("source must not be empty.")
        if not events:
            raise ValidationError("events must contain at least one item.")
        if len(events) > MAX_INGEST_BATCH_SIZE:
            raise ValidationError(f"events must not exceed {MAX_INGEST_BATCH_SIZE} items.")

        saved = 0
        rejected = 0
        now = datetime.now(timezone.utc)
        rate_limit_key = client_id.strip() or "unknown"
        for event in events:
            if not self._rate_limiter.allow(rate_limit_key, now):
                rejected += 1
                self.metrics.increment("ingest.rate_limited.count")
                continue
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
        latency_ms = properties.get("latency_ms")
        if latency_ms is None:
            return True
        if not isinstance(latency_ms, (int, float)):
            return False
        if not 0 <= float(latency_ms) <= 120000:
            return False
        return True
