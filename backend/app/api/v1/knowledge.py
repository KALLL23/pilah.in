from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.db.session import get_db
from app.repositories.knowledge import KnowledgeRepository
from app.schemas.knowledge import KnowledgeListResponse
from app.services.knowledge import KnowledgeService

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


def get_knowledge_service(session: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(KnowledgeRepository(session))


@router.get("", response_model=KnowledgeListResponse)
async def list_knowledge(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _user_id: UUID = Depends(get_current_user_id),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeListResponse:
    return await service.list(limit=limit, offset=offset, active_only=True)
