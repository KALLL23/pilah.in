from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.api.errors import ApiError
from app.db.session import get_db
from app.models.models import User
from app.repositories.facilities import FacilityRepository
from app.schemas.facilities import FacilityCreateRequest, FacilityListResponse, FacilityResponse, FacilityUpdateRequest
from app.services.facilities import (
    FacilityCategoryError,
    FacilityNotFoundError,
    FacilityService,
    FacilityVerificationError,
)

router = APIRouter(prefix="/api/v1/admin/facilities", tags=["admin-facilities"])


def get_admin_facility_service(session: AsyncSession = Depends(get_db)) -> FacilityService:
    return FacilityService(FacilityRepository(session))


def raise_facility_error(error: Exception) -> None:
    if isinstance(error, FacilityNotFoundError):
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Facility tidak ditemukan.") from error
    if isinstance(error, FacilityCategoryError):
        raise ApiError(422, "VALIDATION_ERROR", "Kategori facility tidak valid.") from error
    if isinstance(error, FacilityVerificationError):
        raise ApiError(422, "VALIDATION_ERROR", str(error)) from error
    raise error


@router.get("", response_model=FacilityListResponse)
async def list_admin_facilities(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_admin),
    service: FacilityService = Depends(get_admin_facility_service),
) -> FacilityListResponse:
    return await service.list_admin(limit=limit, offset=offset)


@router.post("", response_model=FacilityResponse, status_code=201)
async def create_facility(
    payload: FacilityCreateRequest,
    _admin: User = Depends(require_admin),
    service: FacilityService = Depends(get_admin_facility_service),
) -> FacilityResponse:
    try:
        return await service.create(payload)
    except (FacilityCategoryError, FacilityVerificationError) as error:
        raise_facility_error(error)


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_admin_facility(
    facility_id: UUID,
    _admin: User = Depends(require_admin),
    service: FacilityService = Depends(get_admin_facility_service),
) -> FacilityResponse:
    try:
        return await service.get(facility_id, public_only=False)
    except FacilityNotFoundError as error:
        raise_facility_error(error)


@router.patch("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: UUID,
    payload: FacilityUpdateRequest,
    _admin: User = Depends(require_admin),
    service: FacilityService = Depends(get_admin_facility_service),
) -> FacilityResponse:
    try:
        return await service.update(facility_id, payload)
    except (FacilityNotFoundError, FacilityCategoryError, FacilityVerificationError) as error:
        raise_facility_error(error)


@router.delete("/{facility_id}", status_code=204)
async def delete_facility(
    facility_id: UUID,
    _admin: User = Depends(require_admin),
    service: FacilityService = Depends(get_admin_facility_service),
) -> Response:
    try:
        await service.delete(facility_id)
    except FacilityNotFoundError as error:
        raise_facility_error(error)
    return Response(status_code=204)
