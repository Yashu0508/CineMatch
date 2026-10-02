from pathlib import PurePosixPath
from urllib.parse import quote

import httpx

from app.core.config import get_settings


ALLOWED_PRESET_AVATARS = {"sunset", "ocean", "forest", "violet"}
ALLOWED_CONTENT_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_AVATAR_BYTES = 5 * 1024 * 1024


class AvatarStorageError(Exception):
    pass


def has_valid_image_signature(content_type: str, content: bytes) -> bool:
    signatures = {
        "image/jpeg": content.startswith(b"\xff\xd8\xff"),
        "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
    }
    return signatures.get(content_type, False)


def _storage_config() -> tuple[str, dict[str, str], str]:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AvatarStorageError("Profile image storage is not configured")
    base = settings.supabase_url.rstrip("/")
    headers = {"apikey": settings.supabase_service_role_key}
    if not settings.supabase_service_role_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {settings.supabase_service_role_key}"
    return base, headers, settings.supabase_storage_bucket


async def upload_avatar(path: str, content: bytes, content_type: str) -> None:
    base, headers, bucket = _storage_config()
    url = f"{base}/storage/v1/object/{quote(bucket, safe='')}/{quote(path, safe='/')}"
    request_headers = {**headers, "Content-Type": content_type, "x-upsert": "true"}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, headers=request_headers, content=content)
    except httpx.RequestError as exc:
        raise AvatarStorageError("Profile image storage is unavailable") from exc
    if response.status_code >= 400:
        raise AvatarStorageError("Profile image upload failed")


async def signed_avatar_url(path: str) -> str:
    base, headers, bucket = _storage_config()
    url = f"{base}/storage/v1/object/sign/{quote(bucket, safe='')}/{quote(path, safe='/')}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, headers={**headers, "Content-Type": "application/json"}, json={"expiresIn": 3600})
    except httpx.RequestError as exc:
        raise AvatarStorageError("Profile image storage is unavailable") from exc
    if response.status_code >= 400:
        raise AvatarStorageError("Profile image could not be opened")
    try:
        payload = response.json()
    except ValueError as exc:
        raise AvatarStorageError("Profile image storage returned invalid data") from exc
    signed = payload.get("signedURL") or payload.get("signedUrl")
    if not signed:
        raise AvatarStorageError("Profile image storage returned an invalid URL")
    if signed.startswith("/"):
        if not signed.startswith("/storage/v1/"):
            signed = f"/storage/v1{signed}"
        return f"{base}{signed}"
    return signed


def avatar_path(user_id: str, extension: str) -> str:
    return str(PurePosixPath(str(user_id)) / f"avatar.{extension}")
