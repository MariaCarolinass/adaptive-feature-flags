from app.domain.services.event_service import EventService
from app.domain.services.evaluation_service import EvaluationService
from app.domain.services.feature_service import FeatureService
from app.domain.services.simulation_service import SimulationService
from app.domain.services.training_job_service import TrainingJobService
from app.domain.services.training_service import TrainingService

from app.infrastructure.db.db import SessionLocal, engine
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository
from app.infrastructure.repositories.sqlite_model_repository import SqliteModelRepository
from app.infrastructure.repositories.sqlite_training_job_repository import SqliteTrainingJobRepository

feature_repository = SqliteFeatureRepository(SessionLocal)
event_repository = SqliteEventRepository(SessionLocal)
model_repository = SqliteModelRepository(SessionLocal)
training_job_repository = SqliteTrainingJobRepository(SessionLocal)

feature_service = FeatureService(feature_repository)
event_service = EventService(event_repository)
evaluation_service = EvaluationService(feature_repository, event_repository, model_repository)
training_service = TrainingService(event_repository, model_repository)
training_job_service = TrainingJobService(training_service, training_job_repository)
simulation_service = SimulationService(engine)