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
    _apply_sqlite_feature_threshold_migration()


def _apply_sqlite_feature_threshold_migration() -> None:
    if not str(engine.url).startswith("sqlite:"):
        return

    with engine.begin() as conn:
        columns = {
            row[1]
            for row in conn.exec_driver_sql("PRAGMA table_info(features)").fetchall()
        }
        if "ml_threshold_mode" not in columns:
            conn.exec_driver_sql(
                "ALTER TABLE features ADD COLUMN ml_threshold_mode VARCHAR(30) NOT NULL DEFAULT 'fixed'"
            )
        if "ml_threshold_value" not in columns:
            conn.exec_driver_sql(
                "ALTER TABLE features ADD COLUMN ml_threshold_value FLOAT NOT NULL DEFAULT 0.1"
            )
