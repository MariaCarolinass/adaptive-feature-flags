from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
        "- Event ingestion: single events via `/events` and batch ingestion via `/ingest/events` "
        "(with operational-metric validation and partial rejection accounting)\n"
        "- Model training: synchronous `/train`\n"
        "- Online decision: user-level evaluation via `/evaluate`\n"
        "- Experimentation: A/B-lite setup and evaluation via `/experiments`\n"
        "- Model governance: current status via `/model/status` and training history via `/model/runs`\n"
        "- Operational observability: in-memory metrics snapshot via `/metrics`\n\n"
        "### Design Principles\n"
        "- Predictable behavior with deterministic rollout\n"
        "- Progressive intelligence with machine learning when ready\n"
        "- Resilience through fallback-first decision flow\n"
        "- Incremental experimentation with deterministic A/B allocation"
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

ui_dir = Path(__file__).resolve().parent.parent / "ui"

@app.get("/", tags=["root"], summary="UI dashboard", description="Serves the web UI dashboard.")
def root():
    index_file = ui_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-store"})
    return {"message": settings.app_name}


@app.get("/health", tags=["health"], summary="Healthcheck", description="Checks if the API is responsive.")
def healthcheck():
    return {"status": "ok"}


if ui_dir.exists():
    app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
