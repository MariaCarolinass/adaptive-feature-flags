from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, NotFoundError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import feature_service
from app.schemas.feature import FeatureCreate, FeatureResponse

router = APIRouter(prefix="/features", tags=["features"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=FeatureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create feature",
    description="Creates a new feature flag.",
    response_description="Feature created successfully.",
)
def create(request: FeatureCreate):
    try:
        return feature_service.create_feature(
            name=request.name,
            key=request.key,
            description=request.description,
            enabled=request.enabled,
            rollout_percentage=request.rollout_percentage,
            ml_enabled=request.ml_enabled,
            ml_threshold_mode=request.ml_threshold_mode,
            ml_threshold_value=request.ml_threshold_value,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to create feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

@router.get(
    "/{feature_id}",
    response_model=FeatureResponse,
    summary="Get feature by ID",
    description="Returns an existing feature by ID.",
    response_description="Feature found.",
)
def retrieve(feature_id: int):
    try:
        feature = feature_service.get_feature_by_id(feature_id)
        if feature is None:
            raise NotFoundError("Feature not found.")
        return feature
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to retrieve feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.put(
    "/{feature_id}",
    response_model=FeatureResponse,
    summary="Update feature",
    description="Updates an existing feature.",
    response_description="Feature updated.",
)
def update(feature_id: int, request: FeatureCreate):
    try:
        return feature_service.update_feature(
            feature_id=feature_id,
            name=request.name,
            key=request.key,
            description=request.description,
            enabled=request.enabled,
            rollout_percentage=request.rollout_percentage,
            ml_enabled=request.ml_enabled,
            ml_threshold_mode=request.ml_threshold_mode,
            ml_threshold_value=request.ml_threshold_value,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to update feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.delete(
    "/{feature_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete feature",
    description="Deletes an existing feature.",
)
def delete(feature_id: int):
    try:
        feature_service.delete_feature(feature_id)
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to delete feature")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

@router.get(
    "",
    response_model=list[FeatureResponse],
    summary="List features",
    description="Lists all features ordered by creation time.",
    response_description="Feature list.",
)
def list():
    try:
        return feature_service.list_features()
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to list features")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
