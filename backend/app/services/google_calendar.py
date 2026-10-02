from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import CalendarReminder, GoogleCalendarConnection, Movie


GOOGLE_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


class GoogleCalendarError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _settings():
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret or not settings.google_redirect_uri:
        raise GoogleCalendarError(503, "Google Calendar is not configured")
    return settings


def _cipher() -> Fernet:
    key = get_settings().google_token_encryption_key
    if not key:
        raise GoogleCalendarError(503, "Google Calendar token encryption is not configured")
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise GoogleCalendarError(503, "Google Calendar token encryption is not configured correctly") from exc


def encrypt_token(token: str) -> str:
    return _cipher().encrypt(token.encode()).decode()


def decrypt_token(value: str) -> str:
    try:
        return _cipher().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError, TypeError) as exc:
        raise GoogleCalendarError(503, "Stored Google Calendar authorization is unreadable") from exc


def ensure_token_encryption_ready() -> None:
    _cipher()


def authorization_url(state: str) -> str:
    settings = _settings()
    return f"{GOOGLE_AUTH_URL}?{urlencode({'client_id': settings.google_client_id, 'redirect_uri': settings.google_redirect_uri, 'response_type': 'code', 'scope': GOOGLE_CALENDAR_SCOPE, 'access_type': 'offline', 'prompt': 'consent', 'state': state})}"


def _provider_error(response: httpx.Response, default: str) -> GoogleCalendarError:
    if response.status_code == 429:
        return GoogleCalendarError(429, "Google Calendar is temporarily rate limited")
    if response.status_code in (400, 401):
        return GoogleCalendarError(502, default)
    return GoogleCalendarError(502, "Google Calendar request failed")


def _json_object(response: httpx.Response, message: str) -> dict:
    try:
        payload = response.json()
    except ValueError as exc:
        raise GoogleCalendarError(502, message) from exc
    if not isinstance(payload, dict):
        raise GoogleCalendarError(502, message)
    return payload


async def _post(url: str, **kwargs) -> httpx.Response:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            return await client.post(url, **kwargs)
    except httpx.RequestError as exc:
        raise GoogleCalendarError(503, "Google Calendar is unavailable") from exc


async def exchange_code(code: str) -> dict:
    settings = _settings()
    response = await _post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    if response.status_code >= 400:
        raise _provider_error(response, "Google authorization could not be completed")
    payload = _json_object(response, "Google authorization returned an invalid response")
    if not payload.get("access_token"):
        raise GoogleCalendarError(502, "Google authorization returned an invalid token response")
    return payload


async def refresh_access_token(refresh_token: str) -> dict:
    settings = _settings()
    response = await _post(
        GOOGLE_TOKEN_URL,
        data={
            "refresh_token": refresh_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "grant_type": "refresh_token",
        },
    )
    if response.status_code >= 400:
        raise _provider_error(response, "Google Calendar authorization has expired; please reconnect it")
    payload = _json_object(response, "Google token refresh returned an invalid response")
    if not payload.get("access_token"):
        raise GoogleCalendarError(502, "Google token refresh returned an invalid response")
    return payload


def _expires_at(expires_in: int | None) -> datetime | None:
    return datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None


async def access_token_for(db: Session, connection: GoogleCalendarConnection) -> str:
    now = datetime.now(timezone.utc)
    expires_at = connection.token_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at is None or expires_at > now + timedelta(seconds=60):
        return decrypt_token(connection.access_token_encrypted)
    if not connection.refresh_token_encrypted:
        raise GoogleCalendarError(409, "Google Calendar authorization has expired; please reconnect it")
    refreshed = await refresh_access_token(decrypt_token(connection.refresh_token_encrypted))
    connection.access_token_encrypted = encrypt_token(refreshed["access_token"])
    connection.token_expires_at = _expires_at(refreshed.get("expires_in"))
    db.commit()
    return refreshed["access_token"]


def save_connection(db: Session, user_id, payload: dict) -> GoogleCalendarConnection:
    existing = db.get(GoogleCalendarConnection, user_id)
    refresh_token = payload.get("refresh_token")
    if existing is None:
        if not refresh_token:
            raise GoogleCalendarError(502, "Google authorization did not provide a refresh token")
        existing = GoogleCalendarConnection(user_id=user_id, refresh_token_encrypted=encrypt_token(refresh_token))
        db.add(existing)
    elif refresh_token:
        existing.refresh_token_encrypted = encrypt_token(refresh_token)
    existing.access_token_encrypted = encrypt_token(payload["access_token"])
    existing.token_expires_at = _expires_at(payload.get("expires_in"))
    existing.scope = payload.get("scope") or GOOGLE_CALENDAR_SCOPE
    db.commit()
    db.refresh(existing)
    return existing


async def create_event(access_token: str, movie: Movie) -> dict:
    if movie.release_date is None or movie.release_date <= date.today():
        raise GoogleCalendarError(400, "A future release date is required for a reminder")
    end_date = movie.release_date + timedelta(days=1)
    payload = {
        "summary": f"{movie.title} — CineMatch reminder",
        "description": f"CineMatch movie reminder\nMovie ID: {movie.id}\nRelease date: {movie.release_date.isoformat()}",
        "start": {"date": movie.release_date.isoformat()},
        "end": {"date": end_date.isoformat()},
    }
    response = await _post(GOOGLE_CALENDAR_EVENTS_URL, json=payload, headers={"Authorization": f"Bearer {access_token}"})
    if response.status_code >= 400:
        raise _provider_error(response, "Google Calendar could not create the reminder")
    result = _json_object(response, "Google Calendar returned an invalid event response")
    if not result.get("id"):
        raise GoogleCalendarError(502, "Google Calendar returned an invalid event response")
    return result


async def create_reminder(db: Session, user_id, movie_id: int) -> tuple[CalendarReminder, bool]:
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise GoogleCalendarError(404, "Movie not found")
    if movie.release_date is None or movie.release_date <= date.today():
        raise GoogleCalendarError(400, "A future release date is required for a reminder")
    existing_reminder = db.scalar(select(CalendarReminder).where(CalendarReminder.user_id == user_id, CalendarReminder.movie_id == movie_id))
    if existing_reminder is not None:
        return existing_reminder, False
    connection = db.get(GoogleCalendarConnection, user_id)
    if connection is None:
        raise GoogleCalendarError(409, "Connect Google Calendar before setting a reminder")
    event = await create_event(await access_token_for(db, connection), movie)
    reminder = CalendarReminder(user_id=user_id, movie_id=movie_id, google_event_id=event["id"], release_date=movie.release_date)
    db.add(reminder)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_reminder = db.scalar(select(CalendarReminder).where(CalendarReminder.user_id == user_id, CalendarReminder.movie_id == movie_id))
        if existing_reminder is not None:
            return existing_reminder, False
        raise
    db.refresh(reminder)
    return reminder, True
