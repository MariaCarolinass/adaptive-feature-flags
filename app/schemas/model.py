from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TrainProcessInfo(BaseModel):
    total_events: int = Field(description="Total de atividades usadas no treino.")
    unique_users: int = Field(description="Quantidade de usuários únicos no conjunto.")
    positive_events: int = Field(description="Quantidade de eventos positivos usados no treino.")
    duration_ms: int = Field(description="Duração do treino em milissegundos.")
    feature_columns: list[str] = Field(description="Colunas derivadas usadas como variáveis do modelo.")
    benchmark: list[dict[str, Any]] = Field(description="Comparação entre os modelos candidatos.")
    dataset_profile: dict[str, Any] = Field(description="Resumo do conjunto de dados usado no treino.")


class TrainResponse(BaseModel):
    status: str = Field(description="Situação do modelo após o treino.")
    model_name: str = Field(description="Nome do modelo selecionado.")
    model_version: str = Field(description="Versão do modelo treinado.")
    artifact_path: str = Field(description="Caminho do artefato salvo no disco.")
    trained_at: datetime = Field(description="Data e hora do treino.")
    metrics: dict[str, Any] = Field(description="Métricas do modelo treinado.")
    process: TrainProcessInfo = Field(description="Detalhes do processo de treino.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "model_name": "random_forest",
                "model_version": "v1",
                "artifact_path": "storage/models/v1.joblib",
                "trained_at": "2015-06-02T05:02:12.117000Z",
                "metrics": {
                    "accuracy": 0.82,
                    "precision": 0.78,
                    "recall": 0.76,
                    "f1_score": 0.77,
                    "roc_auc": 0.84,
                    "confusion_matrix": {
                        "true_negative": 1200,
                        "false_positive": 220,
                        "false_negative": 180,
                        "true_positive": 640
                    }
                },
                "process": {
                    "total_events": 2756101,
                    "unique_users": 1407580,
                    "positive_events": 193634,
                    "duration_ms": 4280,
                    "feature_columns": ["total_events", "positive_events"],
                    "benchmark": [
                        {"model_name": "random_forest", "f1_score": 0.77},
                        {"model_name": "logistic_regression", "f1_score": 0.72}
                    ],
                    "dataset_profile": {
                        "rows": 2400,
                        "train_rows": 1920,
                        "test_rows": 480,
                        "positive_rate": 0.33,
                        "class_distribution": {"0": 1600, "1": 800}
                    }
                },
            }
        }
    )


class ModelStatusResponse(BaseModel):
    status: str = Field(description="Situação atual do modelo.")
    model_name: str | None = Field(default=None, description="Nome do modelo atualmente carregado.")
    model_version: str | None = Field(default=None, description="Versão do modelo atualmente carregado.")
    trained_at: datetime | None = Field(default=None, description="Data e hora do último treino disponível.")
    metrics: dict[str, Any] | None = Field(default=None, description="Métricas do último treino.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "model_name": "random_forest",
                "model_version": "v1",
                "trained_at": "2026-04-21T17:00:00Z",
                "metrics": {"accuracy": 0.82, "f1_score": 0.79, "roc_auc": 0.84},
            }
        }
    )
