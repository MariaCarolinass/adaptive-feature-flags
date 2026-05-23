from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import ingest_service
from app.schemas.event_ingest import CanonicalEventBatchIngest, CanonicalEventBatchIngestResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = get_logger(__name__)


@router.post(
    "/events",
    response_model=CanonicalEventBatchIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest canonical events in batch",
    description="Receives canonical batch events from any external source.",
    response_description="Number of successfully saved events.",
)
def ingest_events(payload: CanonicalEventBatchIngest):
    try:
        result = ingest_service.ingest_events(
            source=payload.source,
            events=[event.model_dump() for event in payload.events],
        )
        return {"saved_events": result["saved_events"], "rejected": 0}
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to ingest events")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
