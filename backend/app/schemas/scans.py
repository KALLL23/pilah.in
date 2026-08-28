from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from app.models.models import WasteAction

WasteCategoryCode = Literal[
    "PLASTIC",
    "PAPER_CARDBOARD",
    "GLASS",
    "METAL",
    "ORGANIC",
    "TEXTILE",
    "ELECTRONIC_SPECIAL",
    "RESIDUAL_MIXED",
]


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: WasteCategoryCode
    name: str
    description: str


class ScanCategory(BaseModel):
    id: int
    code: WasteCategoryCode
    name: str


class ScanConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed_category: WasteCategoryCode
    is_reusable: StrictBool
    is_contaminated: StrictBool
    is_wet: StrictBool


class ScanResponse(BaseModel):
    id: UUID
    predicted_category: ScanCategory
    prediction_confidence: float = Field(ge=0, le=1)
    low_confidence: bool
    confirmed_category: ScanCategory | None
    is_reusable: bool | None
    is_contaminated: bool | None
    is_wet: bool | None
    recommendation_status: str
    recommendation_action: WasteAction | None
    recommendation_reason: str | None
    preparation_steps: list[str] | None
    recommendation_warnings: list[str] | None
    model_version: str
    image_url: str
    created_at: datetime
    updated_at: datetime


class ScanListResponse(BaseModel):
    items: list[ScanResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
