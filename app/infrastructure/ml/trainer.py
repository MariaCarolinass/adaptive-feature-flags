from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
import numpy as np

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

    candidate_models = {
        "random_forest": RandomForestClassifier(class_weight="balanced", random_state=42),
        "logistic_regression": LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
    }
    benchmark: list[dict[str, Any]] = []
    best_model_name = None
    best_model = None
    best_metrics = None

    for model_name, model in candidate_models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        scores = model.predict_proba(X_test)[:, 1]

        metrics = _build_metrics(y_test, preds, scores)
        benchmark.append({"model_name": model_name, **metrics})

        if best_metrics is None or metrics["f1_score"] > best_metrics["f1_score"]:
            best_metrics = metrics
            best_model = model
            best_model_name = model_name

    if best_model is None or best_metrics is None or best_model_name is None:
        raise ValueError("No model was successfully trained.")

    class_distribution = y.value_counts().to_dict()
    dataset_profile = {
        "rows": int(len(dataset)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "positive_rate": float(y.mean()),
        "class_distribution": {str(k): int(v) for k, v in class_distribution.items()},
    }

    model_version = "v1"
    serializer = ModelSerializer()
    artifact_path = serializer.save(
        model=best_model,
        model_version=model_version,
        metadata=best_metrics,
        feature_columns=MODEL_FEATURE_COLUMNS,
    )

    return {
        "model_name": best_model_name,
        "model_version": model_version,
        "trained_at": datetime.now(timezone.utc),
        "metrics": best_metrics,
        "benchmark": benchmark,
        "dataset_profile": dataset_profile,
        "artifact_path": artifact_path,
        "feature_columns": MODEL_FEATURE_COLUMNS,
    }


def _build_metrics(y_true, y_pred, y_score) -> dict[str, Any]:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    try:
        roc_auc = float(roc_auc_score(y_true, y_score))
    except ValueError:
        roc_auc = None

    best_threshold = _best_threshold_by_f1(y_true, y_score)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": roc_auc,
        "best_threshold_by_f1": float(best_threshold),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def _best_threshold_by_f1(y_true, y_score) -> float:
    thresholds = np.linspace(0.05, 0.95, 19)
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in thresholds:
        preds = (y_score >= threshold).astype(int)
        candidate = f1_score(y_true, preds, zero_division=0)
        if candidate > best_f1:
            best_f1 = candidate
            best_threshold = float(threshold)
    return best_threshold
