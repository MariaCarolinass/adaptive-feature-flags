from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.core.exceptions import NotFoundError
from app.domain.entities.feature import Feature
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository


def _feature(
    *,
    name: str = "Feature A",
    key: str = "feature_a",
    enabled: bool = True,
    rollout_percentage: int = 10,
    ml_enabled: bool = False,
    ml_threshold_mode: str = "fixed",
    ml_threshold_value: float = 0.1,
) -> Feature:
    now = datetime.now(timezone.utc)
    return Feature(
        id=None,
        name=name,
        key=key,
        description="descricao",
        enabled=enabled,
        rollout_percentage=rollout_percentage,
        ml_enabled=ml_enabled,
        ml_threshold_mode=ml_threshold_mode,
        ml_threshold_value=ml_threshold_value,
        created_at=now,
        updated_at=now,
    )


def test_create_and_get_feature(session_factory) -> None:
    repo = SqliteFeatureRepository(session_factory)
    feature = _feature()

    created = repo.create(feature)
    by_id = repo.get_by_id(created.id)
    by_key = repo.get_by_key(created.key)

    assert isinstance(created.id, int)
    assert by_id is not None
    assert by_key is not None
    assert by_id.id == created.id
    assert by_key.key == "feature_a"


def test_list_feature_returns_persisted_items(session_factory) -> None:
    repo = SqliteFeatureRepository(session_factory)
    f1 = _feature(name="A", key="a")
    f2 = _feature(name="B", key="b")
    repo.create(f1)
    repo.create(f2)

    result = repo.list()

    assert len(result) == 2
    assert {item.key for item in result} == {"a", "b"}


def test_update_feature_persists_changes(session_factory) -> None:
    repo = SqliteFeatureRepository(session_factory)
    feature = _feature()
    repo.create(feature)

    feature.name = "Atualizada"
    feature.rollout_percentage = 80
    feature.ml_enabled = True
    feature.ml_threshold_mode = "match_rollout"
    feature.ml_threshold_value = 0.35
    feature.updated_at = datetime.now(timezone.utc)
    updated = repo.update(feature)
    loaded = repo.get_by_id(updated.id)

    assert loaded is not None
    assert loaded.name == "Atualizada"
    assert loaded.rollout_percentage == 80
    assert loaded.ml_enabled is True
    assert loaded.ml_threshold_mode == "match_rollout"
    assert loaded.ml_threshold_value == 0.35


def test_delete_feature_removes_record(session_factory) -> None:
    repo = SqliteFeatureRepository(session_factory)
    feature = _feature()
    repo.create(feature)

    deleted = repo.delete(feature.id)
    loaded = repo.get_by_id(feature.id)

    assert deleted is True
    assert loaded is None
    assert repo.delete(feature.id) is False


def test_update_feature_requires_existing_id(session_factory) -> None:
    repo = SqliteFeatureRepository(session_factory)
    feature = _feature()

    with pytest.raises(NotFoundError, match="Feature not found"):
        repo.update(feature)
