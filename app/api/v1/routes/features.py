from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, NotFoundError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import feature_service
from app.schemas.feature import FeatureCreate, FeatureResponse

router = APIRouter(prefix="/features", tags=["features"])
logger = get_logger(__name__)


@router.post("", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
def create(request: FeatureCreate):
    try:
        return feature_service.create_feature(
            name=request.name,
            key=request.key,
            description=request.description,
            enabled=request.enabled,
            rollout_percentage=request.rollout_percentage,
            ml_enabled=request.ml_enabled,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao criar feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

@router.get("/{feature_id}", response_model=FeatureResponse)
def retrieve(feature_id: UUID):
    try:
        feature = feature_service.get_feature_by_id(feature_id)
        if feature is None:
            raise NotFoundError("Feature not found.")
        return feature
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao buscar feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.put("/{feature_id}", response_model=FeatureResponse)
def update(feature_id: UUID, request: FeatureCreate):
    try:
        return feature_service.update_feature(
            feature_id=feature_id,
            name=request.name,
            key=request.key,
            description=request.description,
            enabled=request.enabled,
            rollout_percentage=request.rollout_percentage,
            ml_enabled=request.ml_enabled,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao atualizar feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(feature_id: UUID):
    try:
        feature_service.delete_feature(feature_id)
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao remover feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

@router.get("", response_model=list[FeatureResponse])
def list():
    try:
        return feature_service.list_features()
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao listar features")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")