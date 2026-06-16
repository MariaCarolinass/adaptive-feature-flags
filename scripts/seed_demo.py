from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from random import Random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domain.services.event_service import EventService
from app.domain.services.feature_service import FeatureService
from app.infrastructure.db.db import SessionLocal, init_db
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository
from app.infrastructure.repositories.sqlite_feature_repository import SqliteFeatureRepository

DEFAULT_SEED_DATA_PATH = PROJECT_ROOT / "dataset" / "seed_demo_checkout_focus.json"
USERS_PER_CATALOG = 50


@dataclass(slots=True)
class FeatureSpec:
    name: str
    key: str
    description: str
    enabled: bool
    rollout_percentage: int
    ml_enabled: bool
    ml_threshold_mode: str = "fixed"
    ml_threshold_value: float = 0.1


@dataclass(slots=True)
class ProfileSpec:
    segment: str
    source: str
    device: str
    country: str
    positive_probability: float
    primary_features: tuple[str, ...]
    secondary_features: tuple[str, ...]
    active_days_min: int
    active_days_max: int
    sessions_min: int
    sessions_max: int
    hour_buckets: tuple[int, ...]


@dataclass(slots=True)
class SeedCatalog:
    catalog_name: str
    seed_source: str
    seed_version: str
    user_prefix: str
    seed_anchor: datetime
    seed_window_days: int
    random_seed: int
    features: list[FeatureSpec]
    profiles: list[ProfileSpec]
    journeys: dict[str, dict[str, str]]


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_seed_catalog(path: Path) -> SeedCatalog:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return SeedCatalog(
        catalog_name=path.stem,
        seed_source=str(raw["seed_source"]),
        seed_version=str(raw["seed_version"]),
        user_prefix=str(raw.get("user_prefix", "demo_user")),
        seed_anchor=_parse_datetime(str(raw["seed_anchor"])),
        seed_window_days=int(raw["seed_window_days"]),
        random_seed=int(raw["random_seed"]),
        features=[FeatureSpec(**item) for item in raw["features"]],
        profiles=[ProfileSpec(**item) for item in raw["profiles"]],
        journeys={key: dict(value) for key, value in raw["journeys"].items()},
    )


def _resolve_catalog_paths(catalog_path: Path | None, all_json: bool) -> list[Path]:
    if catalog_path is None:
        catalog_dir = DEFAULT_SEED_DATA_PATH.parent
        paths = sorted(
            path
            for path in catalog_dir.glob("*.json")
            if path.is_file()
        )
        if not paths:
            raise ValueError(f"No JSON seed catalogs found in {catalog_dir}")
        return paths
    if all_json:
        paths = sorted(
            path
            for path in catalog_path.parent.glob("*.json")
            if path.is_file()
        )
        if not paths:
            raise ValueError(f"No JSON seed catalogs found in {catalog_path.parent}")
        return paths
    if not catalog_path.exists():
        raise FileNotFoundError(f"Seed catalog not found: {catalog_path}")
    return [catalog_path]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed demo data into the local database.")
    parser.add_argument(
        "--catalog",
        default=None,
        help="Path to a seed catalog JSON file.",
    )
    parser.add_argument(
        "--all-json",
        action="store_true",
        help="Import every JSON seed catalog in the same directory as --catalog. Defaults to all catalogs when --catalog is omitted.",
    )
    return parser.parse_args(argv)


def _build_feature_service() -> tuple[FeatureService, SqliteFeatureRepository]:
    repository = SqliteFeatureRepository(SessionLocal)
    return FeatureService(repository), repository


def _build_event_service() -> EventService:
    repository = SqliteEventRepository(SessionLocal)
    return EventService(repository)


def _feature_needs_refresh(existing, spec: FeatureSpec) -> bool:
    return any(
        [
            existing.name != spec.name,
            existing.description != spec.description,
            existing.enabled != spec.enabled,
            existing.rollout_percentage != spec.rollout_percentage,
            existing.ml_enabled != spec.ml_enabled,
            existing.ml_threshold_mode != spec.ml_threshold_mode,
            abs(float(existing.ml_threshold_value) - spec.ml_threshold_value) > 1e-9,
        ]
    )


