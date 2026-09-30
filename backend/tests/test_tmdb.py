import httpx
import pytest
from app.services.tmdb import TMDBService

@pytest.mark.asyncio
async def test_tmdb_client_normalizes_transport_without_live_network(monkeypatch):
    monkeypatch.setenv("TMDB_ACCESS_TOKEN", "test-token")
    async def handler(request): return httpx.Response(200, json={"results": [], "page": 1, "total_results": 0})
    service = TMDBService(httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://example.test"))
    service.settings = service.settings.model_copy(update={"tmdb_access_token": "test-token"})
    payload = await service.listing("popular")
    assert payload["results"] == []
