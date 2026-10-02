from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Genre, Movie, MovieGenre


def normalize_movie(payload: dict) -> dict:
    raw_date = payload.get("release_date")
    try: release_date = date.fromisoformat(raw_date) if raw_date else None
    except ValueError: release_date = None
    return {"tmdb_id": payload["id"], "title": payload.get("title") or payload.get("original_title") or "Untitled", "overview": payload.get("overview"), "release_date": release_date, "runtime": payload.get("runtime"), "poster_path": payload.get("poster_path"), "backdrop_path": payload.get("backdrop_path"), "vote_average": payload.get("vote_average"), "vote_count": payload.get("vote_count"), "popularity": payload.get("popularity"), "original_language": payload.get("original_language")}


def upsert_movie(db: Session, payload: dict) -> Movie:
    data = normalize_movie(payload)
    movie = db.scalar(select(Movie).where(Movie.tmdb_id == data["tmdb_id"]))
    if movie is None:
        movie = Movie(**data); db.add(movie); db.flush()
    else:
        for key, value in data.items(): setattr(movie, key, value)
    genre_ids = payload.get("genre_ids") or [genre["id"] for genre in payload.get("genres", [])]
    genre_names = {g["id"]: g.get("name", f"TMDB {g['id']}") for g in payload.get("genres", [])}
    for tmdb_genre_id in genre_ids:
        genre = db.scalar(select(Genre).where(Genre.tmdb_id == tmdb_genre_id))
        if genre is None:
            genre = Genre(tmdb_id=tmdb_genre_id, name=genre_names.get(tmdb_genre_id, f"TMDB {tmdb_genre_id}")); db.add(genre); db.flush()
        if db.get(MovieGenre, {"movie_id": movie.id, "genre_id": genre.id}) is None:
            db.add(MovieGenre(movie_id=movie.id, genre_id=genre.id))
    return movie


def local_movies(db: Session, page: int, page_size: int, query: str | None = None) -> tuple[list[Movie], int]:
    statement = select(Movie)
    if query: statement = statement.where(Movie.title.ilike(f"%{query}%"))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    return list(db.scalars(statement.order_by(Movie.popularity.desc().nullslast()).offset((page - 1) * page_size).limit(page_size))), total


def discovery_movies(db: Session, category: str, page: int, page_size: int = 20) -> tuple[list[Movie], int]:
    statement = select(Movie)
    if category == "top-rated":
        statement = statement.order_by(Movie.vote_average.desc().nullslast(), Movie.vote_count.desc().nullslast())
    elif category == "upcoming":
        statement = statement.where(Movie.release_date > date.today()).order_by(Movie.release_date.asc())
    else:
        statement = statement.order_by(Movie.popularity.desc().nullslast())
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    return list(db.scalars(statement.offset((page - 1) * page_size).limit(page_size))), total
