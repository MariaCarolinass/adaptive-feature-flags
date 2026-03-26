from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.feature import Feature


class FeatureRepository(ABC):
    @abstractmethod
    def create(self, feature: Feature) -> Feature:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[Feature]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, feature_id: UUID) -> Feature | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_key(self, key: str) -> Feature | None:
        raise NotImplementedError