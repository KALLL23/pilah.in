"""YOLO object detection for environmental waste reports."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps
from ultralytics import YOLO

from app.ai.classification import normalize_model_label
from app.core.config import Settings


class DetectionError(Exception):
    pass


@dataclass(frozen=True)
class DetectedWaste:
    category_code: str
    confidence: float
    bbox: dict[str, float]


@dataclass(frozen=True)
class DetectionResult:
    objects: list[DetectedWaste]
    model_version: str

    @property
    def organic_presence(self) -> bool:
        return any(item.category_code == "ORGANIC" for item in self.objects)


class WasteDetector:
    def __init__(self, settings: Settings) -> None:
        self.model_path = Path(settings.detection_model)
        self.model_version = settings.detection_model_version
        self.confidence_threshold = settings.detection_confidence_threshold
        self._model: Any | None = None
        self._lock = asyncio.Lock()

    @property
    def is_configured(self) -> bool:
        return self.model_path.is_file()

    async def load(self) -> None:
        async with self._lock:
            if self._model is not None:
                return
            if not self.model_path.is_file():
                raise DetectionError(f"Detection model not found at {self.model_path}")
            try:
                self._model = await asyncio.to_thread(YOLO, str(self.model_path))
            except Exception as error:
                raise DetectionError("Detection model failed to load") from error

    async def predict(self, image_bytes: bytes) -> DetectionResult:
        await self.load()
        try:
            with Image.open(BytesIO(image_bytes)) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
        except Exception as error:
            raise DetectionError("Validated image could not be decoded") from error
        async with self._lock:
            try:
                results = await asyncio.to_thread(
                    self._model.predict,
                    source=image,
                    conf=self.confidence_threshold,
                    verbose=False,
                )
                result = results[0]
                objects: list[DetectedWaste] = []
                boxes = result.boxes if result.boxes is not None else []
                for box in boxes:
                    class_index = int(box.cls[0].item())
                    coordinates = [float(value) for value in box.xyxy[0].tolist()]
                    objects.append(
                        DetectedWaste(
                            category_code=normalize_model_label(str(result.names[class_index])),
                            confidence=max(0.0, min(1.0, float(box.conf[0].item()))),
                            bbox={"x1": coordinates[0], "y1": coordinates[1], "x2": coordinates[2], "y2": coordinates[3]},
                        )
                    )
            except Exception as error:
                raise DetectionError("Detection inference failed") from error
        return DetectionResult(objects=objects, model_version=self.model_version)
