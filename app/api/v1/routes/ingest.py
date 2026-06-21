from fastapi import APIRouter, HTTPException, Request, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import ingest_service
from app.schemas.event_ingest import CanonicalEventBatchIngest, CanonicalEventBatchIngestResponse

router = APIRouter(prefix="/ingest", tags=["Atividades"])
logger = get_logger(__name__)


def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if forwarded_for:
        return forwarded_for
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@router.post(
    "/events",
    response_model=CanonicalEventBatchIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingerir atividades em lote",
    description="Recebe um lote canônico de atividades a partir de qualquer origem externa.",
    response_description="Quantidade de atividades salvas com sucesso.",
)
def ingest_events(payload: CanonicalEventBatchIngest, request: Request):
    try:
        result = ingest_service.ingest_events(
            source=payload.source,
            events=[event.model_dump() for event in payload.events],
            client_id=_client_identifier(request),
        )
        return {"saved_events": result["saved_events"], "rejected": result["rejected"]}
    except AppError as e:
        raise to_http_exception(e)
    except Exception:
        logger.exception("Failed to ingest events")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
