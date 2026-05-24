from __future__ import annotations

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.services.feature_service import FeatureService
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository


def test_create_feature_and_reject_duplicate_key(session_factory) -> None:
    repo = SqliteFeatureRepository(session_factory)
    service = FeatureService(repo)

    created = service.create_feature(
        name="Feature X",
        key="feature_x",
        description="d",
        enabled=True,
        rollout_percentage=10,
        ml_enabled=False,
        ml_threshold_mode="fixed",
        ml_threshold_value=0.1,
    )

    assert created.key == "feature_x"

    with pytest.raises(ConflictError, match="already exists"):
        service.create_feature(
            name="Feature X2",
            key="feature_x",
            description=None,
            enabled=True,
            rollout_percentage=20,
            ml_enabled=False,
            ml_threshold_mode="fixed",
            ml_threshold_value=0.2,
        )


def test_update_feature_and_delete_feature(session_factory) -> None:
    repo = SqliteFeatureRepository(session_factory)
    service = FeatureService(repo)
    created = service.create_feature(
        name="Original",
        key="original",
        description=None,
        enabled=True,
        rollout_percentage=0,
        ml_enabled=False,
        ml_threshold_mode="fixed",
        ml_threshold_value=0.1,
    )

    updated = service.update_feature(
        feature_id=created.id,
        name="Atualizada",
        key="original",
        description="nova",
        enabled=False,
        rollout_percentage=55,
        ml_enabled=True,
        ml_threshold_mode="match_rollout",
        ml_threshold_value=0.9,
    )

    assert updated.name == "Atualizada"
    assert updated.enabled is False
    assert updated.rollout_percentage == 55
    assert updated.ml_threshold_mode == "match_rollout"
    assert updated.ml_threshold_value == 0.9

    service.delete_feature(created.id)
    assert service.get_feature_by_id(created.id) is None


def test_update_feature_requires_existing_id(session_factory) -> None:
    repo = SqliteFeatureRepository(session_factory)
    service = FeatureService(repo)

    with pytest.raises(NotFoundError, match="Feature not found"):
        service.update_feature(
            feature_id=999999,
            name="A",
            key="a",
            description=None,
            enabled=True,
            rollout_percentage=1,
            ml_enabled=False,
            ml_threshold_mode="fixed",
            ml_threshold_value=0.1,
        )
