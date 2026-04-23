from pydantic import BaseModel, ConfigDict


class SimulateDatasetResponse(BaseModel):
    source_type: str
    source_value: str
    feature_key_mode: str
    sync_features: bool
    raw_rows_processed: int
    normalized_rows: int
    inserted_rows: int
    features_auto_created: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_type": "url",
                "source_value": "https://example.com/events.csv",
                "feature_key_mode": "item",
                "sync_features": True,
                "raw_rows_processed": 10000,
                "normalized_rows": 9750,
                "inserted_rows": 9750,
                "features_auto_created": 240,
            }
        }
    )