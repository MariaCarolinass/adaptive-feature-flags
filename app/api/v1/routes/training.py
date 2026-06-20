from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import training_service
from app.schemas.model import ModelStatusResponse, TrainResponse

router = APIRouter(tags=["Modelo"])
logger = get_logger(__name__)


@router.post(
    "/train",
    response_model=TrainResponse,
    summary="Treinar modelo",
    description="Treina o modelo usando as atividades persistidas e retorna os detalhes do processo.",
    response_description="Resultado do treino com metadados do modelo e informações do processo.",
)
def train():
    try:
        return training_service.train()
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to train model")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get(
    "/model/status",
    response_model=ModelStatusResponse,
    summary="Situação do modelo",
    description="Retorna a situação atual do modelo e as métricas do último treino.",
    response_description="Situação atual do modelo.",
)
def status():
    try:
        return training_service.get_status()
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to retrieve model status")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get(
    "/model/runs",
    summary="Listar treinamentos recentes",
    description="Retorna os snapshots recentes de treino para governança e auditoria.",
)
def list_runs(limit: int = 20):
    try:
        return {"runs": training_service.list_training_runs(limit=limit)}
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to retrieve training runs")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
