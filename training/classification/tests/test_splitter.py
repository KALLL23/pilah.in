from copy import deepcopy
from collections import Counter
from pathlib import Path

import pytest

from training.classification.src.splitter import LeakageError, assign_splits, validate_no_leakage


def _records() -> list[dict[str, str]]:
    records = []
    for index in range(60):
        records.append(
            {
                "image_id": f"image-{index}",
                "sha256": f"hash-{index}",
                "group_id": f"group-{index // 2}",
                "source": "source-a" if index % 2 else "source-b",
                "target_class": "plastic" if index % 3 else "glass",
                "status": "valid",
            }
        )
    return records


def test_split_is_deterministic_and_group_aware(tmp_path: Path) -> None:
    first = _records()
    second = deepcopy(first)
    ratios = {"train": 0.7, "val": 0.15, "test": 0.15}
    assign_splits(first, ratios, seed=42)
    assign_splits(second, ratios, seed=42)
    assert [record["split"] for record in first] == [record["split"] for record in second]
    assert {record["split"] for record in first} == {"train", "val", "test"}
    counts = Counter(record["split"] for record in first)
    assert 38 <= counts["train"] <= 44
    assert 8 <= counts["val"] <= 12
    assert 8 <= counts["test"] <= 12
    by_group: dict[str, set[str]] = {}
    for record in first:
        by_group.setdefault(record["group_id"], set()).add(record["split"])
    assert all(len(splits) == 1 for splits in by_group.values())
    validate_no_leakage(first, tmp_path / "leakage.csv")


def test_leakage_stops_pipeline(tmp_path: Path) -> None:
    records = _records()[:2]
    records[0]["split"] = "train"
    records[1]["split"] = "test"
    records[1]["sha256"] = records[0]["sha256"]
    with pytest.raises(LeakageError, match="Leakage detected"):
        validate_no_leakage(records, tmp_path / "leakage.csv")
