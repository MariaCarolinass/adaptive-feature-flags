import hashlib
from datetime import datetime, timezone

import pandas as pd
from app.core.logging import get_logger
from app.domain.entities.evaluation import EvaluationRecord
from app.domain.repositories.event_repository import EventRepository
from app.domain.repositories.evaluation_repository import EvaluationRepository
from app.domain.repositories.feature_repository import FeatureRepository
from app.domain.repositories.model_repository import ModelRepository
from app.domain.services.experiment_service import ExperimentService
from app.infrastructure.ml.feature_builder import FeatureBuilder
from app.infrastructure.ml.predictor import ModelPredictor
from app.infrastructure.ml.serializer import ModelSerializer
from app.infrastructure.observability.metrics import MetricsSink, NoopMetricsSink

logger = get_logger(__name__)


class EvaluationService:
    """
    Fast online decision service for a single user.

    This service is intentionally low-latency:
    - decides `enabled` true/false for one request
    - uses ML score when available
    - falls back to deterministic rollout
    - never trains models
    """
    def __init__(
        self,
        feature_repository: FeatureRepository,
        event_repository: EventRepository,
        model_repository: ModelRepository,
        experiment_service: ExperimentService,
        evaluation_repository: EvaluationRepository | None = None,
        metrics: MetricsSink | None = None,
    ) -> None:
        self.feature_repository = feature_repository
        self.event_repository = event_repository
        self.model_repository = model_repository
        self.experiment_service = experiment_service
        self.evaluation_repository = evaluation_repository
        self.metrics = metrics or NoopMetricsSink()

    def _stable_percentage(self, user_id: str, feature_key: str) -> int:
        raw = f"{user_id}:{feature_key}".encode()
        digest = hashlib.sha256(raw).hexdigest()
        return int(digest[:8], 16) % 100

    def evaluate(self, feature_key: str, user: dict) -> dict:
        """Return immediate decision for one user/feature pair."""
        self.metrics.increment("evaluation.count")
        feature = self.feature_repository.get_by_key(feature_key)
        activity = self._latest_activity(user["user_id"], feature_key)

        if feature is None:
            self.metrics.increment(
                "evaluation.decision_source",
                tags={"source": "feature_not_found"},
            )
            result = {
                "feature_key": feature_key,
                "user_id": user["user_id"],
                "activity": activity,
                "enabled": False,
                "decision_source": "feature_not_found",
                "score": None,
                "model_version": None,
            }
            self._persist(result)
            return result

        if not feature.enabled:
            self.metrics.increment(
                "evaluation.decision_source",
                tags={"source": "feature_disabled"},
            )
            result = {
                "feature_key": feature_key,
                "user_id": user["user_id"],
                "activity": activity,
                "enabled": False,
                "decision_source": "feature_disabled",
                "score": None,
                "model_version": None,
            }
            self._persist(result)
            return result

        model_status = self.model_repository.get_status()
        experiment = self.experiment_service.maybe_build_context(
            feature_key=feature_key,
            user_id=user["user_id"],
        )

        if feature.ml_enabled and model_status.status == "ready" and model_status.artifact_path:
            score = self._predict_score(
                artifact_path=model_status.artifact_path,
                user_id=user["user_id"],
                reference_timestamp=model_status.trained_at,
            )
            if score is not None:
                threshold = self._resolve_ml_threshold(
                    rollout_percentage=feature.rollout_percentage,
                    mode=feature.ml_threshold_mode,
                    fixed_value=feature.ml_threshold_value,
                    model_metrics=model_status.metrics or {},
                )
                enabled = score >= threshold
                self.metrics.increment(
                    "evaluation.decision_source",
                    tags={"source": "ml"},
                )
                if enabled:
                    self.metrics.increment("evaluation.enabled.count")
                result = {
                    "feature_key": feature_key,
                    "user_id": user["user_id"],
                    "activity": activity,
                    "enabled": enabled,
                    "decision_source": "ml",
                    "score": score,
                    "threshold": threshold,
                    "threshold_mode": feature.ml_threshold_mode,
                    "experiment": experiment,
                    "model_version": model_status.model_version,
                }
                self._persist(result)
                return result

        bucket = self._stable_percentage(user["user_id"], feature_key)
        enabled = bucket < feature.rollout_percentage
        self.metrics.increment(
            "evaluation.decision_source",
            tags={"source": "rollout"},
        )
        if enabled:
            self.metrics.increment("evaluation.enabled.count")

        result = {
            "feature_key": feature_key,
            "user_id": user["user_id"],
            "activity": activity,
            "enabled": enabled,
            "decision_source": "rollout",
            "score": None,
            "threshold": None,
            "threshold_mode": None,
            "experiment": experiment,
            "model_version": None,
        }
        self._persist(result)
        return result

    def list_recent(self, limit: int = 50) -> list[dict]:
        if self.evaluation_repository is None:
            return []
        return [self._to_payload(record) for record in self.evaluation_repository.list(limit=limit)]

    def clear_history(self) -> int:
        if self.evaluation_repository is None:
            return 0
        return self.evaluation_repository.delete_all()

    def _latest_activity(self, user_id: str, feature_key: str) -> str | None:
        events = self.event_repository.list(user_id=user_id, feature_key=feature_key)
        if not events:
            return None
        latest = max(
            events,
            key=lambda event: (
                event.timestamp.astimezone(timezone.utc)
                if event.timestamp.tzinfo is not None
                else event.timestamp.replace(tzinfo=timezone.utc)
            ),
        )
        return latest.event_type or None

    @staticmethod
    def _resolve_ml_threshold(
        *,
        rollout_percentage: int,
        mode: str,
        fixed_value: float,
        model_metrics: dict,
    ) -> float:
        if mode == "match_rollout":
            # Heuristic: approximate coverage target by inverse threshold.
            return max(0.0, min(1.0, 1.0 - (rollout_percentage / 100.0)))
        if mode == "maximize_f1":
            tuned = model_metrics.get("best_threshold_by_f1")
            if isinstance(tuned, (int, float)):
                return max(0.0, min(1.0, float(tuned)))
        return max(0.0, min(1.0, fixed_value))

    def _predict_score(
        self,
        artifact_path: str,
        user_id: str,
        *,
        reference_timestamp=None,
    ) -> float | None:
        try:
            user_events = self.event_repository.list(user_id=user_id)
            if not user_events:
                return None

            rows = [
                {
                    "user_id": event.user_id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp,
                    "feature_key": event.feature_key,
                }
                for event in user_events
            ]
            dataset = FeatureBuilder().build_from_dataframe(
                pd.DataFrame(rows),
                reference_timestamp=reference_timestamp,
            )
            if dataset.empty:
                return None

            serializer = ModelSerializer()
            feature_columns = serializer.load_feature_columns(artifact_path) or [
                "unique_features",
                "active_days",
                "avg_hour",
                "avg_day_of_week",
                "hours_since_last_event",
                "events_per_day",
            ]
            missing = [col for col in feature_columns if col not in dataset.columns]
            if missing:
                return None

            predictor = ModelPredictor(artifact_path)
            payload = dataset.iloc[0][feature_columns].to_dict()
            score = predictor.predict_score(payload)
            return max(0.0, min(1.0, score))
        except Exception:
            logger.warning(
                "ML scoring failed for user_id=%s and artifact_path=%s; falling back to rollout.",
                user_id,
                artifact_path,
            )
            return None

    def _persist(self, result: dict) -> None:
        if self.evaluation_repository is None:
            return
        try:
            created_at = datetime.now(timezone.utc)
            record = EvaluationRecord(
                id=None,
                feature_key=result["feature_key"],
                user_id=result["user_id"],
                activity=result.get("activity"),
                enabled=bool(result["enabled"]),
                decision_source=str(result["decision_source"]),
                score=result.get("score"),
                threshold=result.get("threshold"),
                threshold_mode=result.get("threshold_mode"),
                experiment=result.get("experiment"),
                model_version=result.get("model_version"),
                created_at=created_at,
            )
            saved = self.evaluation_repository.create(record)
            result["id"] = saved.id
            result["created_at"] = saved.created_at.isoformat()
        except Exception:
            logger.warning("Failed to persist evaluation history for feature_key=%s", result.get("feature_key"))

    @staticmethod
    def _to_payload(record: EvaluationRecord) -> dict:
        return {
            "id": record.id,
            "feature_key": record.feature_key,
            "user_id": record.user_id,
            "activity": record.activity,
            "enabled": record.enabled,
            "decision_source": record.decision_source,
            "score": record.score,
            "threshold": record.threshold,
            "threshold_mode": record.threshold_mode,
            "experiment": record.experiment,
            "model_version": record.model_version,
            "created_at": record.created_at.isoformat(),
        }
