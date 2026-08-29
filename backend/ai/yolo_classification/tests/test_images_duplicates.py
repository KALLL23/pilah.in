from pathlib import Path

from PIL import Image

from backend.ai.yolo_classification.src.duplicates import remove_exact_duplicates
from backend.ai.yolo_classification.src.image_validation import validate_images


def _record(path: Path, relative: str) -> dict[str, str]:
    return {
        "source": "sample",
        "source_path": str(path),
        "relative_path": relative,
        "original_class": "plastic",
        "target_class": "plastic",
        "status": "discovered",
        "exclude_reason": "",
    }


def test_corrupt_image_detection(tmp_path: Path) -> None:
    corrupt = tmp_path / "bad.jpg"
    corrupt.write_bytes(b"not an image")
    records = [_record(corrupt, "plastic/bad.jpg")]
    validate_images(records)
    assert records[0]["status"] == "corrupt"
    assert records[0]["exclude_reason"].startswith("corrupt:")


def test_exact_duplicate_detection(tmp_path: Path) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGB", (8, 8), "red").save(first)
    second.write_bytes(first.read_bytes())
    records = [_record(first, "plastic/first.png"), _record(second, "plastic/second.png")]
    validate_images(records)
    duplicates = remove_exact_duplicates(records, tmp_path / "duplicates.csv")
    assert len(duplicates) == 1
    assert [record["status"] for record in records].count("duplicate") == 1
