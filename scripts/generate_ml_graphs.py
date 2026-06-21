from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sqlalchemy import create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.infrastructure.ml.feature_builder import FeatureBuilder
from app.infrastructure.ml.serializer import ModelSerializer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate analytical charts for the ML report.",
    )
    parser.add_argument(
        "--database-url",
        default=settings.database_url,
        help="SQLAlchemy database URL. Default: " + settings.database_url,
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "storage" / "figures" / "ml-report"),
        help="Directory where PNG charts will be stored.",
    )
    parser.add_argument(
        "--model-artifact",
        default=None,
        help="Optional path to a trained model artifact. Defaults to the latest ready model in the database.",
    )
    parser.add_argument(
        "--min-ab-variant-count",
        type=int,
        default=5,
        help="Minimum events per variant required to render the A/B chart.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(args.database_url)
    events = load_events(engine)
    if events.empty:
        raise ValueError("No events found in the database.")

    feature_builder = FeatureBuilder()
    feature_frame = feature_builder.build_from_dataframe(
        events[["user_id", "event_type", "timestamp", "feature_key"]].copy(),
    )
    if feature_frame.empty:
        raise ValueError("Feature builder returned no rows.")

    model_record = load_latest_model_record(engine)
    if model_record is None:
        raise ValueError("No model metadata found in the database.")

    artifact_path = args.model_artifact or model_record["artifact_path"]
    if not artifact_path:
        raise ValueError("Model artifact path is missing.")

    serializer = ModelSerializer()
    artifact = serializer.load(artifact_path)
    model = artifact["model"]
    model_feature_columns = artifact.get("feature_columns") or list(feature_builder.model_feature_columns())

    missing_columns = [column for column in model_feature_columns if column not in feature_frame.columns]
    if missing_columns:
        raise ValueError(f"Feature frame is missing columns required by the model: {missing_columns}")

    metrics = load_model_metrics(model_record)
    training_run = load_latest_training_run(engine)

    generated_files: list[str] = []
    skipped: list[str] = []

    generated_files.append(
        save_figure(
            output_dir / "01_benchmark_metrics.png",
            lambda fig, ax: plot_benchmark_metrics(fig, ax, training_run),
            title="Benchmark de Modelos",
        )
    )
    generated_files.append(
        save_figure(
            output_dir / "02_confusion_matrix.png",
            lambda fig, ax: plot_confusion_matrix(fig, ax, metrics["confusion_matrix"]),
            title="Matriz de Confusão",
        )
    )
    generated_files.append(
        save_figure(
            output_dir / "03_target_distribution.png",
            lambda fig, ax: plot_target_distribution(fig, ax, feature_frame),
            title="Distribuição do Target",
        )
    )
    generated_files.append(
        save_figure(
            output_dir / "04_threshold_curve.png",
            lambda fig, ax: plot_threshold_curve(fig, ax, feature_frame, model, model_feature_columns),
            title="Curva de Threshold",
        )
    )
    generated_files.append(
        save_figure(
            output_dir / "05_feature_importance.png",
            lambda fig, ax: plot_feature_importance(fig, ax, model, model_feature_columns),
            title="Importância dos Atributos",
        )
    )
    generated_files.append(
        save_figure(
            output_dir / "06_event_timeline.png",
            lambda fig, ax: plot_event_timeline(fig, ax, events),
            title="Linha do Tempo dos Eventos",
        )
    )
    generated_files.append(
        save_figure(
            output_dir / "07_feature_distributions.png",
            lambda fig, axes: plot_feature_distributions(fig, axes, feature_frame),
            title="Distribuição das Features",
            multi_axes=True,
        )
    )

    ab_chart = maybe_save_ab_summary(
        output_dir=output_dir,
        events=events,
        engine=engine,
        min_variant_count=args.min_ab_variant_count,
    )
    if ab_chart is not None:
        generated_files.append(ab_chart)
    else:
        skipped.append(
            "A/B summary chart skipped because there were not enough events for both variants.",
        )

    write_summary(output_dir, generated_files, skipped, model_record, training_run)

    print("Charts generated:")
    for path in generated_files:
        print(f"- {path}")
    if skipped:
        print("Skipped:")
        for item in skipped:
            print(f"- {item}")


def load_events(engine) -> pd.DataFrame:
    query = """
        SELECT user_id, feature_key, event_type, timestamp, properties
        FROM events
        ORDER BY timestamp ASC, id ASC
    """
    events = pd.read_sql_query(query, engine)
    if events.empty:
        return events

    events["timestamp"] = pd.to_datetime(events["timestamp"], utc=True, errors="coerce")
    events = events.dropna(subset=["user_id", "event_type", "timestamp"])
    events["feature_key"] = events["feature_key"].astype(str)
    events["event_type"] = events["event_type"].astype(str)
    events["user_id"] = events["user_id"].astype(str)

    properties = events["properties"].apply(parse_properties)
    props = pd.json_normalize(properties)
    props.index = events.index
    events = pd.concat([events.drop(columns=["properties"]), props], axis=1)
    return events


def parse_properties(value: Any) -> dict[str, Any]:
    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def load_latest_model_record(engine) -> dict[str, Any] | None:
    query = """
        SELECT id, status, model_name, model_version, trained_at, metrics, artifact_path
        FROM model_metadata
        ORDER BY id DESC
        LIMIT 1
    """
    rows = pd.read_sql_query(query, engine)
    if rows.empty:
        return None
    record = rows.iloc[0].to_dict()
    record["metrics"] = parse_json_field(record.get("metrics"))
    return record


def load_latest_training_run(engine) -> dict[str, Any] | None:
    query = """
        SELECT id, model_version, trained_at, status, duration_ms, snapshot
        FROM model_training_runs
        ORDER BY id DESC
        LIMIT 1
    """
    rows = pd.read_sql_query(query, engine)
    if rows.empty:
        return None
    record = rows.iloc[0].to_dict()
    record["snapshot"] = parse_json_field(record.get("snapshot"))
    return record


def load_model_metrics(model_record: dict[str, Any]) -> dict[str, Any]:
    metrics = model_record.get("metrics") or {}
    if not metrics:
        raise ValueError("Model metrics are missing.")
    return metrics


def parse_json_field(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def save_figure(
    path: Path,
    plot_fn,
    *,
    title: str,
    multi_axes: bool = False,
) -> str:
    if multi_axes:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        plot_fn(fig, axes)
    else:
        fig, ax = plt.subplots(figsize=(12, 7))
        plot_fn(fig, ax)
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def plot_benchmark_metrics(fig, ax, training_run: dict[str, Any] | None) -> None:
    if not training_run:
        ax.text(0.5, 0.5, "Sem snapshot de treino disponível", ha="center", va="center")
        ax.axis("off")
        return

    snapshot = training_run.get("snapshot") or {}
    process = snapshot.get("process") or {}
    benchmark = process.get("benchmark") or []
    if not benchmark:
        ax.text(0.5, 0.5, "Benchmark não encontrado no snapshot", ha="center", va="center")
        ax.axis("off")
        return

    df = pd.DataFrame(benchmark).set_index("model_name")
    metrics = [column for column in ["accuracy", "precision", "recall", "f1_score", "roc_auc"] if column in df.columns]
    x = np.arange(len(metrics))
    width = 0.25
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for idx, model_name in enumerate(df.index):
        values = df.loc[model_name, metrics].astype(float).to_numpy()
        ax.bar(x + (idx - 1) * width, values, width, label=model_name.replace("_", " ").title(), color=palette[idx % len(palette)])

    ax.set_xticks(x)
    ax.set_xticklabels([metric.replace("_", " ").title() for metric in metrics])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()


def plot_confusion_matrix(fig, ax, confusion_matrix: dict[str, Any]) -> None:
    matrix = np.array(
        [
            [confusion_matrix.get("true_negative", 0), confusion_matrix.get("false_positive", 0)],
            [confusion_matrix.get("false_negative", 0), confusion_matrix.get("true_positive", 0)],
        ]
    )
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks([0, 1], labels=["Previsto 0", "Previsto 1"])
    ax.set_yticks([0, 1], labels=["Real 0", "Real 1"])
    ax.set_xlabel("Classe prevista")
    ax.set_ylabel("Classe real")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, int(matrix[i, j]), ha="center", va="center", color="black", fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def plot_target_distribution(fig, ax, feature_frame: pd.DataFrame) -> None:
    counts = feature_frame["target"].value_counts().sort_index()
    labels = ["Classe 0", "Classe 1"]
    values = [int(counts.get(0, 0)), int(counts.get(1, 0))]
    bars = ax.bar(labels, values, color=["#7f8c8d", "#27ae60"])
    total = max(sum(values), 1)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value}\n({value / total:.1%})", ha="center", va="bottom")
    ax.set_ylabel("Usuários")
    ax.set_title("Distribuição da variável alvo")
    ax.grid(axis="y", alpha=0.25)


def plot_threshold_curve(fig, ax, feature_frame: pd.DataFrame, model, feature_columns: list[str]) -> None:
    X = feature_frame[feature_columns]
    y_true = feature_frame["target"].astype(int)
    scores = model.predict_proba(X)[:, 1]
    thresholds = np.arange(0.05, 1.0, 0.05)
    f1_scores = [f1_score(y_true, (scores >= threshold).astype(int), zero_division=0) for threshold in thresholds]
    ax.plot(thresholds, f1_scores, marker="o", color="#8e44ad")
    best_idx = int(np.argmax(f1_scores))
    ax.scatter([thresholds[best_idx]], [f1_scores[best_idx]], color="#c0392b", zorder=3)
    ax.annotate(
        f"melhor = {thresholds[best_idx]:.2f}",
        xy=(thresholds[best_idx], f1_scores[best_idx]),
        xytext=(thresholds[best_idx] + 0.03, f1_scores[best_idx] - 0.05),
        arrowprops=dict(arrowstyle="->", color="#c0392b"),
    )
    ax.set_xlabel("Threshold")
    ax.set_ylabel("F1")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)


