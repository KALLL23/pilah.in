"""Ultralytics YOLO classification training adapter."""

from __future__ import annotations

import csv
import shutil
import time
from pathlib import Path
from typing import Any


class TrainingError(RuntimeError):
    """Raised with actionable context when training cannot start or finish."""


def _resolve_weight_reference(config: Any) -> str:
    """Return a local weight path or an official model name for auto-download."""
    configured_value = str(config.data["model"]["name"])
    configured = Path(configured_value)
    candidates = [configured] if configured.is_absolute() else [config.repo_root / configured]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    if configured.is_absolute() or configured.parent != Path("."):
        raise TrainingError(f"Configured local pretrained weight does not exist: {configured}")
    # Bare official filenames are intentionally passed to Ultralytics. It will
    # download the exact model on first use and reuse the local file afterward.
    return configured_value


def _best_epoch(results_csv: Path) -> int | None:
    if not results_csv.is_file():
        return None
    with results_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return None
    metric_keys = [key for key in rows[0] if "fitness" in key.casefold() or "accuracy_top1" in key.casefold()]
    if not metric_keys:
        return None
    key = metric_keys[0]
    scored = [(float(row[key]), index + 1) for index, row in enumerate(rows) if row.get(key, "").strip()]
    return max(scored)[1] if scored else None


def train(config: Any, dataset_root: Path) -> tuple[Path, float, int | None]:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise TrainingError("Ultralytics is not installed; install backend/ai/yolo_classification/requirements.txt") from exc
    weight = _resolve_weight_reference(config)
    model_cfg = config.data["model"]
    train_cfg = dict(model_cfg.get("train", {}))
    started = time.monotonic()
    try:
        model = YOLO(weight)
        model.train(
            data=str(dataset_root),
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
            f"Ultralytics classification training failed for '{weight}': {exc}. "
            "If the weight is not cached yet, check the internet connection and retry; "
            "offline runs require the weight to have been downloaded previously."
        ) from exc
    best = config.run_root / "ultralytics" / "train" / "weights" / "best.pt"
    if not best.is_file():
        raise TrainingError(f"Training completed without the required best.pt: {best}")
    return best, time.monotonic() - started, _best_epoch(best.parents[1] / "results.csv")


def publish_best(config: Any, best: Path) -> tuple[Path, Path]:
    production = config.resolve(config.data["output"]["production_model"])
    archive = config.resolve(config.data["output"]["archive_dir"]) / f"{config.data['model']['version']}.pt"
    production.parent.mkdir(parents=True, exist_ok=True)
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, production)
    shutil.copy2(best, archive)
    return production, archive
