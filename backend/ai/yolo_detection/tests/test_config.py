from pathlib import Path

import pytest

from backend.ai.yolo_detection.src.config import ConfigError, load_config


def _write_config(path: Path, *, taxonomy: str = "") -> None:
    path.write_text(
        f"""
dataset:
  version: test-v1
  raw_root: raw
  processed_root: processed
  images_dir: images
  labels_dir: labels
  source_names: [plastic, paper]
  class_mapping:
    plastic: plastic
    paper: paper_cardboard
{taxonomy}
split:
  train: 0.7
  val: 0.15
  test: 0.15
  seed: 42
model:
  version: PILAH-DET-test
  name: yolo26n.pt
  imgsz: 640
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
    assert config.source_names == ("plastic", "paper")
    assert config.raw_root == Path.cwd().resolve() / "raw"


def test_incompatible_taxonomy_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _write_config(path, taxonomy="  taxonomy: [plastic, paper_cardboard]\n")
    with pytest.raises(ConfigError, match="must exactly match"):
        load_config(path)