def plot_feature_importance(fig, ax, model, feature_columns: list[str]) -> None:
    if hasattr(model, "coef_"):
        values = np.abs(np.asarray(model.coef_)).ravel()
        title = "Coeficientes absolutos"
    elif hasattr(model, "feature_importances_"):
        values = np.asarray(model.feature_importances_)
        title = "Importância das features"
    else:
        ax.text(0.5, 0.5, "Modelo não expõe coeficientes nem importâncias", ha="center", va="center")
        ax.axis("off")
        return

    ordering = np.argsort(values)
    ax.barh(np.array(feature_columns)[ordering], values[ordering], color="#2980b9")
    ax.set_title(title)
    ax.set_xlabel("Peso / importância")
    ax.grid(axis="x", alpha=0.25)


def plot_event_timeline(fig, ax, events: pd.DataFrame) -> None:
    series = events.groupby(events["timestamp"].dt.date).size().sort_index()
    ax.plot(series.index, series.values, marker="o", color="#16a085")
    rolling = series.rolling(window=min(7, max(len(series), 1)), min_periods=1).mean()
    ax.plot(series.index, rolling.values, color="#c0392b", linewidth=2, alpha=0.8, label="Média móvel")
    ax.set_xlabel("Data")
    ax.set_ylabel("Eventos")
    ax.legend()
    ax.grid(alpha=0.25)


