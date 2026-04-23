from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from app.infrastructure.ml.feature_builder import FeatureBuilder
from app.infrastructure.ml.serializer import ModelSerializer

MODEL_FEATURE_COLUMNS = [
    "unique_features",
    "active_days",
    "avg_hour",
    "avg_day_of_week",
    "hours_since_last_event",
    "events_per_day",
]


def train_from_events(events: list[Any]) -> dict[str, Any]:
    rows = []
    for event in events:
        rows.append(
            {
                "user_id": event.user_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "feature_key": event.feature_key,
            }
        )

    if not rows:
        raise ValueError("Training requires at least one event.")

    df = pd.DataFrame(rows)
    builder = FeatureBuilder()
    dataset = builder.build_from_dataframe(df)

    X = dataset[MODEL_FEATURE_COLUMNS]
    y = dataset["target"]

    if y.nunique() < 2:
        raise ValueError("Training requires examples from at least two classes.")
    if (y.value_counts() < 2).any():
        raise ValueError("Training requires at least two samples per class.")

    test_size = max(0.2, 2 / len(X))
    if test_size >= 1:
        test_size = 0.5

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(class_weight="balanced", random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "f1_score": float(f1_score(y_test, preds)),
    }

    model_version = "v1"
    serializer = ModelSerializer()
    artifact_path = serializer.save(
        model=model,
        model_version=model_version,
        metadata=metrics,
        feature_columns=MODEL_FEATURE_COLUMNS,
    )

    return {
        "model_name": "random_forest",
        "model_version": model_version,
        "trained_at": datetime.now(timezone.utc),
        "metrics": metrics,
        "artifact_path": artifact_path,
        "feature_columns": MODEL_FEATURE_COLUMNS,
    }