from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from app.domain.entities.model_metadata import ModelMetadata
from app.domain.repositories.model_repository import ModelRepository
from app.infrastructure.models import ModelMetadataModel


class SqliteModelRepository(ModelRepository):
    _SINGLETON_ID = 1

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def save_status(self, metadata: ModelMetadata) -> ModelMetadata:
        with self._session_factory() as session:
            row = session.get(ModelMetadataModel, self._SINGLETON_ID)
            if row is None:
                row = ModelMetadataModel(id=self._SINGLETON_ID, status=metadata.status)
                session.add(row)

            row.status = metadata.status
            row.model_name = metadata.model_name
            row.model_version = metadata.model_version
            row.trained_at = metadata.trained_at
            row.metrics = metadata.metrics

            session.commit()
        return metadata

    def get_status(self) -> ModelMetadata:
        with self._session_factory() as session:
            row = session.get(ModelMetadataModel, self._SINGLETON_ID)
            if row is None:
                return ModelMetadata(
                    status="idle",
                    model_name=None,
                    model_version=None,
                    trained_at=None,
                    metrics=None,
                )

            return ModelMetadata(
                status=row.status,
                model_name=row.model_name,
                model_version=row.model_version,
                trained_at=row.trained_at,
                metrics=row.metrics,
            )

