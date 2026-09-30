from datetime import date
from app.schemas.common import ORMModel, Page


class GenreOut(ORMModel):
    id: int
    tmdb_id: int
    name: str


class MovieOut(ORMModel):
    id: int
    tmdb_id: int
    title: str
    overview: str | None = None
    release_date: date | None = None
    runtime: int | None = None
    poster_path: str | None = None
    backdrop_path: str | None = None
    vote_average: float | None = None
    vote_count: int | None = None
    popularity: float | None = None
    original_language: str | None = None
    genres: list[GenreOut] = []


class MoviePage(Page):
    items: list[MovieOut]
