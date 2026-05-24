from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TrainProcessInfo(BaseModel):
    total_events: int
    unique_users: int
    positive_events: int
    duration_ms: int
    feature_columns: list[str]
    benchmark: list[dict[str, Any]]
    dataset_profile: dict[str, Any]


class TrainResponse(BaseModel):
    status: str
    model_name: str
    model_version: str
    artifact_path: str
    trained_at: datetime
    metrics: dict[str, Any]
    process: TrainProcessInfo

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "model_name": "random_forest",
                "model_version": "v1",
                "artifact_path": "storage/models/v1.joblib",
                "trained_at": "2015-06-02T05:02:12.117000Z",
                "metrics": {
                    "accuracy": 0.82,
                    "precision": 0.78,
                    "recall": 0.76,
                    "f1_score": 0.77,
                    "roc_auc": 0.84,
                    "confusion_matrix": {
                        "true_negative": 1200,
                        "false_positive": 220,
                        "false_negative": 180,
                        "true_positive": 640
                    }
                },
                "process": {
                    "total_events": 2756101,
                    "unique_users": 1407580,
                    "positive_events": 193634,
                    "duration_ms": 4280,
                    "feature_columns": ["total_events", "positive_events"],
                    "benchmark": [
                        {"model_name": "random_forest", "f1_score": 0.77},
                        {"model_name": "logistic_regression", "f1_score": 0.72}
                    ],
                    "dataset_profile": {
                        "rows": 2400,
                        "train_rows": 1920,
                        "test_rows": 480,
                        "positive_rate": 0.33,
                        "class_distribution": {"0": 1600, "1": 800}
                    }
                },
            }
        }
    )


class ModelStatusResponse(BaseModel):
    status: str
    model_name: str | None = None
    model_version: str | None = None
    trained_at: datetime | None = None
    metrics: dict[str, Any] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "model_name": "random_forest",
                "model_version": "v1",
                "trained_at": "2026-04-21T17:00:00Z",
                "metrics": {"accuracy": 0.82, "f1_score": 0.79, "roc_auc": 0.84},
            }
        }
    )
