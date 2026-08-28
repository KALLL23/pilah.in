import json
from dataclasses import dataclass
from typing import Any

from ai.llm.schemas import LLMRecommendation, RecommendationContext


@dataclass(frozen=True)
class PromptPackage:
    messages: list[dict[str, str]]
    response_format: dict[str, Any]


SYSTEM_PROMPTS = {
    "v1": """You are the Waste Recommendation Decision Engine for pilah.in, not a general-purpose assistant.
Use only facts explicitly present in the supplied context. Do not use external knowledge. Do not invent materials,
facilities, regulations, waste-management facts, warnings, or facility IDs. Choose exactly one action from REUSE,
RECYCLE, COMPOST, RESIDUAL, or SPECIAL_HANDLING. A facility ID may be returned only when it appears under
VERIFIED FACILITIES. An empty facility list is valid; when it is empty, recommended_facility_ids must be empty,
even when facility_required is true. Preserve warnings supported by WASTE KNOWLEDGE. All user-facing text in
reason, preparation_steps, and warnings must be concise, clear Bahasa Indonesia. Return only JSON matching the
provided schema."""
}


class UnsupportedPromptVersionError(ValueError):
    pass


def build_recommendation_prompt(context: RecommendationContext, version: str) -> PromptPackage:
    try:
        system_prompt = SYSTEM_PROMPTS[version]
    except KeyError as error:
        raise UnsupportedPromptVersionError(f"Unsupported LLM prompt version: {version}") from error

    context_payload = context.model_dump(mode="json")
    user_prompt = "RECOMMENDATION CONTEXT\n" + json.dumps(
        {
            "CATEGORY": context_payload["category"],
            "CONDITIONS": context_payload["conditions"],
            "WASTE KNOWLEDGE": context_payload["knowledge"],
            "VERIFIED FACILITIES": context_payload["facilities"],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return PromptPackage(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "waste_recommendation",
                "strict": True,
                "schema": LLMRecommendation.model_json_schema(),
            },
        },
    )
