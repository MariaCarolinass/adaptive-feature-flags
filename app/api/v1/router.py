from fastapi import APIRouter
from app.api.v1.routes.features import router as features_router
from app.api.v1.routes.events import router as events_router
from app.api.v1.routes.evaluate import router as evaluate_router
from app.api.v1.routes.ingest import router as ingest_router
from app.api.v1.routes.training import router as training_router
from app.api.v1.routes.simulation import router as simulation_router

api_router = APIRouter()
api_router.include_router(features_router)
api_router.include_router(events_router)
api_router.include_router(ingest_router)
api_router.include_router(evaluate_router)
api_router.include_router(training_router)
api_router.include_router(simulation_router)
