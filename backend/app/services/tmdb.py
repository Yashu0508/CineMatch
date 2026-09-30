import logging
from typing import Any
import httpx
from fastapi import HTTPException, status
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from app.core.config import get_settings
from app.utils.caching import TTLCache

logger = logging.getLogger(__name__)


class TMDBService:
    def __init__(self, client: httpx.AsyncClient | None = None, cache: TTLCache | None = None) -> None:
        self.settings = get_settings()
        self.client = client or httpx.AsyncClient(base_url=self.settings.tmdb_api_base_url, timeout=httpx.Timeout(10.0))
        self._owns_client = client is None
        self.cache = cache or TTLCache()

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    @retry(retry=retry_if_exception_type(httpx.TransportError), stop=stop_after_attempt(3), wait=wait_exponential(min=0.2, max=2), reraise=True)
    async def _request(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.settings.tmdb_access_token:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Movie provider is not configured")
        headers = {"Authorization": f"Bearer {self.settings.tmdb_access_token}", "Accept": "application/json"}
        query = {"language": self.settings.tmdb_language, **(params or {})}
        try:
            response = await self.client.get(path, headers=headers, params=query)
        except httpx.TimeoutException as exc:
            logger.warning("TMDB request timed out for %s", path)
            raise HTTPException(status_code=504, detail="Movie provider timed out") from exc
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Movie not found")
        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="Movie provider rate limit reached")
        if response.status_code >= 400:
            logger.warning("TMDB request failed: path=%s status=%s", path, response.status_code)
            raise HTTPException(status_code=502, detail="Movie provider request failed")
        return response.json()

    async def get(self, path: str, params: dict[str, Any] | None = None, cacheable: bool = True) -> dict[str, Any]:
        key = f"{path}:{sorted((params or {}).items())}"
        if cacheable and (cached := self.cache.get(key)) is not None:
            return cached
        try:
            payload = await self._request(path, params)
        except httpx.TransportError as exc:
            # Keep provider outages actionable without exposing request headers
            # or credentials. Tenacity has already exhausted its retries.
            logger.warning("TMDB transport failure: path=%s error=%s", path, type(exc).__name__)
            raise HTTPException(status_code=503, detail="Movie provider is temporarily unavailable") from exc
        if cacheable:
            self.cache.set(key, payload, self.settings.tmdb_cache_ttl_seconds)
        return payload

    async def listing(self, category: str, page: int = 1) -> dict[str, Any]:
        paths = {"trending": "/trending/movie/week", "popular": "/movie/popular", "top-rated": "/movie/top_rated", "upcoming": "/movie/upcoming"}
        return await self.get(paths[category], {"page": page, "region": self.settings.tmdb_region})

    async def search(self, query: str, page: int = 1) -> dict[str, Any]: return await self.get("/search/movie", {"query": query, "page": page})
    async def details(self, tmdb_id: int) -> dict[str, Any]: return await self.get(f"/movie/{tmdb_id}")
    async def similar(self, tmdb_id: int, page: int = 1) -> dict[str, Any]: return await self.get(f"/movie/{tmdb_id}/similar", {"page": page})
    async def recommendations(self, tmdb_id: int, page: int = 1) -> dict[str, Any]: return await self.get(f"/movie/{tmdb_id}/recommendations", {"page": page})
    async def credits(self, tmdb_id: int) -> dict[str, Any]: return await self.get(f"/movie/{tmdb_id}/credits")
    async def videos(self, tmdb_id: int) -> dict[str, Any]: return await self.get(f"/movie/{tmdb_id}/videos")
    async def genres(self) -> dict[str, Any]: return await self.get("/genre/movie/list")
    async def discover(self, params: dict[str, Any]) -> dict[str, Any]: return await self.get("/discover/movie", params)
    async def watch_providers(self, tmdb_id: int) -> dict[str, Any]: return await self.get(f"/movie/{tmdb_id}/watch/providers")
