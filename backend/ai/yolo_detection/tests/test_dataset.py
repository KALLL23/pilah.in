from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from backend.ai.yolo_detection.src.dataset import DatasetError, assign_splits, discover_and_validate


def _config(tmp_path: Path) -> SimpleNamespace:
    images = tmp_path / "images"
    labels = tmp_path / "labels"
    images.mkdir()
    labels.mkdir()
    return SimpleNamespace(
        images_root=images,
        labels_root=labels,
        source_names=("paper", "cardboard", "battery"),
        data={
            "dataset": {
                "class_mapping": {
                    "paper": "paper_cardboard",
                    "cardboard": "paper_cardboard",
                    "battery": "electronic_special",
                }
            }
        },
    )


def test_annotations_are_validated_and_remapped(tmp_path: Path) -> None:
    config = _config(tmp_path)
    Image.new("RGB", (32, 32), "white").save(config.images_root / "sample.jpg")
    (config.labels_root / "sample.txt").write_text(
        "0 0.25 0.25 0.2 0.2\n1 0.75 0.75 0.2 0.2\n2 0.5 0.5 0.4 0.4\n",
        encoding="utf-8",
    )
    record = discover_and_validate(config)[0]
    assert [item.target_class_id for item in record.annotations] == [1, 1, 6]


def test_out_of_bounds_box_is_rejected(tmp_path: Path) -> None:
    config = _config(tmp_path)
    Image.new("RGB", (32, 32), "white").save(config.images_root / "bad.jpg")
    (config.labels_root / "bad.txt").write_text("0 0.95 0.5 0.2 0.2\n", encoding="utf-8")
    with pytest.raises(DatasetError, match="exceeds image width"):
        discover_and_validate(config)


def test_split_is_deterministic_capacity_bounded_and_disjoint(tmp_path: Path) -> None:
    config = _config(tmp_path)
    for index in range(20):
        Image.new("RGB", (16, 16), (index, index, index)).save(config.images_root / f"{index}.jpg")
        (config.labels_root / f"{index}.txt").write_text(
            f"{index % 3} 0.5 0.5 0.25 0.25\n",
            encoding="utf-8",
        )
    records = discover_and_validate(config)
    assign_splits(records, {"train": 0.7, "val": 0.15, "test": 0.15}, 42)
    first = {record.image_id: record.split for record in records}
    assert list(first.values()).count("train") == 14
    assert list(first.values()).count("val") == 3
    assert list(first.values()).count("test") == 3
    assign_splits(records, {"train": 0.7, "val": 0.15, "test": 0.15}, 42)
    assert {record.image_id: record.split for record in records} == first
