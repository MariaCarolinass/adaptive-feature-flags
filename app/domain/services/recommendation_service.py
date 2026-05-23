from __future__ import annotations

import hashlib

import pandas as pd

from app.domain.repositories.event_repository import EventRepository
from app.domain.repositories.feature_repository import FeatureRepository
from app.domain.repositories.model_repository import ModelRepository
from app.infrastructure.ml.feature_builder import FeatureBuilder
from app.infrastructure.ml.predictor import ModelPredictor
from app.infrastructure.ml.serializer import ModelSerializer
from app.infrastructure.observability.metrics import MetricsSink, NoopMetricsSink


class RecommendationService:
    """
    Strategic recommendation service for feature rollout policy.

    This service analyzes aggregated feature-level evidence (events + ML selection)
    and suggests a rollout action, but does not mutate feature state.
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

    @staticmethod
    def _stable_percentage(user_id: str, feature_key: str) -> int:
        raw = f"{user_id}:{feature_key}".encode()
        digest = hashlib.sha256(raw).hexdigest()
        return int(digest[:8], 16) % 100

    def get_recommendation(self, feature_key: str) -> dict:
        """Return explainable recommendation for rollout strategy."""
        feature = self.feature_repository.get_by_key(feature_key)
        if feature is None:
            return {
                "feature_key": feature_key,
                "current_rollout": 0,
                "recommendation": "maintain_rollout",
                "suggested_rollout": 0,
                "reason": "Feature not found; recommendation unavailable.",
                "metrics": {
                    "ml_engagement": 0.0,
                    "rollout_engagement": 0.0,
                    "uplift": 0.0,
                    "coverage": 0.0,
                },
            }

        feature_events = self.event_repository.list(feature_key=feature_key)
        users = sorted({event.user_id for event in feature_events})
        if not users:
            return self._build_response(
                feature_key=feature.key,
                current_rollout=feature.rollout_percentage,
                recommendation="maintain_rollout",
                suggested_rollout=feature.rollout_percentage,
                reason="No events found for this feature yet.",
                ml_engagement=0.0,
                rollout_engagement=0.0,
                coverage=0.0,
            )

        positive_types = {"addtocart", "transaction", "used_feature"}
        user_engagement = {
            user_id: any(e.event_type in positive_types for e in feature_events if e.user_id == user_id)
            for user_id in users
        }

        rollout_users = [u for u in users if self._stable_percentage(u, feature.key) < feature.rollout_percentage]
        rollout_engagement = self._engagement_ratio(rollout_users, user_engagement)

        ml_users: list[str] = []
        ml_engagement = 0.0
        if feature.ml_enabled:
            model_status = self.model_repository.get_status()
            if model_status.status == "ready" and model_status.artifact_path:
                ml_users = self._ml_selected_users(feature_events, model_status.artifact_path)
                ml_engagement = self._engagement_ratio(ml_users, user_engagement)

        coverage = (len(ml_users) / len(users)) if users else 0.0
        uplift = ml_engagement - rollout_engagement
        recommendation, suggested_rollout, reason = self._recommend(
            current_rollout=feature.rollout_percentage,
            uplift=uplift,
            coverage=coverage,
            ml_users=ml_users,
        )
        self.metrics.gauge("recommendation.uplift", uplift, tags={"feature_key": feature.key})

        return self._build_response(
            feature_key=feature.key,
            current_rollout=feature.rollout_percentage,
            recommendation=recommendation,
            suggested_rollout=suggested_rollout,
            reason=reason,
            ml_engagement=ml_engagement,
            rollout_engagement=rollout_engagement,
            coverage=coverage,
        )

    @staticmethod
    def _engagement_ratio(users: list[str], user_engagement: dict[str, bool]) -> float:
        if not users:
            return 0.0
        engaged = sum(1 for user_id in users if user_engagement.get(user_id, False))
        return engaged / len(users)

    def _ml_selected_users(self, feature_events: list, artifact_path: str) -> list[str]:
        serializer = ModelSerializer()
        feature_columns = serializer.load_feature_columns(artifact_path) or [
            "unique_features",
            "active_days",
            "avg_hour",
            "avg_day_of_week",
            "hours_since_last_event",
            "events_per_day",
        ]
        predictor = ModelPredictor(artifact_path)
        builder = FeatureBuilder()

        selected_users: list[str] = []
        grouped: dict[str, list] = {}
        for event in feature_events:
            grouped.setdefault(event.user_id, []).append(event)

        for user_id, events in grouped.items():
            rows = [
                {
                    "user_id": event.user_id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp,
                    "feature_key": event.feature_key,
                }
                for event in events
            ]
            frame = builder.build_from_dataframe(pd.DataFrame(rows))
            if frame.empty:
                continue
            if any(column not in frame.columns for column in feature_columns):
                continue
            payload = frame.iloc[0][feature_columns].to_dict()
            score = predictor.predict_score(payload)
            if score >= 0.1:
                selected_users.append(user_id)
        return selected_users

    @staticmethod
    def _recommend(
        *,
        current_rollout: int,
        uplift: float,
        coverage: float,
        ml_users: list[str],
    ) -> tuple[str, int, str]:
        if not ml_users:
            return (
                "maintain_rollout",
                current_rollout,
                "Insufficient ML-selected users for a reliable recommendation.",
            )
        if uplift >= 0.05:
            suggested = min(100, current_rollout + 20)
            return (
                "increase_rollout",
                suggested,
                "ML-selected users showed higher engagement than random rollout.",
            )
        if uplift <= -0.02:
            return (
                "pause_rollout",
                0,
                "ML-selected users underperformed against random rollout.",
            )
        if coverage < 0.05:
            return (
                "maintain_rollout",
                current_rollout,
                "Coverage is still low; keep rollout while collecting more evidence.",
            )
        return (
            "maintain_rollout",
            current_rollout,
            "Current rollout is adequate based on observed engagement.",
        )

    @staticmethod
    def _build_response(
        *,
        feature_key: str,
        current_rollout: int,
        recommendation: str,
        suggested_rollout: int,
        reason: str,
        ml_engagement: float,
        rollout_engagement: float,
        coverage: float,
    ) -> dict:
        uplift = ml_engagement - rollout_engagement
        return {
            "feature_key": feature_key,
            "current_rollout": current_rollout,
            "recommendation": recommendation,
            "suggested_rollout": suggested_rollout,
            "reason": reason,
            "metrics": {
                "ml_engagement": round(ml_engagement, 4),
                "rollout_engagement": round(rollout_engagement, 4),
                "uplift": round(uplift, 4),
                "coverage": round(coverage, 4),
            },
        }
