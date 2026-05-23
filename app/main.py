from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from app.api.v1.router import api_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
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
        "- Model training: synchronous `/train` and asynchronous `/train/async`\n"
        "- Online decision: user-level evaluation via `/evaluate`\n"
        "- Strategic recommendation: rollout guidance via `/features/{feature_key}/recommendation`\n\n"
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

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

app.include_router(api_router)


@app.get("/", tags=["root"], summary="Root message", description="Simple endpoint that identifies the API.")
def root():
    return {"message": settings.app_name}

@app.get("/health", tags=["health"], summary="Healthcheck", description="Checks if the API is responsive.")
def healthcheck():
    return {"status": "ok"}


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-XSS-Protection"] = "0"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
