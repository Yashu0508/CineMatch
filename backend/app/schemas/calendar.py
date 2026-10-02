from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class CalendarStartOut(BaseModel):
    authorization_url: str | None = None
    reminder_created: bool = False
    message: str


class ReminderCreate(BaseModel):
    movie_id: int


class ReminderOut(ORMModel):
    movie_id: int
    google_event_id: str
    release_date: date
    created_at: datetime
    created: bool = True
