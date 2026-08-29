"""Dataset audit helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any


def status_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get("status", "unknown")) for record in records).items()))


def assert_trainable(records: list[dict[str, Any]]) -> None:
    valid = [record for record in records if record.get("status") == "valid"]
    if not valid:
        raise RuntimeError("No valid mapped images remain after validation and deduplication")
