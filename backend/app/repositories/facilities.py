from dataclasses import dataclass
from uuid import UUID

from geoalchemy2 import Geography, Geometry
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Facility,
    FacilityAccessScope,
    FacilityCategory,
    FacilityType,
    WasteCategory,
)


@dataclass(frozen=True)
class FacilityView:
    facility: Facility
    latitude: float
    longitude: float
    categories: list[str]
    distance_m: float | None = None


class FacilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _point(latitude: float, longitude: float):
        return func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326).cast(
            Geography("POINT", srid=4326)
        )

    @staticmethod
    def _coordinates():
        geometry = Facility.location.cast(Geometry("POINT", srid=4326))
        return func.ST_Y(geometry).label("latitude"), func.ST_X(geometry).label("longitude")

    async def category_map(self, codes: list[str]) -> dict[str, WasteCategory]:
        if not codes:
            return {}
        result = await self.session.execute(select(WasteCategory).where(WasteCategory.code.in_(codes)))
        return {item.code: item for item in result.scalars().all()}

    async def _categories_for(self, facility_ids: list[UUID]) -> dict[UUID, list[str]]:
        if not facility_ids:
            return {}
        result = await self.session.execute(
            select(FacilityCategory.facility_id, WasteCategory.code)
            .join(WasteCategory, WasteCategory.id == FacilityCategory.category_id)
            .where(FacilityCategory.facility_id.in_(facility_ids))
            .order_by(WasteCategory.id)
        )
        mapping: dict[UUID, list[str]] = {item: [] for item in facility_ids}
        for facility_id, code in result.all():
            mapping.setdefault(facility_id, []).append(code)
        return mapping

    async def list_public(
        self,
        *,
        category: str | None,
        facility_type: FacilityType | None,
        limit: int,
        offset: int,
    ) -> tuple[list[FacilityView], int]:
        filters = [
            Facility.verified.is_(True),
            Facility.is_active.is_(True),
            Facility.access_scope == FacilityAccessScope.PUBLIC,
        ]
        statement = select(Facility, *self._coordinates()).where(*filters)
        count_statement = select(func.count(func.distinct(Facility.id))).select_from(Facility).where(*filters)
        if category:
            statement = statement.join(FacilityCategory).join(WasteCategory).where(WasteCategory.code == category)
            count_statement = count_statement.join(FacilityCategory).join(WasteCategory).where(WasteCategory.code == category)
        if facility_type:
            statement = statement.where(Facility.facility_type == facility_type)
            count_statement = count_statement.where(Facility.facility_type == facility_type)
        total = int(await self.session.scalar(count_statement) or 0)
        result = await self.session.execute(statement.order_by(Facility.name, Facility.id).limit(limit).offset(offset))
        rows = result.all()
        categories = await self._categories_for([row[0].id for row in rows])
        return [FacilityView(row[0], float(row.latitude), float(row.longitude), categories[row[0].id]) for row in rows], total

    async def list_admin(self, *, limit: int, offset: int) -> tuple[list[FacilityView], int]:
        total = int(await self.session.scalar(select(func.count()).select_from(Facility)) or 0)
        result = await self.session.execute(
            select(Facility, *self._coordinates()).order_by(Facility.created_at.desc(), Facility.id).limit(limit).offset(offset)
        )
        rows = result.all()
        categories = await self._categories_for([row[0].id for row in rows])
        return [FacilityView(row[0], float(row.latitude), float(row.longitude), categories[row[0].id]) for row in rows], total

    async def nearby(
        self,
        *,
        latitude: float,
        longitude: float,
        category: str,
        radius_m: float,
        limit: int,
    ) -> list[FacilityView]:
        point = self._point(latitude, longitude)
        distance = func.ST_Distance(Facility.location, point).label("distance_m")
        result = await self.session.execute(
            select(Facility, *self._coordinates(), distance)
            .join(FacilityCategory)
            .join(WasteCategory)
            .where(
                WasteCategory.code == category,
                Facility.verified.is_(True),
                Facility.is_active.is_(True),
                Facility.access_scope == FacilityAccessScope.PUBLIC,
                func.ST_DWithin(Facility.location, point, radius_m),
            )
            .order_by(distance, Facility.id)
            .limit(limit)
        )
        rows = result.all()
        categories = await self._categories_for([row[0].id for row in rows])
        return [
            FacilityView(row[0], float(row.latitude), float(row.longitude), categories[row[0].id], float(row.distance_m))
            for row in rows
        ]

    async def get(self, facility_id: UUID, *, public_only: bool) -> FacilityView | None:
        statement = select(Facility, *self._coordinates()).where(Facility.id == facility_id)
        if public_only:
            statement = statement.where(
                Facility.verified.is_(True),
                Facility.is_active.is_(True),
                Facility.access_scope == FacilityAccessScope.PUBLIC,
            )
        result = await self.session.execute(statement)
        row = result.one_or_none()
        if row is None:
            return None
        categories = await self._categories_for([facility_id])
        return FacilityView(row[0], float(row.latitude), float(row.longitude), categories[facility_id])

    async def create(self, *, category_ids: list[int], latitude: float, longitude: float, **values) -> Facility:
        facility = Facility(location=self._point(latitude, longitude), **values)
        self.session.add(facility)
        await self.session.flush()
        self.session.add_all([FacilityCategory(facility_id=facility.id, category_id=item) for item in category_ids])
        await self.session.commit()
        await self.session.refresh(facility)
        return facility

    async def replace_categories(self, facility_id: UUID, category_ids: list[int]) -> None:
        await self.session.execute(delete(FacilityCategory).where(FacilityCategory.facility_id == facility_id))
        self.session.add_all([FacilityCategory(facility_id=facility_id, category_id=item) for item in category_ids])

    async def commit(self, facility: Facility) -> None:
        await self.session.commit()
        await self.session.refresh(facility)
