from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.models import CalendarReminder, GoogleCalendarConnection, GoogleOAuthState, Movie, User
from app.main import app
from app.services import google_calendar


def seed_future_movie(session, user):
    session.add(User(id=user.id, email=user.email))
    movie = Movie(tmdb_id=901, title="Future Film", release_date=date.today() + timedelta(days=14))
    session.add(movie)
    session.commit()
    session.refresh(movie)
    return movie


def calendar_settings():
    return get_settings().model_copy(update={
        "google_client_id": "client-id",
        "google_client_secret": "client-secret",
        "google_redirect_uri": "http://localhost:8000/api/calendar/oauth/callback",
        "google_token_encryption_key": Fernet.generate_key().decode(),
    })


def test_oauth_start_requires_authentication(client):
    api, Session, user = client
    with Session() as db:
        movie = seed_future_movie(db, user)

    def reject_auth():
        raise HTTPException(status_code=401, detail="Authentication required")

    original = app.dependency_overrides[get_current_user]
    app.dependency_overrides[get_current_user] = reject_auth
    try:
        assert api.get(f"/api/calendar/oauth/start?movie_id={movie.id}").status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = original


def test_oauth_start_stores_hashed_state(client, monkeypatch):
    api, Session, user = client
    with Session() as db:
        movie = seed_future_movie(db, user)
    monkeypatch.setattr("app.services.google_calendar.get_settings", calendar_settings)
    monkeypatch.setattr("app.api.calendar.authorization_url", lambda state: f"https://accounts.google.test/auth?state={state}")

    response = api.get(f"/api/calendar/oauth/start?movie_id={movie.id}")
    assert response.status_code == 200
    state = parse_qs(urlparse(response.json()["authorization_url"]).query)["state"][0]
    with Session() as db:
        stored = db.get(GoogleOAuthState, sha256(state.encode()).hexdigest())
        assert stored is not None
        assert stored.user_id == user.id
        assert stored.movie_id == movie.id


def test_callback_rejects_invalid_state(client):
    api, _, _ = client
    response = api.get("/api/calendar/oauth/callback?state=invalid")
    assert response.status_code == 400


def test_callback_handles_authorization_denial(client):
    api, Session, user = client
    state = "denied-state"
    with Session() as db:
        db.add(User(id=user.id, email=user.email))
        db.add(GoogleOAuthState(state_hash=sha256(state.encode()).hexdigest(), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)))
        db.commit()
    response = api.get(f"/api/calendar/oauth/callback?state={state}&error=access_denied", follow_redirects=False)
    assert response.status_code == 303
    assert "calendar=denied" in response.headers["location"]


@pytest.mark.asyncio
async def test_callback_handles_provider_error(client, monkeypatch):
    api, Session, user = client
    state = "provider-error-state"
    with Session() as db:
        db.add(User(id=user.id, email=user.email))
        db.add(GoogleOAuthState(state_hash=sha256(state.encode()).hexdigest(), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)))
        db.commit()
    async def exchange(_code):
        raise google_calendar.GoogleCalendarError(502, "provider failure")
    monkeypatch.setattr("app.api.calendar.exchange_code", exchange)
    response = api.get(f"/api/calendar/oauth/callback?state={state}&code=code", follow_redirects=False)
    assert response.status_code == 303
    assert "calendar=error" in response.headers["location"]


@pytest.mark.asyncio
async def test_successful_callback_encrypts_and_stores_authorization(client, monkeypatch):
    api, Session, user = client
    settings = calendar_settings()
    monkeypatch.setattr("app.services.google_calendar.get_settings", lambda: settings)
    state = "known-state"
    with Session() as db:
        db.add(User(id=user.id, email=user.email))
        db.add(GoogleOAuthState(state_hash=sha256(state.encode()).hexdigest(), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)))
        db.commit()
    async def exchange(_code):
        return {"access_token": "access-token", "refresh_token": "refresh-token", "expires_in": 3600, "scope": google_calendar.GOOGLE_CALENDAR_SCOPE}
    monkeypatch.setattr("app.api.calendar.exchange_code", exchange)
    async def no_reminder(*args):
        return None
    monkeypatch.setattr("app.api.calendar.create_reminder", no_reminder)

    response = api.get(f"/api/calendar/oauth/callback?state={state}&code=code", follow_redirects=False)
    assert response.status_code == 303
    with Session() as db:
        connection = db.get(GoogleCalendarConnection, user.id)
        assert connection is not None
        assert connection.access_token_encrypted != "access-token"
        assert google_calendar.decrypt_token(connection.refresh_token_encrypted) == "refresh-token"


def test_reminder_rejects_missing_release_date(client):
    api, Session, user = client
    with Session() as db:
        db.add(User(id=user.id, email=user.email))
        movie = Movie(tmdb_id=902, title="Undated Film")
        db.add(movie)
        db.commit()
        db.refresh(movie)
    response = api.post("/api/calendar/reminders", json={"movie_id": movie.id})
    assert response.status_code == 400


def test_reminder_requires_google_authorization(client):
    api, Session, user = client
    with Session() as db:
        movie = seed_future_movie(db, user)
    response = api.post("/api/calendar/reminders", json={"movie_id": movie.id})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_reminder_creation_is_idempotent(client, monkeypatch):
    api, Session, user = client
    settings = calendar_settings()
    monkeypatch.setattr("app.services.google_calendar.get_settings", lambda: settings)
    with Session() as db:
        movie = seed_future_movie(db, user)
        db.add(GoogleCalendarConnection(user_id=user.id, access_token_encrypted=google_calendar.encrypt_token("access"), refresh_token_encrypted=None, token_expires_at=None))
        db.commit()
    calls = []
    async def access_token(*args):
        return "access"
    async def event(*args):
        calls.append(True)
        return {"id": "event-1"}
    monkeypatch.setattr("app.services.google_calendar.access_token_for", access_token)
    monkeypatch.setattr("app.services.google_calendar.create_event", event)
    first = api.post("/api/calendar/reminders", json={"movie_id": movie.id})
    second = api.post("/api/calendar/reminders", json={"movie_id": movie.id})
    assert first.status_code == 201 and first.json()["created"] is True
    assert second.status_code == 201 and second.json()["created"] is False
    assert len(calls) == 1
    with Session() as db:
        assert db.query(CalendarReminder).count() == 1
