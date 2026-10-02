import pytest
from fastapi import HTTPException

from app.api.auth import register_out, token_out
from app.services.auth_service import AuthService


def test_register_out_handles_email_confirmation_without_session():
    response = register_out({"id": "user-id", "email": "user@example.com", "session": None})
    assert response.confirmation_required is True
    assert response.access_token is None
    assert "confirm your email" in (response.message or "")


def test_token_out_rejects_missing_access_token_without_key_error():
    with pytest.raises(HTTPException) as error:
        token_out({"id": "user-id", "session": None})
    assert error.value.status_code == 502


@pytest.mark.asyncio
async def test_auth_service_preserves_rate_limit_status(monkeypatch):
    class FakeResponse:
        status_code = 429

        def json(self):
            return {"error_code": "over_request_rate_limit"}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.services.auth_service.httpx.AsyncClient", lambda **kwargs: FakeClient())
    with pytest.raises(HTTPException) as error:
        await AuthService()._request("signup", {"email": "user@example.com", "password": "password"})
    assert error.value.status_code == 429
