"""Apply source-specific labels to the fixed pilah.in taxonomy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import TAXONOMY
from .discovery import load_mapping


class UnmappedClassError(ValueError):
    """Raised instead of silently discarding an unknown source class."""


def apply_mappings(records: list[dict[str, Any]], sources: list[dict[str, Any]], repo_root: Path) -> None:
    by_source: dict[str, dict[str, str]] = {}
    for source in sources:
        path = Path(source["mapping"])
        by_source[source["name"]] = load_mapping(path if path.is_absolute() else repo_root / path)
    unknown: dict[str, set[str]] = {}
    for record in records:
        source_mapping = by_source[record["source"]]
        original = record["original_class"].strip().casefold()
        if original not in source_mapping:
            unknown.setdefault(record["source"], set()).add(record["original_class"])
            continue
        target = source_mapping[original]
        if target.upper() == "EXCLUDE":
            if record.get("status") == "corrupt":
                record["target_class"] = ""
            else:
                record.update(target_class="", status="excluded", exclude_reason="mapping:EXCLUDE")
        elif target.casefold() not in TAXONOMY:
            raise ValueError(f"Invalid target class '{target}' in mapping for {record['source']}:{original}")
        else:
            record.update(
                target_class=target.casefold(),
                status=record.get("status", "discovered"),
                exclude_reason="",
            )
    if unknown:
        detail = "; ".join(f"{source}: {sorted(classes)}" for source, classes in sorted(unknown.items()))
        raise UnmappedClassError(
            f"Unmapped source class detected — {detail}. Review training/classification/mappings/<source>.yaml."
        )
