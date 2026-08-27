"""Non-destructive image validation and normalization."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError


def deterministic_image_id(source: str, relative_path: str) -> str:
    value = f"{source}\0{relative_path.replace('\\', '/')}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()[:24]


def validate_images(records: list[dict[str, Any]]) -> None:
    for record in records:
        record["image_id"] = deterministic_image_id(record["source"], record["relative_path"])
        record.setdefault("group_id", f"image:{record['image_id']}")
        record.update(width="", height="", sha256="", processed_path="")
        if record.get("status") == "excluded":
            continue
        path = Path(record["source_path"])
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                normalized = ImageOps.exif_transpose(image)
                normalized.convert("RGB").load()
                width, height = normalized.size
            record.update(width=width, height=height, sha256=digest, status="valid")
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            record.update(status="corrupt", exclude_reason=f"corrupt:{type(exc).__name__}")


def normalize_copy(source: Path, destination: Path) -> None:
    """Create a normalized RGB copy; the source file is never modified."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        normalized = ImageOps.exif_transpose(image).convert("RGB")
        normalized.save(destination, format="JPEG", quality=95, optimize=True)
