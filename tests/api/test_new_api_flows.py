from __future__ import annotations

from app.api.v1.routes import evaluate as evaluate_route
from app.api.v1.routes import experiments as experiments_route
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
            "threshold": None,
            "threshold_mode": None,
            "experiment": None,
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
            "threshold": 0.2,
            "threshold_mode": "fixed",
            "experiment": {"experiment_id": 1, "experiment_name": "Checkout A/B", "variant": "B"},
            "model_version": "v1",
        },
    )

    result = evaluate_route.evaluate(
        EvaluateRequest(feature_key="new_checkout", user=EvaluateUser(user_id="u2"))
    )
    assert result["decision_source"] == "ml"
    assert result["enabled"] is True


def test_experiment_routes_create_and_evaluate(monkeypatch) -> None:
    monkeypatch.setattr(
        experiments_route.experiment_service,
        "create_experiment",
        lambda **_kwargs: {
            "id": 1,
            "name": "Checkout A/B",
            "feature_key": "new_checkout",
            "primary_metric_event": "purchase",
            "min_samples_per_variant": 100,
            "min_lift": 0.02,
            "enabled": True,
            "created_at": "2026-05-24T10:00:00Z",
            "updated_at": "2026-05-24T10:00:00Z",
        },
    )
    monkeypatch.setattr(
        experiments_route.experiment_service,
        "evaluate_experiment",
        lambda _id: {
            "experiment_id": 1,
            "experiment_name": "Checkout A/B",
            "feature_key": "new_checkout",
            "primary_metric_event": "purchase",
            "variant_stats": {"A": {"samples": 100, "positives": 12}, "B": {"samples": 100, "positives": 15}},
            "rate_a": 0.12,
            "rate_b": 0.15,
            "lift_b_vs_a": 0.03,
            "min_lift": 0.02,
            "min_samples_per_variant": 100,
            "decision": "stop_promote_b",
        },
    )

    created = experiments_route.create_experiment(
        experiments_route.ExperimentCreate(
            name="Checkout A/B",
            feature_key="new_checkout",
            primary_metric_event="purchase",
        )
    )
    assert created["id"] == 1

    result = experiments_route.evaluate_experiment(1)
    assert result["decision"] == "stop_promote_b"
