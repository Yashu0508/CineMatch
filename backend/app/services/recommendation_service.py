from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Movie, Rating, UserPreferences, WatchHistory
from app.ml.content_based import tfidf_similarity
from app.ml.hybrid import combine
from app.ml.popularity import score as popularity_score


class RecommendationService:
    def for_user(self, db: Session, user_id, limit: int = 20) -> list[dict]:
        consumed = set(db.scalars(select(Rating.movie_id).where(Rating.user_id == user_id))) | set(db.scalars(select(WatchHistory.movie_id).where(WatchHistory.user_id == user_id)))
        pref = db.get(UserPreferences, user_id)
        movies = list(db.scalars(select(Movie).where(Movie.id.not_in(consumed) if consumed else True).order_by(Movie.popularity.desc().nullslast()).limit(200)))
        results = []
        for movie in movies:
            preference = 1.0 if pref and set(pref.preferred_genres) & {g.id for g in movie.genres} else 0.0
            results.append({"movie": movie, "score": combine(popularity=popularity_score(movie.popularity, movie.vote_average, movie.vote_count) / 100), "reason_type": "preferred_genre" if preference else "popular", "reason_value": None})
        return sorted(results, key=lambda row: row["score"], reverse=True)[:limit]

    def similar(self, db: Session, movie_id: int, limit: int = 20) -> list[dict]:
        source = db.get(Movie, movie_id)
        if not source: return []
        candidates = list(db.scalars(select(Movie).where(Movie.id != movie_id)))
        scores = tfidf_similarity(source.metadata_text or f"{source.title} {source.overview or ''}", [m.metadata_text or f"{m.title} {m.overview or ''}" for m in candidates])
        rows = [{"movie": m, "score": s, "reason_type": "similar_to", "reason_value": source.title} for m, s in zip(candidates, scores)]
        return sorted(rows, key=lambda row: row["score"], reverse=True)[:limit]
