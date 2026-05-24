from datetime import datetime

from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    feature_key: str = Field(min_length=1, max_length=50)
    primary_metric_event: str = Field(min_length=1, max_length=50)
    min_samples_per_variant: int = Field(default=100, ge=1)
    min_lift: float = Field(default=0.02, ge=0.0, le=1.0)
    enabled: bool = True


class ExperimentResponse(BaseModel):
    id: int
    name: str
    feature_key: str
    primary_metric_event: str
    min_samples_per_variant: int
    min_lift: float
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ExperimentEvaluationResponse(BaseModel):
    experiment_id: int
    experiment_name: str
    feature_key: str
    primary_metric_event: str
    variant_stats: dict
    rate_a: float
    rate_b: float
    lift_b_vs_a: float
    min_lift: float
    min_samples_per_variant: int
    decision: str
