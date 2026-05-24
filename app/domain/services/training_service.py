from datetime import datetime, timezone

from app.core.event_types import POSITIVE_EVENT_TYPES
from app.core.exceptions import ValidationError
from app.domain.entities.model_metadata import ModelMetadata
from app.domain.repositories.event_repository import EventRepository
from app.domain.repositories.model_repository import ModelRepository
from app.infrastructure.ml.trainer import train_from_events
from app.infrastructure.observability.metrics import MetricsSink, NoopMetricsSink


class TrainingService:
    def __init__(
        self,
        event_repository: EventRepository,
        model_repository: ModelRepository,
        metrics: MetricsSink | None = None,
    ) -> None:
        self.event_repository = event_repository
        self.model_repository = model_repository
        self.metrics = metrics or NoopMetricsSink()

    def train(self) -> dict:
        started_at = datetime.now(timezone.utc)
        events = self.event_repository.list()
        if not events:
            raise ValidationError("Training requires at least one event.")

        total_events = len(events)
        unique_users = len({event.user_id for event in events})
        positive_events = sum(1 for event in events if event.event_type in POSITIVE_EVENT_TYPES)

        try:
            result = train_from_events(events)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        metadata = ModelMetadata(
            status="ready",
            model_name=result["model_name"],
            model_version=result["model_version"],
            trained_at=result["trained_at"],
            metrics=result["metrics"],
            artifact_path=result["artifact_path"],
        )

        saved = self.model_repository.save_status(metadata)
        snapshot = {
            "model_name": saved.model_name,
            "model_version": saved.model_version,
            "trained_at": saved.trained_at.isoformat() if saved.trained_at else None,
            "metrics": saved.metrics,
            "artifact_path": saved.artifact_path,
            "process": {
                "total_events": total_events,
                "unique_users": unique_users,
                "positive_events": positive_events,
                "feature_columns": result.get("feature_columns", []),
                "benchmark": result.get("benchmark", []),
                "dataset_profile": result.get("dataset_profile", {}),
            },
            "threshold_policy": {
                "modes_supported": ["fixed", "match_rollout", "maximize_f1"],
                "fallback_policy": "rollout_deterministic",
            },
        }
        self.model_repository.append_training_run(
            model_version=saved.model_version or "unknown",
            trained_at=saved.trained_at or started_at,
            status=saved.status,
            snapshot=snapshot,
        )
        duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
        self.metrics.timing("training.duration_ms", duration_ms)
        if saved.metrics:
            accuracy = saved.metrics.get("accuracy")
            f1_score = saved.metrics.get("f1_score")
            if accuracy is not None:
                self.metrics.gauge("model.accuracy", float(accuracy))
            if f1_score is not None:
                self.metrics.gauge("model.f1_score", float(f1_score))

        return {
            "status": saved.status,
            "model_name": saved.model_name,
            "model_version": saved.model_version,
            "artifact_path": saved.artifact_path,
            "trained_at": saved.trained_at,
            "metrics": saved.metrics,
            "process": {
                "total_events": total_events,
                "unique_users": unique_users,
                "positive_events": positive_events,
                "duration_ms": duration_ms,
                "feature_columns": result.get("feature_columns", []),
                "benchmark": result.get("benchmark", []),
                "dataset_profile": result.get("dataset_profile", {}),
            },
        }

    def get_status(self) -> ModelMetadata:
        return self.model_repository.get_status()

    def list_training_runs(self, limit: int = 20) -> list[dict]:
        return self.model_repository.list_training_runs(limit=limit)
