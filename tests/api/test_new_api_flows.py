from __future__ import annotations

from app.api.v1.routes import evaluate as evaluate_route
from app.api.v1.routes import training as training_route
from app.schemas.evaluate import EvaluateRequest, EvaluateUser


def test_post_train_returns_ready_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        training_route.training_service,
        "train",
        lambda: {
            "status": "ready",
            "model_name": "random_forest",
            "model_version": "v1",
            "artifact_path": "storage/models/v1.joblib",
            "trained_at": "2026-04-22T10:00:00Z",
            "metrics": {"accuracy": 0.82, "f1_score": 0.79},
            "process": {
                "total_events": 100,
                "unique_users": 40,
                "positive_events": 20,
                "duration_ms": 420,
                "feature_columns": ["unique_features"],
            },
        },
    )

    payload = training_route.train()
    assert payload["status"] == "ready"


def test_post_evaluate_rollout_when_model_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        evaluate_route.evaluation_service,
        "evaluate",
        lambda **_kwargs: {
            "feature_key": "new_checkout",
            "user_id": "u1",
            "enabled": False,
            "decision_source": "rollout",
            "score": None,
            "model_version": None,
        },
    )

    result = evaluate_route.evaluate(
        EvaluateRequest(feature_key="new_checkout", user=EvaluateUser(user_id="u1"))
    )
    assert result["decision_source"] == "rollout"


def test_post_evaluate_ml_when_model_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        evaluate_route.evaluation_service,
        "evaluate",
        lambda **_kwargs: {
            "feature_key": "new_checkout",
            "user_id": "u2",
            "enabled": True,
            "decision_source": "ml",
            "score": 0.91,
            "model_version": "v1",
        },
    )

    result = evaluate_route.evaluate(
        EvaluateRequest(feature_key="new_checkout", user=EvaluateUser(user_id="u2"))
    )
    assert result["decision_source"] == "ml"
    assert result["enabled"] is True
