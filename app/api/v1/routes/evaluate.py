from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import evaluation_service
from app.schemas.evaluate import EvaluateRequest, EvaluateResponse

router = APIRouter(prefix="/evaluate", tags=["evaluation"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=EvaluateResponse,
    summary="Evaluate feature for user",
    description=(
        "Fast user-level decision endpoint.\n\n"
        "Evaluates whether a feature should be enabled for a single user.\n"
        "This endpoint is optimized for low latency and does not train models.\n\n"
        "- Tries model score when `ml_enabled=true` and model status is `ready`\n"
        "- Falls back to deterministic rollout when scoring is unavailable"
    ),
    response_description="Feature evaluation result.",
)
def evaluate(request: EvaluateRequest):
    try:
        return evaluation_service.evaluate(
            feature_key=request.feature_key,
            user=request.user.model_dump(),
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to evaluate feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
