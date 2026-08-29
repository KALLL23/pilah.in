from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.detection import WasteDetector
from app.api.dependencies import require_admin
from app.api.errors import ApiError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.models import ReportStatus, User
from app.repositories.reports import ReportRepository
from app.schemas.reports import ReportListResponse, ReportResponse, ReportStatusUpdateRequest
from app.services.geocoding import ReverseGeocoder
from app.services.reports import InvalidStatusTransitionError, ReportNotFoundError, ReportService
from app.services.storage import ObjectStorage, StorageError, get_object_storage

router = APIRouter(prefix="/api/v1/admin/reports", tags=["admin-reports"])


def get_admin_report_service(
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReportService:
    repository = ReportRepository(session)
    storage: ObjectStorage = getattr(request.app.state, "object_storage", get_object_storage())
    detector: WasteDetector = getattr(request.app.state, "waste_detector", None) or WasteDetector(settings)
    return ReportService(repository, detector, storage, ReverseGeocoder(repository, settings), settings)


@router.get("", response_model=ReportListResponse)
async def list_admin_reports(
    status: ReportStatus | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_admin),
    service: ReportService = Depends(get_admin_report_service),
) -> ReportListResponse:
    return await service.list_admin(status=status, limit=limit, offset=offset)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_admin_report(
    report_id: UUID,
    _admin: User = Depends(require_admin),
    service: ReportService = Depends(get_admin_report_service),
) -> ReportResponse:
    try:
        return await service.get_admin(report_id)
    except ReportNotFoundError as error:
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Laporan tidak ditemukan.") from error
    except StorageError as error:
        raise ApiError(503, "SERVER_UNAVAILABLE", "Penyimpanan gambar belum tersedia.") from error


@router.patch("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(
    report_id: UUID,
    payload: ReportStatusUpdateRequest,
    admin: User = Depends(require_admin),
    service: ReportService = Depends(get_admin_report_service),
) -> ReportResponse:
    try:
        return await service.change_status(report_id, admin.id, payload.status)
    except ReportNotFoundError as error:
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Laporan tidak ditemukan.") from error
    except InvalidStatusTransitionError as error:
        raise ApiError(409, "INVALID_STATUS_TRANSITION", "Transisi status laporan tidak valid.") from error
    except StorageError as error:
        raise ApiError(503, "SERVER_UNAVAILABLE", "Penyimpanan gambar belum tersedia.") from error
