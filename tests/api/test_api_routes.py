from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_root_serves_ui_index() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "<!doctype html>" in response.text.lower()


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


def test_evaluations_endpoint_lists_backend_history(monkeypatch) -> None:
    from app.api.v1.routes import evaluations as evaluations_route

    class _Service:
        def list_recent(self, limit: int = 1000):
            return [
                {
                    "id": 1,
                    "created_at": "2026-06-04T14:19:00+00:00",
                    "feature_key": "new_checkout",
                    "user_id": "u1",
                    "enabled": True,
                    "decision_source": "ml",
                    "score": 0.91,
                    "threshold": 0.2,
                    "threshold_mode": "fixed",
                    "experiment": None,
                    "model_version": "v1",
                }
            ]

        def clear_history(self) -> int:
            return 1

    monkeypatch.setattr(evaluations_route, "evaluation_service", _Service())

    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/evaluations")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["user_id"] == "u1"

        cleared = client.delete("/evaluations")
        assert cleared.status_code == 200
        assert cleared.json() == {"deleted": 1}


def test_security_headers_present() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("referrer-policy") == "no-referrer"


def test_ingest_events_batch_returns_saved_count(monkeypatch) -> None:
    from app.api.v1.routes import ingest as ingest_route

    monkeypatch.setattr(
        ingest_route.ingest_service,
        "ingest_events",
        lambda **_kwargs: {"saved_events": 2, "rejected": 0},
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
        assert body["detail"]["message"] == "events must contain at least one item."


def test_metrics_endpoint_returns_snapshot() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        payload = response.json()
        assert "counters" in payload
        assert "gauges" in payload
        assert "timings_ms" in payload
