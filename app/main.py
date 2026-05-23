from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.v1.router import api_router

from app.core.config import settings
from app.core.http import attach_openapi_auth, register_http_stack
from app.core.logging import setup_logging
from app.infrastructure.db.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Event-driven feature flag API for adaptive rollout decisions.\n\n"
        "This service combines deterministic rollout with machine learning-assisted evaluation, "
        "using safe fallback behavior when model scoring is unavailable.\n\n"
        "### Main Flows\n"
        "- Feature lifecycle: create, list, update, and delete via `/features`\n"
        "- Event ingestion: single events via `/events` and batch ingestion via `/ingest/events`\n"
        "- Model training: synchronous `/train`\n"
        "- Online decision: user-level evaluation via `/evaluate`\n"
        "- Model observability: current status via `/model/status`\n\n"
        "### Design Principles\n"
        "- Predictable behavior with deterministic rollout\n"
        "- Progressive intelligence with machine learning when ready\n"
        "- Resilience through fallback-first decision flow"
    ),
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
    lifespan=lifespan,
)

setup_logging()
register_http_stack(app, settings)
attach_openapi_auth(app)

app.include_router(api_router)


@app.get("/", tags=["root"], summary="Root message", description="Simple endpoint that identifies the API.")
def root():
    return {"message": settings.app_name}

@app.get("/health", tags=["health"], summary="Healthcheck", description="Checks if the API is responsive.")
def healthcheck():
    return {"status": "ok"}