def seed_features(
    catalog: SeedCatalog,
    feature_service: FeatureService,
    feature_repository: SqliteFeatureRepository,
) -> tuple[int, int, int]:
    created = 0
    updated = 0
    unchanged = 0

    for spec in catalog.features:
        existing = feature_repository.get_by_key(spec.key)
        if existing is None:
            feature_service.create_feature(
                name=spec.name,
                key=spec.key,
                description=spec.description,
                enabled=spec.enabled,
                rollout_percentage=spec.rollout_percentage,
                ml_enabled=spec.ml_enabled,
                ml_threshold_mode=spec.ml_threshold_mode,
                ml_threshold_value=spec.ml_threshold_value,
            )
            created += 1
            continue

        if _feature_needs_refresh(existing, spec):
            feature_service.update_feature(
                feature_id=existing.id,
                name=spec.name,
                key=spec.key,
                description=spec.description,
                enabled=spec.enabled,
                rollout_percentage=spec.rollout_percentage,
                ml_enabled=spec.ml_enabled,
                ml_threshold_mode=spec.ml_threshold_mode,
                ml_threshold_value=spec.ml_threshold_value,
            )
            updated += 1
        else:
            unchanged += 1

    return created, updated, unchanged


def _make_latency_ms(rng: Random, event_type: str) -> int:
    ranges = {
        "view": (120, 320),
        "viewed_feature": (180, 560),
        "checkout_upsell_shown": (180, 560),
        "pricing_tooltip_shown": (180, 560),
        "upgrade_prompt_shown": (180, 560),
        "cart_reminder_shown": (180, 560),
        "homepage_hero_seen": (180, 560),
        "search_suggestions_shown": (180, 560),
        "retention_banner_shown": (180, 560),
        "community_invite_shown": (180, 560),
        "onboarding_step_shown": (180, 560),
        "empty_state_shown": (180, 560),
        "profile_setup_shown": (180, 560),
        "success_tip_shown": (180, 560),
        "weekly_digest_shown": (180, 560),
        "streak_banner_shown": (180, 560),
        "alert_center_shown": (180, 560),
        "community_digest_shown": (180, 560),
        "login_page_viewed": (120, 320),
        "signup_page_viewed": (120, 320),
        "magic_link_prompt_shown": (180, 560),
        "social_login_prompt_shown": (180, 560),
        "password_reset_prompt_shown": (180, 560),
        "signup_form_shown": (180, 560),
        "login_form_submitted": (240, 760),
        "signup_form_submitted": (240, 760),
        "magic_link_requested": (220, 640),
        "magic_link_verified": (320, 920),
        "social_login_clicked": (220, 640),
        "login_success": (320, 920),
        "signup_completed": (320, 920),
        "password_reset_requested": (220, 640),
        "password_reset_completed": (320, 920),
        "checkout_upsell_clicked": (240, 760),
        "pricing_details_opened": (220, 640),
        "upgrade_cta_clicked": (260, 720),
        "cart_reminder_clicked": (220, 620),
        "hero_cta_clicked": (180, 540),
        "search_suggestion_selected": (180, 560),
        "retention_banner_clicked": (200, 580),
        "community_invite_clicked": (200, 600),
        "onboarding_completed": (300, 900),
        "first_task_created": (260, 840),
        "profile_completed": (260, 760),
        "first_success_action_taken": (280, 860),
        "weekly_digest_opened": (180, 520),
        "streak_banner_clicked": (180, 540),
        "alert_center_opened": (180, 560),
        "addtocart": (360, 900),
        "transaction": (700, 1800),
        "purchase_completed": (700, 1800),
        "subscription_upgraded": (700, 1800),
    }
    low, high = ranges.get(event_type, (150, 600))
    return rng.randint(low, high)


def _event_identity_timestamp(timestamp: datetime) -> str:
    normalized = timestamp
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=timezone.utc)
    else:
        normalized = normalized.astimezone(timezone.utc)
    return normalized.replace(microsecond=0).isoformat()


