"""Master metadata persistence."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

METADATA_FIELDS = [
    "image_id",
    "source",
    "source_path",
    "relative_path",
    "processed_path",
    "original_class",
    "target_class",
    "width",
    "height",
    "sha256",
    "group_id",
    "split",
    "status",
    "exclude_reason",
]


def write_metadata(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METADATA_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in METADATA_FIELDS})


def read_metadata(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
