import logging
from dataclasses import dataclass
from uuid import UUID
import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import User

logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    email: str | None = None


def _decode_supabase_token(token: str) -> dict:
    settings = get_settings()
    if not settings.supabase_url:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication is not configured")
    try:
        jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
        return jwt.decode(token, signing_key.key, algorithms=[signing_key.algorithm_name], audience="authenticated")
    except jwt.PyJWTError as exc:
        logger.info("Rejected invalid authentication token: %s", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> AuthenticatedUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    claims = _decode_supabase_token(credentials.credentials)
    try:
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc
    email = claims.get("email")
    profile = db.get(User, user_id)
    if profile is None:
        profile = User(id=user_id, email=email or "")
        db.add(profile)
        db.commit()
    return AuthenticatedUser(id=user_id, email=email)
