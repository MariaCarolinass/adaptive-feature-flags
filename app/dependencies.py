from app.domain.services.event_service import EventService
from app.domain.services.evaluation_service import EvaluationService
from app.domain.services.feature_service import FeatureService
from app.domain.services.simulation_service import SimulationService
from app.domain.services.training_service import TrainingService

from app.infrastructure.db import SessionLocal, init_db
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository
from app.infrastructure.repositories.sqlite_model_repository import SqliteModelRepository

feature_repository = SqliteFeatureRepository(SessionLocal)
event_repository = SqliteEventRepository(SessionLocal)
model_repository = SqliteModelRepository(SessionLocal)

feature_service = FeatureService(feature_repository)
event_service = EventService(event_repository)
evaluation_service = EvaluationService(feature_repository, model_repository)
training_service = TrainingService(model_repository)
simulation_service = SimulationService(event_service)