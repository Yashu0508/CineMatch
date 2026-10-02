import httpx
import pytest

from app.services.omdb import OMDbService


@pytest.mark.asyncio
async def test_omdb_search_uses_backend_key_without_exposing_it(monkeypatch):
    monkeypatch.setenv("OMDB_API_KEY", "test-key")

    async def handler(request: httpx.Request):
        assert request.url.params["apikey"] == "test-key"
        assert request.url.params["s"] == "Matrix"
        return httpx.Response(200, json={"Response": "True", "Search": [{"Title": "The Matrix", "Type": "movie"}]})

    service = OMDbService(httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://example.test"))
    service.settings = service.settings.model_copy(update={"omdb_api_key": "test-key"})
    payload = await service.search("Matrix")
    assert payload["Search"][0]["Title"] == "The Matrix"


@pytest.mark.asyncio
async def test_omdb_invalid_key_is_safe(monkeypatch):
    monkeypatch.setenv("OMDB_API_KEY", "test-key")

    async def handler(request: httpx.Request):
        return httpx.Response(200, json={"Response": "False", "Error": "Invalid API key!"})

    service = OMDbService(httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://example.test"))
    service.settings = service.settings.model_copy(update={"omdb_api_key": "test-key"})
    with pytest.raises(Exception) as error:
        await service.search("Matrix")
    assert "test-key" not in str(error.value)
