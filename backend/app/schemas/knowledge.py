from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator


class ConditionScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_reusable: StrictBool | None = None
    is_contaminated: StrictBool | None = None
    is_wet: StrictBool | None = None


class KnowledgeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=40)
    condition_scope: ConditionScope = Field(default_factory=ConditionScope)
    content: str = Field(min_length=1, max_length=2000)
    source: str = Field(min_length=1, max_length=1000)
    source_url: str | None = Field(default=None, max_length=2000)
    last_reviewed_at: datetime
    is_active: bool = True

    @field_validator("category", "content", "source")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()


class KnowledgeUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str | None = Field(default=None, min_length=1, max_length=40)
    condition_scope: ConditionScope | None = None
    content: str | None = Field(default=None, min_length=1, max_length=2000)
    source: str | None = Field(default=None, min_length=1, max_length=1000)
    source_url: str | None = Field(default=None, max_length=2000)
    last_reviewed_at: datetime | None = None
    is_active: bool | None = None

    @field_validator("category", "content", "source")
    @classmethod
    def optional_required_text_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be blank")
        return value.strip() if value is not None else None


class KnowledgeResponse(BaseModel):
    id: UUID
    category: str
    condition_scope: dict[str, bool]
    content: str
    source: str
    source_url: str | None
    last_reviewed_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
