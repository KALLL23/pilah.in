"""SQLAlchemy models for the pilah.in operational database."""

from __future__ import annotations

import enum
import uuid

from geoalchemy2 import Geography, Geometry
from sqlalchemy import (Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index,
                        Integer, Numeric, PrimaryKeyConstraint, SmallInteger, String,
                        Text, UniqueConstraint, func, text)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class WasteAction(str, enum.Enum):
    REUSE = "REUSE"
    RECYCLE = "RECYCLE"
    COMPOST = "COMPOST"
    RESIDUAL = "RESIDUAL"
    SPECIAL_HANDLING = "SPECIAL_HANDLING"


class FacilityType(str, enum.Enum):
    BANK_SAMPAH = "BANK_SAMPAH"
    TPS3R = "TPS3R"
    COLLECTOR = "COLLECTOR"
    RECYCLING_FACILITY = "RECYCLING_FACILITY"
    SPECIAL_WASTE_FACILITY = "SPECIAL_WASTE_FACILITY"


class WasteVolume(str, enum.Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReportStatus(str, enum.Enum):
    REPORTED = "REPORTED"
    VERIFIED = "VERIFIED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


def enum_type(enum_class: type[enum.Enum], name: str) -> Enum:
    return Enum(enum_class, name=name, native_enum=True, validate_strings=True)


class TimestampMixin:
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(enum_type(UserRole, "user_role"), nullable=False, server_default=UserRole.USER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_tokens_user_id", "user_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class WasteCategory(Base):
    __tablename__ = "waste_categories"
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class WasteScan(TimestampMixin, Base):
    __tablename__ = "waste_scans"
    __table_args__ = (
        CheckConstraint("prediction_confidence IS NULL OR (prediction_confidence >= 0 AND prediction_confidence <= 1)", name="ck_waste_scans_prediction_confidence"),
        Index("ix_waste_scans_user_created", "user_id", "created_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    image_key: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_category_id: Mapped[int | None] = mapped_column(SmallInteger, ForeignKey("waste_categories.id", ondelete="RESTRICT"))
    prediction_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    confirmed_category_id: Mapped[int | None] = mapped_column(SmallInteger, ForeignKey("waste_categories.id", ondelete="RESTRICT"))
    is_reusable: Mapped[bool | None] = mapped_column(Boolean)
    is_contaminated: Mapped[bool | None] = mapped_column(Boolean)
    is_wet: Mapped[bool | None] = mapped_column(Boolean)
    recommendation_action: Mapped[WasteAction | None] = mapped_column(enum_type(WasteAction, "waste_action"))
    recommendation_reason: Mapped[str | None] = mapped_column(Text)
    preparation_steps: Mapped[list | None] = mapped_column(JSONB)
    recommendation_warnings: Mapped[list | None] = mapped_column(JSONB)
    recommendation_status: Mapped[str | None] = mapped_column(String(20))
    llm_model: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[str | None] = mapped_column(String(40))
    knowledge_ids: Mapped[list | None] = mapped_column(JSONB)
    facility_ids_in_context: Mapped[list | None] = mapped_column(JSONB)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)


class WasteKnowledge(TimestampMixin, Base):
    __tablename__ = "waste_knowledge"
    __table_args__ = (Index("ix_waste_knowledge_category_active", "category_id", "is_active"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("waste_categories.id", ondelete="RESTRICT"), nullable=False)
    condition_scope: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    management_guidance: Mapped[str] = mapped_column(Text, nullable=False)
    preparation_guidance: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    warnings: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    last_reviewed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class Facility(TimestampMixin, Base):
    __tablename__ = "facilities"
    __table_args__ = (Index("ix_facilities_location_gist", "location", postgresql_using="gist"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    facility_type: Mapped[FacilityType] = mapped_column(enum_type(FacilityType, "facility_type"), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    opening_hours: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    location: Mapped[object] = mapped_column(Geography("POINT", srid=4326, spatial_index=False), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class FacilityCategory(Base):
    __tablename__ = "facility_categories"
    __table_args__ = (PrimaryKeyConstraint("facility_id", "category_id"),)
    facility_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("waste_categories.id", ondelete="RESTRICT"), nullable=False)


class WasteReport(TimestampMixin, Base):
    __tablename__ = "waste_reports"
    __table_args__ = (
        CheckConstraint("risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)", name="ck_waste_reports_risk_score"),
        CheckConstraint("location_accuracy_m IS NULL OR location_accuracy_m >= 0", name="ck_waste_reports_location_accuracy"),
        Index("ix_waste_reports_location_gist", "location", postgresql_using="gist"),
        Index("ix_waste_reports_status_created", "status", "created_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    image_key: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[object] = mapped_column(Geography("POINT", srid=4326, spatial_index=False), nullable=False)
    location_accuracy_m: Mapped[float | None] = mapped_column(Numeric(8, 2))
    address: Mapped[str | None] = mapped_column(Text)
    user_description: Mapped[str | None] = mapped_column(Text)
    waste_volume: Mapped[WasteVolume] = mapped_column(enum_type(WasteVolume, "waste_volume"), nullable=False)
    standing_water: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    drainage_blockage: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    organic_presence: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    location_vulnerability_score: Mapped[int | None] = mapped_column(SmallInteger)
    persistence_score: Mapped[int | None] = mapped_column(SmallInteger)
    risk_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    risk_level: Mapped[RiskLevel | None] = mapped_column(enum_type(RiskLevel, "risk_level"))
    risk_reasons: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    status: Mapped[ReportStatus] = mapped_column(enum_type(ReportStatus, "report_status"), nullable=False, server_default=ReportStatus.REPORTED.value)
    model_version: Mapped[str | None] = mapped_column(String(80))
    resolved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class WasteReportObject(Base):
    __tablename__ = "waste_report_objects"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_waste_report_objects_confidence"),
        Index("ix_waste_report_objects_report_id", "report_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("waste_reports.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("waste_categories.id", ondelete="RESTRICT"), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    bbox: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReportConfirmation(Base):
    __tablename__ = "report_confirmations"
    __table_args__ = (UniqueConstraint("report_id", "user_id", name="uq_report_confirmations_report_user"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("waste_reports.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReportStatusHistory(Base):
    __tablename__ = "report_status_history"
    __table_args__ = (Index("ix_report_status_history_report_created", "report_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("waste_reports.id", ondelete="CASCADE"), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    from_status: Mapped[ReportStatus | None] = mapped_column(enum_type(ReportStatus, "report_status"))
    to_status: Mapped[ReportStatus] = mapped_column(enum_type(ReportStatus, "report_status"), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CityBoundary(Base):
    __tablename__ = "city_boundaries"
    __table_args__ = (Index("ix_city_boundaries_geometry_gist", "geometry", postgresql_using="gist"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    geometry: Mapped[object] = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=False), nullable=False)


class Waterway(Base):
    __tablename__ = "waterways"
    __table_args__ = (Index("ix_waterways_geometry_gist", "geometry", postgresql_using="gist"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str | None] = mapped_column(Text)
    geometry: Mapped[object] = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=False), nullable=False)


class ResidentialArea(Base):
    __tablename__ = "residential_areas"
    __table_args__ = (Index("ix_residential_areas_geometry_gist", "geometry", postgresql_using="gist"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str | None] = mapped_column(Text)
    geometry: Mapped[object] = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=False), nullable=False)


class PublicFacility(Base):
    __tablename__ = "public_facilities"
    __table_args__ = (Index("ix_public_facilities_geometry_gist", "geometry", postgresql_using="gist"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    facility_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    geometry: Mapped[object] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)


class GeocodeCache(Base):
    __tablename__ = "geocode_cache"
    __table_args__ = (
        UniqueConstraint("lat_round", "lon_round", name="uq_geocode_cache_lat_lon"),
        CheckConstraint("lat_round >= -90 AND lat_round <= 90", name="ck_geocode_cache_lat"),
        CheckConstraint("lon_round >= -180 AND lon_round <= 180", name="ck_geocode_cache_lon"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lat_round: Mapped[float] = mapped_column(Numeric(8, 5), nullable=False)
    lon_round: Mapped[float] = mapped_column(Numeric(8, 5), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
