from pydantic import BaseModel, Field, ConfigDict


class EvaluateUser(BaseModel):
    user_id: str = Field(description="User identifier.")
    age: int | None = Field(default=None, ge=0, le=120)
    country: str | None = None
    plan: str | None = None
    days_since_signup: int | None = Field(default=None, ge=0)


class EvaluateRequest(BaseModel):
    feature_key: str = Field(description="Feature key to evaluate for the user.")
    user: EvaluateUser

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feature_key": "item_355908",
                "user": {
                    "user_id": "257597"
                }
            }
        }
    )


class EvaluateResponse(BaseModel):
    feature_key: str
    user_id: str
    enabled: bool
    decision_source: str
    score: float | None = None
    threshold: float | None = None
    threshold_mode: str | None = None
    experiment: dict | None = None
    model_version: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feature_key": "item_355908",
                "user_id": "257597",
                "enabled": True,
                "decision_source": "ml",
                "score": 0.81,
                "threshold": 0.2,
                "threshold_mode": "fixed",
                "experiment": {
                    "experiment_id": 1,
                    "experiment_name": "Checkout CTA A/B",
                    "variant": "B"
                },
                "model_version": "v1",
            }
        }
    )
