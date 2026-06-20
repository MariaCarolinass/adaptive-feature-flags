from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.dependencies import metrics_sink

router = APIRouter(prefix="/metrics", tags=["Observabilidade"])
logger = get_logger(__name__)


@router.get(
    "",
    summary="Ver métricas em memória",
    description="Retorna contadores, gauges e tempos armazenados no coletor de métricas em memória.",
)
def get_metrics():
    try:
        return metrics_sink.snapshot()
    except Exception:
        logger.exception("Failed to retrieve metrics snapshot")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
