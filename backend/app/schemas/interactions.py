from datetime import datetime
from pydantic import Field
from app.schemas.common import ORMModel, Page
from app.schemas.movie import MovieOut


class RatingCreate(ORMModel):
    movie_id: int = Field(gt=0)
    rating: float = Field(ge=0.5, le=5.0)


class RatingOut(ORMModel):
    movie_id: int
    rating: float
    movie: MovieOut


class RatingPage(Page):
    items: list[RatingOut]


class WatchlistOut(ORMModel):
    movie_id: int
    created_at: datetime
    movie: MovieOut


class WatchlistPage(Page):
    items: list[WatchlistOut]


class HistoryOut(ORMModel):
    movie_id: int
    watched_at: datetime
    movie: MovieOut


class HistoryPage(Page):
    items: list[HistoryOut]


class PreferencesIn(ORMModel):
    preferred_genres: list[int] = []
    preferred_languages: list[str] = []
    onboarding_complete: bool = False


class PreferencesOut(PreferencesIn):
    pass
