from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.security import AuthenticatedUser, get_current_user
from app.db.database import get_db
from app.schemas.movie import MovieOut
from app.schemas.recommendation import RecommendationOut
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

def serialize(row):
    movie = MovieOut.model_validate(row["movie"]).model_dump()
    return {**movie, "score": row["score"], "reason_type": row["reason_type"], "reason_value": row["reason_value"]}

@router.get("/for-you", response_model=list[RecommendationOut])
def for_you(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    return [serialize(row) for row in RecommendationService().for_user(db, user.id, limit)]

@router.get("/similar/{movie_id}", response_model=list[RecommendationOut])
def similar(movie_id: int, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    rows = RecommendationService().similar(db, movie_id, limit)
    if not rows: raise HTTPException(404, "Movie not found")
    return [serialize(row) for row in rows]

@router.get("/because-you-liked/{movie_id}", response_model=list[RecommendationOut])
def because_liked(movie_id: int, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    return similar(movie_id, limit, db)
