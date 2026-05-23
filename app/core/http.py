from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response

from app.core.config import Settings
from app.core.security import verify_jwt


def _is_exempt_path(path: str, exempt_paths: list[str]) -> bool:
    for exempt in exempt_paths:
        if path == exempt or path.startswith(f"{exempt}/"):
            return True
    return False


def _extract_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "").strip()
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return ""


def register_http_stack(app: FastAPI, settings: Settings) -> None:
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

    @app.middleware("http")
    async def auth_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not settings.auth_enabled:
            return await call_next(request)

        if _is_exempt_path(request.url.path, settings.auth_exempt_paths):
            return await call_next(request)

        jwt_secret = settings.auth_jwt_secret.strip()
        if not jwt_secret:
            return JSONResponse(
                status_code=500,
                content={"detail": "Authentication is enabled but AUTH_JWT_SECRET is not configured."},
            )

        token = _extract_bearer_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            verify_jwt(token=token, secret=jwt_secret)
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)

    @app.middleware("http")
    async def security_headers_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
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


def attach_openapi_auth(app: FastAPI) -> None:
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        components = openapi_schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT bearer authentication.",
        }

        public_paths = {"/", "/health", "/auth/token"}
        for path, methods in openapi_schema.get("paths", {}).items():
            for method_name, operation in methods.items():
                if method_name.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                    continue
                if path in public_paths:
                    operation["security"] = []
                else:
                    operation["security"] = [{"BearerAuth": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
