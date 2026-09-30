from app.schemas.movie import MovieOut


class RecommendationOut(MovieOut):
    score: float
    reason_type: str
    reason_value: str | None = None

