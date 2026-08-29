import importlib.util
import sys
from pathlib import Path
from types import ModuleType


class RecordingOp:
    def __init__(self) -> None:
        self.sql = []

    def execute(self, statement) -> None:
        self.sql.append(" ".join(str(statement).split()))


def load_migration(monkeypatch, op):
    fake_alembic = ModuleType("alembic")
    fake_alembic.op = op
    monkeypatch.setitem(sys.modules, "alembic", fake_alembic)
    path = Path(__file__).resolve().parents[1] / "migrations" / "versions" / "20260829_0002_context_facts_and_facility_access.py"
    spec = importlib.util.spec_from_file_location("knowledge_facility_migration", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_knowledge_migration_upgrade_splits_atomic_content_and_adds_facility_state(monkeypatch) -> None:
    operation = RecordingOp()
    migration = load_migration(monkeypatch, operation)

    migration.upgrade()
    sql = "\n".join(operation.sql)

    assert "UPDATE waste_knowledge SET content = management_guidance" in sql
    assert "jsonb_array_elements_text" in sql
    assert "preparation_guidance" in sql and "warnings" in sql
    assert "DROP COLUMN management_guidance" in sql
    assert "CREATE TYPE facility_access_scope" in sql
    assert "ADD COLUMN is_active boolean NOT NULL DEFAULT true" in sql


def test_knowledge_migration_downgrade_restores_previous_columns(monkeypatch) -> None:
    operation = RecordingOp()
    migration = load_migration(monkeypatch, operation)

    migration.downgrade()
    sql = "\n".join(operation.sql)

    assert "ADD COLUMN management_guidance text" in sql
    assert "ADD COLUMN preparation_guidance jsonb" in sql
    assert "ADD COLUMN warnings jsonb" in sql
    assert "UPDATE waste_knowledge SET management_guidance = content" in sql
    assert "DROP TYPE facility_access_scope" in sql
