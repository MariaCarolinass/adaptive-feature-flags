from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120, description="Nome do teste.")
    feature_key: str = Field(min_length=1, max_length=50, description="Identificador da regra avaliada.")
    primary_metric_event: str = Field(min_length=1, max_length=50, description="Identificador da atividade principal usada como sucesso.")
    min_samples_per_variant: int = Field(default=100, ge=1, description="Número mínimo de registros por variante antes de decidir.")
    min_lift: float = Field(default=0.02, ge=0.0, le=1.0, description="Diferença mínima entre A e B para encerrar o teste.")
    enabled: bool = Field(default=True, description="Indica se o teste está ativo.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Novo checkout A/B",
                "feature_key": "new_checkout",
                "primary_metric_event": "viewed_feature",
                "min_samples_per_variant": 100,
                "min_lift": 0.02,
                "enabled": True,
            }
        }
    )


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Novo checkout A/B",
                "feature_key": "new_checkout",
                "primary_metric_event": "viewed_feature",
                "min_samples_per_variant": 100,
                "min_lift": 0.02,
                "enabled": True,
                "created_at": "2026-06-19T12:00:00Z",
                "updated_at": "2026-06-19T12:00:00Z",
            }
        }
    )


class ExperimentEvaluationResponse(BaseModel):
    experiment_id: int
    experiment_name: str
    feature_key: str
    primary_metric_event: str
    variant_stats: dict
    user_stats: dict | None = None
    rate_a: float
    rate_b: float
    lift_b_vs_a: float
    min_lift: float
    min_samples_per_variant: int
    decision: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_id": 1,
                "experiment_name": "Novo checkout A/B",
                "feature_key": "new_checkout",
                "primary_metric_event": "viewed_feature",
                "variant_stats": {
                    "A": {"samples": 120, "positives": 40},
                    "B": {"samples": 118, "positives": 54}
                },
                "user_stats": {
                    "A": {"users": 88},
                    "B": {"users": 85}
                },
                "rate_a": 0.3333,
                "rate_b": 0.4576,
                "lift_b_vs_a": 0.1243,
                "min_lift": 0.02,
                "min_samples_per_variant": 100,
                "decision": "continue",
            }
        }
    )
