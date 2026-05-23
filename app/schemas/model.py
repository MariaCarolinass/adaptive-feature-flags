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
