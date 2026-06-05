from fastapi import APIRouter, HTTPException, Query, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import evaluation_service
from app.schemas.evaluate import EvaluationHistoryItem

router = APIRouter(prefix="/evaluations", tags=["evaluation-history"])
logger = get_logger(__name__)


@router.get(
    "",
    response_model=list[EvaluationHistoryItem],
    summary="List recent evaluations",
    description="Returns the most recent saved feature evaluations from the backend store.",
)
def list_evaluations(limit: int = Query(default=1000, ge=1, le=1000)):
    try:
        return evaluation_service.list_recent(limit=limit)
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to list evaluations")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.delete(
    "",
    summary="Clear evaluation history",
    description="Deletes all stored evaluation history records.",
)
def clear_evaluations():
    try:
        deleted = evaluation_service.clear_history()
        return {"deleted": deleted}
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to clear evaluations")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
