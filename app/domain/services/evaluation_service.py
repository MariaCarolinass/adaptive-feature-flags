import hashlib

from app.domain.repositories.feature_repository import FeatureRepository
from app.domain.repositories.model_repository import ModelRepository


class EvaluationService:
    def __init__(
        self,
        feature_repository: FeatureRepository,
        model_repository: ModelRepository,
    ) -> None:
        self.feature_repository = feature_repository
        self.model_repository = model_repository

    def _stable_percentage(self, user_id: str, feature_key: str) -> int:
        raw = f"{user_id}:{feature_key}".encode()
        digest = hashlib.sha256(raw).hexdigest()
        return int(digest[:8], 16) % 100

    def evaluate(self, feature_key: str, user: dict) -> dict:
        feature = self.feature_repository.get_by_key(feature_key)

        if feature is None:
            return {
                "feature_key": feature_key,
                "user_id": user["user_id"],
                "enabled": False,
                "decision_source": "feature_not_found",
                "score": None,
                "model_version": None,
            }

        if not feature.enabled:
            return {
                "feature_key": feature_key,
                "user_id": user["user_id"],
                "enabled": False,
                "decision_source": "feature_disabled",
                "score": None,
                "model_version": None,
            }

        model_status = self.model_repository.get_status()

        if feature.ml_enabled and model_status.status == "ready":
            score = 0.82
            return {
                "feature_key": feature_key,
                "user_id": user["user_id"],
                "enabled": score >= 0.5,
                "decision_source": "ml",
                "score": score,
                "model_version": model_status.model_version,
            }

        bucket = self._stable_percentage(user["user_id"], feature_key)
        enabled = bucket < feature.rollout_percentage

        return {
            "feature_key": feature_key,
            "user_id": user["user_id"],
            "enabled": enabled,
            "decision_source": "rollout",
            "score": None,
            "model_version": None,
        }