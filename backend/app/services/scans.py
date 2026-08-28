from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.ai.classification import ClassificationError, WasteClassifier
from app.core.config import Settings
from app.repositories.scans import ScanRepository, ScanView
from app.schemas.scans import (
    CategoryResponse,
    ScanCategory,
    ScanConfirmRequest,
    ScanListResponse,
    ScanResponse,
)
from app.services.image_validation import ImageValidationError, validate_image_upload
from app.services.storage import ObjectStorage, StorageError


class ScanNotFoundError(Exception):
    pass


class ScanDataError(Exception):
    pass


class ScanService:
    def __init__(
        self,
        repository: ScanRepository,
        classifier: WasteClassifier,
        storage: ObjectStorage,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.classifier = classifier
        self.storage = storage
        self.settings = settings

    async def infer(self, upload: UploadFile, user_id: UUID) -> ScanResponse:
        image = await validate_image_upload(upload, self.settings.max_image_bytes)
        prediction = await self.classifier.predict(image.content)
        category = await self.repository.get_category_by_code(prediction.category_code)
        if category is None:
            raise ScanDataError(f"Category {prediction.category_code} is not seeded")

        now = datetime.now(timezone.utc)
        image_key = f"scans/{now:%Y/%m}/{uuid4()}{image.extension}"
        await self.storage.upload(image_key, image.content, image.content_type)
        try:
            scan = await self.repository.create_scan(
                user_id=user_id,
                image_key=image_key,
                predicted_category_id=category.id,
                confidence=prediction.confidence,
                model_version=prediction.model_version,
            )
        except Exception:
            try:
                await self.storage.delete(image_key)
            except StorageError:
                pass
            raise

        view = ScanView(
            scan=scan,
            predicted_code=category.code,
            predicted_name=category.name,
            confirmed_code=None,
            confirmed_name=None,
        )
        return self._response(view)

    async def confirm(self, scan_id: UUID, user_id: UUID, request: ScanConfirmRequest) -> ScanResponse:
        view = await self.repository.get_owned_scan(scan_id, user_id)
        if view is None:
            raise ScanNotFoundError
        category = await self.repository.get_category_by_code(request.confirmed_category)
        if category is None:
            raise ScanDataError(f"Category {request.confirmed_category} is not seeded")

        await self.repository.confirm_scan(
            view.scan,
            category_id=category.id,
            is_reusable=request.is_reusable,
            is_contaminated=request.is_contaminated,
            is_wet=request.is_wet,
        )
        refreshed = await self.repository.get_owned_scan(scan_id, user_id)
        if refreshed is None:
            raise ScanNotFoundError
        return self._response(refreshed)

    async def get(self, scan_id: UUID, user_id: UUID) -> ScanResponse:
        view = await self.repository.get_owned_scan(scan_id, user_id)
        if view is None:
            raise ScanNotFoundError
        return self._response(view)

    async def list(self, user_id: UUID, *, limit: int, offset: int) -> ScanListResponse:
        views, total = await self.repository.list_owned_scans(user_id, limit=limit, offset=offset)
        return ScanListResponse(
            items=[self._response(view) for view in views],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def categories(self) -> list[CategoryResponse]:
        return [CategoryResponse.model_validate(category) for category in await self.repository.list_categories()]

    def _response(self, view: ScanView) -> ScanResponse:
        scan = view.scan
        predicted = ScanCategory(
            id=scan.predicted_category_id,
            code=view.predicted_code,
            name=view.predicted_name,
        )
        confirmed = None
        if scan.confirmed_category_id is not None and view.confirmed_code and view.confirmed_name:
            confirmed = ScanCategory(
                id=scan.confirmed_category_id,
                code=view.confirmed_code,
                name=view.confirmed_name,
            )
        return ScanResponse(
            id=scan.id,
            predicted_category=predicted,
            prediction_confidence=float(scan.prediction_confidence),
            low_confidence=float(scan.prediction_confidence) < self.settings.model_confidence_threshold,
            confirmed_category=confirmed,
            is_reusable=scan.is_reusable,
            is_contaminated=scan.is_contaminated,
            is_wet=scan.is_wet,
            recommendation_status=scan.recommendation_status or "NOT_REQUESTED",
            recommendation_action=scan.recommendation_action,
            recommendation_reason=scan.recommendation_reason,
            preparation_steps=scan.preparation_steps,
            recommendation_warnings=scan.recommendation_warnings,
            model_version=scan.model_version,
            image_url=self.storage.presigned_get_url(scan.image_key),
            created_at=scan.created_at,
            updated_at=scan.updated_at,
        )


__all__ = [
    "ClassificationError",
    "ImageValidationError",
    "ScanDataError",
    "ScanNotFoundError",
    "ScanService",
    "StorageError",
]
