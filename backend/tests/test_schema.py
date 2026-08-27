import re
from pathlib import Path

from app.models.models import Base


EXPECTED_TABLES = {
    "users",
    "refresh_tokens",
    "waste_categories",
    "waste_scans",
    "waste_knowledge",
    "facilities",
    "facility_categories",
    "waste_reports",
    "waste_report_objects",
    "report_confirmations",
    "report_status_history",
    "city_boundaries",
    "waterways",
    "residential_areas",
    "public_facilities",
    "geocode_cache",
}

EXPECTED_TAXONOMY = {
    "PLASTIC",
    "PAPER_CARDBOARD",
    "GLASS",
    "METAL",
    "ORGANIC",
    "TEXTILE",
    "ELECTRONIC_SPECIAL",
    "RESIDUAL_MIXED",
}


def test_operational_tables_are_complete() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_all_foreign_keys_define_delete_behavior() -> None:
    foreign_keys = [fk for table in Base.metadata.tables.values() for fk in table.foreign_keys]
    assert foreign_keys
    assert all(fk.ondelete for fk in foreign_keys)


def test_ai_taxonomy_matches_database_seed() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    mapping = (repository_root / "backend/ai/training/mapping.yaml").read_text(encoding="utf-8")
    migration = (repository_root / "backend/migrations/versions/20260827_0001_initial_schema.py").read_text(encoding="utf-8")
    taxonomy_block = mapping.split("mappings:", maxsplit=1)[0]
    training_codes = set(re.findall(r"^  - ([A-Z_]+)$", taxonomy_block, flags=re.MULTILINE))
    seeded_codes = set(re.findall(r"\(\d+, '([A-Z_]+)'", migration))
    assert training_codes == EXPECTED_TAXONOMY
    assert seeded_codes == EXPECTED_TAXONOMY
