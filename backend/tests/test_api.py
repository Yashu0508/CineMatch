from datetime import date, timedelta

from app.db.models import Movie, User

def seed(session, user):
    session.add(User(id=user.id, email=user.email)); session.add(Movie(tmdb_id=42, title="Interstellar", overview="Space isolation", popularity=90, vote_average=8.7, vote_count=100)); session.commit()

def test_health(client):
    api, _, _ = client
    assert api.get("/api/health").json() == {"status": "ok"}

def test_movie_detail_and_missing_movie(client):
    api, Session, user = client
    with Session() as db: seed(db, user)
    assert api.get("/api/movies/1").status_code == 200
    assert api.get("/api/movies/999").status_code == 404

def test_rating_watchlist_history_are_user_scoped(client):
    api, Session, user = client
    with Session() as db: seed(db, user)
    assert api.post("/api/ratings", json={"movie_id": 1, "rating": 4.5}).status_code == 201
    assert api.post("/api/watchlist/1").status_code == 201
    assert api.post("/api/history/1").status_code == 201
    assert api.get("/api/ratings").json()["total"] == 1
    assert api.get("/api/watchlist").json()["total"] == 1
    assert api.get("/api/history").json()["total"] == 1

def test_invalid_rating_validation(client):
    api, Session, user = client
    with Session() as db: seed(db, user)
    assert api.post("/api/ratings", json={"movie_id": 1, "rating": 6}).status_code == 422


def test_upcoming_only_returns_future_dated_movies(client):
    api, Session, user = client
    with Session() as db:
        db.add(User(id=user.id, email=user.email))
        db.add_all(
            [
                Movie(tmdb_id=101, title="Future Release", release_date=date.today() + timedelta(days=7)),
                Movie(tmdb_id=102, title="Today Release", release_date=date.today()),
                Movie(tmdb_id=103, title="Past Release", release_date=date.today() - timedelta(days=7)),
                Movie(tmdb_id=104, title="Unknown Release", release_date=None),
            ]
        )
        db.commit()

    response = api.get("/api/movies/upcoming")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items", "page", "total", "total_pages"}
    assert payload["total"] == 1
    assert [item["title"] for item in payload["items"]] == ["Future Release"]


def test_popular_and_trending_use_distinct_rankings(client):
    api, Session, user = client
    with Session() as db:
        db.add(User(id=user.id, email=user.email))
        db.add_all(
            [
                Movie(tmdb_id=201, title="Popular Older", popularity=100, release_date=date.today() - timedelta(days=500)),
                Movie(tmdb_id=202, title="Recent Trending", popularity=90, release_date=date.today() - timedelta(days=7)),
                Movie(tmdb_id=204, title="Future Release", popularity=80, release_date=date.today() + timedelta(days=7)),
                Movie(tmdb_id=203, title="No Metadata", popularity=None, release_date=None),
            ]
        )
        db.commit()

    popular = api.get("/api/movies/popular").json()
    trending = api.get("/api/movies/trending").json()

    assert [item["title"] for item in popular["items"][:2]] == ["Popular Older", "Recent Trending"]
    assert [item["title"] for item in trending["items"][:2]] == ["Recent Trending", "Popular Older"]
    assert [item["title"] for item in trending["items"]][2] == "Future Release"
    assert trending["items"][-1]["title"] == "No Metadata"
