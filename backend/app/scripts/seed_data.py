"""Idempotently load verified operational seed files when they are available."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid5

from geoalchemy2.elements import WKTElement
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models.models import (
    Facility,
    FacilityAccessScope,
    FacilityCategory,
    FacilityType,
    WasteCategory,
    WasteKnowledge,
)

SEED_NAMESPACE = UUID("cd88f545-e649-47f1-9fba-0a3fd2bb4ef3")


def _seed_id(kind: str, key: str) -> UUID:
    return uuid5(SEED_NAMESPACE, f"{kind}:{key}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _parse_bool(value: str, *, default: bool) -> bool:
    normalized = (value or "").strip().lower()
    if not normalized:
        return default
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"Invalid boolean seed value: {value}")


def _parse_datetime(value: str) -> datetime | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    return datetime.fromisoformat(normalized.replace("Z", "+00:00"))


def _parse_json(value: str, default):
    normalized = (value or "").strip()
    return json.loads(normalized) if normalized else default


def _category_map(session: Session) -> dict[str, WasteCategory]:
    return {item.code: item for item in session.scalars(select(WasteCategory)).all()}


def seed_knowledge(session: Session, directory: Path) -> int:
    rows = _read_csv(directory / "waste_knowledge.csv")
    if not rows:
        return 0
    categories = _category_map(session)
    for row in rows:
        category = categories.get(row["category"].strip())
        if category is None:
            raise ValueError(f"Unknown waste knowledge category: {row['category']}")
        scope = _parse_json(row.get("condition_scope", ""), {})
        content = row["content"].strip()
        source = row["source"].strip()
        reviewed_at = _parse_datetime(row.get("last_reviewed_at", ""))
        if not content or not source or reviewed_at is None:
            raise ValueError("Waste knowledge requires content, source, and last_reviewed_at")
        identifier = _seed_id(
            "knowledge",
            f"{category.code}|{json.dumps(scope, sort_keys=True)}|{content}|{source}",
        )
        session.merge(
            WasteKnowledge(
                id=identifier,
                category_id=category.id,
                condition_scope=scope,
                content=content,
                source=source,
                source_url=(row.get("source_url") or "").strip() or None,
                last_reviewed_at=reviewed_at,
                is_active=_parse_bool(row.get("is_active", ""), default=True),
            )
        )
    return len(rows)


def seed_facilities(session: Session, directory: Path) -> int:
    rows = _read_csv(directory / "facilities.csv")
    if not rows:
        return 0
    categories = _category_map(session)
    for row in rows:
        codes = [item.strip() for item in (row.get("accepted_categories") or "").split("|") if item.strip()]
        unknown = sorted(set(codes) - set(categories))
        if unknown:
            raise ValueError(f"Unknown facility categories: {', '.join(unknown)}")
        verified = _parse_bool(row.get("verified", ""), default=False)
        reviewed_at = _parse_datetime(row.get("last_verified_at", ""))
        source = row["source"].strip()
        if verified and (not source or reviewed_at is None or not codes):
            raise ValueError("Verified facility requires source, last_verified_at, and accepted_categories")
        name = row["name"].strip()
        address = row["address"].strip()
        identifier = _seed_id("facility", f"{name}|{address}|{source}")
        facility = Facility(
            id=identifier,
            name=name,
            facility_type=FacilityType(row["facility_type"].strip()),
            access_scope=FacilityAccessScope((row.get("access_scope") or "UNKNOWN").strip()),
            address=address,
            phone=(row.get("phone") or "").strip() or None,
            opening_hours=_parse_json(row.get("opening_hours", ""), {}),
            location=WKTElement(f"POINT({float(row['longitude'])} {float(row['latitude'])})", srid=4326),
            verified=verified,
            is_active=_parse_bool(row.get("is_active", ""), default=True),
            source=source,
            source_url=(row.get("source_url") or "").strip() or None,
            last_verified_at=reviewed_at,
        )
        session.merge(facility)
        session.flush()
        session.execute(delete(FacilityCategory).where(FacilityCategory.facility_id == identifier))
        session.add_all(
            FacilityCategory(facility_id=identifier, category_id=categories[code].id)
            for code in codes
        )
    return len(rows)


SPATIAL_DATASETS = {
    "city_boundary.geojson": ("city_boundaries", "name", "ST_Multi"),
    "waterways.geojson": ("waterways", "name", None),
    "residential.geojson": ("residential_areas", "name", "ST_Multi"),
    "public_facilities.geojson": ("public_facilities", "name", None),
}


def seed_spatial(session: Session, directory: Path) -> int:
    inserted = 0
    for filename, (table_name, name_field, wrapper) in SPATIAL_DATASETS.items():
        path = directory / filename
        if not path.is_file() or path.stat().st_size == 0:
            continue
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        features = payload.get("features", []) if payload.get("type") == "FeatureCollection" else []
        for index, feature in enumerate(features):
            geometry = feature.get("geometry")
            if not geometry:
                continue
            properties = feature.get("properties") or {}
            name = str(properties.get(name_field) or properties.get("name") or f"{path.stem}-{index}")
            identifier = _seed_id("spatial", f"{filename}|{index}|{name}")
            expression = "ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326)"
            if wrapper:
                expression = f"{wrapper}({expression})"
            if table_name == "public_facilities":
                session.execute(
                    text(
                        f"""
                        INSERT INTO {table_name} (id, name, facility_kind, geometry)
                        VALUES (:id, :name, :facility_kind, {expression})
                        ON CONFLICT (id) DO UPDATE SET
                          name = EXCLUDED.name,
                          facility_kind = EXCLUDED.facility_kind,
                          geometry = EXCLUDED.geometry
                        """
                    ),
                    {
                        "id": identifier,
                        "name": name,
                        "facility_kind": str(properties.get("facility_kind") or properties.get("kind") or "UNKNOWN"),
                        "geometry": json.dumps(geometry),
                    },
                )
            else:
                session.execute(
                    text(
                        f"""
                        INSERT INTO {table_name} (id, name, geometry)
                        VALUES (:id, :name, {expression})
                        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, geometry = EXCLUDED.geometry
                        """
                    ),
                    {"id": identifier, "name": name, "geometry": json.dumps(geometry)},
                )
            inserted += 1
    return inserted


def seed_data() -> None:
    directory = get_settings().seed_data_dir
    if not directory.is_dir():
        print(f"Operational seed skipped: {directory} is not available")
        return
    has_knowledge = bool(_read_csv(directory / "waste_knowledge.csv"))
    has_facilities = bool(_read_csv(directory / "facilities.csv"))
    has_spatial = any(
        (directory / filename).is_file() and (directory / filename).stat().st_size > 0
        for filename in SPATIAL_DATASETS
    )
    if not (has_knowledge or has_facilities or has_spatial):
        print("Operational seed reconciled: knowledge=0, facilities=0, spatial_features=0")
        return
    with get_session_factory()() as session:
        knowledge_count = seed_knowledge(session, directory)
        facility_count = seed_facilities(session, directory)
        spatial_count = seed_spatial(session, directory)
        session.commit()
    print(
        "Operational seed reconciled: "
        f"knowledge={knowledge_count}, facilities={facility_count}, spatial_features={spatial_count}"
    )


if __name__ == "__main__":
    seed_data()
