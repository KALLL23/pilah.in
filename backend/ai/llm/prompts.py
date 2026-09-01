import json
from dataclasses import dataclass
from typing import Any

from ai.llm.schemas import LLMRecommendation, RecommendationContext


@dataclass(frozen=True)
class PromptPackage:
    messages: list[dict[str, str]]
    response_format: dict[str, Any]


SCHEMA_INSTRUCTIONS = """
EXPECTED JSON OUTPUT FORMAT (return ONLY valid JSON matching this structure):
{
  "action": "REUSE" | "RECYCLE" | "COMPOST" | "RESIDUAL" | "SPECIAL_HANDLING",
  "reason": "string (Bahasa Indonesia)",
  "recycling_target": "string (Bahasa Indonesia)",
  "preparation_steps": ["step1", "step2", "step3"],
  "recycling_products": [
    {
      "name": "string",
      "description": "string",
      "tools_needed": ["tool1", "tool2"],
      "steps": ["step1", "step2", "step3", "step4", "step5"],
      "difficulty": "MUDAH" | "SEDANG" | "SULIT",
      "estimated_time": "string (e.g. '30 menit', '1 jam')"
    }
  ],
  "facility_required": true | false,
  "recommended_facility_ids": ["uuid1", "uuid2"],
  "warnings": ["warning1", "warning2"]
}
"""

SYSTEM_PROMPTS = {
    "v1": """Anda adalah Mesin Rekomendasi Daur Ulang untuk pilah.in.
Gunakan HANYA fakta dari konteks yang diberikan. Jangan mengarang fasilitas, material, atau regulasi.
Pilih tepat satu tindakan: REUSE, RECYCLE, COMPOST, RESIDUAL, atau SPECIAL_HANDLING.
ID fasilitas hanya boleh dari daftar VERIFIED FACILITIES. Daftar kosong berarti recommended_facility_ids kosong.
Untuk recycling_target, deskripsikan spesifik apa yang bisa dihasilkan dari sampah tersebut.
Untuk preparation_steps, berikan 3-5 langkah konkret dan dapat ditindaklanjuti.
Buat 3-5 opsi produk daur ulang yang realistis untuk masyarakat umum.
Semua teks harus dalam Bahasa Indonesia yang jelas dan singkat. Return hanya JSON.""",

    "v2": """Anda adalah Mesin Rekomendasi Daur Ulang untuk pilah.in.
Jika foto tersedia, analisis foto secara visual untuk mengidentifikasi jenis sampah dan kondisi fisik.
Gunakan HANYA fakta dari konteks yang diberikan dan analisis visual foto.
Jangan mengarang fasilitas, material, atau regulasi.
ID fasilitas hanya boleh dari daftar VERIFIED FACILITIES.
Buat 3-5 opsi produk daur ulang yang realistis untuk masyarakat umum.
Semua teks harus dalam Bahasa Indonesia yang jelas dan singkat. Return hanya JSON.""",
}


class UnsupportedPromptVersionError(ValueError):
    pass


def build_recommendation_prompt(context: RecommendationContext, version: str) -> PromptPackage:
    try:
        system_prompt = SYSTEM_PROMPTS[version]
    except KeyError as error:
        raise UnsupportedPromptVersionError(f"Unsupported LLM prompt version: {version}") from error

    context_payload = context.model_dump(mode="json")
    user_prompt = (
        "RECOMMENDATION CONTEXT\n"
        + json.dumps(
            {
                "CATEGORY": context_payload["category"],
                "CONDITIONS": context_payload["conditions"],
                "VERIFIED WASTE FACTS": context_payload["facts"],
                "VERIFIED FACILITIES": context_payload["facilities"],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n\n"
        + SCHEMA_INSTRUCTIONS
    )
    return PromptPackage(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_object",
        },
    )
