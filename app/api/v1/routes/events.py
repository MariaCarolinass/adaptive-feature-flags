from fastapi import APIRouter, HTTPException, Query, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import event_service
from app.schemas.event import EventCreate, EventResponse

router = APIRouter(prefix="/events", tags=["Atividades"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar atividade",
    description="Registra uma atividade individual para uma regra.",
    response_description="Atividade registrada com sucesso.",
)
def create(event: EventCreate):
    try:
        return event_service.create_event(
            user_id=event.user_id,
            feature_key=event.feature_key,
            event_type=event.event_type,
            timestamp=event.timestamp,
            properties=event.properties,
            source=event.source,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to create event")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get(
    "",
    response_model=list[EventResponse],
    summary="Listar atividades",
    description="Lista atividades com filtros opcionais por usuário, regra e identificador da atividade.",
    response_description="Lista de atividades filtradas.",
)
def list(
    user_id: str | None = Query(default=None, description="Filtrar por usuário."),
    feature_key: str | None = Query(default=None, description="Filtrar por regra."),
    event_type: str | None = Query(default=None, description="Filtrar pelo identificador da atividade."),
):
    try:
        return event_service.list_events(
            user_id=user_id,
            feature_key=feature_key,
            event_type=event_type,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Failed to list events")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
