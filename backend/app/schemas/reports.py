from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.models import ReportStatus, RiskLevel, WasteVolume


class ReportObjectResponse(BaseModel):
    id: UUID
    category: str
    confidence: float = Field(ge=0, le=1)
    bbox: dict[str, float]


class ReportResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    image_url: str
    latitude: float
    longitude: float
    location_accuracy_m: float | None
    address: str | None
    user_description: str | None
    waste_volume: WasteVolume
    standing_water: bool
    drainage_blockage: bool
    organic_presence: bool
    location_vulnerability_score: int
    persistence_score: int
    risk_score: float
    risk_level: RiskLevel
    risk_reasons: list[str]
    status: ReportStatus
    model_version: str | None
    objects: list[ReportObjectResponse]
    confirmation_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class ReportStatusUpdateRequest(BaseModel):
    status: ReportStatus


class StatusSyncItem(BaseModel):
    history_id: UUID
    report_id: UUID
    from_status: ReportStatus | None
    to_status: ReportStatus
    changed_at: datetime


class StatusSyncResponse(BaseModel):
    items: list[StatusSyncItem]
    server_time: datetime
