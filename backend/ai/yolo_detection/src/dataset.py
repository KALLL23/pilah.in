"""Validate, remap, split, and export a YOLO object-detection dataset."""

from __future__ import annotations

import csv
import json
import math
import random
import shutil
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from . import TAXONOMY

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SPLITS = ("train", "val", "test")


class DatasetError(RuntimeError):
    """Raised when raw images or YOLO annotations violate the dataset contract."""


@dataclass(frozen=True)
class Annotation:
    source_class_id: int
    target_class_id: int
    x_center: float
    y_center: float
    width: float
    height: float

    def to_yolo(self) -> str:
        return (
            f"{self.target_class_id} {self.x_center:.6f} {self.y_center:.6f} "
            f"{self.width:.6f} {self.height:.6f}"
        )


@dataclass
class DetectionRecord:
    image_id: str
    image_path: Path
    label_path: Path
    annotations: list[Annotation] = field(default_factory=list)
    split: str = ""

    @property
    def target_classes(self) -> set[int]:
        return {annotation.target_class_id for annotation in self.annotations}


def _parse_label(
    label_path: Path,
    source_names: tuple[str, ...],
    class_mapping: dict[str, str],
) -> list[Annotation]:
    annotations: list[Annotation] = []
    for line_number, raw_line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) != 5:
            raise DatasetError(f"Invalid YOLO annotation at {label_path}:{line_number}; expected 5 fields")
        try:
            class_id = int(fields[0])
            x_center, y_center, width, height = (float(value) for value in fields[1:])
        except ValueError as exc:
            raise DatasetError(f"Invalid numeric annotation at {label_path}:{line_number}") from exc
        if class_id < 0 or class_id >= len(source_names):
            raise DatasetError(f"Unknown class ID {class_id} at {label_path}:{line_number}")
        values = (x_center, y_center, width, height)
        if not all(math.isfinite(value) for value in values):
            raise DatasetError(f"Non-finite bounding box at {label_path}:{line_number}")
        if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and 0 < width <= 1 and 0 < height <= 1):
            raise DatasetError(f"Bounding box values must be normalized at {label_path}:{line_number}")
        if x_center - width / 2 < -1e-6 or x_center + width / 2 > 1 + 1e-6:
            raise DatasetError(f"Bounding box exceeds image width at {label_path}:{line_number}")
        if y_center - height / 2 < -1e-6 or y_center + height / 2 > 1 + 1e-6:
            raise DatasetError(f"Bounding box exceeds image height at {label_path}:{line_number}")
        source_name = source_names[class_id]
        target_name = class_mapping[source_name]
        annotations.append(
            Annotation(class_id, TAXONOMY.index(target_name), x_center, y_center, width, height)
        )
    return annotations


def discover_and_validate(config: Any) -> list[DetectionRecord]:
    if not config.images_root.is_dir():
        raise DatasetError(f"Raw image directory does not exist: {config.images_root}")
    if not config.labels_root.is_dir():
        raise DatasetError(f"Raw label directory does not exist: {config.labels_root}")
    images = sorted(
        (path for path in config.images_root.iterdir() if path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS),
        key=lambda path: path.name.casefold(),
    )
    if not images:
        raise DatasetError(f"No supported images found in {config.images_root}")
    image_stems = [path.stem.casefold() for path in images]
    if len(image_stems) != len(set(image_stems)):
        raise DatasetError("Raw image filenames must have unique stems")
    labels = {path.stem.casefold(): path for path in config.labels_root.iterdir() if path.is_file() and path.suffix.casefold() == ".txt"}
    if len(labels) != len([path for path in config.labels_root.iterdir() if path.is_file() and path.suffix.casefold() == ".txt"]):
        raise DatasetError("Raw label filenames must have unique stems")
    missing_labels = sorted(set(image_stems) - set(labels))
    orphan_labels = sorted(set(labels) - set(image_stems))
    if missing_labels:
        raise DatasetError(f"Images without labels: {', '.join(missing_labels[:5])}")
    if orphan_labels:
        raise DatasetError(f"Labels without images: {', '.join(orphan_labels[:5])}")

    class_mapping = {str(key): str(value) for key, value in config.data["dataset"]["class_mapping"].items()}
    records: list[DetectionRecord] = []
    for image_path in images:
        try:
            with Image.open(image_path) as image:
                image.verify()
        except Exception as exc:
            raise DatasetError(f"Corrupt or unsupported image: {image_path}") from exc
        label_path = labels[image_path.stem.casefold()]
        records.append(
            DetectionRecord(
                image_id=image_path.stem,
                image_path=image_path,
                label_path=label_path,
                annotations=_parse_label(label_path, config.source_names, class_mapping),
            )
        )
    return records


def _target_sizes(total: int, ratios: dict[str, float]) -> dict[str, int]:
    exact = {split: total * ratios[split] for split in SPLITS}
    sizes = {split: math.floor(exact[split]) for split in SPLITS}
    for split in sorted(SPLITS, key=lambda name: (exact[name] - sizes[name], -SPLITS.index(name)), reverse=True)[: total - sum(sizes.values())]:
        sizes[split] += 1
    return sizes


