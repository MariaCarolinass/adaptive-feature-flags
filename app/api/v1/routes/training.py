from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import training_service
from app.schemas.model import ModelStatusResponse, TrainResponse

router = APIRouter(tags=["model"])
logger = get_logger(__name__)


@router.post(
    "/train",
    response_model=TrainResponse,
    summary="Train model",
    description="Trains the ML model using persisted events and returns process details.",
    response_description="Training result with model metadata and process information.",
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
    summary="Get model status",
    description="Returns current model status and metrics from the latest training.",
    response_description="Current model status.",
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
    summary="List training runs",
    description="Returns recent model training snapshots for governance and audit.",
)
def list_runs(limit: int = 20):
    try:
        return {"runs": training_service.list_training_runs(limit=limit)}
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to retrieve training runs")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
