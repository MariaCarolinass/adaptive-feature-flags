from __future__ import annotations

"""
Examples:
python3 scripts/import_events_csv.py \
  --adapter retailrocket \
  --csv dataset-ml/retailrocket/events.csv \
  --feature-key-mode item \
  --limit 10000

python3 scripts/import_events_csv.py \
  --adapter generic \
  --csv ./events.csv \
  --source web_app \
  --mapping-json '{"user_id":"uid","feature_key":"feature","event_type":"event_name","timestamp":"ts"}'
"""

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domain.services.event_service import EventService
from app.infrastructure.db.db import SessionLocal, init_db
from app.infrastructure.integrations.base import CSVAdapterConfig
from app.infrastructure.integrations.csv_adapter import GenericCSVAdapter
from app.infrastructure.integrations.retailrocket_adapter import RetailrocketCSVAdapter
from app.infrastructure.repositories.sqlite_event_repository import SqliteEventRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import CSV events into canonical event schema.")
    parser.add_argument("--csv", required=True, help="Path to CSV file.")
    parser.add_argument("--adapter", choices=["retailrocket", "generic"], default="retailrocket")
    parser.add_argument("--chunk-size", type=int, default=50000)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--feature-key-mode", choices=["item", "single"], default="item")
    parser.add_argument("--source", default=None, help="Source name for generic adapter.")
    parser.add_argument(
        "--mapping-json",
        default=None,
        help='JSON mapping for generic adapter, e.g. \'{"user_id":"uid","feature_key":"flag","event_type":"action","timestamp":"ts"}\'',
    )
    return parser.parse_args()


def build_adapter(args: argparse.Namespace):
    if args.adapter == "retailrocket":
        return RetailrocketCSVAdapter(feature_key_mode=args.feature_key_mode)

    if not args.source:
        raise ValueError("--source is required when adapter=generic")
    if not args.mapping_json:
        raise ValueError("--mapping-json is required when adapter=generic")

    mapping = json.loads(args.mapping_json)
    config = CSVAdapterConfig(source=args.source, field_mapping=mapping)
    return GenericCSVAdapter(config)


def main() -> None:
    args = parse_args()
    init_db()

    adapter = build_adapter(args)
    event_service = EventService(SqliteEventRepository(SessionLocal))

    saved = 0
    for event in adapter.iter_events(args.csv, chunk_size=args.chunk_size, limit=args.limit):
        event_service.create_event(
            source=event["source"],
            user_id=str(event["user_id"]),
            feature_key=str(event["feature_key"]),
            event_type=str(event["event_type"]),
            timestamp=event["timestamp"],
            properties=event["properties"],
        )
        saved += 1

    print(f"Import finished. saved_events={saved}")


if __name__ == "__main__":
    main()
