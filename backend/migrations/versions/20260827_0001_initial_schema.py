"""Create the initial pilah.in operational schema and category taxonomy."""

from typing import Sequence, Union

from alembic import op

revision: str = "20260827_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE TYPE user_role AS ENUM ('USER', 'ADMIN')")
    op.execute("CREATE TYPE waste_action AS ENUM ('REUSE', 'RECYCLE', 'COMPOST', 'RESIDUAL', 'SPECIAL_HANDLING')")
    op.execute("CREATE TYPE facility_type AS ENUM ('BANK_SAMPAH', 'TPS3R', 'COLLECTOR', 'RECYCLING_FACILITY', 'SPECIAL_WASTE_FACILITY')")
    op.execute("CREATE TYPE waste_volume AS ENUM ('SMALL', 'MEDIUM', 'LARGE')")
    op.execute("CREATE TYPE risk_level AS ENUM ('LOW', 'MEDIUM', 'HIGH')")
    op.execute("CREATE TYPE report_status AS ENUM ('REPORTED', 'VERIFIED', 'IN_PROGRESS', 'RESOLVED')")

    op.execute("""
        CREATE TABLE users (
            id uuid PRIMARY KEY,
            name varchar(120) NOT NULL,
            email varchar(255) NOT NULL UNIQUE,
            password_hash text NOT NULL,
            role user_role NOT NULL DEFAULT 'USER',
            is_active boolean NOT NULL DEFAULT true,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE refresh_tokens (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash text NOT NULL UNIQUE,
            expires_at timestamptz NOT NULL,
            revoked_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id)")
    op.execute("""
        CREATE TABLE waste_categories (
            id smallint PRIMARY KEY,
            code varchar(40) NOT NULL UNIQUE,
            name varchar(80) NOT NULL,
            description text NOT NULL
        )
    """)
    op.execute("""
        INSERT INTO waste_categories (id, code, name, description) VALUES
        (1, 'PLASTIC', 'Plastik', 'Kemasan dan benda berbahan plastik.'),
        (2, 'PAPER_CARDBOARD', 'Kertas dan Kardus', 'Kertas, karton, dan kardus yang dapat dipilah.'),
        (3, 'GLASS', 'Kaca', 'Botol, wadah, dan benda berbahan kaca.'),
        (4, 'METAL', 'Logam', 'Kaleng dan benda berbahan logam.'),
        (5, 'ORGANIC', 'Organik', 'Sisa makanan dan bahan organik yang dapat terurai.'),
        (6, 'TEXTILE', 'Tekstil', 'Pakaian, kain, dan alas kaki.'),
        (7, 'ELECTRONIC_SPECIAL', 'Elektronik dan Khusus', 'Elektronik, baterai, dan material yang membutuhkan penanganan khusus.'),
        (8, 'RESIDUAL_MIXED', 'Residu Campuran', 'Sampah campuran atau residu yang tidak masuk kategori lain.')
    """)
    op.execute("""
        CREATE TABLE waste_scans (
            id uuid PRIMARY KEY,
            user_id uuid REFERENCES users(id) ON DELETE SET NULL,
            image_key text NOT NULL,
            predicted_category_id smallint REFERENCES waste_categories(id) ON DELETE RESTRICT,
            prediction_confidence numeric(5,4),
            confirmed_category_id smallint REFERENCES waste_categories(id) ON DELETE RESTRICT,
            is_reusable boolean,
            is_contaminated boolean,
            is_wet boolean,
            recommendation_action waste_action,
            recommendation_reason text,
            preparation_steps jsonb,
            recommendation_warnings jsonb,
            recommendation_status varchar(20),
            llm_model varchar(120),
            prompt_version varchar(40),
            knowledge_ids jsonb,
            facility_ids_in_context jsonb,
            llm_latency_ms integer,
            model_version varchar(80) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_waste_scans_prediction_confidence CHECK (prediction_confidence IS NULL OR prediction_confidence BETWEEN 0 AND 1)
        )
    """)
    op.execute("CREATE INDEX ix_waste_scans_user_created ON waste_scans(user_id, created_at)")
    op.execute("""
        CREATE TABLE waste_knowledge (
            id uuid PRIMARY KEY,
            category_id smallint NOT NULL REFERENCES waste_categories(id) ON DELETE RESTRICT,
            condition_scope jsonb NOT NULL DEFAULT '{}'::jsonb,
            management_guidance text NOT NULL,
            preparation_guidance jsonb NOT NULL DEFAULT '[]'::jsonb,
            warnings jsonb NOT NULL DEFAULT '[]'::jsonb,
            source text NOT NULL,
            source_url text,
            last_reviewed_at timestamptz NOT NULL,
            is_active boolean NOT NULL DEFAULT true,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_waste_knowledge_category_active ON waste_knowledge(category_id, is_active)")
    op.execute("""
        CREATE TABLE facilities (
            id uuid PRIMARY KEY,
            name varchar(255) NOT NULL,
            facility_type facility_type NOT NULL,
            address text NOT NULL,
            phone varchar(50),
            opening_hours jsonb NOT NULL DEFAULT '{}'::jsonb,
            location geography(POINT, 4326) NOT NULL,
            verified boolean NOT NULL DEFAULT false,
            source text NOT NULL,
            source_url text,
            last_verified_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_facilities_location_gist ON facilities USING gist(location)")
    op.execute("""
        CREATE TABLE facility_categories (
            facility_id uuid NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
            category_id smallint NOT NULL REFERENCES waste_categories(id) ON DELETE RESTRICT,
            PRIMARY KEY (facility_id, category_id)
        )
    """)
    op.execute("""
        CREATE TABLE waste_reports (
            id uuid PRIMARY KEY,
            user_id uuid REFERENCES users(id) ON DELETE SET NULL,
            image_key text NOT NULL,
            location geography(POINT, 4326) NOT NULL,
            location_accuracy_m numeric(8,2),
            address text,
            user_description text,
            waste_volume waste_volume NOT NULL,
            standing_water boolean NOT NULL DEFAULT false,
            drainage_blockage boolean NOT NULL DEFAULT false,
            organic_presence boolean NOT NULL DEFAULT false,
            location_vulnerability_score smallint,
            persistence_score smallint,
            risk_score numeric(5,2),
            risk_level risk_level,
            risk_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
            status report_status NOT NULL DEFAULT 'REPORTED',
            model_version varchar(80),
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            resolved_at timestamptz,
            CONSTRAINT ck_waste_reports_risk_score CHECK (risk_score IS NULL OR risk_score BETWEEN 0 AND 100),
            CONSTRAINT ck_waste_reports_location_accuracy CHECK (location_accuracy_m IS NULL OR location_accuracy_m >= 0)
        )
    """)
    op.execute("CREATE INDEX ix_waste_reports_location_gist ON waste_reports USING gist(location)")
    op.execute("CREATE INDEX ix_waste_reports_status_created ON waste_reports(status, created_at)")
    op.execute("""
        CREATE TABLE waste_report_objects (
            id uuid PRIMARY KEY,
            report_id uuid NOT NULL REFERENCES waste_reports(id) ON DELETE CASCADE,
            category_id smallint NOT NULL REFERENCES waste_categories(id) ON DELETE RESTRICT,
            confidence numeric(5,4) NOT NULL,
            bbox jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_waste_report_objects_confidence CHECK (confidence BETWEEN 0 AND 1)
        )
    """)
    op.execute("CREATE INDEX ix_waste_report_objects_report_id ON waste_report_objects(report_id)")
    op.execute("""
        CREATE TABLE report_confirmations (
            id uuid PRIMARY KEY,
            report_id uuid NOT NULL REFERENCES waste_reports(id) ON DELETE CASCADE,
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_report_confirmations_report_user UNIQUE (report_id, user_id)
        )
    """)
    op.execute("""
        CREATE TABLE report_status_history (
            id uuid PRIMARY KEY,
            report_id uuid NOT NULL REFERENCES waste_reports(id) ON DELETE CASCADE,
            changed_by uuid REFERENCES users(id) ON DELETE SET NULL,
            from_status report_status,
            to_status report_status NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_report_status_history_report_created ON report_status_history(report_id, created_at)")
    op.execute("CREATE TABLE city_boundaries (id uuid PRIMARY KEY, name varchar(120) NOT NULL, geometry geometry(MULTIPOLYGON, 4326) NOT NULL)")
    op.execute("CREATE INDEX ix_city_boundaries_geometry_gist ON city_boundaries USING gist(geometry)")
    op.execute("CREATE TABLE waterways (id uuid PRIMARY KEY, name text, geometry geometry(GEOMETRY, 4326) NOT NULL)")
    op.execute("CREATE INDEX ix_waterways_geometry_gist ON waterways USING gist(geometry)")
    op.execute("CREATE TABLE residential_areas (id uuid PRIMARY KEY, name text, geometry geometry(MULTIPOLYGON, 4326) NOT NULL)")
    op.execute("CREATE INDEX ix_residential_areas_geometry_gist ON residential_areas USING gist(geometry)")
    op.execute("CREATE TABLE public_facilities (id uuid PRIMARY KEY, name text NOT NULL, facility_kind varchar(80) NOT NULL, geometry geometry(POINT, 4326) NOT NULL)")
    op.execute("CREATE INDEX ix_public_facilities_geometry_gist ON public_facilities USING gist(geometry)")
    op.execute("""
        CREATE TABLE geocode_cache (
            id uuid PRIMARY KEY,
            lat_round numeric(8,5) NOT NULL,
            lon_round numeric(8,5) NOT NULL,
            address text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_geocode_cache_lat_lon UNIQUE (lat_round, lon_round),
            CONSTRAINT ck_geocode_cache_lat CHECK (lat_round BETWEEN -90 AND 90),
            CONSTRAINT ck_geocode_cache_lon CHECK (lon_round BETWEEN -180 AND 180)
        )
    """)


def downgrade() -> None:
    for table in (
        "geocode_cache", "public_facilities", "residential_areas", "waterways", "city_boundaries",
        "report_status_history", "report_confirmations", "waste_report_objects", "waste_reports",
        "facility_categories", "facilities", "waste_knowledge", "waste_scans", "waste_categories",
        "refresh_tokens", "users",
    ):
        op.execute(f"DROP TABLE {table}")
    for enum_name in ("report_status", "risk_level", "waste_volume", "facility_type", "waste_action", "user_role"):
        op.execute(f"DROP TYPE {enum_name}")
