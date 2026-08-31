"""YOLO object detection for environmental waste reports."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
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
    standing_water_detected: bool = False
    drainage_blockage_detected: bool = False

    @property
    def organic_presence(self) -> bool:
        return any(item.category_code == "ORGANIC" for item in self.objects)

    @property
    def object_count(self) -> int:
        return len(self.objects)

    @property
    def total_bbox_area_ratio(self) -> float:
        if not self.objects:
            return 0.0
        total_area = 0.0
        for item in self.objects:
            w = item.bbox["x2"] - item.bbox["x1"]
            h = item.bbox["y2"] - item.bbox["y1"]
            total_area += max(0, w) * max(0, h)
        return total_area

    def estimate_volume(self) -> str:
        count = self.object_count
        area = self.total_bbox_area_ratio
        if count == 0:
            return "MEDIUM"
        if count <= 2 and area < 50000:
            return "SMALL"
        if count >= 5 or area >= 200000:
            return "LARGE"
        if count >= 3:
            return "LARGE"
        return "MEDIUM"


def _detect_standing_water_from_image(image: Image.Image) -> bool:
    try:
        w, h = image.size
        bottom_region = image.crop((0, int(h * 0.6), w, h))
        hsv = bottom_region.convert("HSV")
        pixels = list(hsv.getdata())
        water_pixels = 0
        total = len(pixels)
        if total == 0:
            return False
        for h_val, s_val, v_val in pixels:
            if 90 <= h_val <= 140 and s_val >= 40 and v_val <= 140:
                water_pixels += 1
        ratio = water_pixels / total
        return ratio > 0.04
    except Exception:
        return False


def _detect_drainage_from_image(image: Image.Image, objects: list[DetectedWaste]) -> bool:
    try:
        if len(objects) < 2:
            return False
        w, h = image.size
        bottom_third_y = h * 0.67
        clustered_count = 0
        for obj in objects:
            center_y = (obj.bbox["y1"] + obj.bbox["y2"]) / 2
            if center_y >= bottom_third_y:
                clustered_count += 1
        if clustered_count < 2:
            return False
        gray = image.convert("L")
        bottom_region = gray.crop((0, int(h * 0.5), w, h))
        pixels = list(bottom_region.getdata())
        dark_count = sum(1 for p in pixels if p < 80)
        dark_ratio = dark_count / max(1, len(pixels))
        return dark_ratio > 0.3
    except Exception:
        return False


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
        standing_water = await asyncio.to_thread(_detect_standing_water_from_image, image)
        drainage = await asyncio.to_thread(_detect_drainage_from_image, image, objects)
        return DetectionResult(
            objects=objects,
            model_version=self.model_version,
            standing_water_detected=standing_water,
            drainage_blockage_detected=drainage,
        )
