from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.movie import MovieOut, MoviePage
from app.services.movie_service import local_movies, upsert_movie
from app.services.tmdb import TMDBService
from app.utils.pagination import page_payload

router = APIRouter(prefix="/movies", tags=["movies"])


async def _listing(category: str, page: int, db: Session) -> dict:
    service = TMDBService()
    try:
        payload = await service.listing(category, page)
    finally:
        await service.aclose()
    movies = [upsert_movie(db, movie) for movie in payload.get("results", [])]
    db.commit()
    return page_payload(movies, page, 20, payload.get("total_results", len(movies)))


@router.get("/trending", response_model=MoviePage)
async def trending(page: int = Query(1, ge=1), db: Session = Depends(get_db)): return await _listing("trending", page, db)
@router.get("/popular", response_model=MoviePage)
async def popular(page: int = Query(1, ge=1), db: Session = Depends(get_db)): return await _listing("popular", page, db)
@router.get("/top-rated", response_model=MoviePage)
async def top_rated(page: int = Query(1, ge=1), db: Session = Depends(get_db)): return await _listing("top-rated", page, db)
@router.get("/upcoming", response_model=MoviePage)
async def upcoming(page: int = Query(1, ge=1), db: Session = Depends(get_db)): return await _listing("upcoming", page, db)

@router.get("/search", response_model=MoviePage)
async def search(q: str = Query(min_length=1, max_length=200), page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    local, total = local_movies(db, page, 20, q)
    if local: return page_payload(local, page, 20, total)
    service = TMDBService()
    try: payload = await service.search(q, page)
    finally: await service.aclose()
    movies = [upsert_movie(db, movie) for movie in payload.get("results", [])]; db.commit()
    return page_payload(movies, page, 20, payload.get("total_results", len(movies)))

@router.get("/{movie_id}", response_model=MovieOut)
async def detail(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(__import__("app.db.models", fromlist=["Movie"]).Movie, movie_id)
    if movie: return movie
    from fastapi import HTTPException
    raise HTTPException(404, "Movie not found")

@router.get("/{movie_id}/similar", response_model=MoviePage)
async def similar(movie_id: int, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    movie = db.get(__import__("app.db.models", fromlist=["Movie"]).Movie, movie_id)
    from fastapi import HTTPException
    if not movie: raise HTTPException(404, "Movie not found")
    service = TMDBService()
    try: payload = await service.similar(movie.tmdb_id, page)
    finally: await service.aclose()
    movies = [upsert_movie(db, m) for m in payload.get("results", [])]; db.commit()
    return page_payload(movies, page, 20, payload.get("total_results", len(movies)))

@router.get("/{movie_id}/recommendations", response_model=MoviePage)
async def movie_recommendations(movie_id: int, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    return await similar(movie_id, page, db)
