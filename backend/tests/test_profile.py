from app.core.security import get_current_user
from app.db.models import User
from app.main import app
from fastapi import HTTPException


def seed_user(session, user):
    session.add(User(id=user.id, email=user.email))
    session.commit()


def test_profile_requires_authentication(client):
    api, Session, user = client
    with Session() as db:
        seed_user(db, user)
    def reject_auth():
        raise HTTPException(status_code=401, detail="Authentication required")
    original = app.dependency_overrides[get_current_user]
    app.dependency_overrides[get_current_user] = reject_auth
    try:
        response = api.get("/api/users/profile")
        assert response.status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = original


def test_preset_avatar_is_persisted_and_scoped_to_current_user(client):
    api, Session, user = client
    with Session() as db:
        seed_user(db, user)
        other = User(email="other@example.com")
        db.add(other)
        db.commit()
        other_id = other.id

    response = api.put("/api/users/avatar/preset", json={"avatar_id": "ocean"})
    assert response.status_code == 200
    assert response.json()["avatar_type"] == "preset"
    assert response.json()["avatar_id"] == "ocean"

    with Session() as db:
        assert db.get(User, user.id).avatar_ref == "ocean"
        assert db.get(User, other_id).avatar_ref is None


def test_invalid_avatar_type_is_rejected(client):
    api, Session, user = client
    with Session() as db:
        seed_user(db, user)
    response = api.put("/api/users/avatar/preset", json={"avatar_id": "not-a-cinematch-avatar"})
    assert response.status_code == 400


def test_upload_validates_type_and_size(client):
    api, Session, user = client
    with Session() as db:
        seed_user(db, user)
    invalid = api.post("/api/users/avatar/upload", files={"file": ("avatar.gif", b"gif", "image/gif")})
    assert invalid.status_code == 415
    oversized = api.post("/api/users/avatar/upload", files={"file": ("avatar.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")})
    assert oversized.status_code == 413


def test_upload_persists_reference_without_exposing_storage_credentials(client, monkeypatch):
    api, Session, user = client
    with Session() as db:
        seed_user(db, user)

    async def upload(*args, **kwargs):
        return None

    async def signed(path):
        return "https://signed.example/avatar.png"

    monkeypatch.setattr("app.api.profile.upload_avatar", upload)
    monkeypatch.setattr("app.api.profile.signed_avatar_url", signed)
    response = api.post("/api/users/avatar/upload", files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\nvalid", "image/png")})
    assert response.status_code == 200
    assert response.json()["avatar_type"] == "upload"
    assert response.json()["avatar_url"] == "https://signed.example/avatar.png"
    with Session() as db:
        profile = db.get(User, user.id)
        assert profile.avatar_upload_ref == profile.avatar_ref
        assert profile.avatar_ref.startswith(str(user.id))
