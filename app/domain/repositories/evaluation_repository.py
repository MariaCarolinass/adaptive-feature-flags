from abc import ABC, abstractmethod

from app.domain.entities.evaluation import EvaluationRecord


class EvaluationRepository(ABC):
    @abstractmethod
    def create(self, evaluation: EvaluationRecord) -> EvaluationRecord:
        raise NotImplementedError

    @abstractmethod
    def list(self, limit: int = 50) -> list[EvaluationRecord]:
        raise NotImplementedError

    @abstractmethod
    def delete_all(self) -> int:
        raise NotImplementedError
