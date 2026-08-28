from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Facility,
    FacilityCategory,
    WasteCategory,
    WasteKnowledge,
    WasteScan,
)
from ai.llm.schemas import FacilityContextItem, KnowledgeContextItem


@dataclass(frozen=True)
class OwnedScan:
    scan: WasteScan
    category_code: str | None


def condition_scope_matches(scope: dict[str, Any], conditions: dict[str, bool]) -> bool:
    if not isinstance(scope, dict):
        return False
    allowed_keys = set(conditions)
    if not set(scope).issubset(allowed_keys):
        return False
    return all(type(expected) is bool and conditions[key] == expected for key, expected in scope.items())


def knowledge_record_matches(
    record: WasteKnowledge,
    category_id: int,
    conditions: dict[str, bool],
) -> bool:
    return (
        record.category_id == category_id
        and record.is_active is True
        and condition_scope_matches(record.condition_scope, conditions)
    )


class RecommendationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_owned_scan(self, scan_id: UUID, user_id: UUID) -> OwnedScan | None:
        result = await self.session.execute(
            select(WasteScan, WasteCategory.code)
            .outerjoin(WasteCategory, WasteCategory.id == WasteScan.confirmed_category_id)
            .where(WasteScan.id == scan_id, WasteScan.user_id == user_id)
        )
        row = result.one_or_none()
        return OwnedScan(scan=row[0], category_code=row[1]) if row else None

    async def get_relevant_knowledge(
        self,
        category_id: int,
        conditions: dict[str, bool],
    ) -> list[KnowledgeContextItem]:
        result = await self.session.execute(
            select(WasteKnowledge)
            .where(WasteKnowledge.category_id == category_id, WasteKnowledge.is_active.is_(True))
            .order_by(WasteKnowledge.id)
        )
        records = [
            record
            for record in result.scalars().all()
            if knowledge_record_matches(record, category_id, conditions)
        ]
        return [
            KnowledgeContextItem(
                id=record.id,
                management_guidance=record.management_guidance,
                preparation_guidance=record.preparation_guidance,
                warnings=record.warnings,
                source=record.source,
                source_url=record.source_url,
            )
            for record in records
        ]

    async def get_relevant_facilities(self, category_id: int) -> list[FacilityContextItem]:
        result = await self.session.execute(
            select(Facility)
            .join(FacilityCategory, FacilityCategory.facility_id == Facility.id)
            .where(FacilityCategory.category_id == category_id, Facility.verified.is_(True))
            .order_by(Facility.name, Facility.id)
        )
        return [
            FacilityContextItem(
                id=facility.id,
                name=facility.name,
                facility_type=facility.facility_type.value,
                address=facility.address,
            )
            for facility in result.scalars().all()
        ]

    async def save_pending(
        self,
        scan: WasteScan,
        *,
        llm_model: str | None,
        prompt_version: str,
        knowledge_ids: list[UUID],
        facility_ids: list[UUID],
    ) -> None:
        scan.recommendation_action = None
        scan.recommendation_reason = None
        scan.preparation_steps = None
        scan.recommendation_warnings = None
        scan.recommendation_status = "PENDING"
        scan.llm_model = llm_model
        scan.prompt_version = prompt_version
        scan.knowledge_ids = [str(item) for item in knowledge_ids]
        scan.facility_ids_in_context = [str(item) for item in facility_ids]
        scan.llm_latency_ms = None
        await self.session.commit()

    async def save_success(
        self,
        scan: WasteScan,
        *,
        action: Any,
        reason: str,
        preparation_steps: list[str],
        warnings: list[str],
        latency_ms: int,
    ) -> None:
        scan.recommendation_action = action
        scan.recommendation_reason = reason
        scan.preparation_steps = preparation_steps
        scan.recommendation_warnings = warnings
        scan.recommendation_status = "SUCCESS"
        scan.llm_latency_ms = latency_ms
        await self.session.commit()

    async def save_failed(self, scan: WasteScan, *, latency_ms: int | None = None) -> None:
        scan.recommendation_action = None
        scan.recommendation_reason = None
        scan.preparation_steps = None
        scan.recommendation_warnings = None
        scan.recommendation_status = "FAILED"
        scan.llm_latency_ms = latency_ms
        await self.session.commit()
