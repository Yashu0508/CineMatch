from app.db.models import Movie, User
from app.services.recommendation_service import RecommendationService

def test_similar_movies_uses_tfidf(client):
    _, Session, user = client
    with Session() as db:
        db.add(User(id=user.id, email=user.email))
        db.add_all([Movie(tmdb_id=1, title="Space", overview="space exploration", metadata_text="space exploration science fiction"), Movie(tmdb_id=2, title="Mars", overview="space mission", metadata_text="space mission science fiction"), Movie(tmdb_id=3, title="Comedy", overview="funny", metadata_text="funny comedy")]); db.commit()
        result = RecommendationService().similar(db, 1)
        assert result[0]["movie"].id == 2


def test_for_you_serializes_recommendation_metadata(client):
    api, Session, user = client
    with Session() as db:
        db.add(User(id=user.id, email=user.email))
        db.add(Movie(tmdb_id=11, title="Recommended", popularity=10, vote_average=8, vote_count=100))
        db.commit()

    response = api.get("/api/recommendations/for-you?limit=20")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Recommended"
    assert isinstance(payload[0]["score"], (int, float))
    assert payload[0]["reason_type"] == "popular"
