from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from geoalchemy2 import Geography, Geometry
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.detection import DetectedWaste
from app.models.models import (
    GeocodeCache,
    ReportConfirmation,
    ReportStatus,
    ReportStatusHistory,
    WasteCategory,
    WasteReport,
    WasteReportObject,
)


@dataclass(frozen=True)
class ReportView:
    report: WasteReport
    latitude: float
    longitude: float
    objects: list[tuple[WasteReportObject, str]]
    confirmation_count: int


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def point(latitude: float, longitude: float):
        return func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326).cast(
            Geography("POINT", srid=4326)
        )

    @staticmethod
    def coordinates():
        geometry = WasteReport.location.cast(Geometry("POINT", srid=4326))
        return func.ST_Y(geometry).label("latitude"), func.ST_X(geometry).label("longitude")

    async def spatial_ready(self) -> bool:
        query = text(
            """
            SELECT
              EXISTS (SELECT 1 FROM city_boundaries) AND
              EXISTS (SELECT 1 FROM waterways) AND
              EXISTS (SELECT 1 FROM residential_areas) AND
              EXISTS (SELECT 1 FROM public_facilities)
            """
        )
        return bool(await self.session.scalar(query))

    async def inside_semarang(self, latitude: float, longitude: float) -> bool:
        query = text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM city_boundaries
                WHERE ST_Covers(
                    geometry,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
                )
            )
            """
        )
        return bool(await self.session.scalar(query, {"latitude": latitude, "longitude": longitude}))

    async def location_vulnerability(self, latitude: float, longitude: float) -> int:
        query = text(
            """
            WITH p AS (SELECT ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326) AS geom)
            SELECT CASE
              WHEN EXISTS (SELECT 1 FROM waterways, p WHERE ST_DWithin(waterways.geometry::geography, p.geom::geography, 25))
                OR EXISTS (SELECT 1 FROM public_facilities, p WHERE ST_DWithin(public_facilities.geometry::geography, p.geom::geography, 50)) THEN 100
              WHEN EXISTS (SELECT 1 FROM waterways, p WHERE ST_DWithin(waterways.geometry::geography, p.geom::geography, 100))
                OR EXISTS (SELECT 1 FROM public_facilities, p WHERE ST_DWithin(public_facilities.geometry::geography, p.geom::geography, 100)) THEN 70
              WHEN EXISTS (SELECT 1 FROM residential_areas, p WHERE ST_Covers(residential_areas.geometry, p.geom)) THEN 40
              ELSE 20
            END
            """
        )
        return int(await self.session.scalar(query, {"latitude": latitude, "longitude": longitude}) or 20)

    async def find_duplicate(self, latitude: float, longitude: float) -> UUID | None:
        point = self.point(latitude, longitude)
        result = await self.session.execute(
            select(WasteReport.id)
            .where(
                WasteReport.status.in_([ReportStatus.REPORTED, ReportStatus.VERIFIED, ReportStatus.IN_PROGRESS]),
                WasteReport.created_at >= datetime.now(timezone.utc) - timedelta(days=3),
                func.ST_DWithin(WasteReport.location, point, 30),
            )
            .order_by(WasteReport.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def category_map(self, codes: list[str]) -> dict[str, WasteCategory]:
        if not codes:
            return {}
        result = await self.session.execute(select(WasteCategory).where(WasteCategory.code.in_(codes)))
        return {item.code: item for item in result.scalars().all()}

    async def create(
        self,
        *,
        detected_objects: list[DetectedWaste],
        category_map: dict[str, WasteCategory],
        latitude: float,
        longitude: float,
        **values,
    ) -> WasteReport:
        report = WasteReport(location=self.point(latitude, longitude), **values)
        self.session.add(report)
        await self.session.flush()
        self.session.add_all(
            [
                WasteReportObject(
                    report_id=report.id,
                    category_id=category_map[item.category_code].id,
                    confidence=item.confidence,
                    bbox=item.bbox,
                )
                for item in detected_objects
            ]
        )
        self.session.add(
            ReportStatusHistory(
                report_id=report.id,
                changed_by=None,
                from_status=None,
                to_status=ReportStatus.REPORTED,
            )
        )
        await self.session.flush()
        return report

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def _objects(self, report_id: UUID) -> list[tuple[WasteReportObject, str]]:
        result = await self.session.execute(
            select(WasteReportObject, WasteCategory.code)
            .join(WasteCategory, WasteCategory.id == WasteReportObject.category_id)
            .where(WasteReportObject.report_id == report_id)
            .order_by(WasteReportObject.confidence.desc(), WasteReportObject.id)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def _view(self, row) -> ReportView:
        report = row[0]
        count = int(
            await self.session.scalar(
                select(func.count()).select_from(ReportConfirmation).where(
                    ReportConfirmation.report_id == report.id,
                    ReportConfirmation.created_at >= datetime.now(timezone.utc) - timedelta(days=14),
                )
            )
            or 0
        )
        return ReportView(report, float(row.latitude), float(row.longitude), await self._objects(report.id), count)

    async def get(self, report_id: UUID) -> ReportView | None:
        result = await self.session.execute(
            select(WasteReport, *self.coordinates()).where(WasteReport.id == report_id)
        )
        row = result.one_or_none()
        return await self._view(row) if row else None

    async def list_owned(self, user_id: UUID, *, limit: int, offset: int) -> tuple[list[ReportView], int]:
        total = int(
            await self.session.scalar(
                select(func.count()).select_from(WasteReport).where(WasteReport.user_id == user_id)
            )
            or 0
        )
        result = await self.session.execute(
            select(WasteReport, *self.coordinates())
            .where(WasteReport.user_id == user_id)
            .order_by(WasteReport.created_at.desc(), WasteReport.id)
            .limit(limit)
            .offset(offset)
        )
        return [await self._view(row) for row in result.all()], total

    async def list_admin(self, *, status: ReportStatus | None, limit: int, offset: int) -> tuple[list[ReportView], int]:
        filters = [] if status is None else [WasteReport.status == status]
        total = int(await self.session.scalar(select(func.count()).select_from(WasteReport).where(*filters)) or 0)
        result = await self.session.execute(
            select(WasteReport, *self.coordinates())
            .where(*filters)
            .order_by(WasteReport.created_at.desc(), WasteReport.id)
            .limit(limit)
            .offset(offset)
        )
        return [await self._view(row) for row in result.all()], total

    async def has_confirmation(self, report_id: UUID, user_id: UUID) -> bool:
        return bool(
            await self.session.scalar(
                select(func.count()).select_from(ReportConfirmation).where(
                    ReportConfirmation.report_id == report_id,
                    ReportConfirmation.user_id == user_id,
                )
            )
        )

    async def confirm(self, report: WasteReport, user_id: UUID, *, persistence: int, risk_score: float, risk_level, risk_reasons: list[str]) -> None:
        self.session.add(ReportConfirmation(report_id=report.id, user_id=user_id))
        report.persistence_score = persistence
        report.risk_score = risk_score
        report.risk_level = risk_level
        report.risk_reasons = risk_reasons
        await self.session.commit()

    async def change_status(self, report: WasteReport, admin_id: UUID, new_status: ReportStatus) -> None:
        old_status = report.status
        report.status = new_status
        if new_status == ReportStatus.RESOLVED:
            report.resolved_at = datetime.now(timezone.utc)
        self.session.add(
            ReportStatusHistory(report_id=report.id, changed_by=admin_id, from_status=old_status, to_status=new_status)
        )
        await self.session.commit()
        await self.session.refresh(report)

    async def geocode_cache_get(self, latitude: float, longitude: float) -> str | None:
        result = await self.session.execute(
            select(GeocodeCache.address).where(
                GeocodeCache.lat_round == round(latitude, 5),
                GeocodeCache.lon_round == round(longitude, 5),
            )
        )
        return result.scalar_one_or_none()

    async def geocode_cache_put(self, latitude: float, longitude: float, address: str) -> None:
        query = text(
            """
            INSERT INTO geocode_cache (id, lat_round, lon_round, address)
            VALUES (gen_random_uuid(), :latitude, :longitude, :address)
            ON CONFLICT (lat_round, lon_round) DO UPDATE SET address = EXCLUDED.address
            """
        )
        await self.session.execute(
            query,
            {"latitude": round(latitude, 5), "longitude": round(longitude, 5), "address": address},
        )
        await self.session.commit()

    async def sync_status(self, user_id: UUID, since: datetime) -> list[tuple[ReportStatusHistory, UUID]]:
        result = await self.session.execute(
            select(ReportStatusHistory, WasteReport.id)
            .join(WasteReport, WasteReport.id == ReportStatusHistory.report_id)
            .where(WasteReport.user_id == user_id, ReportStatusHistory.created_at > since)
            .order_by(ReportStatusHistory.created_at, ReportStatusHistory.id)
        )
        return [(row[0], row[1]) for row in result.all()]
