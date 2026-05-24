from __future__ import annotations

from datetime import datetime, timezone

from app.domain.entities.event import Event
from app.domain.entities.experiment import Experiment
from app.domain.services.experiment_service import ExperimentService


class _ExperimentRepo:
    def __init__(self) -> None:
        self.items: list[Experiment] = []

    def create(self, experiment: Experiment) -> Experiment:
        experiment.id = len(self.items) + 1
        self.items.append(experiment)
        return experiment

    def list(self) -> list[Experiment]:
        return list(self.items)

    def get_active_by_feature_key(self, feature_key: str) -> Experiment | None:
        for item in self.items:
            if item.feature_key == feature_key and item.enabled:
                return item
        return None


class _EventRepo:
    def __init__(self, events: list[Event]) -> None:
        self._events = events

    def list(self, user_id: str | None = None, feature_key: str | None = None, event_type: str | None = None) -> list[Event]:
        events = self._events
        if user_id is not None:
            events = [e for e in events if e.user_id == user_id]
        if feature_key is not None:
            events = [e for e in events if e.feature_key == feature_key]
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        return events


def _event(*, user_id: str, event_type: str, variant: str) -> Event:
    return Event(
        id=None,
        source="web",
        user_id=user_id,
        feature_key="feature_a",
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        properties={"ab_variant": variant},
    )


def test_assign_variant_is_deterministic() -> None:
    first = ExperimentService.assign_variant(user_id="u1", experiment_id=1)
    second = ExperimentService.assign_variant(user_id="u1", experiment_id=1)
    assert first == second


def test_evaluate_experiment_returns_stop_when_lift_and_sample_thresholds_are_met() -> None:
    repo = _ExperimentRepo()
    service = ExperimentService(
        experiment_repository=repo,
        event_repository=_EventRepo(
            [
                _event(user_id="a1", event_type="purchase", variant="A"),
                _event(user_id="a2", event_type="view", variant="A"),
                _event(user_id="b1", event_type="purchase", variant="B"),
                _event(user_id="b2", event_type="purchase", variant="B"),
            ]
        ),
    )

    created = service.create_experiment(
        name="Checkout AB",
        feature_key="feature_a",
        primary_metric_event="purchase",
        min_samples_per_variant=2,
        min_lift=0.2,
        enabled=True,
    )
    result = service.evaluate_experiment(created.id or 0)
    assert result is not None
    assert result["decision"] == "stop_promote_b"
