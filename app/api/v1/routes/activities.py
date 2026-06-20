from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, NotFoundError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import activity_service
from app.schemas.activity import ActivityCreate, ActivityResponse

router = APIRouter(prefix="/activities", tags=["Catálogo de atividades"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar atividade",
    description="Cria uma atividade no catálogo usado pela UI e pelos eventos.",
    response_description="Atividade criada com sucesso.",
)
def create(request: ActivityCreate):
    try:
        return activity_service.create_activity(
            key=request.key,
            name=request.name,
            description=request.description,
            enabled=request.enabled,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to create activity")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
    summary="Buscar atividade por ID",
    description="Retorna uma atividade existente pelo ID.",
    response_description="Atividade encontrada.",
)
def retrieve(activity_id: int):
    try:
        activity = activity_service.get_activity_by_id(activity_id)
        if activity is None:
            raise NotFoundError("Activity not found.")
        return activity
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to retrieve activity")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.put(
    "/{activity_id}",
    response_model=ActivityResponse,
    summary="Atualizar atividade",
    description="Atualiza uma atividade existente.",
    response_description="Atividade atualizada.",
)
def update(activity_id: int, request: ActivityCreate):
    try:
        return activity_service.update_activity(
            activity_id=activity_id,
            key=request.key,
            name=request.name,
            description=request.description,
            enabled=request.enabled,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to update activity")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover atividade",
    description="Remove uma atividade existente.",
)
def delete(activity_id: int):
    try:
        activity_service.delete_activity(activity_id)
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to delete activity")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get(
    "",
    response_model=list[ActivityResponse],
    summary="Listar atividades",
    description="Lista todas as atividades ordenadas por criação.",
    response_description="Lista de atividades.",
)
def list():
    try:
        return activity_service.list_activities()
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to list activities")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
