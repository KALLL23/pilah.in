from uuid import UUID

from app.models.models import FacilityAccessScope, FacilityType
from app.repositories.facilities import FacilityRepository, FacilityView
from app.schemas.facilities import (
    FacilityCreateRequest,
    FacilityListResponse,
    FacilityResponse,
    FacilityUpdateRequest,
)


class FacilityNotFoundError(Exception):
    pass


class FacilityCategoryError(Exception):
    pass


class FacilityVerificationError(Exception):
    pass


class FacilityService:
    def __init__(self, repository: FacilityRepository) -> None:
        self.repository = repository

    async def list_public(self, *, category: str | None, facility_type: FacilityType | None, limit: int, offset: int) -> FacilityListResponse:
        if category is not None:
            await self._category_ids([category])
        records, total = await self.repository.list_public(category=category, facility_type=facility_type, limit=limit, offset=offset)
        return FacilityListResponse(items=[self._response(item) for item in records], total=total, limit=limit, offset=offset)

    async def list_admin(self, *, limit: int, offset: int) -> FacilityListResponse:
        records, total = await self.repository.list_admin(limit=limit, offset=offset)
        return FacilityListResponse(items=[self._response(item) for item in records], total=total, limit=limit, offset=offset)

    async def nearby(self, *, latitude: float, longitude: float, category: str, radius_km: float, limit: int) -> list[FacilityResponse]:
        await self._category_ids([category])
        records = await self.repository.nearby(latitude=latitude, longitude=longitude, category=category, radius_m=radius_km * 1000, limit=limit)
        return [self._response(item) for item in records]

    async def get(self, facility_id: UUID, *, public_only: bool = True) -> FacilityResponse:
        view = await self.repository.get(facility_id, public_only=public_only)
        if view is None:
            raise FacilityNotFoundError
        return self._response(view)

    async def create(self, request: FacilityCreateRequest) -> FacilityResponse:
        category_ids = await self._category_ids(request.accepted_categories)
        self._validate_verified(request.verified, request.source, request.last_verified_at, category_ids)
        data = request.model_dump(exclude={"latitude", "longitude", "accepted_categories"})
        facility = await self.repository.create(
            category_ids=category_ids,
            latitude=request.latitude,
            longitude=request.longitude,
            **data,
        )
        view = await self.repository.get(facility.id, public_only=False)
        assert view is not None
        return self._response(view)

    async def update(self, facility_id: UUID, request: FacilityUpdateRequest) -> FacilityResponse:
        view = await self.repository.get(facility_id, public_only=False)
        if view is None:
            raise FacilityNotFoundError
        facility = view.facility
        non_nullable_fields = {
            "name",
            "facility_type",
            "access_scope",
            "address",
            "opening_hours",
            "verified",
            "source",
            "is_active",
        }
        if any(field in request.model_fields_set and getattr(request, field) is None for field in non_nullable_fields):
            raise FacilityVerificationError("Field facility wajib tidak boleh null.")
        changes = request.model_dump(exclude_unset=True, exclude={"latitude", "longitude", "accepted_categories"})
        category_codes = request.accepted_categories if request.accepted_categories is not None else view.categories
        category_ids = await self._category_ids(category_codes)
        verified = changes.get("verified", facility.verified)
        source = changes.get("source", facility.source)
        last_verified_at = changes.get("last_verified_at", facility.last_verified_at)
        self._validate_verified(verified, source, last_verified_at, category_ids)
        if (request.latitude is None) != (request.longitude is None):
            raise FacilityVerificationError("Latitude dan longitude harus diperbarui bersama.")
        if request.latitude is not None and request.longitude is not None:
            facility.location = self.repository._point(request.latitude, request.longitude)
        for field, value in changes.items():
            setattr(facility, field, value.strip() if isinstance(value, str) else value)
        if request.accepted_categories is not None:
            await self.repository.replace_categories(facility.id, category_ids)
        await self.repository.commit(facility)
        refreshed = await self.repository.get(facility.id, public_only=False)
        assert refreshed is not None
        return self._response(refreshed)

    async def delete(self, facility_id: UUID) -> None:
        view = await self.repository.get(facility_id, public_only=False)
        if view is None:
            raise FacilityNotFoundError
        view.facility.is_active = False
        await self.repository.commit(view.facility)

    async def _category_ids(self, codes: list[str]) -> list[int]:
        if len(codes) != len(set(codes)):
            raise FacilityCategoryError
        mapping = await self.repository.category_map(codes)
        if len(mapping) != len(codes):
            raise FacilityCategoryError
        return [mapping[code].id for code in codes]

    @staticmethod
    def _validate_verified(verified: bool, source: str, last_verified_at, category_ids: list[int]) -> None:
        if verified and (not source.strip() or last_verified_at is None or not category_ids):
            raise FacilityVerificationError(
                "Facility verified memerlukan sumber, last_verified_at, dan minimal satu kategori."
            )

    @staticmethod
    def _response(view: FacilityView) -> FacilityResponse:
        facility = view.facility
        return FacilityResponse(
            id=facility.id,
            name=facility.name,
            facility_type=facility.facility_type,
            access_scope=facility.access_scope,
            address=facility.address,
            latitude=view.latitude,
            longitude=view.longitude,
            distance_m=view.distance_m,
            phone=facility.phone,
            opening_hours=facility.opening_hours,
            accepted_categories=view.categories,
            verified=facility.verified,
            is_active=facility.is_active,
            source=facility.source,
            source_url=facility.source_url,
            last_verified_at=facility.last_verified_at,
            created_at=facility.created_at,
            updated_at=facility.updated_at,
        )
