import time

import httpx
import pytest

from app.core.config import Settings
from app.services.geocoding import ReverseGeocoder


class FakeRepository:
    def __init__(self, cached=None) -> None:
        self.cached = cached
        self.puts = []

    async def geocode_cache_get(self, _latitude, _longitude):
        return self.cached

    async def geocode_cache_put(self, latitude, longitude, address):
        self.puts.append((latitude, longitude, address))


@pytest.mark.asyncio
async def test_reverse_geocoder_uses_cache_without_network(monkeypatch) -> None:
    repository = FakeRepository("Alamat cache")

    class ForbiddenClient:
        def __init__(self, **_kwargs): raise AssertionError("network must not run on cache hit")

    monkeypatch.setattr(httpx, "AsyncClient", ForbiddenClient)
    result = await ReverseGeocoder(repository, Settings()).reverse(-6.9, 110.4)

    assert result == "Alamat cache"


@pytest.mark.asyncio
async def test_reverse_geocoder_network_failure_returns_none(monkeypatch) -> None:
    repository = FakeRepository()
    ReverseGeocoder._last_request_at = 0

    class FailingClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
        async def get(self, *_args, **_kwargs):
            raise httpx.ConnectError("offline", request=httpx.Request("GET", "https://example.test"))

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: FailingClient())
    result = await ReverseGeocoder(repository, Settings()).reverse(-6.9, 110.4)

    assert result is None
    assert repository.puts == []


@pytest.mark.asyncio
async def test_reverse_geocoder_enforces_one_second_spacing(monkeypatch) -> None:
    repository = FakeRepository()
    sleeps = []
    ReverseGeocoder._last_request_at = time.monotonic()

    class Response:
        def raise_for_status(self): return None
        def json(self): return {"display_name": "Semarang"}

    class Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
        async def get(self, *_args, **_kwargs): return Response()

    async def fake_sleep(delay): sleeps.append(delay)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: Client())
    monkeypatch.setattr("app.services.geocoding.asyncio.sleep", fake_sleep)

    await ReverseGeocoder(repository, Settings()).reverse(-6.9, 110.4)

    assert sleeps and 0 < sleeps[0] <= 1
    assert repository.puts == [(-6.9, 110.4, "Semarang")]
