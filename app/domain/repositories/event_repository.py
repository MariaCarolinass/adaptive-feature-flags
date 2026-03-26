from abc import ABC, abstractmethod

from app.domain.entities.event import Event


class EventRepository(ABC):
    @abstractmethod
    def create(self, event: Event) -> Event:
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        user_id: str | None = None,
        feature_key: str | None = None,
        event_type: str | None = None,
    ) -> list[Event]:
        raise NotImplementedError