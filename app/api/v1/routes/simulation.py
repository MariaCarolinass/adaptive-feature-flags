from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import AppError, to_http_exception
from app.core.logging import get_logger
from app.dependencies import simulation_service
from app.schemas.simulation import SimulateUsersRequest, SimulateEventsRequest

router = APIRouter(prefix="/simulate", tags=["simulation"])
logger = get_logger(__name__)


@router.post("/users")
def simulate_users(request: SimulateUsersRequest):
    try:
        return simulation_service.simulate_users(request.count)
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao simular usuários")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

@router.post("/events")
def simulate_events(request: SimulateEventsRequest):
    try:
        return simulation_service.simulate_events(request.count, request.feature_key)
    except AppError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.exception("Erro ao simular eventos")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")