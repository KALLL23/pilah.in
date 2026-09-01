import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

import httpx

from app.core.config import Settings
from ai.llm.prompts import PromptPackage

logger = logging.getLogger(__name__)


_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*?)\n\s*```\s*$", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    match = _CODE_FENCE_RE.match(text)
    if match:
        return match.group(1).strip()
    return text


class LLMError(Exception):
    def __init__(self, message: str, *, latency_ms: int = 0, status_code: int | None = None) -> None:
        self.latency_ms = latency_ms
        self.status_code = status_code
        super().__init__(message)


class LLMConfigurationError(LLMError):
    pass


class LLMProviderError(LLMError):
    pass


class LLMResponseError(LLMError):
    pass


class OpenRouterClient:
    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.settings = settings
        self.http_client = http_client
        self.sleep = sleep

    def validate_configuration(self) -> None:
        if self.settings.llm_api_key is None:
            raise LLMConfigurationError("LLM_API_KEY is required")
        if self.settings.llm_model is None or not self.settings.llm_model.strip():
            raise LLMConfigurationError("LLM_MODEL is required")

    async def complete(self, prompt: PromptPackage, *, image_url: str | None = None) -> tuple[str, int]:
        self.validate_configuration()
        started_at = perf_counter()

        messages = []
        for msg in prompt.messages:
            if msg["role"] == "user" and image_url:
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": msg["content"]},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                })
            else:
                messages.append(msg)

        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "temperature": self.settings.llm_temperature,
            "response_format": prompt.response_format,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(self.settings.llm_timeout_seconds)

        if self.http_client is not None:
            return await self._complete_with_client(self.http_client, payload, headers, started_at)
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await self._complete_with_client(client, payload, headers, started_at)

    async def _complete_with_client(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
        headers: dict[str, str],
        started_at: float,
    ) -> tuple[str, int]:
        endpoint = f"{str(self.settings.llm_base_url).rstrip('/')}/chat/completions"
        attempts = self.settings.llm_max_retries + 1

        for attempt in range(1, attempts + 1):
            try:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.settings.llm_timeout_seconds,
                )
            except httpx.RequestError as error:
                latency_ms = round((perf_counter() - started_at) * 1000)
                logger.warning(
                    "LLM network failure model=%s prompt_version=%s attempt=%s latency_ms=%s",
                    self.settings.llm_model,
                    self.settings.llm_prompt_version,
                    attempt,
                    latency_ms,
                )
                if attempt < attempts:
                    await self.sleep(0.25 * (2 ** (attempt - 1)))
                    continue
                raise LLMProviderError("LLM network request failed", latency_ms=latency_ms) from error

            latency_ms = round((perf_counter() - started_at) * 1000)
            if response.status_code == 429 or response.status_code >= 500:
                logger.warning(
                    "LLM transient response model=%s prompt_version=%s attempt=%s status=%s latency_ms=%s",
                    self.settings.llm_model,
                    self.settings.llm_prompt_version,
                    attempt,
                    response.status_code,
                    latency_ms,
                )
                if attempt < attempts:
                    await self.sleep(0.25 * (2 ** (attempt - 1)))
                    continue
                raise LLMProviderError(
                    "LLM provider unavailable",
                    latency_ms=latency_ms,
                    status_code=response.status_code,
                )

            if response.status_code >= 400:
                logger.warning(
                    "LLM non-retryable response model=%s prompt_version=%s attempt=%s status=%s latency_ms=%s body=%s",
                    self.settings.llm_model,
                    self.settings.llm_prompt_version,
                    attempt,
                    response.status_code,
                    latency_ms,
                    response.text[:500],
                )
                raise LLMProviderError(
                    "LLM request was rejected",
                    latency_ms=latency_ms,
                    status_code=response.status_code,
                )

            try:
                body = response.json()
                content = body["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError, TypeError) as error:
                raise LLMResponseError("Invalid LLM provider response envelope", latency_ms=latency_ms) from error
            if not isinstance(content, str) or not content.strip():
                raise LLMResponseError("LLM response content is empty or invalid", latency_ms=latency_ms)

            content = _strip_code_fences(content)

            logger.info(
                "LLM request complete model=%s prompt_version=%s attempt=%s status=%s latency_ms=%s",
                self.settings.llm_model,
                self.settings.llm_prompt_version,
                attempt,
                response.status_code,
                latency_ms,
            )
            return content, latency_ms

        raise AssertionError("unreachable")
