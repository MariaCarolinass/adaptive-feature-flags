from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import simulation_service
from app.schemas.simulation import SimulateDatasetResponse

router = APIRouter(prefix="/simulate", tags=["simulation"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=SimulateDatasetResponse,
    summary="Import or simulate dataset from CSV",
    description=(
        "Imports dataset rows from a CSV source into `events` for test simulations.\n\n"
        "- Send exactly one source: `csv_url` OR `csv_file`\n"
        "- Required CSV columns: `timestamp`, `visitorid`, `event`, `itemid`\n"
        "- Compatible with Retailrocket `events.csv` format"
    ),
    response_description="Import summary with processed and inserted row counts.",
)
async def simulate_dataset(
    csv_url: str | None = Form(default=None, description="Public URL to a CSV dataset."),
    csv_file: UploadFile | None = File(default=None, description="CSV file upload."),
    feature_key_mode: str = Form(
        default="item",
        description="'item' maps to item_<itemid>, 'single' maps all to retailrocket_import.",
    ),
    limit: int | None = Form(default=None, description="Optional max number of rows to process."),
    chunk_size: int = Form(default=200000, description="CSV rows processed per chunk."),
    batch_size: int = Form(default=10000, description="Rows inserted per DB transaction batch."),
    sync_features: bool = Form(default=True, description="Auto-create missing features from imported keys."),
    feature_rollout_percentage: int = Form(
        default=10,
        description="Default rollout percentage for auto-created features (0-100).",
    ),
    feature_ml_enabled: bool = Form(
        default=True,
        description="Whether auto-created features should have ml_enabled=true.",
    ),
):
    try:
        csv_bytes = await csv_file.read() if csv_file is not None else None
        return simulation_service.import_retailrocket_dataset(
            csv_url=csv_url,
            csv_file_bytes=csv_bytes,
            csv_file_name=csv_file.filename if csv_file else None,
            feature_key_mode=feature_key_mode,
            limit=limit,
            chunk_size=chunk_size,
            batch_size=batch_size,
            sync_features_enabled=sync_features,
            feature_rollout_percentage=feature_rollout_percentage,
            feature_ml_enabled=feature_ml_enabled,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to import simulation dataset")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")