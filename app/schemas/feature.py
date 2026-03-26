from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class FeatureCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    key: str = Field(min_length=3, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    enabled: bool = True
    rollout_percentage: int = Field(default=0, ge=0, le=100)
    ml_enabled: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Nova Home",
                "key": "new_home",
                "description": "Nova experiência da home",
                "enabled": True,
                "rollout_percentage": 20,
                "ml_enabled": True
            }
        }
    )


class FeatureResponse(BaseModel):
    id: UUID
    name: str
    key: str
    description: str | None
    enabled: bool
    rollout_percentage: int
    ml_enabled: bool
    created_at: datetime
    updated_at: datetime