"""Machine-readable and human-readable pipeline reports."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from . import TAXONOMY


def _write_distribution(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate_distributions(records: list[dict[str, Any]], report_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid = [record for record in records if record.get("status") == "valid"]
    class_rows = []
    for target in TAXONOMY:
        counts = Counter(record["split"] for record in valid if record["target_class"] == target)
        class_rows.append({"class": target, **{split: counts[split] for split in ("train", "val", "test")}, "total": sum(counts.values())})
    sources = sorted({record["source"] for record in records})
    source_rows = []
    for source in sources:
        counts = Counter(record["split"] for record in valid if record["source"] == source)
        source_rows.append({"source": source, **{split: counts[split] for split in ("train", "val", "test")}, "total": sum(counts.values())})
    split_rows = []
    for split in ("train", "val", "test"):
        split_records = [record for record in valid if record["split"] == split]
        for target in TAXONOMY:
            for source in sources:
                count = sum(1 for record in split_records if record["target_class"] == target and record["source"] == source)
                split_rows.append({"split": split, "class": target, "source": source, "count": count})
    _write_distribution(report_dir / "class_distribution.csv", class_rows, ["class", "train", "val", "test", "total"])
    _write_distribution(report_dir / "source_distribution.csv", source_rows, ["source", "train", "val", "test", "total"])
    _write_distribution(report_dir / "split_distribution.csv", split_rows, ["split", "class", "source", "count"])
    return class_rows, source_rows


def print_distributions(class_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> None:
    print(f"{'Class':24} {'Train':>7} {'Val':>7} {'Test':>7} {'Total':>7}")
    for row in class_rows:
        print(f"{row['class'].upper():24} {row['train']:7} {row['val']:7} {row['test']:7} {row['total']:7}")
    print()
    print(f"{'Source':24} {'Train':>7} {'Val':>7} {'Test':>7}")
    for row in source_rows:
        print(f"{row['source']:24} {row['train']:7} {row['val']:7} {row['test']:7}")


def write_dataset_report(config: Any, records: list[dict[str, Any]], duplicate_count: int, report_dir: Path) -> dict[str, Any]:
    statuses = Counter(record.get("status", "unknown") for record in records)

    def reason_category(reason: str) -> str:
        # Duplicate reasons include a canonical image ID. Aggregate them in the
        # summary report; the complete pair-level detail remains in duplicates.csv.
        return reason.split(":", maxsplit=1)[0] if reason else "unspecified"

    excluded_breakdown = [
        {"source": source, "original_class": original_class, "reason": reason, "count": count}
        for (source, original_class, reason), count in sorted(
            Counter(
                (
                    record["source"],
                    record["original_class"],
                    reason_category(record.get("exclude_reason", "")),
                )
                for record in records
                if record.get("status") in {"excluded", "corrupt", "duplicate"}
            ).items()
        )
    ]
    report = {
        "dataset_version": config.data["dataset"]["version"],
        "sources": [source["name"] for source in config.data["dataset"]["sources"]],
        "taxonomy": [target.upper() for target in TAXONOMY],
        "split": {key: config.data["split"][key] for key in ("train", "val", "test")},
        "seed": config.data["split"]["seed"],
        "raw_images": len(records),
        "valid_images": statuses["valid"],
        "excluded": statuses["excluded"],
        "corrupt": statuses["corrupt"],
        "exact_duplicates_removed": duplicate_count,
        "unmapped": 0,
        "excluded_breakdown": excluded_breakdown,
        "known_limitations": [
            "group_id defaults to one image per group unless a source-specific grouping rule is configured",
            "near-duplicate detection is not automatic; exact SHA-256 duplicates are removed",
            "source mappings must be reviewed against the exact dataset editions extracted locally",
        ],
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "dataset_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# PILAH-CLS Dataset Report",
        "",
        f"- Dataset Version: `{report['dataset_version']}`",
        f"- Sources: {', '.join(report['sources'])}",
        f"- Taxonomy: {len(TAXONOMY)} classes",
        f"- Split: {report['split']['train']}/{report['split']['val']}/{report['split']['test']}",
        f"- Seed: {report['seed']}",
        f"- Raw Images: {report['raw_images']}",
        f"- Valid Images: {report['valid_images']}",
        f"- Excluded: {report['excluded']}",
        f"- Corrupt: {report['corrupt']}",
        f"- Exact Duplicates Removed: {report['exact_duplicates_removed']}",
        "",
        "## Known Limitations",
        "",
        *[f"- {item}" for item in report["known_limitations"]],
        "",
        "## Excluded / Invalid Breakdown",
        "",
        *(
            [f"- `{item['source']}:{item['original_class']}` — {item['reason']} ({item['count']})" for item in excluded_breakdown]
            or ["- None"]
        ),
    ]
    (report_dir / "dataset_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def write_training_report(config: Any, metrics: dict[str, Any], duration: float, model_path: Path, report_dir: Path, best_epoch: int | None = None) -> None:
    model = config.data["model"]
    report = {
        "model_version": model["version"],
        "dataset_version": config.data["dataset"]["version"],
        "base_weight": model["name"],
        "epochs": model["epochs"],
        "imgsz": model["imgsz"],
        "batch": model["batch"],
        "device": model["device"],
        "training_duration_seconds": duration,
        "best_epoch": best_epoch,
        "test_metrics": metrics,
        "model_path": str(model_path),
        "known_issues": [],
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    overall = metrics["overall"]
    lines = [
        "# PILAH-CLS Training Report", "",
        f"- Model version: `{model['version']}`",
        f"- Dataset version: `{config.data['dataset']['version']}`",
        f"- Base weight: `{model['name']}`",
        f"- Duration: {duration:.1f} seconds",
        f"- Test accuracy: {overall['accuracy']:.6f}",
        f"- Test macro F1: {overall['macro_f1']:.6f}",
        f"- Production model: `{model_path}`",
    ]
    (report_dir / "training_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
