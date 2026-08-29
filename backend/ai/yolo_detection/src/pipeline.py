"""One-command SynWasteNet preparation, YOLO training, evaluation, and publishing."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

from .config import load_config
from .dataset import assign_splits, discover_and_validate, export_dataset, write_dataset_report, write_metadata
from .trainer import evaluate, publish_best, train, write_training_report

STAGE_NAMES = ("validate", "split", "export", "report", "train", "evaluate", "publish")
CURRENT_STAGE = "startup"


def _log(index: int, message: str) -> None:
    global CURRENT_STAGE
    CURRENT_STAGE = f"{index}/{len(STAGE_NAMES)} - {message}"
    print(f"\n[PILAH-DET] Stage {index}/{len(STAGE_NAMES)} - {message}")


def _prepare_output(config: object, force: bool) -> None:
    occupied = [path for path in (config.processed_root, config.run_root) if path.exists() and any(path.iterdir())]
    if occupied and not force:
        joined = ", ".join(str(path) for path in occupied)
        raise RuntimeError(f"Generated output already exists: {joined}. Re-run with --force; raw data is never deleted.")
    if force:
        for path in (config.processed_root, config.run_root):
            if path.exists():
                shutil.rmtree(path)


def run_pipeline(config_path: str | Path, *, force: bool = False, skip_training: bool = False) -> None:
    config = load_config(config_path)
    _prepare_output(config, force)
    dataset_root = config.processed_root / "dataset"
    reports_root = config.processed_root / "reports"

    _log(1, "Canonical image and annotation validation")
    records = discover_and_validate(config)
    print(f"[PILAH-DET] Validated {len(records):,} images and {sum(len(record.annotations) for record in records):,} boxes")

    _log(2, "Deterministic multi-label split")
    split_cfg = config.data["split"]
    assign_splits(records, {key: float(split_cfg[key]) for key in ("train", "val", "test")}, int(split_cfg["seed"]))
    print("[PILAH-DET] Rebuilt train/val/test from canonical files; downloaded overlapping split was ignored")

    _log(3, "Eight-class YOLO dataset export")
    dataset_yaml = export_dataset(records, dataset_root)
    write_metadata(records, config.processed_root / "metadata.csv")

    _log(4, "Dataset report and configuration snapshot")
    write_dataset_report(config, records, reports_root)
    config.run_root.mkdir(parents=True, exist_ok=True)
    (config.run_root / "config_snapshot.yaml").write_text(yaml.safe_dump(config.data, sort_keys=False), encoding="utf-8")
    if skip_training:
        print("[PILAH-DET] Training, evaluation, and model publishing skipped by --skip-training")
        print(f"[PILAH-DET] Prepared dataset: {dataset_root}")
        return

    _log(5, f"{config.data['model']['name']} object-detection training")
    best, duration, best_epoch = train(config, dataset_yaml)

    _log(6, "Held-out test evaluation")
    metrics = evaluate(config, best, dataset_yaml)
    write_training_report(config, metrics, duration, best_epoch)

    _log(7, "Publish best model")
    production, archive = publish_best(config, best)
    print("[PILAH-DET] Training complete")
    print(f"[PILAH-DET] Best model: {production}")
    print(f"[PILAH-DET] Archive: {archive}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare SynWasteNet and train PILAH-DET with one command")
    parser.add_argument("--config", required=True, help="Path to the pipeline YAML configuration")
    parser.add_argument("--force", action="store_true", help="Rebuild generated processed/run output; never deletes raw data")
    parser.add_argument("--skip-training", action="store_true", help="Validate, remap, split, export, and report only")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        run_pipeline(args.config, force=args.force, skip_training=args.skip_training)
        return 0
    except Exception as exc:
        print(f"\n[PILAH-DET] FAILED at stage {CURRENT_STAGE}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
