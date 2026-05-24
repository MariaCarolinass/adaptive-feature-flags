from fastapi import APIRouter
from app.api.v1.routes.features import router as features_router
from app.api.v1.routes.events import router as events_router
from app.api.v1.routes.evaluate import router as evaluate_router
from app.api.v1.routes.ingest import router as ingest_router
from app.api.v1.routes.training import router as training_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.metrics import router as metrics_router
from app.api.v1.routes.experiments import router as experiments_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(features_router)
api_router.include_router(events_router)
api_router.include_router(ingest_router)
api_router.include_router(evaluate_router)
api_router.include_router(training_router)
api_router.include_router(metrics_router)
api_router.include_router(experiments_router)
