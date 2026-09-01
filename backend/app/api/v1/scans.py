from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.classification import ClassificationError, WasteClassifier
from app.api.dependencies import get_current_user_id
from app.api.errors import ApiError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.scans import ScanRepository
from app.schemas.scans import ScanConfirmRequest, ScanListResponse, ScanResponse
from app.services.image_validation import ImageValidationError
from app.services.scans import ScanDataError, ScanNotFoundError as WasteScanNotFoundError, ScanService
from app.services.storage import ObjectStorage, StorageError, get_object_storage
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


def get_scan_service(
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ScanService:
    classifier: WasteClassifier = getattr(request.app.state, "waste_classifier", WasteClassifier(settings))
    storage: ObjectStorage = getattr(request.app.state, "object_storage", get_object_storage())
    return ScanService(ScanRepository(session), classifier, storage, settings)


def get_recommendation_service(
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RecommendationService:
    storage: ObjectStorage = getattr(request.app.state, "object_storage", get_object_storage())
    return RecommendationService(
        RecommendationRepository(session),
        OpenRouterClient(settings),
        settings,
        storage=storage,
    )


def raise_scan_api_error(error: Exception) -> None:
    if isinstance(error, ImageValidationError):
        status_code = 413 if error.code == "IMAGE_TOO_LARGE" else 415
        raise ApiError(status_code, error.code, error.message) from error
    if isinstance(error, WasteScanNotFoundError):
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Scan tidak ditemukan.") from error
    if isinstance(error, ClassificationError):
        raise ApiError(503, "SERVER_UNAVAILABLE", "Model klasifikasi belum dapat digunakan.") from error
    if isinstance(error, StorageError):
        raise ApiError(503, "SERVER_UNAVAILABLE", "Penyimpanan gambar belum dapat digunakan.") from error
    if isinstance(error, ScanDataError):
        raise ApiError(503, "SERVER_UNAVAILABLE", "Data taxonomy scan belum tersedia.") from error
    raise error


@router.post("/infer", response_model=ScanResponse, status_code=201)
async def infer_scan(
    image: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
    service: ScanService = Depends(get_scan_service),
) -> ScanResponse:
    try:
        return await service.infer(image, user_id)
    except (ImageValidationError, ClassificationError, StorageError, ScanDataError) as error:
        raise_scan_api_error(error)


@router.get("", response_model=ScanListResponse)
async def list_scans(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: ScanService = Depends(get_scan_service),
) -> ScanListResponse:
    try:
        return await service.list(user_id, limit=limit, offset=offset)
    except StorageError as error:
        raise_scan_api_error(error)


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ScanService = Depends(get_scan_service),
) -> ScanResponse:
    try:
        return await service.get(scan_id, user_id)
    except (WasteScanNotFoundError, StorageError) as error:
        raise_scan_api_error(error)


@router.patch("/{scan_id}/confirm", response_model=ScanResponse)
async def confirm_scan(
    scan_id: UUID,
    payload: ScanConfirmRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: ScanService = Depends(get_scan_service),
) -> ScanResponse:
    try:
        return await service.confirm(scan_id, user_id, payload)
    except (WasteScanNotFoundError, StorageError, ScanDataError) as error:
        raise_scan_api_error(error)


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
