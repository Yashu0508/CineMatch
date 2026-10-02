"""Backend-only OMDb client for title search and movie metadata."""
import logging
from typing import Any

import httpx
from fastapi import HTTPException, status
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.utils.caching import TTLCache

logger = logging.getLogger(__name__)


class OMDbService:
    def __init__(self, client: httpx.AsyncClient | None = None, cache: TTLCache | None = None) -> None:
        self.settings = get_settings()
        self.client = client or httpx.AsyncClient(base_url=self.settings.omdb_api_base_url, timeout=httpx.Timeout(10.0))
        self._owns_client = client is None
        self.cache = cache or TTLCache()

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    @retry(retry=retry_if_exception_type(httpx.TransportError), stop=stop_after_attempt(3), wait=wait_exponential(min=0.2, max=2), reraise=True)
    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.omdb_api_key:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Movie provider is not configured")
        try:
            response = await self.client.get("", params={"apikey": self.settings.omdb_api_key, "r": "json", **params})
        except httpx.TimeoutException as exc:
            logger.warning("OMDb request timed out: operation=%s", params.get("s") or params.get("t") or "unknown")
            raise HTTPException(status_code=504, detail="Movie provider timed out") from exc
        if response.status_code == 401:
            raise HTTPException(status_code=503, detail="Movie provider authentication failed")
        if response.status_code >= 400:
            logger.warning("OMDb request failed: status=%s", response.status_code)
            raise HTTPException(status_code=503, detail="Movie provider request failed")
        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=503, detail="Movie provider returned invalid data") from exc
        if payload.get("Response") != "True":
            error = str(payload.get("Error", "Movie not found"))
            if error.lower() == "movie not found!":
                return {"Response": "False", "Error": error}
            if "invalid api key" in error.lower():
                raise HTTPException(status_code=503, detail="Movie provider authentication failed")
            raise HTTPException(status_code=503, detail="Movie provider request failed")
        return payload

    async def search(self, title: str, page: int = 1) -> dict[str, Any]:
        key = f"search:{title.lower()}:{page}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        payload = await self._request({"s": title, "page": page, "type": "movie"})
        self.cache.set(key, payload, self.settings.omdb_cache_ttl_seconds)
        return payload

    async def details(self, title: str) -> dict[str, Any]:
        key = f"details:{title.lower()}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        payload = await self._request({"t": title, "plot": "full", "type": "movie"})
        self.cache.set(key, payload, self.settings.omdb_cache_ttl_seconds)
        return payload
