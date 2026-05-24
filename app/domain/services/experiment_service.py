from __future__ import annotations

from datetime import datetime, timezone
import hashlib

from app.domain.entities.experiment import Experiment
from app.domain.repositories.event_repository import EventRepository
from app.domain.repositories.experiment_repository import ExperimentRepository


class ExperimentService:
    def __init__(
        self,
        experiment_repository: ExperimentRepository,
        event_repository: EventRepository,
    ) -> None:
        self.experiment_repository = experiment_repository
        self.event_repository = event_repository

    def create_experiment(
        self,
        *,
        name: str,
        feature_key: str,
        primary_metric_event: str,
        min_samples_per_variant: int = 100,
        min_lift: float = 0.02,
        enabled: bool = True,
    ) -> Experiment:
        now = datetime.now(timezone.utc)
        experiment = Experiment(
            id=None,
            name=name,
            feature_key=feature_key,
            primary_metric_event=primary_metric_event,
            min_samples_per_variant=min_samples_per_variant,
            min_lift=min_lift,
            enabled=enabled,
            created_at=now,
            updated_at=now,
        )
        return self.experiment_repository.create(experiment)

    def list_experiments(self) -> list[Experiment]:
        return self.experiment_repository.list()

    @staticmethod
    def assign_variant(*, user_id: str, experiment_id: int) -> str:
        raw = f"{experiment_id}:{user_id}".encode()
        bucket = int(hashlib.sha256(raw).hexdigest()[:8], 16) % 100
        return "A" if bucket < 50 else "B"

    def maybe_build_context(self, *, feature_key: str, user_id: str) -> dict | None:
        experiment = self.experiment_repository.get_active_by_feature_key(feature_key)
        if experiment is None:
            return None

        variant = self.assign_variant(user_id=user_id, experiment_id=experiment.id or 0)
        return {
            "experiment_id": experiment.id,
            "experiment_name": experiment.name,
            "variant": variant,
        }

    def evaluate_experiment(self, experiment_id: int) -> dict | None:
        experiment = next((e for e in self.experiment_repository.list() if e.id == experiment_id), None)
        if experiment is None:
            return None

        events = self.event_repository.list(feature_key=experiment.feature_key)
        variant_stats = {
            "A": {"samples": 0, "positives": 0},
            "B": {"samples": 0, "positives": 0},
        }
        for event in events:
            variant = str(event.properties.get("ab_variant", "")).upper()
            if variant not in ("A", "B"):
                continue
            variant_stats[variant]["samples"] += 1
            if event.event_type == experiment.primary_metric_event:
                variant_stats[variant]["positives"] += 1

        def rate(stats: dict) -> float:
            return stats["positives"] / max(stats["samples"], 1)

        rate_a = rate(variant_stats["A"])
        rate_b = rate(variant_stats["B"])
        lift_b_vs_a = rate_b - rate_a
        enough_samples = all(
            variant_stats[v]["samples"] >= experiment.min_samples_per_variant for v in ("A", "B")
        )
        decision = "continue"
        if enough_samples and abs(lift_b_vs_a) >= experiment.min_lift:
            decision = "stop_promote_b" if lift_b_vs_a > 0 else "stop_keep_a"

        return {
            "experiment_id": experiment.id,
            "experiment_name": experiment.name,
            "feature_key": experiment.feature_key,
            "primary_metric_event": experiment.primary_metric_event,
            "variant_stats": variant_stats,
            "rate_a": rate_a,
            "rate_b": rate_b,
            "lift_b_vs_a": lift_b_vs_a,
            "min_lift": experiment.min_lift,
            "min_samples_per_variant": experiment.min_samples_per_variant,
            "decision": decision,
        }
