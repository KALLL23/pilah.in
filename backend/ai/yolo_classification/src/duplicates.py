"""Exact duplicate detection before splitting."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def remove_exact_duplicates(records: list[dict[str, Any]], report_path: Path) -> list[dict[str, str]]:
    canonical_by_hash: dict[str, dict[str, Any]] = {}
    duplicates: list[dict[str, str]] = []
    for record in sorted(records, key=lambda item: (item.get("source", ""), item.get("relative_path", ""))):
        if record.get("status") != "valid":
            continue
        digest = record["sha256"]
        canonical = canonical_by_hash.get(digest)
        if canonical is None:
            canonical_by_hash[digest] = record
            continue
        record.update(status="duplicate", exclude_reason=f"exact_duplicate:{canonical['image_id']}")
        duplicates.append(
            {
                "duplicate_image_id": record["image_id"],
                "canonical_image_id": canonical["image_id"],
                "sha256": digest,
                "duplicate_source_path": record["source_path"],
                "canonical_source_path": canonical["source_path"],
            }
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["duplicate_image_id", "canonical_image_id", "sha256", "duplicate_source_path", "canonical_source_path"]
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(duplicates)
    return duplicates
