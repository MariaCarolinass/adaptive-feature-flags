from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import evaluation_service
from app.schemas.evaluate import EvaluateRequest, EvaluateResponse

router = APIRouter(prefix="/evaluate", tags=["evaluation"])
logger = get_logger(__name__)


@router.post("", response_model=EvaluateResponse)
def evaluate(request: EvaluateRequest):
    try:
        return evaluation_service.evaluate(
            feature_key=request.feature_key,
            user=request.user,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao avaliar feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")