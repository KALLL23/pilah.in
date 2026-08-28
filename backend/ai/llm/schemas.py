"""Schemas for grounded recommendation context and output."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints

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
UserText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
UserListItem = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class RecommendationConditions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_reusable: StrictBool
    is_contaminated: StrictBool
    is_wet: StrictBool


class KnowledgeContextItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    management_guidance: str
    preparation_guidance: list[str]
    warnings: list[str]
    source: str
    source_url: str | None = None


class FacilityContextItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    facility_type: str
    address: str


class RecommendationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: WasteCategoryCode
    conditions: RecommendationConditions
    knowledge: list[KnowledgeContextItem]
    facilities: list[FacilityContextItem]


class LLMRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: WasteAction
    reason: UserText
    preparation_steps: list[UserListItem]
    facility_required: StrictBool
    recommended_facility_ids: list[UUID]
    warnings: list[UserListItem]


class RecommendationResponse(BaseModel):
    scan_id: UUID
    recommendation_status: Literal["SUCCESS"]
    action: WasteAction
    reason: str
    preparation_steps: list[str]
    facility_required: bool
    recommended_facility_ids: list[UUID]
    warnings: list[str]
    llm_model: str
    prompt_version: str
    knowledge_ids: list[UUID]
    facility_ids_in_context: list[UUID]
    llm_latency_ms: int = Field(ge=0)
