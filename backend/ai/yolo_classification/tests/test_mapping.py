from pathlib import Path

import pytest

from backend.ai.yolo_classification.src.mapping import UnmappedClassError, apply_mappings


def test_mapping_and_exclude(tmp_path: Path) -> None:
    mapping = tmp_path / "mapping.yaml"
    mapping.write_text("mappings:\n  PET: plastic\n  medical: EXCLUDE\n", encoding="utf-8")
    records = [
        {"source": "sample", "original_class": "pet", "status": "valid"},
        {"source": "sample", "original_class": "Medical", "status": "valid"},
    ]
    apply_mappings(records, [{"name": "sample", "mapping": str(mapping)}], tmp_path)
    assert records[0]["target_class"] == "plastic"
    assert records[0]["status"] == "valid"
    assert records[1]["status"] == "excluded"


def test_unknown_class_fails(tmp_path: Path) -> None:
    mapping = tmp_path / "mapping.yaml"
    mapping.write_text("mappings:\n  paper: paper_cardboard\n", encoding="utf-8")
    records = [{"source": "sample", "original_class": "mystery", "status": "valid"}]
    with pytest.raises(UnmappedClassError, match="Unmapped source class detected"):
        apply_mappings(records, [{"name": "sample", "mapping": str(mapping)}], tmp_path)
