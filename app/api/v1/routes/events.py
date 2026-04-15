from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.exceptions import AppError, NotFoundError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import event_service
from app.schemas.event import EventCreate, EventResponse

router = APIRouter(prefix="/events", tags=["events"])
logger = get_logger(__name__)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create(event: EventCreate):
    try:
        return event_service.create_event(
            user_id=event.user_id,
            feature_key=event.feature_key,
            event_type=event.event_type,
            timestamp=event.timestamp,
            properties=event.properties,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao criar event")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get("/{event_id}", response_model=EventResponse)
def retrieve(event_id: UUID):
    try:
        event = event_service.get_event_by_id(event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        return event
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao buscar event")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.put("/{event_id}", response_model=EventResponse)
def update(event_id: UUID, event: EventCreate):
    try:
        return event_service.update_event(
            event_id=event_id,
            user_id=event.user_id,
            feature_key=event.feature_key,
            event_type=event.event_type,
            timestamp=event.timestamp,
            properties=event.properties,
        )
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao atualizar event")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(event_id: UUID):
    try:
        event_service.delete_event(event_id)
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao remover event")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.get("", response_model=list[EventResponse])
def list(
    user_id: str | None = Query(default=None),
    feature_key: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
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
        logger.exception("Erro ao listar events")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")