from uuid import UUID

from app.repositories.knowledge import KnowledgeRepository, KnowledgeView
from app.schemas.knowledge import (
    KnowledgeCreateRequest,
    KnowledgeListResponse,
    KnowledgeResponse,
    KnowledgeUpdateRequest,
)


class KnowledgeNotFoundError(Exception):
    pass


class KnowledgeCategoryError(Exception):
    pass


class KnowledgeValidationError(Exception):
    pass


class KnowledgeService:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    async def list(self, *, limit: int, offset: int, active_only: bool = False) -> KnowledgeListResponse:
        records, total = await self.repository.list(limit=limit, offset=offset, include_inactive=not active_only)
        return KnowledgeListResponse(items=[self._response(item) for item in records], total=total, limit=limit, offset=offset)

    async def get(self, record_id: UUID) -> KnowledgeResponse:
        view = await self.repository.get(record_id)
        if view is None:
            raise KnowledgeNotFoundError
        return self._response(view)

    async def create(self, request: KnowledgeCreateRequest) -> KnowledgeResponse:
        category = await self.repository.category_by_code(request.category)
        if category is None:
            raise KnowledgeCategoryError
        record = await self.repository.create(
            category_id=category.id,
            condition_scope=request.condition_scope.model_dump(exclude_none=True),
            content=request.content.strip(),
            source=request.source.strip(),
            source_url=request.source_url,
            last_reviewed_at=request.last_reviewed_at,
            is_active=request.is_active,
        )
        return self._response(KnowledgeView(record, category.code))

    async def update(self, record_id: UUID, request: KnowledgeUpdateRequest) -> KnowledgeResponse:
        view = await self.repository.get(record_id)
        if view is None:
            raise KnowledgeNotFoundError
        record = view.record
        non_nullable_fields = {"category", "content", "source", "last_reviewed_at", "is_active"}
        if any(field in request.model_fields_set and getattr(request, field) is None for field in non_nullable_fields):
            raise KnowledgeValidationError("Field knowledge wajib tidak boleh null.")
        category_code = view.category_code
        changes = request.model_dump(exclude_unset=True)
        if "category" in changes:
            category = await self.repository.category_by_code(changes.pop("category"))
            if category is None:
                raise KnowledgeCategoryError
            record.category_id = category.id
            category_code = category.code
        if "condition_scope" in changes:
            scope = request.condition_scope
            record.condition_scope = scope.model_dump(exclude_none=True) if scope else {}
            changes.pop("condition_scope", None)
        for field, value in changes.items():
            setattr(record, field, value.strip() if isinstance(value, str) else value)
        await self.repository.commit(record)
        return self._response(KnowledgeView(record, category_code))

    async def delete(self, record_id: UUID) -> None:
        view = await self.repository.get(record_id)
        if view is None:
            raise KnowledgeNotFoundError
        view.record.is_active = False
        await self.repository.commit(view.record)

    @staticmethod
    def _response(view: KnowledgeView) -> KnowledgeResponse:
        record = view.record
        return KnowledgeResponse(
            id=record.id,
            category=view.category_code,
            condition_scope=record.condition_scope,
            content=record.content,
            source=record.source,
            source_url=record.source_url,
            last_reviewed_at=record.last_reviewed_at,
            is_active=record.is_active,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
