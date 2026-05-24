from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, NotFoundError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import experiment_service
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentEvaluationResponse,
    ExperimentResponse,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create A/B-lite experiment",
)
def create_experiment(payload: ExperimentCreate):
    try:
        return experiment_service.create_experiment(**payload.model_dump())
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to create experiment")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get(
    "",
    response_model=list[ExperimentResponse],
    summary="List experiments",
)
def list_experiments():
    try:
        return experiment_service.list_experiments()
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to list experiments")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get(
    "/{experiment_id}/result",
    response_model=ExperimentEvaluationResponse,
    summary="Evaluate A/B-lite experiment",
)
def evaluate_experiment(experiment_id: int):
    try:
        result = experiment_service.evaluate_experiment(experiment_id)
        if result is None:
            raise NotFoundError("Experiment not found.")
        return result
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to evaluate experiment")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
