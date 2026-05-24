from abc import ABC, abstractmethod

from app.domain.entities.experiment import Experiment


class ExperimentRepository(ABC):
    @abstractmethod
    def create(self, experiment: Experiment) -> Experiment:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[Experiment]:
        raise NotImplementedError

    @abstractmethod
    def get_active_by_feature_key(self, feature_key: str) -> Experiment | None:
        raise NotImplementedError
