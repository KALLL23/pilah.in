import asyncio
import time

import httpx

from app.core.config import Settings
from app.repositories.reports import ReportRepository


class ReverseGeocoder:
    _lock = asyncio.Lock()
    _last_request_at = 0.0

    def __init__(self, repository: ReportRepository, settings: Settings) -> None:
        self.repository = repository
        self.base_url = str(settings.nominatim_base_url).rstrip("/")
        self.user_agent = settings.nominatim_user_agent
        self.timeout = settings.nominatim_timeout_seconds

    async def reverse(self, latitude: float, longitude: float) -> str | None:
        cached = await self.repository.geocode_cache_get(latitude, longitude)
        if cached is not None:
            return cached
        async with self._lock:
            delay = 1.0 - (time.monotonic() - self._last_request_at)
            if delay > 0:
                await asyncio.sleep(delay)
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.base_url}/reverse",
                        params={"lat": latitude, "lon": longitude, "format": "jsonv2"},
                        headers={"User-Agent": self.user_agent},
                    )
                    response.raise_for_status()
                    address = response.json().get("display_name")
            except (httpx.HTTPError, ValueError, TypeError):
                address = None
            finally:
                self.__class__._last_request_at = time.monotonic()
        if isinstance(address, str) and address.strip():
            await self.repository.geocode_cache_put(latitude, longitude, address.strip())
            return address.strip()
        return None
