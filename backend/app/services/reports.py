from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.ai.detection import DetectionError, WasteDetector
from app.core.config import Settings
from app.models.models import ReportStatus, WasteVolume
from app.repositories.reports import ReportRepository, ReportView
from app.schemas.reports import (
    ReportListResponse,
    ReportObjectResponse,
    ReportResponse,
    StatusSyncItem,
    StatusSyncResponse,
)
from app.services.geocoding import ReverseGeocoder
from app.services.image_validation import validate_image_upload
from app.services.risk import calculate_risk, persistence_score
from app.services.storage import ObjectStorage, StorageError


class ReportNotFoundError(Exception):
    pass


class ReportDependencyError(Exception):
    pass


class OutsideSemarangError(Exception):
    pass


class PossibleDuplicateError(Exception):
    def __init__(self, report_id: UUID) -> None:
        self.report_id = report_id


class ReportDataError(Exception):
    pass


class AlreadyConfirmedError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    pass


STATUS_TRANSITIONS = {
    ReportStatus.REPORTED: ReportStatus.VERIFIED,
    ReportStatus.VERIFIED: ReportStatus.IN_PROGRESS,
    ReportStatus.IN_PROGRESS: ReportStatus.RESOLVED,
}


class ReportService:
    def __init__(
        self,
        repository: ReportRepository,
        detector: WasteDetector,
        storage: ObjectStorage,
        geocoder: ReverseGeocoder,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.detector = detector
        self.storage = storage
        self.geocoder = geocoder
        self.settings = settings

    async def create(
        self,
        upload: UploadFile,
        user_id: UUID,
        *,
        latitude: float,
        longitude: float,
        location_accuracy_m: float | None,
        user_description: str | None,
        waste_volume: WasteVolume | None,
        standing_water: bool | None,
        drainage_blockage: bool | None,
        demo_mode: bool = False,
    ) -> ReportResponse:
        try:
            spatial_ready = await self.repository.spatial_ready()
        except SQLAlchemyError as error:
            raise ReportDependencyError from error
        if not self.detector.is_configured or not spatial_ready:
            raise ReportDependencyError
        image = await validate_image_upload(upload, self.settings.max_image_bytes)
        try:
            if not demo_mode:
                if not await self.repository.inside_semarang(latitude, longitude):
                    raise OutsideSemarangError
            duplicate_id = await self.repository.find_duplicate(latitude, longitude)
            if duplicate_id is not None:
                raise PossibleDuplicateError(duplicate_id)
        except SQLAlchemyError as error:
            raise ReportDependencyError from error
        try:
            detection = await self.detector.predict(image.content)
        except DetectionError as error:
            raise ReportDependencyError from error
        auto_volume = WasteVolume(detection.estimate_volume())
        final_volume = waste_volume if waste_volume is not None else auto_volume
        final_standing = standing_water if standing_water is not None else detection.standing_water_detected
        final_drainage = drainage_blockage if drainage_blockage is not None else detection.drainage_blockage_detected
        try:
            category_map = await self.repository.category_map([item.category_code for item in detection.objects])
        except SQLAlchemyError as error:
            raise ReportDataError from error
        if len(category_map) != len(set(item.category_code for item in detection.objects)):
            raise ReportDataError
        try:
            vulnerability = await self.repository.location_vulnerability(latitude, longitude)
        except SQLAlchemyError as error:
            raise ReportDependencyError from error
        risk = calculate_risk(
            waste_volume=final_volume,
            organic_presence=detection.organic_presence,
            standing_water=final_standing,
            drainage_blockage=final_drainage,
            location_vulnerability=vulnerability,
            confirmations=0,
        )
        address = await self.geocoder.reverse(latitude, longitude)
        now = datetime.now(timezone.utc)
        image_key = f"reports/{now:%Y/%m}/{uuid4()}{image.extension}"
        await self.storage.upload(image_key, image.content, image.content_type)
        try:
            report = await self.repository.create(
                detected_objects=detection.objects,
                category_map=category_map,
                latitude=latitude,
                longitude=longitude,
                user_id=user_id,
                image_key=image_key,
                location_accuracy_m=location_accuracy_m,
                address=address,
                user_description=user_description.strip() if user_description else None,
                waste_volume=final_volume,
                standing_water=final_standing,
                drainage_blockage=final_drainage,
                organic_presence=detection.organic_presence,
                location_vulnerability_score=vulnerability,
                persistence_score=0,
                risk_score=risk.score,
                risk_level=risk.level,
                risk_reasons=risk.reasons,
                status=ReportStatus.REPORTED,
                model_version=detection.model_version,
            )
            await self.repository.commit()
        except Exception as error:
            await self.repository.rollback()
            try:
                await self.storage.delete(image_key)
            except StorageError:
                pass
            if isinstance(error, SQLAlchemyError):
                raise ReportDataError from error
            raise
        view = await self.repository.get(report.id)
        assert view is not None
        return self._response(view)

    async def get_owned(self, report_id: UUID, user_id: UUID) -> ReportResponse:
        view = await self.repository.get(report_id)
        if view is None or view.report.user_id != user_id:
            raise ReportNotFoundError
        return self._response(view)

    async def get_admin(self, report_id: UUID) -> ReportResponse:
        view = await self.repository.get(report_id)
        if view is None:
            raise ReportNotFoundError
        return self._response(view)

    async def list_owned(self, user_id: UUID, *, limit: int, offset: int) -> ReportListResponse:
        records, total = await self.repository.list_owned(user_id, limit=limit, offset=offset)
        return ReportListResponse(items=[self._response(item) for item in records], total=total, limit=limit, offset=offset)

    async def list_admin(self, *, status: ReportStatus | None, limit: int, offset: int) -> ReportListResponse:
        records, total = await self.repository.list_admin(status=status, limit=limit, offset=offset)
        return ReportListResponse(items=[self._response(item) for item in records], total=total, limit=limit, offset=offset)

    async def confirm(self, report_id: UUID, user_id: UUID) -> ReportResponse:
        view = await self.repository.get(report_id)
        if view is None or view.report.status == ReportStatus.RESOLVED:
            raise ReportNotFoundError
        if await self.repository.has_confirmation(report_id, user_id):
            raise AlreadyConfirmedError
        confirmations = view.confirmation_count + 1
        risk = calculate_risk(
            waste_volume=view.report.waste_volume,
            organic_presence=view.report.organic_presence,
            standing_water=view.report.standing_water,
            drainage_blockage=view.report.drainage_blockage,
            location_vulnerability=view.report.location_vulnerability_score,
            confirmations=confirmations,
        )
        try:
            await self.repository.confirm(
                view.report,
                user_id,
                persistence=persistence_score(confirmations),
                risk_score=risk.score,
                risk_level=risk.level,
                risk_reasons=risk.reasons,
            )
        except IntegrityError as error:
            await self.repository.rollback()
            raise AlreadyConfirmedError from error
        refreshed = await self.repository.get(report_id)
        assert refreshed is not None
        return self._response(refreshed)

    async def change_status(self, report_id: UUID, admin_id: UUID, new_status: ReportStatus) -> ReportResponse:
        view = await self.repository.get(report_id)
        if view is None:
            raise ReportNotFoundError
        if STATUS_TRANSITIONS.get(view.report.status) != new_status:
            raise InvalidStatusTransitionError
        await self.repository.change_status(view.report, admin_id, new_status)
        refreshed = await self.repository.get(report_id)
        assert refreshed is not None
        return self._response(refreshed)

    async def sync(self, user_id: UUID, since: datetime) -> StatusSyncResponse:
        items = await self.repository.sync_status(user_id, since)
        return StatusSyncResponse(
            items=[
                StatusSyncItem(
                    history_id=history.id,
                    report_id=report_id,
                    from_status=history.from_status,
                    to_status=history.to_status,
                    changed_at=history.created_at,
                )
                for history, report_id in items
            ],
            server_time=datetime.now(timezone.utc),
        )

    def _response(self, view: ReportView) -> ReportResponse:
        report = view.report
        return ReportResponse(
            id=report.id,
            user_id=report.user_id,
            image_url=self.storage.presigned_get_url(report.image_key),
            latitude=view.latitude,
            longitude=view.longitude,
            location_accuracy_m=float(report.location_accuracy_m) if report.location_accuracy_m is not None else None,
            address=report.address,
            user_description=report.user_description,
            waste_volume=report.waste_volume,
            standing_water=report.standing_water,
            drainage_blockage=report.drainage_blockage,
            organic_presence=report.organic_presence,
            location_vulnerability_score=report.location_vulnerability_score,
            persistence_score=report.persistence_score,
            risk_score=float(report.risk_score),
            risk_level=report.risk_level,
            risk_reasons=report.risk_reasons,
            status=report.status,
            model_version=report.model_version,
            objects=[
                ReportObjectResponse(
                    id=item.id,
                    category=category,
                    confidence=float(item.confidence),
                    bbox=item.bbox,
                )
                for item, category in view.objects
            ],
            confirmation_count=view.confirmation_count,
            created_at=report.created_at,
            updated_at=report.updated_at,
            resolved_at=report.resolved_at,
        )
