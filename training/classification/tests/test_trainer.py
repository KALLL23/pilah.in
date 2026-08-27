from pathlib import Path
from types import SimpleNamespace

import pytest

from training.classification.src.trainer import TrainingError, _resolve_weight_reference


def _config(tmp_path: Path, name: str) -> SimpleNamespace:
    return SimpleNamespace(repo_root=tmp_path, data={"model": {"name": name}})


def test_official_weight_name_is_forwarded_for_automatic_download(tmp_path: Path) -> None:
    assert _resolve_weight_reference(_config(tmp_path, "yolo26l-cls.pt")) == "yolo26l-cls.pt"


def test_missing_explicit_local_weight_fails(tmp_path: Path) -> None:
    with pytest.raises(TrainingError, match="does not exist"):
        _resolve_weight_reference(_config(tmp_path, "weights/custom.pt"))


def test_existing_local_weight_is_resolved(tmp_path: Path) -> None:
    weight = tmp_path / "custom.pt"
    weight.write_bytes(b"test-weight-placeholder")
    assert _resolve_weight_reference(_config(tmp_path, "custom.pt")) == str(weight.resolve())
