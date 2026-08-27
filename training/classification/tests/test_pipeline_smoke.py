from pathlib import Path

from PIL import Image

from training.classification.src.metadata import read_metadata
from training.classification.src.pipeline import run_pipeline


def test_offline_pipeline_smoke_without_training(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    mapping_paths: dict[str, Path] = {}
    sources = ("new_trash", "garbage_classification", "indo_waste")
    for source_index, source in enumerate(sources):
        mapping = tmp_path / f"{source}.yaml"
        mapping.write_text("mappings:\n  plastic: plastic\n  paper: paper_cardboard\n", encoding="utf-8")
        mapping_paths[source] = mapping
        for class_index, original_class in enumerate(("plastic", "paper")):
            directory = raw_root / source / "wrapper" / original_class
            directory.mkdir(parents=True)
            for image_index in range(8):
                # Different dimensions make the encoded image content unique,
                # so this fixture also exercises discovery through a wrapper.
                color = (source_index * 60 + 20, class_index * 90 + 20, image_index * 20)
                Image.new("RGB", (16 + image_index, 18 + source_index), color).save(directory / f"{image_index}.png")

    processed = tmp_path / "processed"
    runs = tmp_path / "runs"
    source_yaml = "\n".join(
        f"    - name: {source}\n      mapping: '{mapping_paths[source].as_posix()}'" for source in sources
    )
    config = tmp_path / "smoke.yaml"
    config.write_text(
        f"""
dataset:
  version: smoke-v1
  raw_root: '{raw_root.as_posix()}'
  processed_root: '{processed.as_posix()}'
  sources:
{source_yaml}
split:
  train: 0.70
  val: 0.15
  test: 0.15
  seed: 42
model:
  version: PILAH-CLS-smoke
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

    metadata = read_metadata(processed / "metadata.csv")
    assert len(metadata) == 48
    assert {record["split"] for record in metadata} == {"train", "val", "test"}
    assert (processed / "reports" / "dataset_report.json").is_file()
    assert (processed / "reports" / "leakage.csv").is_file()
    assert (processed / "dataset_cls" / "train" / "plastic").is_dir()
    assert (runs / "PILAH-CLS-smoke" / "config_snapshot.yaml").is_file()
