from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FeatureCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100, description="Human-friendly feature name.")
    key: str = Field(min_length=3, max_length=50, description="Unique feature key used in evaluation.")
    description: str | None = Field(default=None, max_length=500, description="Optional feature description.")
    enabled: bool = Field(default=True, description="Global feature toggle.")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Rollout percentage when ML is not used.")
    ml_enabled: bool = Field(default=False, description="If true, tries ML scoring when a model is ready.")
    ml_threshold_mode: str = Field(
        default="fixed",
        pattern="^(fixed|match_rollout|maximize_f1)$",
        description="ML decision threshold mode: fixed value or rollout-matched heuristic.",
    )
    ml_threshold_value: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Fixed threshold value used when ml_threshold_mode=fixed.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "e-commerce dataset Item 355908",
                "key": "item_355908",
                "description": "Feature linked to e-commerce dataset item 355908",
                "enabled": True,
                "rollout_percentage": 35,
                "ml_enabled": True,
                "ml_threshold_mode": "fixed",
                "ml_threshold_value": 0.2,
            }
        }
    )


class FeatureResponse(BaseModel):
    id: int
    name: str
    key: str
    description: str | None
    enabled: bool
    rollout_percentage: int
    ml_enabled: bool
    ml_threshold_mode: str
    ml_threshold_value: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "e-commerce dataset Item 355908",
                "key": "item_355908",
                "description": "Feature linked to e-commerce dataset item 355908",
                "enabled": True,
                "rollout_percentage": 35,
                "ml_enabled": True,
                "ml_threshold_mode": "match_rollout",
                "ml_threshold_value": 0.1,
                "created_at": "2015-06-02T05:02:12.117000Z",
                "updated_at": "2015-06-02T05:02:12.117000Z",
            }
        }
    )
