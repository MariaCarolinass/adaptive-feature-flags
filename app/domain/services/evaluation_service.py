import hashlib

import pandas as pd
from app.core.logging import get_logger
from app.domain.repositories.event_repository import EventRepository
from app.domain.repositories.feature_repository import FeatureRepository
from app.domain.repositories.model_repository import ModelRepository
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
        metrics: MetricsSink | None = None,
    ) -> None:
        self.feature_repository = feature_repository
        self.event_repository = event_repository
        self.model_repository = model_repository
        self.metrics = metrics or NoopMetricsSink()

    def _stable_percentage(self, user_id: str, feature_key: str) -> int:
        raw = f"{user_id}:{feature_key}".encode()
        digest = hashlib.sha256(raw).hexdigest()
        return int(digest[:8], 16) % 100

    def evaluate(self, feature_key: str, user: dict) -> dict:
        """Return immediate decision for one user/feature pair."""
        self.metrics.increment("evaluation.count")
        feature = self.feature_repository.get_by_key(feature_key)

        if feature is None:
            self.metrics.increment(
                "evaluation.decision_source",
                tags={"source": "feature_not_found"},
            )
            return {
                "feature_key": feature_key,
                "user_id": user["user_id"],
                "enabled": False,
                "decision_source": "feature_not_found",
                "score": None,
                "model_version": None,
            }

        if not feature.enabled:
            self.metrics.increment(
                "evaluation.decision_source",
                tags={"source": "feature_disabled"},
            )
            return {
                "feature_key": feature_key,
                "user_id": user["user_id"],
                "enabled": False,
                "decision_source": "feature_disabled",
                "score": None,
                "model_version": None,
            }

        model_status = self.model_repository.get_status()

        if feature.ml_enabled and model_status.status == "ready" and model_status.artifact_path:
            score = self._predict_score(
                artifact_path=model_status.artifact_path,
                user_id=user["user_id"],
                reference_timestamp=model_status.trained_at,
            )
            if score is not None:
                enabled = score >= 0.1
                self.metrics.increment(
                    "evaluation.decision_source",
                    tags={"source": "ml"},
                )
                if enabled:
                    self.metrics.increment("evaluation.enabled.count")
                return {
                    "feature_key": feature_key,
                    "user_id": user["user_id"],
                    "enabled": enabled,
                    "decision_source": "ml",
                    "score": score,
                    "model_version": model_status.model_version,
                }

        bucket = self._stable_percentage(user["user_id"], feature_key)
        enabled = bucket < feature.rollout_percentage
        self.metrics.increment(
            "evaluation.decision_source",
            tags={"source": "rollout"},
        )
        if enabled:
            self.metrics.increment("evaluation.enabled.count")

        return {
            "feature_key": feature_key,
            "user_id": user["user_id"],
            "enabled": enabled,
            "decision_source": "rollout",
            "score": None,
            "model_version": None,
        }

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
