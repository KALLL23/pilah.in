from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import WasteCategory, WasteKnowledge


@dataclass(frozen=True)
class KnowledgeView:
    record: WasteKnowledge
    category_code: str


class KnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def category_by_code(self, code: str) -> WasteCategory | None:
        result = await self.session.execute(select(WasteCategory).where(WasteCategory.code == code))
        return result.scalar_one_or_none()

    async def list(self, *, limit: int, offset: int, include_inactive: bool = True) -> tuple[list[KnowledgeView], int]:
        filters = [] if include_inactive else [WasteKnowledge.is_active.is_(True)]
        count = await self.session.scalar(select(func.count()).select_from(WasteKnowledge).where(*filters))
        result = await self.session.execute(
            select(WasteKnowledge, WasteCategory.code)
            .join(WasteCategory, WasteCategory.id == WasteKnowledge.category_id)
            .where(*filters)
            .order_by(WasteCategory.id, WasteKnowledge.created_at, WasteKnowledge.id)
            .limit(limit)
            .offset(offset)
        )
        return [KnowledgeView(row[0], row[1]) for row in result.all()], int(count or 0)

    async def get(self, record_id: UUID) -> KnowledgeView | None:
        result = await self.session.execute(
            select(WasteKnowledge, WasteCategory.code)
            .join(WasteCategory, WasteCategory.id == WasteKnowledge.category_id)
            .where(WasteKnowledge.id == record_id)
        )
        row = result.one_or_none()
        return KnowledgeView(row[0], row[1]) if row else None

    async def create(self, **values) -> WasteKnowledge:
        record = WasteKnowledge(**values)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def commit(self, record: WasteKnowledge) -> None:
        await self.session.commit()
        await self.session.refresh(record)
