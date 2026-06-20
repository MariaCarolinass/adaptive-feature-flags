from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FeatureCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100, description="Nome legível da regra.")
    key: str = Field(min_length=3, max_length=50, description="Identificador técnico da regra usado na API e na avaliação.")
    description: str | None = Field(default=None, max_length=500, description="Descrição curta opcional da regra.")
    enabled: bool = Field(default=True, description="Indica se a regra está ativa.")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Percentual de liberação gradual da regra.")
    ml_enabled: bool = Field(default=False, description="Se verdadeiro, tenta usar machine learning quando o modelo estiver pronto.")
    ml_threshold_mode: str = Field(
        default="fixed",
        pattern="^(fixed|match_rollout|maximize_f1)$",
        description="Modo de liberação usado na avaliação: limite fixo, acompanhar cobertura ou automática.",
    )
    ml_threshold_value: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Pontuação mínima usada quando o modo é limite fixo.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Novo checkout",
                "key": "new_checkout",
                "description": "Versão nova do checkout",
                "enabled": True,
                "rollout_percentage": 25,
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
                "name": "Novo checkout",
                "key": "new_checkout",
                "description": "Versão nova do checkout",
                "enabled": True,
                "rollout_percentage": 25,
                "ml_enabled": True,
                "ml_threshold_mode": "match_rollout",
                "ml_threshold_value": 0.1,
                "created_at": "2015-06-02T05:02:12.117000Z",
                "updated_at": "2015-06-02T05:02:12.117000Z",
            }
        }
    )
