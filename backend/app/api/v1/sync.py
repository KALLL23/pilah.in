from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.api.errors import ApiError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.reports import ReportRepository
from app.schemas.reports import StatusSyncResponse
from app.services.geocoding import ReverseGeocoder
from app.services.reports import ReportService
from app.services.storage import get_object_storage
from app.ai.detection import WasteDetector

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


@router.get("/report-status", response_model=StatusSyncResponse)
async def sync_report_status(
    since: datetime = Query(...),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> StatusSyncResponse:
    if since.tzinfo is None or since.utcoffset() is None:
        raise ApiError(422, "VALIDATION_ERROR", "Parameter since wajib menyertakan zona waktu.")
    repository = ReportRepository(session)
    service = ReportService(
        repository,
        WasteDetector(settings),
        get_object_storage(),
        ReverseGeocoder(repository, settings),
        settings,
    )
    return await service.sync(user_id, since)
