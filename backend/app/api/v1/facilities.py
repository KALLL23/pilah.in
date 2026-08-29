from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.api.errors import ApiError
from app.db.session import get_db
from app.models.models import FacilityType
from app.repositories.facilities import FacilityRepository
from app.schemas.facilities import FacilityListResponse, FacilityResponse
from app.services.facilities import FacilityCategoryError, FacilityNotFoundError, FacilityService

router = APIRouter(prefix="/api/v1/facilities", tags=["facilities"])


def get_facility_service(session: AsyncSession = Depends(get_db)) -> FacilityService:
    return FacilityService(FacilityRepository(session))


@router.get("", response_model=FacilityListResponse)
async def list_facilities(
    category: str | None = None,
    facility_type: FacilityType | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _user_id: UUID = Depends(get_current_user_id),
    service: FacilityService = Depends(get_facility_service),
) -> FacilityListResponse:
    try:
        return await service.list_public(category=category, facility_type=facility_type, limit=limit, offset=offset)
    except FacilityCategoryError as error:
        raise ApiError(422, "VALIDATION_ERROR", "Kategori fasilitas tidak valid.") from error


@router.get("/nearby", response_model=list[FacilityResponse])
async def nearby_facilities(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    category: str = Query(min_length=1, max_length=40),
    radius_km: float = Query(default=10, gt=0, le=50),
    limit: int = Query(default=20, ge=1, le=20),
    _user_id: UUID = Depends(get_current_user_id),
    service: FacilityService = Depends(get_facility_service),
) -> list[FacilityResponse]:
    try:
        return await service.nearby(
            latitude=latitude,
            longitude=longitude,
            category=category,
            radius_km=radius_km,
            limit=limit,
        )
    except FacilityCategoryError as error:
        raise ApiError(422, "VALIDATION_ERROR", "Kategori fasilitas tidak valid.") from error


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: UUID,
    _user_id: UUID = Depends(get_current_user_id),
    service: FacilityService = Depends(get_facility_service),
) -> FacilityResponse:
    try:
        return await service.get(facility_id)
    except FacilityNotFoundError as error:
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Facility tidak ditemukan.") from error