def _build_event_properties(
    *,
    rng: Random,
    catalog: SeedCatalog,
    profile: ProfileSpec,
    user_id: str,
    session_id: str,
    feature_key: str,
    event_type: str,
    journey: str,
    stage: str,
    day_offset: int,
    session_index: int,
    order_value: float | None = None,
) -> dict[str, str | int | float | bool | None]:
    journey_details = catalog.journeys[feature_key]
    properties: dict[str, str | int | float | bool | None] = {
        "catalog_name": catalog.catalog_name,
        "seed_source": catalog.seed_source,
        "seed_version": catalog.seed_version,
        "journey": journey,
        "stage": stage,
        "segment": profile.segment,
        "device": profile.device,
        "country": profile.country,
        "channel": profile.source,
        "session_id": session_id,
        "user_alias": user_id,
        "page": journey_details["page"],
        "surface": journey_details["surface"],
        "funnel_stage": journey_details["journey"],
        "flag_variant": "treatment" if (day_offset + session_index) % 2 else "control",
        "latency_ms": _make_latency_ms(rng, event_type),
        "step_index": session_index,
        "day_offset": day_offset,
    }

    if order_value is not None:
        properties["order_value"] = round(order_value, 2)
        properties["currency"] = "BRL"

    return properties


def _build_session_events(
    *,
    rng: Random,
    catalog: SeedCatalog,
    profile: ProfileSpec,
    user_id: str,
    day_offset: int,
    session_number: int,
    is_positive_user: bool,
    is_conversion_session: bool,
) -> list[dict]:
    primary_feature = rng.choice(profile.primary_features)
    secondary_feature_pool = tuple(
        feature for feature in profile.secondary_features if feature != primary_feature
    )
    if not secondary_feature_pool:
        secondary_feature_pool = tuple(
            feature for feature in catalog.journeys if feature != primary_feature
        )
    secondary_feature = rng.choice(secondary_feature_pool) if secondary_feature_pool else None

    start_hour = rng.choice(profile.hour_buckets)
    start_minute = rng.choice((0, 10, 20, 30, 40, 50))
    start_timestamp = catalog.seed_anchor + timedelta(days=day_offset, hours=start_hour, minutes=start_minute)
    session_id = f"{user_id}-d{day_offset:02d}-s{session_number:02d}"

    primary_flow = catalog.journeys[primary_feature]
    events: list[dict] = []

    def add_event(
        *,
        offset_minutes: int,
        feature_key: str,
        event_type: str,
        stage: str,
        order_value: float | None = None,
    ) -> None:
        feature_details = catalog.journeys[feature_key]
        events.append(
            {
                "user_id": user_id,
                "feature_key": feature_key,
                "event_type": event_type,
                "timestamp": start_timestamp + timedelta(minutes=offset_minutes),
                "source": profile.source,
                "properties": _build_event_properties(
                    rng=rng,
                    catalog=catalog,
                    profile=profile,
                    user_id=user_id,
                    session_id=session_id,
                    feature_key=feature_key,
                    event_type=event_type,
                    journey=feature_details["journey"],
                    stage=stage,
                    day_offset=day_offset,
                    session_index=session_number,
                    order_value=order_value,
                ),
            }
        )

    add_event(offset_minutes=0, feature_key=primary_feature, event_type="view", stage="awareness")
    primary_exposure_event = primary_flow.get("exposure_event", "viewed_feature")
    add_event(
        offset_minutes=14,
        feature_key=primary_feature,
        event_type=primary_exposure_event,
        stage="exposure",
    )

    if secondary_feature and rng.random() < 0.7:
        secondary_exposure_event = catalog.journeys[secondary_feature].get(
            "exposure_event",
            "viewed_feature",
        )
        add_event(
            offset_minutes=26,
            feature_key=secondary_feature,
            event_type=secondary_exposure_event,
            stage="comparison",
        )

    positive_event = primary_flow["positive_event"]
    conversion_event = primary_flow.get("conversion_event")
    positive_stage = primary_flow["positive_stage"]

    if is_positive_user and is_conversion_session:
        add_event(offset_minutes=38, feature_key=primary_feature, event_type=positive_event, stage=positive_stage)
        if conversion_event:
            add_event(
                offset_minutes=58,
                feature_key=primary_feature,
                event_type=conversion_event,
                stage="conversion",
                order_value=round(rng.uniform(29.9, 249.9), 2),
            )
    elif is_positive_user and rng.random() < 0.35:
        target_feature = secondary_feature if secondary_feature and rng.random() < 0.6 else primary_feature
        target_positive_event = catalog.journeys[target_feature]["positive_event"]
        target_stage = catalog.journeys[target_feature]["positive_stage"]
        add_event(offset_minutes=34, feature_key=target_feature, event_type=target_positive_event, stage=target_stage)
    elif not is_positive_user and secondary_feature and rng.random() < 0.25:
        add_event(offset_minutes=35, feature_key=secondary_feature, event_type="view", stage="drop_off")

    return events


