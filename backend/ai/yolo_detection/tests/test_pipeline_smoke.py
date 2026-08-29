from pathlib import Path

import yaml
from PIL import Image

from backend.ai.yolo_detection.src.pipeline import run_pipeline


def test_offline_pipeline_smoke_without_training(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    images = raw / "images"
    labels = raw / "labels"
    images.mkdir(parents=True)
    labels.mkdir()
    for index in range(20):
        Image.new("RGB", (24 + index, 24), (index * 5, 20, 40)).save(images / f"syn_{index:03d}.jpg")
        (labels / f"syn_{index:03d}.txt").write_text(
            f"{index % 2} 0.5 0.5 0.25 0.25\n",
            encoding="utf-8",
        )
    processed = tmp_path / "processed"
    runs = tmp_path / "runs"
    config = tmp_path / "smoke.yaml"
    config.write_text(
        f"""
dataset:
  version: smoke-v1
  raw_root: '{raw.as_posix()}'
  processed_root: '{processed.as_posix()}'
  images_dir: images
  labels_dir: labels
  source_names: [paper, cardboard]
  class_mapping:
    paper: paper_cardboard
    cardboard: paper_cardboard
split:
  train: 0.70
  val: 0.15
  test: 0.15
  seed: 42
model:
  version: PILAH-DET-smoke
  name: unavailable-offline.pt
  imgsz: 32
  epochs: 1
  batch: 2
  device: cpu
output:
  runs_dir: '{runs.as_posix()}'
  production_model: '{(tmp_path / 'model.pt').as_posix()}'
  archive_dir: '{(tmp_path / 'archive').as_posix()}'
""",
        encoding="utf-8",
    )

    run_pipeline(config, skip_training=True)

    dataset = processed / "dataset"
    assert len(list((dataset / "train" / "images").iterdir())) == 14
    assert len(list((dataset / "val" / "images").iterdir())) == 3
    assert len(list((dataset / "test" / "images").iterdir())) == 3
    generated_config = yaml.safe_load((dataset / "data.yaml").read_text(encoding="utf-8"))
    assert generated_config["test"] == "test/images"
    assert generated_config["names"][1] == "paper_cardboard"
    assert (processed / "reports" / "dataset_report.json").is_file()
    assert (runs / "PILAH-DET-smoke" / "config_snapshot.yaml").is_file()
