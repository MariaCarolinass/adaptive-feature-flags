from fastapi import APIRouter, HTTPException, status

from app.dependencies import simulation_service
from app.schemas.simulation import SimulateUsersRequest, SimulateEventsRequest

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/users")
def simulate_users(request: SimulateUsersRequest):
    try:
        return simulation_service.simulate_users(request.count)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/events")
def simulate_events(request: SimulateEventsRequest):
    try:
        return simulation_service.simulate_events(request.count, request.feature_key)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))