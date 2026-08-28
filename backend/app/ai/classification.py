"""YOLO classification inference for the Scan Waste flow."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps
from ultralytics import YOLO

from app.core.config import Settings

WASTE_CATEGORY_CODES = frozenset(
    {
        "PLASTIC",
        "PAPER_CARDBOARD",
        "GLASS",
        "METAL",
        "ORGANIC",
        "TEXTILE",
        "ELECTRONIC_SPECIAL",
        "RESIDUAL_MIXED",
    }
)


class ClassificationError(Exception):
    """Raised when the classification model cannot produce a valid result."""


@dataclass(frozen=True)
class ClassificationPrediction:
    category_code: str
    confidence: float
    model_version: str


def normalize_model_label(label: str) -> str:
    category_code = label.strip().replace("-", "_").replace(" ", "_").upper()
    if category_code not in WASTE_CATEGORY_CODES:
        raise ClassificationError(f"Unsupported classification label: {label!r}")
    return category_code


class WasteClassifier:
    """Load one YOLO model instance and serialize inference against it."""

    def __init__(self, settings: Settings) -> None:
        self.model_path = Path(settings.classification_model)
        self.model_version = settings.classification_model_version
        self.image_size = settings.classification_image_size
        self._model: Any | None = None
        self._lock = asyncio.Lock()

    async def load(self) -> None:
        async with self._lock:
            if self._model is not None:
                return
            if not self.model_path.is_file():
                raise ClassificationError(f"Classification model not found at {self.model_path}")
            try:
                self._model = await asyncio.to_thread(YOLO, str(self.model_path))
            except Exception as error:
                raise ClassificationError("Classification model failed to load") from error

    async def predict(self, image_bytes: bytes) -> ClassificationPrediction:
        await self.load()
        try:
            with Image.open(BytesIO(image_bytes)) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
        except Exception as error:
            raise ClassificationError("Validated image could not be decoded for inference") from error

        async with self._lock:
            try:
                results = await asyncio.to_thread(
                    self._model.predict,
                    source=image,
                    imgsz=self.image_size,
                    verbose=False,
                )
                result = results[0]
                if result.probs is None:
                    raise ValueError("Model did not return classification probabilities")
                class_index = int(result.probs.top1)
                confidence = float(result.probs.top1conf.item())
                category_code = normalize_model_label(str(result.names[class_index]))
            except ClassificationError:
                raise
            except Exception as error:
                raise ClassificationError("Classification inference failed") from error

        return ClassificationPrediction(
            category_code=category_code,
            confidence=max(0.0, min(1.0, confidence)),
            model_version=self.model_version,
        )
