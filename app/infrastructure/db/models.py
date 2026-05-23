from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class FeatureModel(Base):
    __tablename__ = "features"
    __table_args__ = (UniqueConstraint("key", name="uq_features_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rollout_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ml_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    feature_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    properties: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class ModelMetadataModel(Base):
    __tablename__ = "model_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
