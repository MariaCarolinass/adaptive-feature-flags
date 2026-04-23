from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, NotFoundError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import training_job_service, training_service
from app.schemas.model import ModelStatusResponse, TrainJobStartResponse, TrainJobStatusResponse, TrainResponse

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


@router.post(
    "/train/async",
    response_model=TrainJobStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start async training job",
    description="Starts model training in the background and returns a job ID to poll.",
    response_description="Accepted training job.",
)
def train_async():
    try:
        return training_job_service.start()
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to start async training job")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get(
    "/train/jobs/{job_id}",
    response_model=TrainJobStatusResponse,
    summary="Get async training job status",
    description="Returns current state and result/error for an async training job.",
    response_description="Async training job status.",
)
def train_job_status(job_id: str):
    try:
        job = training_job_service.get(job_id)
        if job is None:
            raise NotFoundError("Training job not found.")
        return job
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to retrieve training job status")
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