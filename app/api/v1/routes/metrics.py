from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.dependencies import metrics_sink

router = APIRouter(prefix="/metrics", tags=["observability"])
logger = get_logger(__name__)


@router.get(
    "",
    summary="Get in-memory metrics snapshot",
    description="Returns process-level counters, gauges and timings currently stored in the in-memory metrics sink.",
)
def get_metrics():
    try:
        return metrics_sink.snapshot()
    except Exception:
        logger.exception("Failed to retrieve metrics snapshot")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
