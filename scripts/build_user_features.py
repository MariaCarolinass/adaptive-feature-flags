from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.infrastructure.ml.feature_aggregation import (
    build_features_from_chunks,
    load_event_chunks,
    save_features,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build user-level features from events table.",
    )
    parser.add_argument(
        "--database-url",
        default=settings.database_url,
        help="SQLAlchemy database URL. Default: " + settings.database_url,
    )
    parser.add_argument(
        "--output-table",
        default="user_features",
        help="Table name to store generated features.",
    )
    parser.add_argument(
        "--if-exists",
        choices=["replace", "append", "fail"],
        default="replace",
        help="Behavior when output table already exists.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=200000,
        help="Number of events to process per chunk.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build features without saving to database.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    print("Loading events...")
    event_chunks = load_event_chunks(args.database_url, args.chunk_size)
    print("Building features incrementally...")
    features_df = build_features_from_chunks(event_chunks)
    if features_df.empty:
        raise ValueError("Feature builder returned no rows.")

    if args.dry_run:
        print("Dry run enabled. Skipping database write.")
    else:
        print("Saving features...")
        save_features(features_df, args.database_url, args.output_table, args.if_exists)

    print("Done.")
    print(f"Rows saved: {len(features_df)}")
    print(f"Output table: {args.output_table}")


if __name__ == "__main__":
    main()
