from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_feature_retrieve_returns_not_found_with_typed_payload() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/features/999999")
        assert response.status_code == 404
        payload = response.json()
        assert "detail" in payload
        assert payload["detail"]["code"] == "not_found"


def test_error_response_does_not_leak_internal_details(monkeypatch) -> None:
    from app.api.v1.routes import evaluate as evaluate_route

    def explode(*args, **kwargs):
        raise RuntimeError("segredo interno")

    monkeypatch.setattr(evaluate_route.evaluation_service, "evaluate", explode)

    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/evaluate", json={"feature_key": "missing", "user": {"user_id": "u1"}})
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error."}


def test_security_headers_present() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("referrer-policy") == "no-referrer"


def test_start_async_training_job_returns_job_metadata(monkeypatch) -> None:
    from app.api.v1.routes import training as training_route

    monkeypatch.setattr(
        training_route.training_job_service,
        "start",
        lambda: {
            "job_id": "job123",
            "status": "queued",
            "submitted_at": "2026-04-21T17:05:12.332000Z",
        },
    )

    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/train/async")
        assert response.status_code == 202
        payload = response.json()
        assert payload["job_id"] == "job123"
        assert payload["status"] == "queued"


def test_get_async_training_job_status_returns_job_details(monkeypatch) -> None:
    from app.api.v1.routes import training as training_route

    monkeypatch.setattr(
        training_route.training_job_service,
        "get",
        lambda _job_id: {
            "job_id": "job123",
            "status": "succeeded",
            "submitted_at": "2026-04-21T17:05:12.332000Z",
            "started_at": "2026-04-21T17:05:12.410000Z",
            "finished_at": "2026-04-21T17:05:18.721000Z",
            "result": {
                "status": "ready",
                "model_name": "random_forest",
                "model_version": "v1",
                "artifact_path": "storage/models/v1.joblib",
                "trained_at": "2026-04-21T17:05:18.700000Z",
                "metrics": {"accuracy": 0.82, "f1_score": 0.79},
                "process": {
                    "total_events": 100,
                    "unique_users": 50,
                    "positive_events": 12,
                    "duration_ms": 450,
                    "feature_columns": ["total_events", "positive_events"],
                },
            },
            "error": None,
        },
    )

    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/train/jobs/job123")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "succeeded"
        assert payload["result"]["model_name"] == "random_forest"


def test_simulate_dataset_import_accepts_csv_url(monkeypatch) -> None:
    from app.api.v1.routes import simulation as simulation_route

    monkeypatch.setattr(
        simulation_route.simulation_service,
        "import_retailrocket_dataset",
        lambda **_kwargs: {
            "source_type": "url",
            "source_value": "https://example.com/events.csv",
            "feature_key_mode": "item",
            "sync_features": True,
            "raw_rows_processed": 10,
            "normalized_rows": 10,
            "inserted_rows": 10,
            "features_auto_created": 2,
        },
    )

    with TestClient(app, base_url="http://localhost") as client:
        response = client.post(
            "/simulate",
            data={
                "csv_url": "https://example.com/events.csv",
                "feature_key_mode": "item",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["source_type"] == "url"
        assert payload["inserted_rows"] == 10


def test_simulate_dataset_import_accepts_csv_file(monkeypatch) -> None:
    from app.api.v1.routes import simulation as simulation_route

    monkeypatch.setattr(
        simulation_route.simulation_service,
        "import_retailrocket_dataset",
        lambda **_kwargs: {
            "source_type": "file",
            "source_value": "events.csv",
            "feature_key_mode": "item",
            "sync_features": True,
            "raw_rows_processed": 2,
            "normalized_rows": 2,
            "inserted_rows": 2,
            "features_auto_created": 1,
        },
    )

    with TestClient(app, base_url="http://localhost") as client:
        response = client.post(
            "/simulate",
            data={"feature_key_mode": "item"},
            files={
                "csv_file": (
                    "events.csv",
                    "timestamp,visitorid,event,itemid\n1,1,view,10\n2,2,transaction,11\n",
                    "text/csv",
                )
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["source_type"] == "file"
        assert payload["inserted_rows"] == 2


def test_ingest_events_batch_returns_saved_count(monkeypatch) -> None:
    from app.api.v1.routes import ingest as ingest_route

    monkeypatch.setattr(
        ingest_route.ingest_service,
        "ingest_events",
        lambda **_kwargs: {"saved_events": 2},
    )

    payload = {
        "source": "web_app",
        "events": [
            {
                "user_id": "u123",
                "feature_key": "new_checkout",
                "event_type": "clicked",
                "timestamp": "2026-04-22T10:00:00Z",
                "properties": {"device": "mobile"},
            },
            {
                "user_id": "u124",
                "feature_key": "new_checkout",
                "event_type": "viewed_feature",
                "timestamp": "2026-04-22T10:01:00Z",
                "properties": {"device": "desktop"},
            },
        ],
    }

    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/ingest/events", json=payload)
        assert response.status_code == 201
        assert response.json() == {"saved_events": 2, "rejected": 0}


def test_ingest_events_batch_validates_payload() -> None:
    payload = {"source": "web_app", "events": []}

    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/ingest/events", json=payload)
        assert response.status_code == 422


def test_ingest_events_batch_returns_typed_error(monkeypatch) -> None:
    from app.api.v1.routes import ingest as ingest_route
    from app.core.exceptions import ValidationError

    def _raise(*_args, **_kwargs):
        raise ValidationError("events must contain at least one item.")

    monkeypatch.setattr(ingest_route.ingest_service, "ingest_events", _raise)

    payload = {
        "source": "web_app",
        "events": [
            {
                "user_id": "u123",
                "feature_key": "new_checkout",
                "event_type": "clicked",
                "timestamp": "2026-04-22T10:00:00Z",
                "properties": {"device": "mobile"},
            }
        ],
    }

    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/ingest/events", json=payload)
        assert response.status_code == 400
        body = response.json()
        assert body["detail"]["code"] == "validation_error"


def test_feature_recommendation_endpoint_returns_recommendation(monkeypatch) -> None:
    from app.api.v1.routes import features as features_route

    monkeypatch.setattr(
        features_route.recommendation_service,
        "get_recommendation",
        lambda _feature_key: {
            "feature_key": "new_checkout",
            "current_rollout": 10,
            "recommendation": "increase_rollout",
            "suggested_rollout": 30,
            "reason": "ML-selected users showed higher engagement than random rollout.",
            "metrics": {
                "ml_engagement": 0.2521,
                "rollout_engagement": 0.0269,
                "uplift": 0.2252,
                "coverage": 0.1034,
            },
        },
    )

    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/features/new_checkout/recommendation")
        assert response.status_code == 200
        payload = response.json()
        assert payload["recommendation"] == "increase_rollout"
        assert payload["suggested_rollout"] == 30
