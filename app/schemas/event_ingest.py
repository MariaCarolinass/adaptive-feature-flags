from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


EventPropertyValue = str | int | float | bool | None


class CanonicalEventItemIngest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100, description="Identificador do usuário.")
    feature_key: str = Field(min_length=1, max_length=50, description="Identificador da regra associada.")
    event_type: str = Field(min_length=1, max_length=50, description="Identificador técnico da atividade.")
    timestamp: datetime = Field(description="Data e hora da atividade em UTC.")
    properties: dict[str, EventPropertyValue] = Field(
        default_factory=dict,
        description=(
            "Propriedades adicionais da atividade. Métricas operacionais opcionais suportadas: "
            "`latency_ms` (0-120000), `error_rate` (0-1), `cpu_pct` (0-100), `mem_pct` (0-100)."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "feature_key": "new_checkout",
                "event_type": "viewed_feature",
                "timestamp": "2026-05-07T12:00:00Z",
                "properties": {"activity_name": "Visualizou a funcionalidade", "page": "checkout"},
            }
        }
    )


class CanonicalEventBatchIngest(BaseModel):
    source: str = Field(
        min_length=1,
        max_length=100,
        description="Identificador da origem da atividade, independente do formato do sistema externo.",
    )
    events: list[CanonicalEventItemIngest] = Field(min_length=1, max_length=5000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "web_app",
                "events": [
                    {
                        "user_id": "user_123",
                        "feature_key": "new_checkout",
                        "event_type": "viewed_feature",
                        "timestamp": "2026-05-07T12:00:00Z",
                        "properties": {"activity_name": "Visualizou a funcionalidade", "page": "checkout"},
                    },
                    {
                        "user_id": "user_123",
                        "feature_key": "new_checkout",
                        "event_type": "addtocart",
                        "timestamp": "2026-05-07T12:01:10Z",
                        "properties": {"activity_name": "Adição ao carrinho", "platform": "ios"},
                    },
                ]
            }
        }
    )


class CanonicalEventBatchIngestResponse(BaseModel):
    saved_events: int
    rejected: int = 0
