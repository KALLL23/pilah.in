from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.api.errors import ApiError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from ai.llm.client import OpenRouterClient
from ai.llm.repository import RecommendationRepository
from ai.llm.schemas import RecommendationResponse
from ai.llm.service import (
    KnowledgeNotAvailableError,
    RecommendationGenerationError,
    RecommendationService,
    ScanNotFoundError,
    ScanNotReadyError,
)

router = APIRouter(prefix="/api/v1/scans", tags=["scans"])


def get_recommendation_service(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RecommendationService:
    return RecommendationService(
        RecommendationRepository(session),
        OpenRouterClient(settings),
        settings,
    )


@router.post("/{scan_id}/recommend", response_model=RecommendationResponse)
async def recommend_scan(
    scan_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    try:
        return await service.recommend(scan_id, user_id)
    except ScanNotFoundError as error:
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Scan tidak ditemukan.") from error
    except ScanNotReadyError as error:
        raise ApiError(
            409,
            "SCAN_NOT_READY",
            "Kategori dan kondisi sampah harus dikonfirmasi sebelum meminta rekomendasi.",
        ) from error
    except KnowledgeNotAvailableError as error:
        raise ApiError(
            422,
            "KNOWLEDGE_NOT_AVAILABLE",
            "Knowledge terverifikasi untuk kondisi scan ini belum tersedia.",
        ) from error
    except RecommendationGenerationError as error:
        raise ApiError(
            502,
            "RECOMMENDATION_FAILED",
            "Rekomendasi belum dapat dibuat. Silakan coba lagi.",
            {"failure_category": error.category},
        ) from error
