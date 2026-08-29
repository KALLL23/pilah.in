from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.detection import WasteDetector
from app.api.dependencies import get_current_user_id
from app.api.errors import ApiError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.models import WasteVolume
from app.repositories.reports import ReportRepository
from app.schemas.reports import ReportListResponse, ReportResponse
from app.services.geocoding import ReverseGeocoder
from app.services.image_validation import ImageValidationError
from app.services.reports import (
    AlreadyConfirmedError,
    OutsideSemarangError,
    PossibleDuplicateError,
    ReportDataError,
    ReportDependencyError,
    ReportNotFoundError,
    ReportService,
)
from app.services.storage import ObjectStorage, StorageError, get_object_storage

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def get_report_service(
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReportService:
    repository = ReportRepository(session)
    storage: ObjectStorage = getattr(request.app.state, "object_storage", get_object_storage())
    detector: WasteDetector = getattr(request.app.state, "waste_detector", None) or WasteDetector(settings)
    return ReportService(
        repository,
        detector,
        storage,
        ReverseGeocoder(repository, settings),
        settings,
    )


def raise_report_error(error: Exception) -> None:
    if isinstance(error, ImageValidationError):
        status_code = 413 if error.code == "IMAGE_TOO_LARGE" else 415
        raise ApiError(status_code, error.code, error.message) from error
    if isinstance(error, ReportDependencyError):
        raise ApiError(503, "SERVER_UNAVAILABLE", "Model detection atau data spasial belum tersedia.") from error
    if isinstance(error, OutsideSemarangError):
        raise ApiError(422, "OUTSIDE_SEMARANG", "Lokasi laporan berada di luar Kota Semarang.") from error
    if isinstance(error, PossibleDuplicateError):
        raise ApiError(
            409,
            "POSSIBLE_DUPLICATE",
            "Masalah serupa sudah dilaporkan.",
            {"existing_report_id": str(error.report_id)},
        ) from error
    if isinstance(error, ReportNotFoundError):
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Laporan tidak ditemukan.") from error
    if isinstance(error, AlreadyConfirmedError):
        raise ApiError(409, "ALREADY_CONFIRMED", "Laporan sudah pernah dikonfirmasi oleh pengguna ini.") from error
    if isinstance(error, (ReportDataError, StorageError)):
        raise ApiError(503, "SERVER_UNAVAILABLE", "Backend laporan belum dapat digunakan.") from error
    raise error


@router.post("", response_model=ReportResponse, status_code=201)
async def create_report(
    image: UploadFile = File(...),
    latitude: float = Form(ge=-90, le=90),
    longitude: float = Form(ge=-180, le=180),
    location_accuracy_m: float | None = Form(default=None, ge=0),
    user_description: str | None = Form(default=None, max_length=2000),
    waste_volume: WasteVolume = Form(...),
    standing_water: bool = Form(...),
    drainage_blockage: bool = Form(...),
    user_id: UUID = Depends(get_current_user_id),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    try:
        return await service.create(
            image,
            user_id,
            latitude=latitude,
            longitude=longitude,
            location_accuracy_m=location_accuracy_m,
            user_description=user_description,
            waste_volume=waste_volume,
            standing_water=standing_water,
            drainage_blockage=drainage_blockage,
        )
    except (
        ImageValidationError,
        ReportDependencyError,
        OutsideSemarangError,
        PossibleDuplicateError,
        ReportDataError,
        StorageError,
    ) as error:
        raise_report_error(error)


@router.get("", response_model=ReportListResponse)
async def list_reports(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: ReportService = Depends(get_report_service),
) -> ReportListResponse:
    try:
        return await service.list_owned(user_id, limit=limit, offset=offset)
    except StorageError as error:
        raise_report_error(error)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    try:
        return await service.get_owned(report_id, user_id)
    except (ReportNotFoundError, StorageError) as error:
        raise_report_error(error)


@router.post("/{report_id}/confirm", response_model=ReportResponse)
async def confirm_report(
    report_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    try:
        return await service.confirm(report_id, user_id)
    except (ReportNotFoundError, AlreadyConfirmedError, StorageError) as error:
        raise_report_error(error)
