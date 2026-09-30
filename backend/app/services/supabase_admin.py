"""Dedicated, session-free Supabase Auth admin client.

This client is backend-only and intentionally never accepts or forwards a
user session. New ``sb_secret_*`` keys are sent as ``apikey`` only; legacy
JWT service-role keys also receive the conventional Bearer header.
"""
import httpx
from fastapi import HTTPException
from app.core.config import get_settings


class SupabaseAdminService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise HTTPException(status_code=503, detail="Supabase admin authentication is not configured")
        self._base_url = settings.supabase_url.rstrip("/") + "/auth/v1"
        self._key = settings.supabase_service_role_key

    @property
    def _headers(self) -> dict[str, str]:
        headers = {"apikey": self._key, "Content-Type": "application/json"}
        if not self._key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self._key}"
        return headers

    async def create_user(self, email: str, password: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=15) as client:
            response = await client.post("/admin/users", headers=self._headers, json={"email": email, "password": password, "email_confirm": True})
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Supabase Auth admin user creation failed")
        return response.json()

    async def delete_user(self, user_id: str) -> None:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=15) as client:
            response = await client.delete(f"/admin/users/{user_id}", headers=self._headers)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Supabase Auth admin user deletion failed")
