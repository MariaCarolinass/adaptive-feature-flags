from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


EventPropertyValue = str | int | float | bool | None
MAX_INGEST_BATCH_SIZE = 1000


class CanonicalEventItemIngest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100, description="Identificador do usuário.")
    feature_key: str = Field(min_length=1, max_length=50, description="Identificador da regra associada.")
    event_type: str = Field(min_length=1, max_length=50, description="Identificador técnico da atividade.")
    timestamp: datetime = Field(description="Data e hora da atividade em UTC.")
    properties: dict[str, EventPropertyValue] = Field(
        default_factory=dict,
        description=(
            "Propriedades adicionais da atividade. Métrica operacional opcional suportada: "
            "`latency_ms` (0-120000)."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "feature_key": "checkout_upsell",
                "event_type": "checkout_upsell_shown",
                "timestamp": "2026-05-07T12:00:00Z",
                "properties": {"activity_name": "Viu oferta no checkout", "page": "cart"},
            }
        }
    )


class CanonicalEventBatchIngest(BaseModel):
    source: str = Field(
        min_length=1,
        max_length=100,
        description="Identificador da origem da atividade, independente do formato do sistema externo.",
    )
    events: list[CanonicalEventItemIngest] = Field(
        min_length=1,
        max_length=MAX_INGEST_BATCH_SIZE,
        description=f"Lista de atividades em lote. Limite máximo de {MAX_INGEST_BATCH_SIZE} itens por requisição.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "web_app",
                "events": [
                    {
                        "user_id": "user_123",
                        "feature_key": "checkout_upsell",
                        "event_type": "checkout_upsell_shown",
                        "timestamp": "2026-05-07T12:00:00Z",
                        "properties": {"activity_name": "Viu oferta no checkout", "page": "cart"},
                    },
                    {
                        "user_id": "user_123",
                        "feature_key": "checkout_upsell",
                        "event_type": "checkout_upsell_clicked",
                        "timestamp": "2026-05-07T12:01:10Z",
                        "properties": {"activity_name": "Clicou na oferta do checkout", "platform": "ios"},
                    },
                ]
            }
        }
    )


class CanonicalEventBatchIngestResponse(BaseModel):
    saved_events: int
    rejected: int = 0
