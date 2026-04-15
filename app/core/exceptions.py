from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AppError(Exception):
    message: str
    code: str = "app_error"
    status_code: int = 400
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found.", *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="not_found", status_code=404, details=details)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict.", *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="conflict", status_code=409, details=details)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation error.", *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="validation_error", status_code=400, details=details)


def to_http_exception(err: AppError):
    from fastapi import HTTPException

    payload: dict[str, Any] = {"message": err.message, "code": err.code}
    if err.details:
        payload["details"] = err.details
    return HTTPException(status_code=err.status_code, detail=payload)

