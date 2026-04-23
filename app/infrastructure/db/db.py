from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite:"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    return create_engine(database_url, pool_pre_ping=True)


engine: Engine = _create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    from app.infrastructure.db.models import Base

    Base.metadata.create_all(bind=engine)