def _build_seed_events(catalog: SeedCatalog) -> list[dict]:
    rng = Random(catalog.random_seed)
    events: list[dict] = []
    profile_count = len(catalog.profiles)

    for idx in range(1, USERS_PER_CATALOG + 1):
        user_id = f"{catalog.user_prefix}_{idx:02d}"
        profile = catalog.profiles[(idx - 1) % profile_count]
        is_positive_user = rng.random() < profile.positive_probability
        active_days = rng.randint(profile.active_days_min, profile.active_days_max)
        sessions_per_day = rng.randint(profile.sessions_min, profile.sessions_max)
        first_day = (idx - 1) % (catalog.seed_window_days - 2)
        day_offsets = [min(catalog.seed_window_days - 1, first_day + step * 2) for step in range(active_days)]

        for day_index, day_offset in enumerate(day_offsets):
            for session_index in range(sessions_per_day):
                is_conversion_session = is_positive_user and day_index == len(day_offsets) - 1 and session_index == sessions_per_day - 1
                events.extend(
                    _build_session_events(
                        rng=rng,
                        catalog=catalog,
                        profile=profile,
                        user_id=user_id,
                        day_offset=day_offset,
                        session_number=session_index + 1,
                        is_positive_user=is_positive_user,
                        is_conversion_session=is_conversion_session,
                    )
                )

    return events


def seed_events(catalog: SeedCatalog, event_service: EventService) -> tuple[int, int]:
    desired_events = _build_seed_events(catalog)
    existing_events = event_service.list_events()
    existing_keys = {
        (
            event.user_id,
            event.feature_key,
            event.event_type,
            _event_identity_timestamp(event.timestamp),
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
            _event_identity_timestamp(event["timestamp"]),
        )
        if key in existing_keys:
            skipped += 1
            continue
        event_service.create_event(**event)
        created += 1

    return created, skipped


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    init_db()

    feature_service, feature_repository = _build_feature_service()
    event_service = _build_event_service()

    catalog_path = Path(args.catalog) if args.catalog else None
    catalog_paths = _resolve_catalog_paths(catalog_path, args.all_json)
    catalogs = [_load_seed_catalog(path) for path in catalog_paths]

    created_features = 0
    updated_features = 0
    unchanged_features = 0
    created_events = 0
    skipped_events = 0

    for catalog in catalogs:
        current_created_features, current_updated_features, current_unchanged_features = seed_features(
            catalog,
            feature_service,
            feature_repository,
        )
        current_created_events, current_skipped_events = seed_events(catalog, event_service)
        created_features += current_created_features
        updated_features += current_updated_features
        unchanged_features += current_unchanged_features
        created_events += current_created_events
        skipped_events += current_skipped_events
        print(f"Catálogo importado: {catalog.catalog_name}")

    print("Seed demo concluído.")
    print(f"Features criadas: {created_features}")
    print(f"Features atualizadas: {updated_features}")
    print(f"Features já consistentes: {unchanged_features}")
    print(f"Eventos criados: {created_events}")
    print(f"Eventos ignorados (idempotência): {skipped_events}")
    print("")
    print("Próximo passo:")
    print("curl -X POST http://localhost:8000/train")


if __name__ == "__main__":
    main()
