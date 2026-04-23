from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from app.domain.entities.training_job import TrainingJob
from app.domain.repositories.training_job_repository import TrainingJobRepository
from app.infrastructure.db.models import TrainingJobModel


class SqliteTrainingJobRepository(TrainingJobRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def create(self, job: TrainingJob) -> TrainingJob:
        with self._session_factory() as session:
            row = TrainingJobModel(
                job_id=job.job_id,
                status=job.status,
                submitted_at=job.submitted_at,
                started_at=job.started_at,
                finished_at=job.finished_at,
                result=job.result,
                error=job.error,
            )
            session.add(row)
            session.commit()
        return job

    def get(self, job_id: str) -> TrainingJob | None:
        with self._session_factory() as session:
            row = session.get(TrainingJobModel, job_id)
            return self._to_entity(row) if row is not None else None

    def update(self, job: TrainingJob) -> TrainingJob:
        with self._session_factory() as session:
            row = session.get(TrainingJobModel, job.job_id)
            if row is None:
                return job

            row.status = job.status
            row.started_at = job.started_at
            row.finished_at = job.finished_at
            row.result = job.result
            row.error = job.error
            session.commit()
        return job

    def prune(self, *, now: datetime, max_jobs: int, retention_minutes: int) -> None:
        terminal_statuses = ("succeeded", "failed")
        cutoff = now - timedelta(minutes=retention_minutes)

        with self._session_factory() as session:
            session.execute(
                delete(TrainingJobModel).where(
                    TrainingJobModel.status.in_(terminal_statuses),
                    TrainingJobModel.finished_at.is_not(None),
                    TrainingJobModel.finished_at < cutoff,
                )
            )

            total_jobs = session.execute(select(TrainingJobModel.job_id)).scalars().all()
            overflow = len(total_jobs) - max_jobs
            if overflow > 0:
                removable_ids = (
                    session.execute(
                        select(TrainingJobModel.job_id)
                        .where(TrainingJobModel.status.in_(terminal_statuses))
                        .order_by(
                            TrainingJobModel.finished_at.asc().nullsfirst(),
                            TrainingJobModel.submitted_at.asc(),
                        )
                        .limit(overflow)
                    )
                    .scalars()
                    .all()
                )
                if removable_ids:
                    session.execute(delete(TrainingJobModel).where(TrainingJobModel.job_id.in_(removable_ids)))

            session.commit()

    @staticmethod
    def _to_entity(row: TrainingJobModel) -> TrainingJob:
        return TrainingJob(
            job_id=row.job_id,
            status=row.status,
            submitted_at=row.submitted_at,
            started_at=row.started_at,
            finished_at=row.finished_at,
            result=row.result,
            error=row.error,
        )
