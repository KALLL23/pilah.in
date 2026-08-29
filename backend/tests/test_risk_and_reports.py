from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import UploadFile
from PIL import Image
from starlette.datastructures import Headers

from app.ai.detection import DetectedWaste, DetectionResult
from app.core.config import Settings
from app.models.models import ReportStatus, RiskLevel, WasteVolume
from app.services.reports import ReportDependencyError, ReportService, STATUS_TRANSITIONS
from app.services.reports import PossibleDuplicateError
from app.api.errors import ApiError
from app.api.v1.reports import raise_report_error
from app.services.risk import calculate_risk, persistence_score


def test_risk_uses_exact_six_factor_formula_and_boundaries() -> None:
    maximum = calculate_risk(
        waste_volume=WasteVolume.LARGE,
        organic_presence=True,
        standing_water=True,
        drainage_blockage=True,
        location_vulnerability=100,
        confirmations=4,
    )
    boundary = calculate_risk(
        waste_volume=WasteVolume.MEDIUM,
        organic_presence=True,
        standing_water=False,
        drainage_blockage=False,
        location_vulnerability=100,
        confirmations=0,
    )

    assert maximum.score == 100
    assert maximum.level == RiskLevel.HIGH
    assert boundary.score == 40
    assert boundary.level == RiskLevel.MEDIUM


def test_persistence_score_is_capped_and_status_path_is_one_way() -> None:
    assert [persistence_score(value) for value in range(6)] == [0, 25, 50, 75, 100, 100]
    assert STATUS_TRANSITIONS == {
        ReportStatus.REPORTED: ReportStatus.VERIFIED,
        ReportStatus.VERIFIED: ReportStatus.IN_PROGRESS,
        ReportStatus.IN_PROGRESS: ReportStatus.RESOLVED,
    }


def test_duplicate_api_error_returns_existing_report_id() -> None:
    report_id = uuid4()

    with pytest.raises(ApiError) as caught:
        raise_report_error(PossibleDuplicateError(report_id))

    assert caught.value.status_code == 409
    assert caught.value.code == "POSSIBLE_DUPLICATE"
    assert caught.value.details == {"existing_report_id": str(report_id)}


class DependencyRepository:
    def __init__(self, ready: bool) -> None:
        self.ready = ready

    async def spatial_ready(self) -> bool:
        return self.ready


class DetectorFlag:
    def __init__(self, configured: bool) -> None:
        self.is_configured = configured


class UntouchedStorage:
    def __init__(self) -> None:
        self.uploaded = False

    async def upload(self, *_args) -> None:
        self.uploaded = True


@pytest.mark.asyncio
@pytest.mark.parametrize("model_ready,spatial_ready", [(False, True), (True, False)])
async def test_report_dependency_failure_happens_without_upload(model_ready: bool, spatial_ready: bool) -> None:
    storage = UntouchedStorage()
    service = ReportService(
        DependencyRepository(spatial_ready),
        DetectorFlag(model_ready),
        storage,
        SimpleNamespace(),
        Settings(),
    )

    with pytest.raises(ReportDependencyError):
        await service.create(
            None,
            uuid4(),
            latitude=-6.99,
            longitude=110.42,
            location_accuracy_m=None,
            user_description=None,
            waste_volume=WasteVolume.SMALL,
            standing_water=False,
            drainage_blockage=False,
        )

    assert storage.uploaded is False


def jpeg_upload() -> UploadFile:
    content = BytesIO()
    Image.new("RGB", (24, 24), color="white").save(content, format="JPEG")
    content.seek(0)
    return UploadFile(file=content, filename="report.jpg", headers=Headers({"content-type": "image/jpeg"}))


class FailingPersistenceRepository:
    def __init__(self) -> None:
        self.rolled_back = False

    async def spatial_ready(self): return True
    async def inside_semarang(self, *_args): return True
    async def find_duplicate(self, *_args): return None
    async def category_map(self, _codes): return {"PLASTIC": SimpleNamespace(id=1)}
    async def location_vulnerability(self, *_args): return 20
    async def create(self, **_values): raise RuntimeError("database write failed")
    async def rollback(self): self.rolled_back = True


class SuccessfulDetector:
    is_configured = True

    async def predict(self, _content):
        return DetectionResult(
            objects=[DetectedWaste("PLASTIC", 0.9, {"x1": 0, "y1": 0, "x2": 10, "y2": 10})],
            model_version="test-detector",
        )


class CleanupStorage:
    def __init__(self) -> None:
        self.uploaded_key = None
        self.deleted_key = None

    async def upload(self, key, _content, _content_type): self.uploaded_key = key
    async def delete(self, key): self.deleted_key = key


@pytest.mark.asyncio
async def test_report_persistence_failure_rolls_back_and_removes_upload() -> None:
    repository = FailingPersistenceRepository()
    storage = CleanupStorage()
    service = ReportService(
        repository,
        SuccessfulDetector(),
        storage,
        SimpleNamespace(reverse=lambda *_args: None),
        Settings(max_image_bytes=1024 * 1024),
    )

    async def reverse(*_args): return None
    service.geocoder.reverse = reverse

    with pytest.raises(RuntimeError, match="database write failed"):
        await service.create(
            jpeg_upload(),
            uuid4(),
            latitude=-6.99,
            longitude=110.42,
            location_accuracy_m=5,
            user_description="Sampah menumpuk",
            waste_volume=WasteVolume.SMALL,
            standing_water=False,
            drainage_blockage=False,
        )

    assert repository.rolled_back is True
    assert storage.uploaded_key is not None
    assert storage.deleted_key == storage.uploaded_key
