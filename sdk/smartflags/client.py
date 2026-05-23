from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib import request


class SmartFlagsClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def evaluate(self, feature_key: str, user_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "feature_key": feature_key,
            "user": {
                "user_id": user_id,
                **(context or {}),
            },
        }
        return self._post("/evaluate", payload)

    def track(
        self,
        user_id: str,
        feature_key: str,
        event_type: str,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "source": "python_sdk",
            "user_id": user_id,
            "feature_key": feature_key,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "properties": properties or {},
        }
        return self._post("/events", payload)

    def train(self) -> dict[str, Any]:
        return self._post("/train", {})

    def model_status(self) -> dict[str, Any]:
        return self._get("/model/status")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.base_url}{path}",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        return self._send(req)

    def _get(self, path: str) -> dict[str, Any]:
        req = request.Request(
            url=f"{self.base_url}{path}",
            method="GET",
            headers={"Accept": "application/json"},
        )
        return self._send(req)

    def _send(self, req: request.Request) -> dict[str, Any]:
        with request.urlopen(req, timeout=self.timeout) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {}
            return json.loads(body)
