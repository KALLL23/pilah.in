from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.models import FacilityAccessScope
from app.repositories.facilities import FacilityRepository
from app.repositories.maps import MapRepository
from app.schemas.facilities import FacilityCreateRequest
from app.services.facilities import FacilityService
from app.services.knowledge import KnowledgeService


class EmptyResult:
    def all(self):
        return []

    def mappings(self):
        return self


class RecordingSession:
    def __init__(self) -> None:
        self.statements = []

    async def scalar(self, statement):
        self.statements.append(statement)
        return 0

    async def execute(self, statement, *_args):
        self.statements.append(statement)
        return EmptyResult()


def test_new_facility_defaults_to_unknown_unverified_and_active() -> None:
    payload = FacilityCreateRequest(
        name="Kandidat",
        facility_type="BANK_SAMPAH",
        address="Semarang",
        latitude=-6.99,
        longitude=110.42,
        source="Survei",
    )

    assert payload.access_scope == FacilityAccessScope.UNKNOWN
    assert payload.verified is False
    assert payload.model_dump().get("is_active", True) is True


@pytest.mark.asyncio
async def test_public_facility_query_enforces_all_visibility_flags() -> None:
    session = RecordingSession()
    await FacilityRepository(session).list_public(category=None, facility_type=None, limit=20, offset=0)
    sql = "\n".join(str(statement) for statement in session.statements)

    assert "facilities.verified IS true" in sql
    assert "facilities.is_active IS true" in sql
    assert "facilities.access_scope" in sql


class SoftDeleteRepository:
    def __init__(self) -> None:
        self.record = SimpleNamespace(id=uuid4(), is_active=True)
        self.committed = False

    async def get(self, *_args, **_kwargs):
        if "public_only" in _kwargs:
            return SimpleNamespace(facility=self.record)
        return SimpleNamespace(record=self.record)

    async def commit(self, _record):
        self.committed = True


@pytest.mark.asyncio
async def test_facility_and_knowledge_delete_are_soft_deletes() -> None:
    facility_repository = SoftDeleteRepository()
    knowledge_repository = SoftDeleteRepository()

    await FacilityService(facility_repository).delete(uuid4())
    await KnowledgeService(knowledge_repository).delete(uuid4())

    assert facility_repository.record.is_active is False
    assert knowledge_repository.record.is_active is False
    assert facility_repository.committed is True
    assert knowledge_repository.committed is True


@pytest.mark.asyncio
async def test_hotspot_sql_uses_engineering_dbscan_contract() -> None:
    session = RecordingSession()
    assert await MapRepository(session).hotspots() == []
    sql = str(session.statements[0])

    assert "ST_ClusterDBSCAN" in sql
    assert "eps => 50" in sql
    assert "minpoints => 3" in sql
    assert "interval '14 days'" in sql
    assert "32749" in sql
