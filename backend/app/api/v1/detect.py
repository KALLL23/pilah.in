from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from app.ai.detection import WasteDetector, DetectionError
from app.api.errors import ApiError
from app.core.config import Settings, get_settings
from app.services.image_validation import ImageValidationError, validate_image_upload

router = APIRouter(prefix="/api/v1/detect", tags=["detect"])


@router.post("")
async def detect_image(
    image: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    detector = WasteDetector(settings)
    if not detector.is_configured:
        raise ApiError(503, "MODEL_UNAVAILABLE", "Model deteksi belum tersedia.")
    try:
        validated = await validate_image_upload(image, settings.max_image_bytes)
    except ImageValidationError as error:
        status_code = 413 if error.code == "IMAGE_TOO_LARGE" else 415
        raise ApiError(status_code, error.code, error.message) from error
    try:
        result = await detector.predict(validated.content)
    except DetectionError as error:
        raise ApiError(500, "DETECTION_FAILED", "Gagal menjalankan deteksi.") from error
    return JSONResponse(content={
        "waste_volume": result.estimate_volume(),
        "standing_water": result.standing_water_detected,
        "drainage_blockage": result.drainage_blockage_detected,
        "organic_presence": result.organic_presence,
        "object_count": result.object_count,
        "objects": [
            {
                "category_code": obj.category_code,
                "confidence": obj.confidence,
            }
            for obj in result.objects
        ],
    })
