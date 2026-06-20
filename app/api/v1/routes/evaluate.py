from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import evaluation_service
from app.schemas.evaluate import EvaluateRequest, EvaluateResponse

router = APIRouter(prefix="/evaluate", tags=["Avaliação"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=EvaluateResponse,
    summary="Avaliar regra para usuário",
    description=(
        "Endpoint rápido de decisão por usuário.\n\n"
        "Avalia se uma regra deve ser liberada para um único usuário.\n"
        "O endpoint é otimizado para baixa latência e não treina modelos.\n\n"
        "- Tenta usar a pontuação do modelo quando `ml_enabled=true` e a situação do modelo é `ready`\n"
        "- Cai para liberação gradual determinística quando a pontuação não está disponível"
    ),
    response_description="Resultado da avaliação da regra.",
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
