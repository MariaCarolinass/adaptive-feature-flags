from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EventCreate(BaseModel):
    source: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Canonical source system identifier (for example: web_app, retailrocket, datadog).",
    )
    user_id: str = Field(min_length=1, max_length=100, description="User identifier from the source system.")
    feature_key: str = Field(min_length=1, max_length=50, description="Feature key related to this event.")
    event_type: str = Field(min_length=1, max_length=50, description="Event type (for example: view, addtocart, transaction).")
    timestamp: datetime = Field(description="Event timestamp in UTC.")
    properties: dict[str, str | int | float | bool | None] = Field(default_factory=dict, description="Additional event properties.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "257597",
                "feature_key": "item_355908",
                "event_type": "view",
                "timestamp": "2015-06-02T05:02:12.117000Z",
                "source": "retailrocket",
                "properties": {
                    "source": "retailrocket",
                    "raw_itemid": "355908",
                    "raw_event": "view",
                    "transactionid": None
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
                "user_id": "257597",
                "feature_key": "item_355908",
                "event_type": "view",
                "timestamp": "2015-06-02T05:02:12.117000Z",
                "source": "retailrocket",
                "properties": {
                    "source": "retailrocket",
                    "raw_itemid": "355908",
                    "raw_event": "view",
                    "transactionid": None
                },
            }
        }
    )