def plot_feature_distributions(fig, axes, feature_frame: pd.DataFrame) -> None:
    columns = [
        "unique_features",
        "active_days",
        "hours_since_last_event",
        "events_per_day",
        "positive_rate",
        "avg_hour",
    ]
    axes = np.asarray(axes).ravel()
    for axis, column in zip(axes, columns):
        axis.hist(feature_frame[column].dropna(), bins=20, color="#34495e", alpha=0.85)
        axis.set_title(column)
        axis.grid(alpha=0.15)
    for axis in axes[len(columns):]:
        axis.axis("off")


def maybe_save_ab_summary(
    *,
    output_dir: Path,
    events: pd.DataFrame,
    engine,
    min_variant_count: int,
) -> str | None:
    query = """
        SELECT id, name, feature_key, primary_metric_event, min_samples_per_variant, min_lift, enabled
        FROM experiments
        WHERE enabled = 1
        ORDER BY id DESC
        LIMIT 1
    """
    experiments = pd.read_sql_query(query, engine)
    if experiments.empty:
        return None

    experiment = experiments.iloc[0].to_dict()
    if "ab_variant" not in events.columns:
        return None

    ab_events = events.dropna(subset=["ab_variant"]).copy()
    if ab_events.empty:
        return None

    if "experiment_id" in ab_events.columns:
        ab_events = ab_events[ab_events["experiment_id"] == experiment["id"]]
    if ab_events.empty:
        return None

    counts = ab_events["ab_variant"].value_counts()
    if len(counts.index) < 2 or counts.min() < min_variant_count:
        return None

    success_mask = ab_events["event_type"] == experiment["primary_metric_event"]
    summary = (
        ab_events.assign(success=success_mask.astype(int))
        .groupby("ab_variant")
        .agg(samples=("success", "size"), successes=("success", "sum"))
        .sort_index()
    )
    summary["rate"] = summary["successes"] / summary["samples"]
    if {"A", "B"}.issubset(summary.index):
        lift = float(summary.loc["B", "rate"] - summary.loc["A", "rate"])
    else:
        return None

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(summary.index, summary["rate"], color=["#1f77b4", "#ff7f0e"])
    for bar, (variant, row) in zip(bars, summary.iterrows()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{int(row['successes'])}/{int(row['samples'])}\n{row['rate']:.1%}",
            ha="center",
            va="bottom",
        )
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Taxa de sucesso")
    ax.set_xlabel("Variante")
    ax.set_title(f"Teste A/B - lift B vs A = {lift:.2%}")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path = output_dir / "08_ab_summary.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def write_summary(
    output_dir: Path,
    generated_files: list[str],
    skipped: list[str],
    model_record: dict[str, Any],
    training_run: dict[str, Any] | None,
) -> None:
    payload = {
        "model_version": model_record.get("model_version"),
        "artifact_path": model_record.get("artifact_path"),
        "generated_files": generated_files,
        "skipped": skipped,
        "training_run": training_run or {},
    }
    (output_dir / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
