from pydantic import BaseModel, Field


class TokenCreateRequest(BaseModel):
    issuer_key: str = Field(min_length=1, description="Provisioning key to issue JWT.")
    subject: str = Field(default="api-client", min_length=1, description="Token subject.")
    expires_minutes: int | None = Field(default=None, ge=1, le=1440, description="Token TTL in minutes.")


class TokenCreateResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
