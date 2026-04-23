from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FeatureCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100, description="Human-friendly feature name.")
    key: str = Field(min_length=3, max_length=50, description="Unique feature key used in evaluation.")
    description: str | None = Field(default=None, max_length=500, description="Optional feature description.")
    enabled: bool = Field(default=True, description="Global feature toggle.")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Rollout percentage when ML is not used.")
    ml_enabled: bool = Field(default=False, description="If true, tries ML scoring when a model is ready.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Retailrocket Item 355908",
                "key": "item_355908",
                "description": "Feature linked to Retailrocket item 355908",
                "enabled": True,
                "rollout_percentage": 35,
                "ml_enabled": True
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
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Retailrocket Item 355908",
                "key": "item_355908",
                "description": "Feature linked to Retailrocket item 355908",
                "enabled": True,
                "rollout_percentage": 35,
                "ml_enabled": True,
                "created_at": "2015-06-02T05:02:12.117000Z",
                "updated_at": "2015-06-02T05:02:12.117000Z",
            }
        }
    )