from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
from sqlalchemy.engine import Engine

from app.core.exceptions import ValidationError
from scripts.import_dataset_csv import (
    REQUIRED_COLUMNS,
    ensure_events_table,
    insert_events,
    load_csv_chunks,
    normalize_events,
    sync_features,
)


class SimulationService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def import_dataset_csv(
        self,
        *,
        csv_url: str | None,
        csv_file_bytes: bytes | None,
        csv_file_name: str | None,
        feature_key_mode: str,
        limit: int | None,
        chunk_size: int,
        batch_size: int,
        sync_features_enabled: bool,
        feature_rollout_percentage: int,
        feature_ml_enabled: bool,
    ) -> dict:
        if bool(csv_url) == bool(csv_file_bytes):
            raise ValidationError("Provide exactly one source: either csv_url or csv_file.")
        if feature_key_mode not in {"item", "single"}:
            raise ValidationError("feature_key_mode must be either 'item' or 'single'.")
        if limit is not None and limit <= 0:
            raise ValidationError("limit must be greater than zero.")
        if chunk_size <= 0:
            raise ValidationError("chunk_size must be greater than zero.")
        if batch_size <= 0:
            raise ValidationError("batch_size must be greater than zero.")
        if not (0 <= feature_rollout_percentage <= 100):
            raise ValidationError("feature_rollout_percentage must be between 0 and 100.")

        ensure_events_table(self._engine)

        total_raw_rows = 0
        total_normalized_rows = 0
        total_inserted_rows = 0
        imported_feature_keys: set[str] = set()

        for raw_chunk in self._iter_csv_chunks(
            csv_url=csv_url,
            csv_file_bytes=csv_file_bytes,
            chunk_size=chunk_size,
            limit=limit,
        ):
            total_raw_rows += len(raw_chunk)
            normalized_chunk = normalize_events(raw_chunk, feature_key_mode=feature_key_mode)
            total_normalized_rows += len(normalized_chunk)
            imported_feature_keys.update(normalized_chunk["feature_key"].astype(str).unique().tolist())
            total_inserted_rows += insert_events(self._engine, normalized_chunk, batch_size=batch_size)

        synced_features = 0
        if sync_features_enabled:
            synced_features = sync_features(
                self._engine,
                imported_feature_keys,
                rollout_percentage=feature_rollout_percentage,
                ml_enabled=feature_ml_enabled,
            )

        return {
            "source_type": "url" if csv_url else "file",
            "source_value": csv_url or (csv_file_name or "uploaded.csv"),
            "feature_key_mode": feature_key_mode,
            "sync_features": sync_features_enabled,
            "raw_rows_processed": total_raw_rows,
            "normalized_rows": total_normalized_rows,
            "inserted_rows": total_inserted_rows,
            "features_auto_created": synced_features,
        }

    @staticmethod
    def _iter_csv_chunks(
        *,
        csv_url: str | None,
        csv_file_bytes: bytes | None,
        chunk_size: int,
        limit: int | None,
    ):
        if csv_url:
            processed_rows = 0
            for chunk in pd.read_csv(csv_url, chunksize=chunk_size):
                missing = REQUIRED_COLUMNS.difference(chunk.columns)
                if missing:
                    raise ValidationError(f"CSV is missing required columns: {sorted(missing)}")
                if limit is not None:
                    remaining = limit - processed_rows
                    if remaining <= 0:
                        break
                    if len(chunk) > remaining:
                        chunk = chunk.head(remaining)
                processed_rows += len(chunk)
                yield chunk
            return

        if not csv_file_bytes:
            raise ValidationError("Uploaded csv_file is empty.")

        with NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp:
            tmp.write(csv_file_bytes)
            temp_path = Path(tmp.name)

        try:
            yield from load_csv_chunks(str(temp_path), chunk_size=chunk_size, limit=limit)
        finally:
            temp_path.unlink(missing_ok=True)