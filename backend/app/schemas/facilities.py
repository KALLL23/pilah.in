from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.models import FacilityAccessScope, FacilityType


class FacilityCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    facility_type: FacilityType
    access_scope: FacilityAccessScope = FacilityAccessScope.UNKNOWN
    address: str = Field(min_length=1, max_length=2000)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    phone: str | None = Field(default=None, max_length=50)
    opening_hours: dict = Field(default_factory=dict)
    accepted_categories: list[str] = Field(default_factory=list, max_length=8)
    verified: bool = False
    source: str = Field(min_length=1, max_length=2000)
    source_url: str | None = Field(default=None, max_length=2000)
    last_verified_at: datetime | None = None

    @field_validator("name", "address", "source")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()


class FacilityUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    facility_type: FacilityType | None = None
    access_scope: FacilityAccessScope | None = None
    address: str | None = Field(default=None, min_length=1, max_length=2000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    phone: str | None = Field(default=None, max_length=50)
    opening_hours: dict | None = None
    accepted_categories: list[str] | None = Field(default=None, max_length=8)
    verified: bool | None = None
    source: str | None = Field(default=None, min_length=1, max_length=2000)
    source_url: str | None = Field(default=None, max_length=2000)
    last_verified_at: datetime | None = None
    is_active: bool | None = None

    @field_validator("name", "address", "source")
    @classmethod
    def optional_required_text_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be blank")
        return value.strip() if value is not None else None


class FacilityResponse(BaseModel):
    id: UUID
    name: str
    facility_type: FacilityType
    access_scope: FacilityAccessScope
    address: str
    latitude: float
    longitude: float
    distance_m: float | None = None
    phone: str | None
    opening_hours: dict
    accepted_categories: list[str]
    verified: bool
    is_active: bool
    source: str
    source_url: str | None
    last_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime


class FacilityListResponse(BaseModel):
    items: list[FacilityResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
