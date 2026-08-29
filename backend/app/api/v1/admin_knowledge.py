from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.api.errors import ApiError
from app.db.session import get_db
from app.models.models import User
from app.repositories.knowledge import KnowledgeRepository
from app.schemas.knowledge import KnowledgeCreateRequest, KnowledgeListResponse, KnowledgeResponse, KnowledgeUpdateRequest
from app.services.knowledge import KnowledgeCategoryError, KnowledgeNotFoundError, KnowledgeService, KnowledgeValidationError

router = APIRouter(prefix="/api/v1/admin/knowledge", tags=["admin-knowledge"])


def get_knowledge_service(session: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(KnowledgeRepository(session))


def raise_knowledge_error(error: Exception) -> None:
    if isinstance(error, KnowledgeNotFoundError):
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Knowledge tidak ditemukan.") from error
    if isinstance(error, KnowledgeCategoryError):
        raise ApiError(422, "VALIDATION_ERROR", "Kategori knowledge tidak valid.") from error
    if isinstance(error, KnowledgeValidationError):
        raise ApiError(422, "VALIDATION_ERROR", str(error)) from error
    raise error


@router.get("", response_model=KnowledgeListResponse)
async def list_knowledge(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_admin),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeListResponse:
    return await service.list(limit=limit, offset=offset)


@router.post("", response_model=KnowledgeResponse, status_code=201)
async def create_knowledge(
    payload: KnowledgeCreateRequest,
    _admin: User = Depends(require_admin),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeResponse:
    try:
        return await service.create(payload)
    except KnowledgeCategoryError as error:
        raise_knowledge_error(error)


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    knowledge_id: UUID,
    _admin: User = Depends(require_admin),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeResponse:
    try:
        return await service.get(knowledge_id)
    except KnowledgeNotFoundError as error:
        raise_knowledge_error(error)


@router.patch("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    knowledge_id: UUID,
    payload: KnowledgeUpdateRequest,
    _admin: User = Depends(require_admin),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeResponse:
    try:
        return await service.update(knowledge_id, payload)
    except (KnowledgeNotFoundError, KnowledgeCategoryError, KnowledgeValidationError) as error:
        raise_knowledge_error(error)


@router.delete("/{knowledge_id}", status_code=204)
async def delete_knowledge(
    knowledge_id: UUID,
    _admin: User = Depends(require_admin),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Response:
    try:
        await service.delete(knowledge_id)
    except KnowledgeNotFoundError as error:
        raise_knowledge_error(error)
    return Response(status_code=204)
