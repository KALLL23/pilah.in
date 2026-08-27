"""Export a Windows-friendly Ultralytics classification directory."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from . import TAXONOMY
from .image_validation import normalize_copy


def _link_or_copy(source: Path, destination: Path) -> None:
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def export_dataset(records: list[dict[str, Any]], dataset_root: Path) -> None:
    for split in ("train", "val", "test"):
        for target in TAXONOMY:
            (dataset_root / split / target).mkdir(parents=True, exist_ok=True)
    normalized_root = dataset_root.parent / "normalized"
    for record in records:
        if record.get("status") != "valid":
            continue
        suffix = Path(record["source_path"]).suffix.casefold()
        needs_normalization = suffix not in {".jpg", ".jpeg"}
        normalized = normalized_root / f"{record['image_id']}.jpg"
        if needs_normalization:
            normalize_copy(Path(record["source_path"]), normalized)
            export_source = normalized
            record["processed_path"] = str(normalized.resolve())
            destination_suffix = ".jpg"
        else:
            # JPEGs are also rewritten when EXIF orientation is non-default or
            # their mode is not RGB; ordinary RGB JPEGs can be hardlinked.
            from PIL import Image

            with Image.open(record["source_path"]) as image:
                orientation = image.getexif().get(274, 1)
                needs_normalization = orientation != 1 or image.mode != "RGB"
            if needs_normalization:
                normalize_copy(Path(record["source_path"]), normalized)
                export_source = normalized
                record["processed_path"] = str(normalized.resolve())
                destination_suffix = ".jpg"
            else:
                export_source = Path(record["source_path"])
                destination_suffix = suffix
        destination = dataset_root / record["split"] / record["target_class"] / f"{record['image_id']}{destination_suffix}"
        _link_or_copy(export_source, destination)


def clear_export(dataset_root: Path) -> None:
    if dataset_root.exists():
        shutil.rmtree(dataset_root)
