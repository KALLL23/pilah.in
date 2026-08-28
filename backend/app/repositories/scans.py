from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.models import WasteCategory, WasteScan


@dataclass(frozen=True)
class ScanView:
    scan: WasteScan
    predicted_code: str
    predicted_name: str
    confirmed_code: str | None
    confirmed_name: str | None


class ScanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_categories(self) -> list[WasteCategory]:
        result = await self.session.execute(select(WasteCategory).order_by(WasteCategory.id))
        return list(result.scalars().all())

    async def get_category_by_code(self, code: str) -> WasteCategory | None:
        result = await self.session.execute(select(WasteCategory).where(WasteCategory.code == code))
        return result.scalar_one_or_none()

    async def create_scan(
        self,
        *,
        user_id: UUID,
        image_key: str,
        predicted_category_id: int,
        confidence: float,
        model_version: str,
    ) -> WasteScan:
        scan = WasteScan(
            user_id=user_id,
            image_key=image_key,
            predicted_category_id=predicted_category_id,
            prediction_confidence=confidence,
            recommendation_status="NOT_REQUESTED",
            model_version=model_version,
        )
        self.session.add(scan)
        await self.session.commit()
        await self.session.refresh(scan)
        return scan

    async def get_owned_scan(self, scan_id: UUID, user_id: UUID) -> ScanView | None:
        statement = self._view_statement().where(WasteScan.id == scan_id, WasteScan.user_id == user_id)
        result = await self.session.execute(statement)
        row = result.one_or_none()
        return self._to_view(row) if row else None

    async def list_owned_scans(
        self,
        user_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[ScanView], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(WasteScan).where(WasteScan.user_id == user_id)
        )
        result = await self.session.execute(
            self._view_statement()
            .where(WasteScan.user_id == user_id)
            .order_by(WasteScan.created_at.desc(), WasteScan.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_view(row) for row in result.all()], int(count_result.scalar_one())

    async def confirm_scan(
        self,
        scan: WasteScan,
        *,
        category_id: int,
        is_reusable: bool,
        is_contaminated: bool,
        is_wet: bool,
    ) -> None:
        scan.confirmed_category_id = category_id
        scan.is_reusable = is_reusable
        scan.is_contaminated = is_contaminated
        scan.is_wet = is_wet
        scan.recommendation_action = None
        scan.recommendation_reason = None
        scan.preparation_steps = None
        scan.recommendation_warnings = None
        scan.recommendation_status = "NOT_REQUESTED"
        scan.llm_model = None
        scan.prompt_version = None
        scan.knowledge_ids = None
        scan.facility_ids_in_context = None
        scan.llm_latency_ms = None
        await self.session.commit()

    @staticmethod
    def _view_statement():
        predicted = aliased(WasteCategory, name="predicted_category")
        confirmed = aliased(WasteCategory, name="confirmed_category")
        return (
            select(
                WasteScan,
                predicted.code.label("predicted_code"),
                predicted.name.label("predicted_name"),
                confirmed.code.label("confirmed_code"),
                confirmed.name.label("confirmed_name"),
            )
            .join(predicted, predicted.id == WasteScan.predicted_category_id)
            .outerjoin(confirmed, confirmed.id == WasteScan.confirmed_category_id)
        )

    @staticmethod
    def _to_view(row) -> ScanView:
        return ScanView(
            scan=row[0],
            predicted_code=row.predicted_code,
            predicted_name=row.predicted_name,
            confirmed_code=row.confirmed_code,
            confirmed_name=row.confirmed_name,
        )
