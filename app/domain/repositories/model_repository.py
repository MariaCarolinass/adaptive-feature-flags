from abc import ABC, abstractmethod

from app.domain.entities.model_metadata import ModelMetadata


class ModelRepository(ABC):
    @abstractmethod
    def save_status(self, metadata: ModelMetadata) -> ModelMetadata:
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> ModelMetadata:
        raise NotImplementedError

    @abstractmethod
    def append_training_run(self, *, model_version: str, trained_at, status: str, snapshot: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_training_runs(self, limit: int = 20) -> list[dict]:
        raise NotImplementedError
