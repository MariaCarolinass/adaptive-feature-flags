from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ActivityCreate(BaseModel):
    key: str = Field(min_length=3, max_length=50, description="Identificador técnico da atividade.")
    name: str = Field(min_length=3, max_length=80, description="Nome amigável da atividade exibido na UI.")
    description: str | None = Field(default=None, max_length=240, description="Descrição curta opcional da atividade.")
    enabled: bool = Field(default=True, description="Indica se a atividade está disponível na UI.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "viewed_feature",
                "name": "Visualizou a funcionalidade",
                "description": "Usuário abriu ou viu a funcionalidade",
                "enabled": True,
            }
        }
    )


class ActivityResponse(BaseModel):
    id: int
    key: str
    name: str
    description: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "key": "viewed_feature",
                "name": "Visualizou a funcionalidade",
                "description": "Usuário abriu ou viu a funcionalidade",
                "enabled": True,
                "created_at": "2026-06-18T12:00:00Z",
                "updated_at": "2026-06-18T12:00:00Z",
            }
        }
    )
