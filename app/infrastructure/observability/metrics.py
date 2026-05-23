from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


Tags = dict[str, str]


class MetricsSink(ABC):
    """
    Minimal metrics interface.

    Keep this interface stable so adapters for Prometheus, Datadog or OpenTelemetry
    can be added later without changing domain/service code.
    """

    @abstractmethod
    def increment(self, name: str, value: int = 1, *, tags: Tags | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def gauge(self, name: str, value: float, *, tags: Tags | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def timing(self, name: str, value_ms: int, *, tags: Tags | None = None) -> None:
        raise NotImplementedError


class NoopMetricsSink(MetricsSink):
    def increment(self, name: str, value: int = 1, *, tags: Tags | None = None) -> None:
        return

    def gauge(self, name: str, value: float, *, tags: Tags | None = None) -> None:
        return

    def timing(self, name: str, value_ms: int, *, tags: Tags | None = None) -> None:
        return


@dataclass(slots=True)
class InMemoryLoggingMetricsSink(MetricsSink):
    """
    Simple internal sink for development.

    - Stores latest gauge/timing values and cumulative counters in memory.
    - Logs every metric emission for quick local observability.
    """

    counters: dict[str, int] = field(default_factory=dict)
    gauges: dict[str, float] = field(default_factory=dict)
    timings_ms: dict[str, int] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def increment(self, name: str, value: int = 1, *, tags: Tags | None = None) -> None:
        key = self._key(name, tags)
        with self._lock:
            self.counters[key] = self.counters.get(key, 0) + value
        logger.info("metric.increment name=%s value=%s tags=%s", name, value, tags or {})

    def gauge(self, name: str, value: float, *, tags: Tags | None = None) -> None:
        key = self._key(name, tags)
        with self._lock:
            self.gauges[key] = float(value)
        logger.info("metric.gauge name=%s value=%s tags=%s", name, value, tags or {})

    def timing(self, name: str, value_ms: int, *, tags: Tags | None = None) -> None:
        key = self._key(name, tags)
        with self._lock:
            self.timings_ms[key] = int(value_ms)
        logger.info("metric.timing name=%s value_ms=%s tags=%s", name, value_ms, tags or {})

    @staticmethod
    def _key(name: str, tags: Tags | None) -> str:
        if not tags:
            return name
        pairs = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{pairs}"


# Default process-level sink used by services.
metrics_sink: MetricsSink = InMemoryLoggingMetricsSink()

