import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import AuthenticatedUser, get_current_user
from app.db.database import get_db
from app.db.models import GoogleCalendarConnection, GoogleOAuthState, Movie
from app.schemas.calendar import CalendarStartOut, ReminderCreate, ReminderOut
from app.services.google_calendar import (
    GoogleCalendarError,
    authorization_url,
    create_reminder,
    exchange_code,
    ensure_token_encryption_ready,
    save_connection,
)


router = APIRouter(prefix="/calendar", tags=["calendar"])
STATE_TTL = timedelta(minutes=10)


def _state_hash(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()


def _future_movie(db: Session, movie_id: int) -> Movie:
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    if movie.release_date is None or movie.release_date <= date.today():
        raise HTTPException(status_code=400, detail="A future release date is required for a reminder")
    return movie


def _frontend_redirect(path: str, status_value: str) -> RedirectResponse:
    settings = get_settings()
    origin = settings.origins[0] if settings.origins else "http://localhost:3000"
    separator = "&" if "?" in path else "?"
    return RedirectResponse(f"{origin}{path}{separator}{urlencode({'calendar': status_value})}", status_code=303)


def _state_is_expired(item: GoogleOAuthState) -> bool:
    expires_at = item.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= datetime.now(timezone.utc)


def _calendar_error(error: GoogleCalendarError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.message)


@router.get("/oauth/start", response_model=CalendarStartOut)
async def start_oauth(
    movie_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    if movie_id is not None:
        _future_movie(db, movie_id)
    connection = db.get(GoogleCalendarConnection, user.id)
    if connection is not None and movie_id is not None:
        try:
            reminder, created = await create_reminder(db, user.id, movie_id)
            return CalendarStartOut(reminder_created=True, message="Reminder added to Google Calendar")
        except GoogleCalendarError as error:
            if error.status_code != 409:
                raise _calendar_error(error) from error
    try:
        ensure_token_encryption_ready()
    except GoogleCalendarError as error:
        raise _calendar_error(error) from error
    state = secrets.token_urlsafe(32)
    db.add(
        GoogleOAuthState(
            state_hash=_state_hash(state),
            user_id=user.id,
            movie_id=movie_id,
            expires_at=datetime.now(timezone.utc) + STATE_TTL,
        )
    )
    db.commit()
    try:
        url = authorization_url(state)
    except GoogleCalendarError as error:
        raise _calendar_error(error) from error
    return CalendarStartOut(authorization_url=url, message="Connect Google Calendar to continue")


@router.get("/oauth/callback")
async def oauth_callback(
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if not state:
        raise HTTPException(status_code=400, detail="OAuth state is required")
    oauth_state = db.get(GoogleOAuthState, _state_hash(state))
    if oauth_state is None or oauth_state.consumed_at is not None or _state_is_expired(oauth_state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    oauth_state.consumed_at = datetime.now(timezone.utc)
    db.commit()
    target = f"/movies/{oauth_state.movie_id}" if oauth_state.movie_id else "/profile"
    if error:
        return _frontend_redirect(target, "denied")
    if not code:
        return _frontend_redirect(target, "error")
    try:
        tokens = await exchange_code(code)
        save_connection(db, oauth_state.user_id, tokens)
        if oauth_state.movie_id is not None:
            await create_reminder(db, oauth_state.user_id, oauth_state.movie_id)
            return _frontend_redirect(target, "reminder_added")
        return _frontend_redirect(target, "connected")
    except GoogleCalendarError:
        return _frontend_redirect(target, "error")


@router.post("/reminders", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
async def add_reminder(
    body: ReminderCreate,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        reminder, created = await create_reminder(db, user.id, body.movie_id)
    except GoogleCalendarError as error:
        raise _calendar_error(error) from error
    return ReminderOut.model_validate({"movie_id": reminder.movie_id, "google_event_id": reminder.google_event_id, "release_date": reminder.release_date, "created_at": reminder.created_at, "created": created})
