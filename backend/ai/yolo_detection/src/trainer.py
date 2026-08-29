"""Ultralytics YOLO object-detection training, evaluation, and publishing."""

from __future__ import annotations

import csv
import json
import shutil
import time
from pathlib import Path
from typing import Any


class TrainingError(RuntimeError):
    """Raised with actionable context when training cannot start or finish."""


def _resolve_weight_reference(config: Any) -> str:
    configured_value = str(config.data["model"]["name"])
    configured = Path(configured_value)
    candidates = [configured] if configured.is_absolute() else [config.repo_root / configured]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    if configured.is_absolute() or configured.parent != Path("."):
        raise TrainingError(f"Configured local pretrained weight does not exist: {configured}")
    return configured_value


def _best_epoch(results_csv: Path) -> int | None:
    if not results_csv.is_file():
        return None
    with results_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return None
    metric_keys = [key for key in rows[0] if "fitness" in key.casefold() or "map50-95" in key.casefold()]
    if not metric_keys:
        return None
    key = metric_keys[0]
    scored = [(float(row[key]), index + 1) for index, row in enumerate(rows) if row.get(key, "").strip()]
    return max(scored)[1] if scored else None


def train(config: Any, dataset_yaml: Path) -> tuple[Path, float, int | None]:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise TrainingError("Ultralytics is not installed; install backend/ai/yolo_detection/requirements.txt") from exc
    weight = _resolve_weight_reference(config)
    model_cfg = config.data["model"]
    train_cfg = dict(model_cfg.get("train", {}))
    started = time.monotonic()
    try:
        model = YOLO(weight)
        model.train(
            data=str(dataset_yaml),
            imgsz=int(model_cfg["imgsz"]),
            epochs=int(model_cfg["epochs"]),
            batch=int(model_cfg["batch"]),
            device=model_cfg["device"],
            project=str(config.run_root / "ultralytics"),
            name="train",
            exist_ok=False,
            **train_cfg,
        )
    except Exception as exc:
        raise TrainingError(
            f"Ultralytics detection training failed for '{weight}': {exc}. "
            "If the weight is not cached yet, check the internet connection and retry."
        ) from exc
    best = config.run_root / "ultralytics" / "train" / "weights" / "best.pt"
    if not best.is_file():
        raise TrainingError(f"Training completed without the required best.pt: {best}")
    return best, time.monotonic() - started, _best_epoch(best.parents[1] / "results.csv")


def evaluate(config: Any, best: Path, dataset_yaml: Path) -> dict[str, float]:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise TrainingError("Ultralytics is required for detection evaluation") from exc
    evaluation_root = config.run_root / "evaluation"
    evaluation_root.mkdir(parents=True, exist_ok=True)
    val_cfg = dict(config.data["model"].get("val", {}))
    try:
        result = YOLO(str(best)).val(
            data=str(dataset_yaml),
            split="test",
            imgsz=int(config.data["model"]["imgsz"]),
            batch=int(config.data["model"]["batch"]),
            device=config.data["model"]["device"],
            project=str(evaluation_root),
            name="test",
            plots=True,
            **val_cfg,
        )
    except Exception as exc:
        raise TrainingError(f"Held-out detection evaluation failed: {exc}") from exc
    metrics = {str(key): float(value) for key, value in result.results_dict.items()}
    (evaluation_root / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def write_training_report(config: Any, metrics: dict[str, float], duration_seconds: float, best_epoch: int | None) -> None:
    reports_root = config.run_root / "reports"
    reports_root.mkdir(parents=True, exist_ok=True)
    report = {
        "model_version": config.data["model"]["version"],
        "base_model": config.data["model"]["name"],
        "duration_seconds": duration_seconds,
        "best_epoch": best_epoch,
        "test_metrics": metrics,
    }
    (reports_root / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    metric_lines = [f"- {key}: {value:.6f}" for key, value in sorted(metrics.items())]
    text = "\n".join(
        [
            f"# {report['model_version']} training report",
            "",
            f"- Base model: {report['base_model']}",
            f"- Duration: {duration_seconds:.1f} seconds",
            f"- Best epoch: {best_epoch if best_epoch is not None else 'unavailable'}",
            "",
            "## Held-out test metrics",
            "",
            *metric_lines,
            "",
        ]
    )
    (reports_root / "training_report.md").write_text(text, encoding="utf-8")


def publish_best(config: Any, best: Path) -> tuple[Path, Path]:
    production = config.resolve(config.data["output"]["production_model"])
    archive = config.resolve(config.data["output"]["archive_dir"]) / f"{config.data['model']['version']}.pt"
    production.parent.mkdir(parents=True, exist_ok=True)
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, production)
    shutil.copy2(best, archive)
    return production, archive
