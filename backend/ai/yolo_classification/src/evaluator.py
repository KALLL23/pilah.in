"""Evaluate the held-out test set beyond Ultralytics' default metrics."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from . import TAXONOMY


def evaluate(
    model_path: Path,
    records: list[dict[str, Any]],
    output_dir: Path,
    batch_size: int = 16,
) -> dict[str, Any]:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Ultralytics is required for evaluation") from exc
    test_records = sorted(
        (record for record in records if record.get("status") == "valid" and record.get("split") == "test"),
        key=lambda record: record["image_id"],
    )
    if not test_records:
        raise RuntimeError("The held-out test split is empty; add more data or revise split ratios")
    output_dir.mkdir(parents=True, exist_ok=True)
    sources = [record.get("processed_path") or record["source_path"] for record in test_records]
    model = YOLO(str(model_path))
    rows: list[dict[str, Any]] = []
    # A list of thousands of paths can be treated as one warm-up batch by
    # Ultralytics. Chunk explicitly as well as streaming to keep both GPU and
    # host memory bounded on consumer hardware.
    for start in range(0, len(test_records), batch_size):
        record_batch = test_records[start : start + batch_size]
        source_batch = sources[start : start + batch_size]
        results = model.predict(
            source=source_batch,
            stream=True,
            batch=batch_size,
            verbose=False,
            augment=False,
        )
        for record, result in zip(record_batch, results, strict=True):
            index = int(result.probs.top1)
            prediction = str(result.names[index]).casefold()
            rows.append(
                {
                    "image_id": record["image_id"],
                    "source": record["source"],
                    "ground_truth": record["target_class"],
                    "prediction": prediction,
                    "confidence": float(result.probs.top1conf),
                    "correct": prediction == record["target_class"],
                }
            )
    with (output_dir / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    truth = [row["ground_truth"] for row in rows]
    predicted = [row["prediction"] for row in rows]
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predicted, labels=list(TAXONOMY), zero_division=0
    )
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        truth, predicted, average="macro", zero_division=0
    )
    per_class = [
        {"class": label, "precision": float(precision[i]), "recall": float(recall[i]), "f1": float(f1[i]), "support": int(support[i])}
        for i, label in enumerate(TAXONOMY)
    ]
    with (output_dir / "per_class_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_class[0]))
        writer.writeheader()
        writer.writerows(per_class)
    source_metrics: dict[str, Any] = {}
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source[row["source"]].append(row)
    for source in sorted({record["source"] for record in records}):
        items = by_source[source]
        source_metrics[source] = (
            {
                "accuracy": float(accuracy_score([x["ground_truth"] for x in items], [x["prediction"] for x in items])),
                "macro_f1": float(precision_recall_fscore_support([x["ground_truth"] for x in items], [x["prediction"] for x in items], average="macro", zero_division=0)[2]),
                "sample_count": len(items),
            }
            if items
            else {"accuracy": None, "macro_f1": None, "sample_count": 0}
        )
    metrics = {
        "overall": {
            "accuracy": float(accuracy_score(truth, predicted)),
            "macro_precision": float(macro_precision),
            "macro_recall": float(macro_recall),
            "macro_f1": float(macro_f1),
            "sample_count": len(rows),
        },
        "per_source": source_metrics,
        "per_class": per_class,
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    matrix = confusion_matrix(truth, predicted, labels=list(TAXONOMY))
    figure, axis = plt.subplots(figsize=(10, 8))
    image = axis.imshow(matrix, cmap="Blues")
    axis.set(xticks=range(len(TAXONOMY)), yticks=range(len(TAXONOMY)), xticklabels=TAXONOMY, yticklabels=TAXONOMY, xlabel="Prediction", ylabel="Ground truth")
    plt.setp(axis.get_xticklabels(), rotation=45, ha="right")
    for row in range(len(TAXONOMY)):
        for column in range(len(TAXONOMY)):
            axis.text(column, row, str(matrix[row, column]), ha="center", va="center")
    figure.colorbar(image, ax=axis)
    figure.tight_layout()
    figure.savefig(output_dir / "confusion_matrix.png", dpi=160)
    plt.close(figure)
    return metrics