def assign_splits(records: list[DetectionRecord], ratios: dict[str, float], seed: int) -> None:
    """Assign deterministic, capacity-bounded splits with multi-label balancing."""
    sizes = _target_sizes(len(records), ratios)
    class_frequency = Counter(class_id for record in records for class_id in record.target_classes)
    randomizer = random.Random(seed)
    ordered = list(records)
    randomizer.shuffle(ordered)
    tie_breaker = {record.image_id: index for index, record in enumerate(ordered)}
    ordered.sort(
        key=lambda record: (
            min((class_frequency[class_id] for class_id in record.target_classes), default=len(records) + 1),
            -len(record.target_classes),
            tie_breaker[record.image_id],
        )
    )
    image_counts = Counter()
    class_counts: dict[str, Counter[int]] = {split: Counter() for split in SPLITS}
    for record in ordered:
        candidates = [split for split in SPLITS if image_counts[split] < sizes[split]]
        if not candidates:
            raise DatasetError("Internal split allocation error: no split has remaining capacity")

        def score(split: str) -> tuple[float, float, int]:
            class_deficit = sum(
                (ratios[split] * class_frequency[class_id] - class_counts[split][class_id])
                / max(ratios[split] * class_frequency[class_id], 1.0)
                for class_id in record.target_classes
            )
            capacity = (sizes[split] - image_counts[split]) / max(sizes[split], 1)
            return class_deficit + 0.25 * capacity, capacity, -SPLITS.index(split)

        selected = max(candidates, key=score)
        record.split = selected
        image_counts[selected] += 1
        class_counts[selected].update(record.target_classes)


def export_dataset(records: list[DetectionRecord], dataset_root: Path) -> Path:
    for split in SPLITS:
        (dataset_root / split / "images").mkdir(parents=True, exist_ok=True)
        (dataset_root / split / "labels").mkdir(parents=True, exist_ok=True)
    for record in records:
        if record.split not in SPLITS:
            raise DatasetError(f"Record has no valid split: {record.image_id}")
        image_target = dataset_root / record.split / "images" / record.image_path.name
        label_target = dataset_root / record.split / "labels" / f"{record.image_id}.txt"
        shutil.copy2(record.image_path, image_target)
        content = "\n".join(annotation.to_yolo() for annotation in record.annotations)
        label_target.write_text(f"{content}\n" if content else "", encoding="utf-8")
    dataset_yaml = dataset_root / "data.yaml"
    dataset_yaml.write_text(
        yaml.safe_dump(
            {
                "path": str(dataset_root.resolve()),
                "train": "train/images",
                "val": "val/images",
                "test": "test/images",
                "names": {index: name for index, name in enumerate(TAXONOMY)},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return dataset_yaml


def write_metadata(records: list[DetectionRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("image_id", "source_path", "label_path", "split", "object_count", "target_classes"))
        writer.writeheader()
        for record in sorted(records, key=lambda item: item.image_id):
            writer.writerow(
                {
                    "image_id": record.image_id,
                    "source_path": str(record.image_path),
                    "label_path": str(record.label_path),
                    "split": record.split,
                    "object_count": len(record.annotations),
                    "target_classes": "|".join(TAXONOMY[index] for index in sorted(record.target_classes)),
                }
            )


def write_dataset_report(config: Any, records: list[DetectionRecord], reports_root: Path) -> dict[str, Any]:
    reports_root.mkdir(parents=True, exist_ok=True)
    split_images = Counter(record.split for record in records)
    split_objects: dict[str, Counter[str]] = {split: Counter() for split in SPLITS}
    total_objects = Counter()
    for record in records:
        for annotation in record.annotations:
            class_name = TAXONOMY[annotation.target_class_id]
            total_objects[class_name] += 1
            split_objects[record.split][class_name] += 1
    report = {
        "dataset_version": config.data["dataset"]["version"],
        "images": len(records),
        "objects": sum(total_objects.values()),
        "image_splits": {split: split_images[split] for split in SPLITS},
        "objects_per_class": {name: total_objects[name] for name in TAXONOMY},
        "objects_per_split_and_class": {
            split: {name: split_objects[split][name] for name in TAXONOMY} for split in SPLITS
        },
        "source_split_policy": "ignored; regenerated from canonical images/ and labels/ to prevent overlap",
    }
    (reports_root / "dataset_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        f"# {config.data['dataset']['version']} dataset report",
        "",
        f"- Images: {report['images']}",
        f"- Objects: {report['objects']}",
        f"- Split: train={split_images['train']}, val={split_images['val']}, test={split_images['test']}",
        "- The downloaded split directory is ignored; fresh non-overlapping splits are built from canonical images and labels.",
        "",
        "| Class | Objects |",
        "|---|---:|",
        *(f"| {name} | {total_objects[name]} |" for name in TAXONOMY),
        "",
    ]
    (reports_root / "dataset_report.md").write_text("\n".join(lines), encoding="utf-8")
    return report
