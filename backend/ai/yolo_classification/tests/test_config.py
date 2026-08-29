from pathlib import Path

import pytest

from backend.ai.yolo_classification.src.config import ConfigError, load_config


def _write_config(path: Path, ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)) -> None:
    path.write_text(
        f"""
dataset:
  version: test-v1
  raw_root: raw
  processed_root: processed
  sources:
    - name: sample
      mapping: mapping.yaml
split:
  train: {ratios[0]}
  val: {ratios[1]}
  test: {ratios[2]}
  seed: 42
model:
  version: model-v1
  name: local.pt
  imgsz: 224
  epochs: 1
  batch: 2
  device: cpu
output:
  runs_dir: runs
  production_model: model.pt
  archive_dir: archive
""",
        encoding="utf-8",
    )


def test_config_parsing(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_config(path)
    config = load_config(path)
    assert config.data["dataset"]["version"] == "test-v1"
    assert config.raw_root == Path.cwd().resolve() / "raw"


def test_invalid_split_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_config(path, (0.8, 0.15, 0.15))
    with pytest.raises(ConfigError, match="must equal 1.0"):
        load_config(path)
