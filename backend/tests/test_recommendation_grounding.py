from types import SimpleNamespace
from uuid import uuid4

import pytest

from ai.llm.prompts import build_recommendation_prompt
from ai.llm.repository import condition_scope_matches, knowledge_record_matches
from ai.llm.schemas import KnowledgeContextItem, RecommendationConditions, RecommendationContext
from ai.llm.service import KnowledgeNotAvailableError, RecommendationService
from app.core.config import Settings


def test_condition_scope_matching_is_deterministic() -> None:
    conditions = {"is_reusable": False, "is_contaminated": True, "is_wet": False}

    assert condition_scope_matches({}, conditions) is True
    assert condition_scope_matches({"is_contaminated": True}, conditions) is True
    assert condition_scope_matches({"is_contaminated": False}, conditions) is False
    assert condition_scope_matches({"unknown": True}, conditions) is False
    assert condition_scope_matches({"is_wet": 0}, conditions) is False


def test_inactive_or_wrong_category_knowledge_never_matches() -> None:
    conditions = {"is_reusable": True, "is_contaminated": False, "is_wet": False}
    record = SimpleNamespace(category_id=1, is_active=True, condition_scope={"is_reusable": True})

    assert knowledge_record_matches(record, 1, conditions) is True
    record.is_active = False
    assert knowledge_record_matches(record, 1, conditions) is False
    record.is_active = True
    assert knowledge_record_matches(record, 2, conditions) is False


def test_prompt_contains_atomic_verified_facts_not_ready_made_guidance() -> None:
    fact_id = uuid4()
    context = RecommendationContext(
        category="PLASTIC",
        conditions=RecommendationConditions(is_reusable=False, is_contaminated=True, is_wet=False),
        facts=[KnowledgeContextItem(id=fact_id, content="Kemasan berminyak menurunkan kualitas material.", source="Sumber")],
        facilities=[],
    )

    prompt = build_recommendation_prompt(context, "v1")
    user_content = prompt.messages[1]["content"]

    assert "VERIFIED WASTE FACTS" in user_content
    assert str(fact_id) in user_content
    assert "management_guidance" not in user_content
    assert "preparation_guidance" not in user_content


class EmptyKnowledgeRepository:
    def __init__(self) -> None:
        self.failed = False
        self.pending_knowledge_ids = None

    async def get_owned_scan(self, _scan_id, _user_id):
        return SimpleNamespace(
            scan=SimpleNamespace(
                id=uuid4(),
                confirmed_category_id=1,
                is_reusable=False,
                is_contaminated=False,
                is_wet=False,
            ),
            category_code="PLASTIC",
        )

    async def get_relevant_knowledge(self, _category_id, _conditions):
        return []

    async def get_relevant_facilities(self, _category_id):
        return []

    async def save_pending(self, _scan, **values):
        self.pending_knowledge_ids = values["knowledge_ids"]

    async def save_failed(self, _scan, **_values):
        self.failed = True


class ClientThatMustNotRun:
    async def complete(self, _prompt):
        raise AssertionError("LLM must not run without verified facts")


@pytest.mark.asyncio
async def test_recommendation_rejects_missing_facts_before_llm_call() -> None:
    repository = EmptyKnowledgeRepository()
    service = RecommendationService(repository, ClientThatMustNotRun(), Settings())

    with pytest.raises(KnowledgeNotAvailableError):
        await service.recommend(uuid4(), uuid4())

    assert repository.pending_knowledge_ids == []
    assert repository.failed is True
