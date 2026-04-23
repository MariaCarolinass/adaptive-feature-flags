from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TrainProcessInfo(BaseModel):
    total_events: int
    unique_users: int
    positive_events: int
    duration_ms: int
    feature_columns: list[str]


class TrainResponse(BaseModel):
    status: str
    model_name: str
    model_version: str
    artifact_path: str
    trained_at: datetime
    metrics: dict[str, float]
    process: TrainProcessInfo

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "model_name": "random_forest",
                "model_version": "v1",
                "artifact_path": "storage/models/v1.joblib",
                "trained_at": "2015-06-02T05:02:12.117000Z",
                "metrics": {"accuracy": 0.82, "f1_score": 0.79},
                "process": {
                    "total_events": 2756101,
                    "unique_users": 1407580,
                    "positive_events": 193634,
                    "duration_ms": 4280,
                    "feature_columns": ["total_events", "positive_events"],
                },
            }
        }
    )


class ModelStatusResponse(BaseModel):
    status: str
    model_name: str | None = None
    model_version: str | None = None
    trained_at: datetime | None = None
    metrics: dict[str, float] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "model_name": "random_forest",
                "model_version": "v1",
                "trained_at": "2026-04-21T17:00:00Z",
                "metrics": {"accuracy": 0.82, "f1_score": 0.79},
            }
        }
    )


class TrainJobStartResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "7f01a2a10b1b4f7b96f8f6f8c4d9a123",
                "status": "queued",
                "submitted_at": "2026-04-21T17:05:12.332000Z",
            }
        }
    )


class TrainJobStatusResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: TrainResponse | None = None
    error: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "7f01a2a10b1b4f7b96f8f6f8c4d9a123",
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
                        "total_events": 2756101,
                        "unique_users": 1407580,
                        "positive_events": 193634,
                        "duration_ms": 6290,
                        "feature_columns": ["total_events", "positive_events"],
                    },
                },
                "error": None,
            }
        }
    )