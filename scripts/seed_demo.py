from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domain.services.event_service import EventService
from app.domain.services.feature_service import FeatureService
from app.infrastructure.db.db import SessionLocal, init_db
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository


def _build_feature_service() -> tuple[FeatureService, SqliteFeatureRepository]:
    repository = SqliteFeatureRepository(SessionLocal)
    return FeatureService(repository), repository


def _build_event_service() -> EventService:
    repository = SqliteEventRepository(SessionLocal)
    return EventService(repository)


def seed_features(feature_service: FeatureService, feature_repository: SqliteFeatureRepository) -> tuple[int, int]:
    seed_features_data = [
        {
            "name": "Checkout Upsell",
            "key": "checkout_upsell",
            "description": "Offer recommended add-ons during checkout.",
            "enabled": True,
            "rollout_percentage": 25,
            "ml_enabled": True,
        },
        {
            "name": "Homepage Hero Variant",
            "key": "homepage_hero_v2",
            "description": "Alternative homepage hero for engagement tests.",
            "enabled": True,
            "rollout_percentage": 40,
            "ml_enabled": True,
        },
        {
            "name": "Retention Banner",
            "key": "retention_banner",
            "description": "Show retention banner for returning users.",
            "enabled": True,
            "rollout_percentage": 15,
            "ml_enabled": False,
        },
    ]

    created = 0
    existing = 0
    for feature in seed_features_data:
        if feature_repository.get_by_key(feature["key"]) is not None:
            existing += 1
            continue
        feature_service.create_feature(**feature)
        created += 1
    return created, existing


def _build_seed_events() -> list[dict]:
    base_time = datetime.now(timezone.utc) - timedelta(days=7)
    feature_cycle = ["checkout_upsell", "homepage_hero_v2", "retention_banner"]
    events: list[dict] = []

    for idx in range(1, 13):
        user_id = f"demo_user_{idx:02d}"
        feature_key = feature_cycle[(idx - 1) % len(feature_cycle)]

        events.append(
            {
                "user_id": user_id,
                "feature_key": feature_key,
                "event_type": "view",
                "timestamp": base_time + timedelta(hours=idx),
                "source": "seed_demo",
                "properties": {"source": "seed_demo", "journey": "awareness"},
            }
        )
        events.append(
            {
                "user_id": user_id,
                "feature_key": feature_key,
                "event_type": "viewed_feature",
                "timestamp": base_time + timedelta(hours=idx, minutes=30),
                "source": "seed_demo",
                "properties": {"source": "seed_demo", "journey": "feature_exposed"},
            }
        )

        # Half of users become positive class for training.
        if idx % 2 == 0:
            events.append(
                {
                    "user_id": user_id,
                    "feature_key": feature_key,
                    "event_type": "addtocart",
                    "timestamp": base_time + timedelta(hours=idx, minutes=50),
                    "source": "seed_demo",
                    "properties": {"source": "seed_demo", "journey": "intent"},
                }
            )
            events.append(
                {
                    "user_id": user_id,
                    "feature_key": feature_key,
                    "event_type": "transaction",
                    "timestamp": base_time + timedelta(hours=idx + 1),
                    "source": "seed_demo",
                    "properties": {"source": "seed_demo", "journey": "conversion"},
                }
            )

    return events


def seed_events(event_service: EventService) -> tuple[int, int]:
    desired_events = _build_seed_events()
    existing_events = event_service.list_events()
    existing_keys = {
        (
            event.user_id,
            event.feature_key,
            event.event_type,
            event.timestamp.isoformat(),
        )
        for event in existing_events
    }

    created = 0
    skipped = 0
    for event in desired_events:
        key = (
            event["user_id"],
            event["feature_key"],
            event["event_type"],
            event["timestamp"].isoformat(),
        )
        if key in existing_keys:
            skipped += 1
            continue
        event_service.create_event(**event)
        created += 1
    return created, skipped


def main() -> None:
    init_db()

    feature_service, feature_repository = _build_feature_service()
    event_service = _build_event_service()

    created_features, existing_features = seed_features(feature_service, feature_repository)
    created_events, skipped_events = seed_events(event_service)

    print("Seed demo concluido.")
    print(f"Features criadas: {created_features}")
    print(f"Features ja existentes: {existing_features}")
    print(f"Eventos criados: {created_events}")
    print(f"Eventos ignorados (idempotencia): {skipped_events}")
    print("")
    print("Proximo passo:")
    print("curl -X POST http://localhost:8000/train")


if __name__ == "__main__":
    main()
