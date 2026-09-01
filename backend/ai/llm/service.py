import asyncio
import base64
import io
import logging
import mimetypes
from typing import Protocol
from uuid import UUID

from PIL import Image
from pydantic import ValidationError

from app.core.config import Settings
from app.services.storage import ObjectStorage
from ai.llm.client import LLMConfigurationError, LLMError
from ai.llm.prompts import PromptPackage, UnsupportedPromptVersionError, build_recommendation_prompt
from ai.llm.repository import RecommendationRepository
from ai.llm.schemas import (
    LLMRecommendation,
    RecommendationConditions,
    RecommendationContext,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)


class RecommendationClient(Protocol):
    async def complete(self, prompt: PromptPackage, *, image_url: str | None = None) -> tuple[str, int]: ...


class ScanNotFoundError(Exception):
    pass


class ScanNotReadyError(Exception):
    pass


class KnowledgeNotAvailableError(Exception):
    pass


class RecommendationGenerationError(Exception):
    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


def validate_facility_recommendations(recommendation: LLMRecommendation, allowed_facility_ids: set[UUID]) -> None:
    recommended_ids = recommendation.recommended_facility_ids
    if len(set(recommended_ids)) != len(recommended_ids):
        raise ValueError("Duplicate facility IDs are not allowed")
    hallucinated_ids = set(recommended_ids) - allowed_facility_ids
    if hallucinated_ids:
        raise ValueError("Recommendation contains facility IDs outside the supplied context")


class RecommendationService:
    def __init__(
        self,
        repository: RecommendationRepository,
        client: RecommendationClient,
        settings: Settings,
        storage: ObjectStorage | None = None,
    ) -> None:
        self.repository = repository
        self.client = client
        self.settings = settings
        self.storage = storage

    async def recommend(self, scan_id: UUID, user_id: UUID) -> RecommendationResponse:
        owned_scan = await self.repository.get_owned_scan(scan_id, user_id)
        if owned_scan is None:
            raise ScanNotFoundError

        scan = owned_scan.scan
        condition_values = (scan.is_reusable, scan.is_contaminated, scan.is_wet)
        if scan.confirmed_category_id is None or owned_scan.category_code is None or any(value is None for value in condition_values):
            raise ScanNotReadyError

        conditions = RecommendationConditions(
            is_reusable=scan.is_reusable,
            is_contaminated=scan.is_contaminated,
            is_wet=scan.is_wet,
        )
        condition_dict = conditions.model_dump()
        knowledge = await self.repository.get_relevant_knowledge(scan.confirmed_category_id, condition_dict)
        facilities = await self.repository.get_relevant_facilities(scan.confirmed_category_id)
        context = RecommendationContext(
            category=owned_scan.category_code,
            conditions=conditions,
            facts=knowledge,
            facilities=facilities,
        )
        knowledge_ids = [item.id for item in knowledge]
        facility_ids = [item.id for item in facilities]

        await self.repository.save_pending(
            scan,
            llm_model=self.settings.llm_model,
            prompt_version=self.settings.llm_prompt_version,
            knowledge_ids=knowledge_ids,
            facility_ids=facility_ids,
        )

        if not knowledge:
            await self.repository.save_failed(scan)
            raise KnowledgeNotAvailableError

        image_url = None
        if self.storage is not None:
            try:
                image_bytes = await asyncio.to_thread(self.storage.download, scan.image_key)
                img = Image.open(io.BytesIO(image_bytes))
                img.thumbnail((512, 512))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=80)
                b64 = base64.b64encode(buf.getvalue()).decode()
                image_url = f"data:image/jpeg;base64,{b64}"
            except Exception:
                logger.warning("Failed to prepare image for scan %s, proceeding without vision", scan_id)

        try:
            prompt = build_recommendation_prompt(context, self.settings.llm_prompt_version)
            content, latency_ms = await self.client.complete(prompt, image_url=image_url)
            recommendation = LLMRecommendation.model_validate_json(content)
            validate_facility_recommendations(recommendation, set(facility_ids))
        except LLMConfigurationError as error:
            await self.repository.save_failed(scan, latency_ms=error.latency_ms)
            logger.warning("Recommendation failed scan_id=%s category=configuration", scan_id)
            raise RecommendationGenerationError("configuration") from error
        except LLMError as error:
            await self.repository.save_failed(scan, latency_ms=error.latency_ms)
            logger.warning(
                "Recommendation failed scan_id=%s model=%s prompt_version=%s category=provider",
                scan_id,
                self.settings.llm_model,
                self.settings.llm_prompt_version,
            )
            raise RecommendationGenerationError("provider") from error
        except UnsupportedPromptVersionError as error:
            await self.repository.save_failed(scan)
            logger.warning("Recommendation failed scan_id=%s category=configuration", scan_id)
            raise RecommendationGenerationError("configuration") from error
        except (ValidationError, ValueError) as error:
            latency = locals().get("latency_ms")
            await self.repository.save_failed(scan, latency_ms=latency)
            logger.warning("Recommendation failed scan_id=%s category=validation", scan_id)
            raise RecommendationGenerationError("validation") from error

        recycling_products = [p.model_dump() for p in recommendation.recycling_products]

        await self.repository.save_success(
            scan,
            action=recommendation.action,
            reason=recommendation.reason,
            recycling_target=recommendation.recycling_target,
            preparation_steps=recommendation.preparation_steps,
            recycling_products=recycling_products,
            warnings=recommendation.warnings,
            latency_ms=latency_ms,
        )
        return RecommendationResponse(
            scan_id=scan.id,
            recommendation_status="SUCCESS",
            action=recommendation.action,
            reason=recommendation.reason,
            recycling_target=recommendation.recycling_target,
            preparation_steps=recommendation.preparation_steps,
            recycling_products=recycling_products,
            facility_required=recommendation.facility_required,
            recommended_facility_ids=recommendation.recommended_facility_ids,
            warnings=recommendation.warnings,
            llm_model=self.settings.llm_model or "",
            prompt_version=self.settings.llm_prompt_version,
            knowledge_ids=knowledge_ids,
            facility_ids_in_context=facility_ids,
            llm_latency_ms=latency_ms,
        )
