from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Movie
from app.schemas.movie import MovieOut, MoviePage
from app.services.movie_service import discovery_movies, local_movies
from app.services.omdb import OMDbService
from app.services.recommendation_service import RecommendationService
from app.utils.pagination import page_payload

router = APIRouter(prefix="/movies", tags=["movies"])


def _local_title_matches(db: Session, titles: list[str], page: int, page_size: int = 20) -> dict:
    normalized = {title.casefold().strip() for title in titles}
    if not normalized:
        return page_payload([], page, page_size, 0)
    rows = list(db.scalars(select(Movie).where(func.lower(Movie.title).in_(normalized)).order_by(Movie.popularity.desc().nullslast())))
    start = (page - 1) * page_size
    return page_payload(rows[start:start + page_size], page, page_size, len(rows))


async def _discovery(category: str, page: int, db: Session) -> dict:
    items, total = discovery_movies(db, category, page)
    return page_payload(items, page, 20, total)


@router.get("/trending", response_model=MoviePage)
async def trending(page: int = Query(1, ge=1), db: Session = Depends(get_db)): return await _discovery("trending", page, db)


@router.get("/popular", response_model=MoviePage)
async def popular(page: int = Query(1, ge=1), db: Session = Depends(get_db)): return await _discovery("popular", page, db)


@router.get("/top-rated", response_model=MoviePage)
async def top_rated(page: int = Query(1, ge=1), db: Session = Depends(get_db)): return await _discovery("top-rated", page, db)


@router.get("/upcoming", response_model=MoviePage)
async def upcoming(page: int = Query(1, ge=1), db: Session = Depends(get_db)): return await _discovery("upcoming", page, db)


@router.get("/search", response_model=MoviePage)
async def search(q: str = Query(min_length=1, max_length=200), page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    service = OMDbService()
    try:
        payload = await service.search(q, page)
    except HTTPException:
        payload = {}
    finally:
        await service.aclose()
    titles = [item.get("Title", "") for item in payload.get("Search", []) if item.get("Type", "movie") == "movie"]
    result = _local_title_matches(db, titles, page)
    if result["total"]:
        return result
    local, total = local_movies(db, page, 20, q)
    return page_payload(local, page, 20, total)


@router.get("/{movie_id}", response_model=MovieOut)
async def detail(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    service = OMDbService()
    try:
        payload = await service.details(movie.title)
    except HTTPException:
        payload = {}
    finally:
        await service.aclose()
    if payload.get("Response") != "True":
        return movie
    # Keep the existing response shape and internal identifiers while using
    # OMDb for title metadata. Poster paths remain local-compatible because the
    # frontend image contract expects the existing stored path format.
    data = {column.name: getattr(movie, column.name) for column in Movie.__table__.columns}
    if payload.get("Plot") not in (None, "N/A"):
        data["overview"] = payload["Plot"]
    if payload.get("Year", "").isdigit():
        data["release_date"] = date(int(payload["Year"]), 1, 1)
    runtime = payload.get("Runtime", "")
    if runtime.endswith(" min") and runtime[:-4].isdigit():
        data["runtime"] = int(runtime[:-4])
    return data


def _recommendation_page(movie_id: int, page: int, db: Session) -> dict:
    if not db.get(Movie, movie_id):
        raise HTTPException(404, "Movie not found")
    rows = RecommendationService().similar(db, movie_id, 20)
    movies = [row["movie"] for row in rows]
    start = (page - 1) * 20
    return page_payload(movies[start:start + 20], page, 20, len(movies))


@router.get("/{movie_id}/similar", response_model=MoviePage)
async def similar(movie_id: int, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    return _recommendation_page(movie_id, page, db)


@router.get("/{movie_id}/recommendations", response_model=MoviePage)
async def movie_recommendations(movie_id: int, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    return _recommendation_page(movie_id, page, db)
