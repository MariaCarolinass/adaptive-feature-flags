from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.infrastructure.ml.feature_builder import FeatureBuilder
from app.infrastructure.ml.serializer import ModelSerializer
from scripts.build_user_features import build_features_from_chunks, load_event_chunks
from app.infrastructure.ml.trainer import MODEL_FEATURE_COLUMNS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark a Decision Tree classifier on the current ML dataset.",
    )
    parser.add_argument(
        "--database-url",
        default=settings.database_url,
        help="SQLAlchemy database URL. Default: " + settings.database_url,
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=200000,
        help="Number of events processed per chunk while building features.",
    )
    parser.add_argument(
        "--feature-set",
        choices=["mvp", "full"],
        default="mvp",
        help="Feature set to use: the compact MVP columns or the full builder output.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=4,
        help="Maximum tree depth. Lower values reduce overfitting.",
    )
    parser.add_argument(
        "--min-samples-leaf",
        type=int,
        default=2,
        help="Minimum samples per leaf.",
    )
    parser.add_argument(
        "--min-samples-split",
        type=int,
        default=4,
        help="Minimum samples required to split a node.",
    )
    parser.add_argument(
        "--save-artifact",
        action="store_true",
        help="Persist the trained tree artifact under storage/models/.",
    )
    parser.add_argument(
        "--artifact-version",
        default="decision_tree_v1",
        help="Artifact version used when saving the model.",
    )
    parser.add_argument(
        "--tree-plot-path",
        default=None,
        help="Optional path to save a visual representation of the tree.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("Loading events...")
    event_chunks = load_event_chunks(args.database_url, chunk_size=args.chunk_size)
    print("Building features...")
    dataset = build_features_from_chunks(event_chunks)
    if dataset.empty:
        raise ValueError("Feature builder returned no rows.")

    feature_columns = (
        MODEL_FEATURE_COLUMNS
        if args.feature_set == "mvp"
        else FeatureBuilder.model_feature_columns()
    )

    missing_columns = [column for column in feature_columns if column not in dataset.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    X = dataset[feature_columns]
    y = dataset["target"].astype(int)

    if y.nunique() < 2:
        raise ValueError("Training requires examples from at least two classes.")
    if (y.value_counts() < 2).any():
        raise ValueError("Training requires at least two samples per class.")

    test_size = max(0.2, 2 / len(dataset))
    if test_size >= 1:
        test_size = 0.5

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=42,
        stratify=y,
    )

    print("Training DecisionTreeClassifier...")
    model = DecisionTreeClassifier(
        class_weight="balanced",
        random_state=42,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        min_samples_split=args.min_samples_split,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)[:, 1]

    metrics = build_metrics(y_test, y_pred, y_score)
    threshold = metrics["best_threshold_by_f1"]
    threshold_pred = (y_score >= threshold).astype(int)

    print("\n=== Decision Tree Benchmark ===")
    print(f"Feature set: {args.feature_set}")
    print(f"Rows: {len(dataset)}")
    print(f"Train rows: {len(X_train)}")
    print(f"Test rows: {len(X_test)}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1: {metrics['f1_score']:.4f}")
    print(f"ROC AUC: {metrics['roc_auc']:.4f}")
    print(f"Best threshold by F1: {threshold:.2f}")
    print(
        "Confusion matrix:",
        metrics["confusion_matrix"],
    )
    print(f"F1 at tuned threshold: {f1_score(y_test, threshold_pred, zero_division=0):.4f}")

    print("\nFeature importance:")
    for name, importance in sorted(
        zip(feature_columns, model.feature_importances_),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"- {name}: {importance:.4f}")

    if args.save_artifact:
        serializer = ModelSerializer()
        artifact_path = serializer.save(
            model=model,
            model_version=args.artifact_version,
            metadata=metrics,
            feature_columns=feature_columns,
        )
        print(f"\nArtifact saved to: {artifact_path}")

    if args.tree_plot_path:
        save_tree_plot(
            model=model,
            feature_names=feature_columns,
            output_path=Path(args.tree_plot_path),
        )
        print(f"Tree plot saved to: {args.tree_plot_path}")

    print("\nDone.")


def build_metrics(y_true, y_pred, y_score) -> dict[str, Any]:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    try:
        roc_auc = float(roc_auc_score(y_true, y_score))
    except ValueError:
        roc_auc = None

    best_threshold = best_threshold_by_f1(y_true, y_score)
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


def best_threshold_by_f1(y_true, y_score) -> float:
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


def save_tree_plot(*, model: DecisionTreeClassifier, feature_names: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(18, 10))
    plot_tree(
        model,
        feature_names=feature_names,
        class_names=["0", "1"],
        filled=True,
        rounded=True,
        impurity=False,
        proportion=True,
        ax=ax,
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
