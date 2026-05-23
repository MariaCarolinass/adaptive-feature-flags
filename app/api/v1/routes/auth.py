from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.security import create_jwt
from app.schemas.auth import TokenCreateRequest, TokenCreateResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/token",
    response_model=TokenCreateResponse,
    summary="Issue JWT access token",
    description="Issues a bearer token with expiration for API authentication.",
)
def issue_token(request: TokenCreateRequest):
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication is disabled.",
        )

    issuer_key = settings.auth_issuer_key.strip()
    jwt_secret = settings.auth_jwt_secret.strip()
    if not issuer_key or not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is enabled but AUTH_ISSUER_KEY or AUTH_JWT_SECRET is not configured.",
        )

    if request.issuer_key != issuer_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid issuer key.")

    ttl_minutes = request.expires_minutes or settings.auth_token_expire_minutes
    ttl_seconds = int(ttl_minutes) * 60
    token = create_jwt(
        secret=jwt_secret,
        subject=request.subject,
        expires_in_seconds=ttl_seconds,
    )

    return TokenCreateResponse(
        access_token=token,
        expires_in_seconds=ttl_seconds,
    )
