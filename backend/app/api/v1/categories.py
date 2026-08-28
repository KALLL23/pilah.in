from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.scans import ScanRepository
from app.schemas.scans import CategoryResponse

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(session: AsyncSession = Depends(get_db)) -> list[CategoryResponse]:
    repository = ScanRepository(session)
    return [CategoryResponse.model_validate(item) for item in await repository.list_categories()]
