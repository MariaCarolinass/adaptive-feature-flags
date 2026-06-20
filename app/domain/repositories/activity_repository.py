from abc import ABC, abstractmethod

from app.domain.entities.activity import Activity


class ActivityRepository(ABC):
    @abstractmethod
    def create(self, activity: Activity) -> Activity:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[Activity]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, activity_id: int) -> Activity | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_key(self, key: str) -> Activity | None:
        raise NotImplementedError

    @abstractmethod
    def update(self, activity: Activity) -> Activity:
        raise NotImplementedError

    @abstractmethod
    def delete(self, activity_id: int) -> bool:
        raise NotImplementedError
