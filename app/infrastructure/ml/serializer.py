from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from app.core.config import Settings

settings = Settings()

class ModelSerializer:
    """
    Handles model artifact persistence.

    This class stores:
    - trained sklearn model
    - metadata dict
    - optional feature column list
    """

    def __init__(self, base_dir: str = settings.models_dir) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        *,
        model: Any,
        model_version: str,
        metadata: dict[str, Any],
        feature_columns: list[str] | None = None,
    ) -> str:
        artifact = {
            "model": model,
            "metadata": metadata,
            "feature_columns": feature_columns or [],
        }

        path = self.base_dir / f"{model_version}.joblib"
        joblib.dump(artifact, path)
        return str(path)

    def load(self, artifact_path: str) -> dict[str, Any]:
        path = Path(artifact_path)
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found: {artifact_path}")

        artifact = joblib.load(path)

        if not isinstance(artifact, dict):
            raise ValueError("Invalid model artifact format.")

        if "model" not in artifact:
            raise ValueError("Invalid model artifact: missing 'model'.")

        artifact.setdefault("metadata", {})
        artifact.setdefault("feature_columns", [])
        return artifact

    def load_model(self, artifact_path: str) -> Any:
        artifact = self.load(artifact_path)
        return artifact["model"]

    def load_feature_columns(self, artifact_path: str) -> list[str]:
        artifact = self.load(artifact_path)
        return list(artifact.get("feature_columns", []))

    def load_metadata(self, artifact_path: str) -> dict[str, Any]:
        artifact = self.load(artifact_path)
        return dict(artifact.get("metadata", {}))