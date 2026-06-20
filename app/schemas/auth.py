from pydantic import BaseModel, Field


class TokenCreateRequest(BaseModel):
    issuer_key: str = Field(min_length=1, description="Chave de provisionamento usada para emitir o JWT.")
    subject: str = Field(default="api-client", min_length=1, description="Assunto do token.")
    expires_minutes: int | None = Field(default=None, ge=1, le=1440, description="Tempo de vida do token em minutos.")


class TokenCreateResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
