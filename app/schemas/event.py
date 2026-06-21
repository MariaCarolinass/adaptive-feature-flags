from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EventCreate(BaseModel):
    source: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Identificador da origem da atividade, como web_app, mobile_app ou email_campaign.",
    )
    user_id: str = Field(min_length=1, max_length=100, description="Identificador do usuário.")
    feature_key: str = Field(min_length=1, max_length=50, description="Identificador da regra relacionada à atividade.")
    event_type: str = Field(min_length=1, max_length=50, description="Identificador técnico da atividade.")
    timestamp: datetime = Field(description="Data e hora da atividade em UTC.")
    properties: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict,
        description=(
            "Propriedades adicionais da atividade. Suporta a métrica operacional opcional "
            "`latency_ms`."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "feature_key": "checkout_upsell",
                "event_type": "checkout_upsell_shown",
                "timestamp": "2026-05-23T12:00:00Z",
                "source": "web_app",
                "properties": {
                    "activity_name": "Viu oferta no checkout",
                    "page": "cart"
                }
            }
        }
    )


class EventResponse(BaseModel):
    id: int
    source: str | None = None
    user_id: str
    feature_key: str
    event_type: str
    timestamp: datetime
    properties: dict[str, str | int | float | bool | None]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 10,
                "user_id": "user_123",
                "feature_key": "checkout_upsell",
                "event_type": "checkout_upsell_shown",
                "timestamp": "2026-05-23T12:00:00Z",
                "source": "web_app",
                "properties": {
                    "activity_name": "Viu oferta no checkout",
                    "page": "cart"
                },
            }
        }
    )
