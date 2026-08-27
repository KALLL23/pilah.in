# PILAH-CLS Training Pipeline

This package builds and trains the eight-class **YOLO classification** model. It is intentionally separate from `backend/app`; it does not implement object detection or download datasets.

## Setup (Windows)

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r training/classification/requirements.txt
```

## Raw dataset location

The current local datasets are read from the existing ignored directory:

```text
backend/ai/raw_data/
├── new-dataset-trash-type-v2/
├── garbage_classification/
└── indo_waste/
```

Nested wrapper directories are supported. The closest parent directory whose name occurs in the source mapping is treated as the original class. Supported image extensions are `.jpg`, `.jpeg`, `.png`, and `.webp`, case-insensitively. Raw files are read-only to this pipeline and `/backend/ai/raw_data/` is ignored by Git.

The three mapping files mirror the class directories currently present in those sources. An unknown class stops the pipeline with `Unmapped source class detected`; it is never discarded silently. `Sampah_Medis` from `indo_waste` is explicitly `EXCLUDE`: medical waste is neither ordinary residual waste nor electronic waste, and pilah.in does not yet have a dedicated medical taxonomy.

## Run the full pipeline

The configured baseline is `yolo26l-cls.pt`. On first use, Ultralytics downloads this official classification weight automatically if it is not already available locally. Then run:

```powershell
python -m training.classification.src.pipeline --config training/classification/configs/pilah_cls_v0.1.yaml
```

For a fully offline run, start the model once while online or place the exact weight in the repository root beforehand. The pipeline never substitutes a different model silently.

Useful safe re-run options:

```powershell
# Prepare/export and report without training (also used for smoke tests)
python -m training.classification.src.pipeline --config training/classification/configs/pilah_cls_v0.1.yaml --skip-training

# Explicitly rebuild generated processed/run output; raw data is never removed
python -m training.classification.src.pipeline --config training/classification/configs/pilah_cls_v0.1.yaml --force
```

## Pipeline and outputs

The command discovers sources, audits and validates images, applies explicit mappings, removes exact SHA-256 duplicates, assigns deterministic group-aware stratified splits, verifies leakage, exports the YOLO classification dataset, trains, evaluates the held-out test set, writes reports, and copies only `best.pt`.

```text
data/processed/classification/
├── metadata.csv
├── dataset_cls/{train,val,test}/<class>/
├── normalized/                       # non-destructive RGB/EXIF-normalized copies when needed
└── reports/
    ├── duplicates.csv
    ├── leakage.csv
    ├── class_distribution.csv
    ├── source_distribution.csv
    ├── split_distribution.csv
    ├── dataset_report.json
    └── dataset_report.md

runs/classification/PILAH-CLS-v0.1.0/
├── config_snapshot.yaml
├── ultralytics/
├── evaluation/{metrics.json,per_class_metrics.csv,confusion_matrix.png,predictions.csv}
└── reports/{training_report.json,training_report.md}

models/waste_cls.pt
models/archive/PILAH-CLS-v0.1.0.pt
```

By default, each image is its own `group_id` because the configured sources do not provide reliable object/scene metadata. The splitter already keeps any shared group intact when group IDs are supplied in future source adapters. This limitation is included in the dataset report. Exact duplicates are removed before splitting; perceptual near-duplicates are not auto-removed.

## Tests

```powershell
python -m pytest training/classification/tests -q
```
