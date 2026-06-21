from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class EvaluateUser(BaseModel):
    user_id: str = Field(description="Identificador do usuário.")
    age: int | None = Field(default=None, ge=0, le=120)
    country: str | None = None
    plan: str | None = None
    days_since_signup: int | None = Field(default=None, ge=0)


class EvaluateRequest(BaseModel):
    feature_key: str = Field(description="Identificador da regra avaliada.")
    user: EvaluateUser

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feature_key": "checkout_upsell",
                "user": {
                    "user_id": "user_123"
                }
            }
        }
    )


class EvaluateResponse(BaseModel):
    feature_key: str
    user_id: str
    activity: str | None = Field(default=None, description="Identificador da atividade da regra avaliada.")
    enabled: bool
    decision_source: str = Field(description="Origem da decisão, como ml, rollout, feature_disabled ou feature_not_found.")
    score: float | None = Field(default=None, description="Pontuação calculada pela decisão assistida por modelo.")
    threshold: float | None = Field(default=None, description="Pontuação mínima usada para liberar a regra.")
    threshold_mode: str | None = Field(default=None, description="Modo de liberação aplicado na decisão.")
    experiment: dict | None = Field(default=None, description="Contexto do teste associado à avaliação, quando houver.")
    model_version: str | None = Field(default=None, description="Versão do modelo usada na decisão.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feature_key": "checkout_upsell",
                "user_id": "user_123",
                "activity": "checkout_upsell_shown",
                "enabled": True,
                "decision_source": "ml",
                "score": 0.81,
                "threshold": 0.2,
                "threshold_mode": "fixed",
                "experiment": {
                    "experiment_id": 1,
                    "experiment_name": "Checkout Upsell A/B",
                    "variant": "B"
                },
                "model_version": "v1",
            }
        }
    )


class EvaluationHistoryItem(EvaluateResponse):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 12,
                "created_at": "2026-06-04T14:19:00+00:00",
                "feature_key": "checkout_upsell",
                "user_id": "user_123",
                "activity": "checkout_upsell_shown",
                "enabled": True,
                "decision_source": "ml",
                "score": 0.81,
                "threshold": 0.2,
                "threshold_mode": "fixed",
                "experiment": {
                    "experiment_id": 1,
                    "experiment_name": "Checkout Upsell A/B",
                    "variant": "B"
                },
                "model_version": "v1",
            }
        }
    )
