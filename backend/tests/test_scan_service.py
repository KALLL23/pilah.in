from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import UploadFile
from PIL import Image
from starlette.datastructures import Headers

from app.ai.classification import ClassificationPrediction
from app.core.config import Settings
from app.services.scans import ScanService


class FakeClassifier:
    async def predict(self, _content: bytes) -> ClassificationPrediction:
        return ClassificationPrediction(
            category_code="PLASTIC",
            confidence=0.65,
            model_version="PILAH-CLS-v0.1.0",
        )


class FakeStorage:
    def __init__(self) -> None:
        self.uploaded: tuple[str, bytes, str] | None = None

    async def upload(self, key: str, content: bytes, content_type: str) -> None:
        self.uploaded = (key, content, content_type)

    async def delete(self, _key: str) -> None:
        return None

    def presigned_get_url(self, key: str) -> str:
        return f"http://minio.test/{key}?signed=true"


class FakeRepository:
    def __init__(self) -> None:
        self.category = SimpleNamespace(id=1, code="PLASTIC", name="Plastik")

    async def get_category_by_code(self, code: str):
        return self.category if code == "PLASTIC" else None

    async def create_scan(
        self,
        *,
        user_id: UUID,
        image_key: str,
        predicted_category_id: int,
        confidence: float,
        model_version: str,
    ):
        now = datetime.now(timezone.utc)
        return SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            image_key=image_key,
            predicted_category_id=predicted_category_id,
            prediction_confidence=confidence,
            confirmed_category_id=None,
            is_reusable=None,
            is_contaminated=None,
            is_wet=None,
            recommendation_status="NOT_REQUESTED",
            recommendation_action=None,
            recommendation_reason=None,
            preparation_steps=None,
            recommendation_warnings=None,
            model_version=model_version,
            created_at=now,
            updated_at=now,
        )


def jpeg_upload() -> UploadFile:
    content = BytesIO()
    Image.new("RGB", (24, 24), color="white").save(content, format="JPEG")
    content.seek(0)
    return UploadFile(
        file=content,
        filename="scan.jpg",
        headers=Headers({"content-type": "image/jpeg"}),
    )


@pytest.mark.asyncio
async def test_infer_persists_prediction_and_returns_low_confidence() -> None:
    repository = FakeRepository()
    storage = FakeStorage()
    settings = Settings(max_image_bytes=1024 * 1024, model_confidence_threshold=0.70)
    service = ScanService(repository, FakeClassifier(), storage, settings)

    response = await service.infer(jpeg_upload(), uuid4())

    assert response.predicted_category.code == "PLASTIC"
    assert response.prediction_confidence == pytest.approx(0.65)
    assert response.low_confidence is True
    assert response.recommendation_status == "NOT_REQUESTED"
    assert storage.uploaded is not None
    assert storage.uploaded[0].startswith("scans/")
    assert storage.uploaded[0].endswith(".jpg")
