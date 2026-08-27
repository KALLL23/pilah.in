import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, SmallInteger, Numeric, Text, ForeignKey, DateTime, Enum, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geography, Geometry

Base = declarative_base()

# ==========================================
# ENUMS
# ==========================================
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

# ==========================================
# TABLES
# ==========================================
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    token_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class WasteCategory(Base):
    __tablename__ = "waste_categories"
    id = Column(SmallInteger, primary_key=True)
    code = Column(String(40), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    description = Column(Text)

class WasteScan(Base):
    __tablename__ = "waste_scans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    image_key = Column(Text, nullable=False)
    predicted_category_id = Column(SmallInteger, ForeignKey("waste_categories.id"))
    prediction_confidence = Column(Numeric(5, 4))
    confirmed_category_id = Column(SmallInteger, ForeignKey("waste_categories.id"))
    is_reusable = Column(Boolean)
    is_contaminated = Column(Boolean)
    is_wet = Column(Boolean)
    recommendation_action = Column(Enum(WasteAction), nullable=True)
    recommendation_reason = Column(Text, nullable=True)
    preparation_steps = Column(JSONB, nullable=True)
    recommendation_warnings = Column(JSONB, nullable=True)
    recommendation_status = Column(String(20))
    llm_model = Column(String(120), nullable=True)
    prompt_version = Column(String(40), nullable=True)
    knowledge_ids = Column(JSONB, nullable=True)
    facility_ids_in_context = Column(JSONB, nullable=True)
    llm_latency_ms = Column(Integer, nullable=True)
    model_version = Column(String(80))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class WasteKnowledge(Base):
    __tablename__ = "waste_knowledge"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(SmallInteger, ForeignKey("waste_categories.id"))
    condition_scope = Column(JSONB)
    management_guidance = Column(Text)
    preparation_guidance = Column(JSONB)
    warnings = Column(JSONB)
    source = Column(Text)
    source_url = Column(Text, nullable=True)
    last_reviewed_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class Facility(Base):
    __tablename__ = "facilities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    facility_type = Column(Enum(FacilityType), nullable=False)
    address = Column(Text, nullable=False)
    phone = Column(String(50), nullable=True)
    opening_hours = Column(JSONB)
    location = Column(Geography('POINT', srid=4326))
    verified = Column(Boolean, default=False)
    source = Column(Text)
    source_url = Column(Text, nullable=True)
    last_verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class FacilityCategory(Base):
    __tablename__ = "facility_categories"
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.id"))
    category_id = Column(SmallInteger, ForeignKey("waste_categories.id"))
    __table_args__ = (PrimaryKeyConstraint('facility_id', 'category_id'),)

class WasteReport(Base):
    __tablename__ = "waste_reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    image_key = Column(Text, nullable=False)
    location = Column(Geography('POINT', srid=4326))
    location_accuracy_m = Column(Numeric)
    address = Column(Text)
    user_description = Column(Text, nullable=True)
    waste_volume = Column(Enum(WasteVolume))
    standing_water = Column(Boolean)
    drainage_blockage = Column(Boolean)
    organic_presence = Column(Boolean)
    location_vulnerability_score = Column(SmallInteger)
    persistence_score = Column(SmallInteger)
    risk_score = Column(Numeric(5, 2))
    risk_level = Column(Enum(RiskLevel))
    risk_reasons = Column(JSONB)
    status = Column(Enum(ReportStatus), default=ReportStatus.REPORTED)
    model_version = Column(String(80))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class WasteReportObject(Base):
    __tablename__ = "waste_report_objects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("waste_reports.id"))
    category_id = Column(SmallInteger, ForeignKey("waste_categories.id"))
    confidence = Column(Numeric(5, 4))
    bbox = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class ReportConfirmation(Base):
    __tablename__ = "report_confirmations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("waste_reports.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('report_id', 'user_id', name='uix_report_user_confirmation'),)

class ReportStatusHistory(Base):
    __tablename__ = "report_status_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("waste_reports.id"))
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    from_status = Column(Enum(ReportStatus))
    to_status = Column(Enum(ReportStatus))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class CityBoundary(Base):
    __tablename__ = "city_boundaries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120))
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326))

class Waterway(Base):
    __tablename__ = "waterways"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=True)
    geometry = Column(Geometry('GEOMETRY', srid=4326))

class ResidentialArea(Base):
    __tablename__ = "residential_areas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=True)
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326))

class PublicFacility(Base):
    __tablename__ = "public_facilities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text)
    facility_kind = Column(String(80))
    geometry = Column(Geometry('POINT', srid=4326))

class GeocodeCache(Base):
    __tablename__ = "geocode_cache"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lat_round = Column(Numeric(8, 5))
    lon_round = Column(Numeric(8, 5))
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('lat_round', 'lon_round', name='uix_lat_lon_round'),)