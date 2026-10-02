import httpx
from fastapi import HTTPException
from app.core.config import get_settings


class AuthService:
    async def _request(self, path: str, body: dict) -> dict:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise HTTPException(status_code=503, detail="Authentication is not configured")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{settings.supabase_url.rstrip('/')}/auth/v1/{path}", json=body, headers={"apikey": settings.supabase_anon_key})
        if response.status_code >= 400:
            if response.status_code == 429:
                raise HTTPException(status_code=429, detail="Authentication service is temporarily rate limited")
            raise HTTPException(status_code=401 if path == "token?grant_type=password" else 400, detail="Authentication request failed")
        return response.json()

    async def register(self, email: str, password: str) -> dict: return await self._request("signup", {"email": email, "password": password})
    async def login(self, email: str, password: str) -> dict: return await self._request("token?grant_type=password", {"email": email, "password": password})
