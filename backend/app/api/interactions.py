from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.security import AuthenticatedUser, get_current_user
from app.db.database import get_db
from app.db.models import Movie, Rating, UserPreferences, WatchHistory, Watchlist
from app.schemas.interactions import HistoryOut, HistoryPage, PreferencesIn, PreferencesOut, RatingCreate, RatingOut, RatingPage, WatchlistOut, WatchlistPage
from app.utils.pagination import page_payload

ratings_router = APIRouter(prefix="/ratings", tags=["ratings"])
watchlist_router = APIRouter(prefix="/watchlist", tags=["watchlist"])
history_router = APIRouter(prefix="/history", tags=["watch history"])
users_router = APIRouter(prefix="/users", tags=["users"])

def movie_or_404(db, movie_id):
    if not db.get(Movie, movie_id): raise HTTPException(404, "Movie not found")

@ratings_router.post("", response_model=RatingOut, status_code=status.HTTP_201_CREATED)
def create_rating(body: RatingCreate, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    movie_or_404(db, body.movie_id); item = db.scalar(select(Rating).where(Rating.user_id == user.id, Rating.movie_id == body.movie_id))
    if item: item.rating = body.rating
    else: item = Rating(user_id=user.id, movie_id=body.movie_id, rating=body.rating); db.add(item)
    db.commit(); db.refresh(item); return item

@ratings_router.get("", response_model=RatingPage)
def ratings(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    total = db.scalar(select(func.count()).select_from(Rating).where(Rating.user_id == user.id)) or 0
    items = list(db.scalars(select(Rating).where(Rating.user_id == user.id).offset((page-1)*page_size).limit(page_size)))
    return page_payload(items, page, page_size, total)

@ratings_router.put("/{movie_id}", response_model=RatingOut)
def update_rating(movie_id: int, body: RatingCreate, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    if body.movie_id != movie_id: raise HTTPException(400, "Movie ID must match path")
    return create_rating(body, db, user)

@ratings_router.delete("/{movie_id}", status_code=204)
def delete_rating(movie_id: int, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    item = db.scalar(select(Rating).where(Rating.user_id == user.id, Rating.movie_id == movie_id))
    if not item: raise HTTPException(404, "Rating not found")
    db.delete(item); db.commit()

@watchlist_router.get("", response_model=WatchlistPage)
def watchlist(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    total = db.scalar(select(func.count()).select_from(Watchlist).where(Watchlist.user_id == user.id)) or 0
    items = list(db.scalars(select(Watchlist).where(Watchlist.user_id == user.id).offset((page-1)*page_size).limit(page_size)))
    return page_payload(items, page, page_size, total)

@watchlist_router.post("/{movie_id}", response_model=WatchlistOut, status_code=201)
def add_watchlist(movie_id: int, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    movie_or_404(db, movie_id); item = db.scalar(select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.movie_id == movie_id))
    if item: return item
    item = Watchlist(user_id=user.id, movie_id=movie_id); db.add(item); db.commit(); db.refresh(item); return item

@watchlist_router.delete("/{movie_id}", status_code=204)
def remove_watchlist(movie_id: int, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    item = db.scalar(select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.movie_id == movie_id))
    if not item: raise HTTPException(404, "Watchlist item not found")
    db.delete(item); db.commit()

@history_router.get("", response_model=HistoryPage)
def history(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    total = db.scalar(select(func.count()).select_from(WatchHistory).where(WatchHistory.user_id == user.id)) or 0
    items = list(db.scalars(select(WatchHistory).where(WatchHistory.user_id == user.id).order_by(WatchHistory.watched_at.desc()).offset((page-1)*page_size).limit(page_size)))
    return page_payload(items, page, page_size, total)

@history_router.post("/{movie_id}", response_model=HistoryOut, status_code=201)
def mark_watched(movie_id: int, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    movie_or_404(db, movie_id); item = WatchHistory(user_id=user.id, movie_id=movie_id); db.add(item); db.commit(); db.refresh(item); return item

@users_router.get("/preferences", response_model=PreferencesOut)
def preferences(db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    return db.get(UserPreferences, user.id) or PreferencesOut()

@users_router.put("/preferences", response_model=PreferencesOut)
def update_preferences(body: PreferencesIn, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    item = db.get(UserPreferences, user.id)
    if item is None: item = UserPreferences(user_id=user.id); db.add(item)
    item.preferred_genres, item.preferred_languages, item.onboarding_complete = body.preferred_genres, body.preferred_languages, body.onboarding_complete
    db.commit(); db.refresh(item); return item
