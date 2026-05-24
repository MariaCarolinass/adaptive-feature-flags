from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


EventPropertyValue = str | int | float | bool | None


class CanonicalEventItemIngest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    feature_key: str = Field(min_length=1, max_length=50)
    event_type: str = Field(min_length=1, max_length=50)
    timestamp: datetime
    properties: dict[str, EventPropertyValue] = Field(
        default_factory=dict,
        description=(
            "Arbitrary event properties. Optional operational metrics supported: "
            "`latency_ms` (0-120000), `error_rate` (0-1), `cpu_pct` (0-100), `mem_pct` (0-100)."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "feature_key": "checkout_upsell",
                "event_type": "viewed_feature",
                "timestamp": "2026-05-07T12:00:00Z",
                "properties": {"page": "checkout", "ab_group": "B"},
            }
        }
    )


class CanonicalEventBatchIngest(BaseModel):
    source: str = Field(
        min_length=1,
        max_length=100,
        description="Canonical source identifier independent of vendor-specific schemas.",
    )
    events: list[CanonicalEventItemIngest] = Field(min_length=1, max_length=5000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "web_app",
                "events": [
                    {
                        "user_id": "user_123",
                        "feature_key": "checkout_upsell",
                        "event_type": "view",
                        "timestamp": "2026-05-07T12:00:00Z",
                        "properties": {"page": "checkout"},
                    },
                    {
                        "user_id": "user_123",
                        "feature_key": "checkout_upsell",
                        "event_type": "addtocart",
                        "timestamp": "2026-05-07T12:01:10Z",
                        "properties": {"platform": "ios"},
                    },
                ]
            }
        }
    )


class CanonicalEventBatchIngestResponse(BaseModel):
    saved_events: int
    rejected: int = 0
