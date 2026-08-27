"""One-command PILAH-CLS preparation, training, evaluation, and publishing."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

from .audit import assert_trainable
from .config import load_config
from .discovery import discover_all
from .duplicates import remove_exact_duplicates
from .exporter import export_dataset
from .mapping import apply_mappings
from .metadata import write_metadata
from .reporting import generate_distributions, print_distributions, write_dataset_report, write_training_report
from .splitter import assign_splits, validate_no_leakage
from .trainer import publish_best, train
from .image_validation import validate_images


STAGE_NAMES = ("discover", "audit", "validate", "map", "duplicates", "metadata", "split", "export", "train", "evaluate", "report", "publish")
CURRENT_STAGE = "startup"


def _log(index: int, message: str) -> None:
    global CURRENT_STAGE
    CURRENT_STAGE = f"{index}/{len(STAGE_NAMES)} - {message}"
    print(f"\n[PILAH-CLS] Stage {index}/{len(STAGE_NAMES)} - {message}")


def _prepare_output(config: object, force: bool) -> None:
    processed_root = config.processed_root
    run_root = config.run_root
    occupied = [path for path in (processed_root, run_root) if path.exists() and any(path.iterdir())]
    if occupied and not force:
        joined = ", ".join(str(path) for path in occupied)
        raise RuntimeError(f"Generated output already exists: {joined}. Re-run with --force to rebuild it; raw data is never deleted.")
    if force:
        for path in (processed_root, run_root):
            if path.exists():
                shutil.rmtree(path)


def run_pipeline(config_path: str | Path, *, force: bool = False, skip_training: bool = False) -> None:
    config = load_config(config_path)
    _prepare_output(config, force)
    reports = config.processed_root / "reports"
    dataset_root = config.processed_root / "dataset_cls"
    run_reports = config.run_root / "reports"

    _log(1, "Dataset discovery")
    records = discover_all(config)
    print(f"[PILAH-CLS] Found {len(records):,} images")

    _log(2, "Source audit")
    print(f"[PILAH-CLS] Sources: {', '.join(source['name'] for source in config.data['dataset']['sources'])}")

    _log(3, "Image validation")
    validate_images(records)
    corrupt = sum(record["status"] == "corrupt" for record in records)
    print(f"[PILAH-CLS] Valid: {sum(record['status'] == 'valid' for record in records):,}; corrupt: {corrupt:,}")

    _log(4, "Fixed-taxonomy label mapping")
    apply_mappings(records, config.data["dataset"]["sources"], config.repo_root)
    print(f"[PILAH-CLS] Excluded by mapping: {sum(record['status'] == 'excluded' for record in records):,}")

    _log(5, "Exact duplicate detection")
    duplicates = remove_exact_duplicates(records, reports / "duplicates.csv")
    print(f"[PILAH-CLS] Exact duplicates removed: {len(duplicates):,}")
    assert_trainable(records)

    _log(6, "Master metadata")
    for record in records:
        record.setdefault("split", "")
    write_metadata(records, config.processed_root / "metadata.csv")

    _log(7, "Stratified/group-aware split and leakage validation")
    split_cfg = config.data["split"]
    assign_splits(records, {key: float(split_cfg[key]) for key in ("train", "val", "test")}, int(split_cfg["seed"]))
    validate_no_leakage(records, reports / "leakage.csv")
    class_rows, source_rows = generate_distributions(records, reports)
    print_distributions(class_rows, source_rows)

    _log(8, "YOLO classification dataset export")
    export_dataset(records, dataset_root)
    write_metadata(records, config.processed_root / "metadata.csv")

    _log(9, "YOLO classification training")
    write_dataset_report(config, records, len(duplicates), reports)
    config.run_root.mkdir(parents=True, exist_ok=True)
    (config.run_root / "config_snapshot.yaml").write_text(yaml.safe_dump(config.data, sort_keys=False), encoding="utf-8")
    if skip_training:
        print("[PILAH-CLS] Training, evaluation, and model publishing skipped by --skip-training")
        print(f"[PILAH-CLS] Prepared dataset: {dataset_root}")
        return
    best, duration, best_epoch = train(config, dataset_root)

    _log(10, "Held-out test evaluation")
    from .evaluator import evaluate

    metrics = evaluate(
        best,
        records,
        config.run_root / "evaluation",
        batch_size=int(config.data["model"]["batch"]),
    )

    _log(11, "Training report")
    write_training_report(config, metrics, duration, config.resolve(config.data["output"]["production_model"]), run_reports, best_epoch)

    _log(12, "Publish best model")
    production, archive = publish_best(config, best)
    print("[PILAH-CLS] Training complete")
    print(f"[PILAH-CLS] Macro F1: {metrics['overall']['macro_f1']:.6f}")
    print(f"[PILAH-CLS] Best model: {production}")
    print(f"[PILAH-CLS] Archive: {archive}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare datasets and train PILAH-CLS with one command")
    parser.add_argument("--config", required=True, help="Path to the pipeline YAML configuration")
    parser.add_argument("--force", action="store_true", help="Rebuild generated processed/run output; never deletes raw data")
    parser.add_argument("--skip-training", action="store_true", help="Prepare, validate, split, export, and report only")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        run_pipeline(args.config, force=args.force, skip_training=args.skip_training)
        return 0
    except Exception as exc:
        print(f"\n[PILAH-CLS] FAILED at stage {CURRENT_STAGE}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
