from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain.entities.training_job import TrainingJob
from app.domain.services.training_job_service import TrainingJobService


class _TrainingServiceStub:
    def train(self) -> dict:
        return {"status": "ready"}


class _NoopExecutor:
    def submit(self, *_args, **_kwargs) -> None:
        return None


class _TrainingJobRepoStub:
    def __init__(self) -> None:
        self.jobs: dict[str, TrainingJob] = {}

    def create(self, job: TrainingJob) -> TrainingJob:
        self.jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> TrainingJob | None:
        return self.jobs.get(job_id)

    def update(self, job: TrainingJob) -> TrainingJob:
        self.jobs[job.job_id] = job
        return job

    def prune(self, *, now: datetime, max_jobs: int, retention_minutes: int) -> None:
        cutoff = now - timedelta(minutes=retention_minutes)
        terminal_statuses = {"succeeded", "failed"}

        expired_ids = [
            job_id
            for job_id, job in self.jobs.items()
            if job.status in terminal_statuses and job.finished_at is not None and job.finished_at < cutoff
        ]
        for job_id in expired_ids:
            self.jobs.pop(job_id, None)

        overflow = len(self.jobs) - max_jobs
        if overflow <= 0:
            return

        removable_jobs = sorted(
            (job for job in self.jobs.values() if job.status in terminal_statuses),
            key=lambda job: (job.finished_at or job.submitted_at),
        )
        for job in removable_jobs[:overflow]:
            self.jobs.pop(job.job_id, None)


def _finished_job(job_id: str, *, minutes_ago: int) -> TrainingJob:
    now = datetime.now(timezone.utc)
    finished_at = now - timedelta(minutes=minutes_ago)
    return TrainingJob(
        job_id=job_id,
        status="succeeded",
        submitted_at=finished_at - timedelta(minutes=1),
        started_at=finished_at - timedelta(seconds=30),
        finished_at=finished_at,
        result={"status": "ready"},
    )


def test_start_prunes_expired_terminal_jobs() -> None:
    repo = _TrainingJobRepoStub()
    service = TrainingJobService(
        _TrainingServiceStub(),
        repo,
        retention_minutes=1,
    )
    service._executor = _NoopExecutor()
    repo.jobs["old"] = _finished_job("old", minutes_ago=10)

    payload = service.start()

    assert payload["status"] == "queued"
    assert "old" not in repo.jobs


def test_start_prunes_oldest_terminal_jobs_when_capacity_exceeded() -> None:
    repo = _TrainingJobRepoStub()
    service = TrainingJobService(
        _TrainingServiceStub(),
        repo,
        max_jobs=2,
        retention_minutes=60,
    )
    service._executor = _NoopExecutor()
    repo.jobs["oldest"] = _finished_job("oldest", minutes_ago=9)
    repo.jobs["middle"] = _finished_job("middle", minutes_ago=6)
    repo.jobs["newest"] = _finished_job("newest", minutes_ago=3)

    payload = service.start()

    assert payload["status"] == "queued"
    assert "oldest" not in repo.jobs
    assert "middle" not in repo.jobs
    assert "newest" in repo.jobs


def test_get_prunes_expired_jobs_before_lookup() -> None:
    repo = _TrainingJobRepoStub()
    service = TrainingJobService(
        _TrainingServiceStub(),
        repo,
        retention_minutes=1,
    )
    service._executor = _NoopExecutor()
    repo.jobs["old"] = _finished_job("old", minutes_ago=10)

    result = service.get("old")

    assert result is None
    assert "old" not in repo.jobs
