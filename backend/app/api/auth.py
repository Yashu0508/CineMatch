from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.auth import Credentials, MeOut, RegisterOut, TokenOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

def token_out(payload: dict) -> TokenOut:
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Authentication provider returned an invalid token response")
    return TokenOut(access_token=access_token, refresh_token=payload.get("refresh_token"))


def register_out(payload: dict) -> RegisterOut:
    access_token = payload.get("access_token")
    if isinstance(access_token, str) and access_token:
        return RegisterOut(access_token=access_token, refresh_token=payload.get("refresh_token"))
    # Supabase returns a user object without a session when email confirmation is enabled.
    if payload.get("id") or isinstance(payload.get("user"), dict):
        return RegisterOut(
            confirmation_required=True,
            message="Account created. Please confirm your email before signing in.",
        )
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Authentication provider returned an invalid signup response")


@router.post("/register", response_model=RegisterOut, status_code=201)
async def register(body: Credentials): return register_out(await AuthService().register(body.email, body.password))
@router.post("/login", response_model=TokenOut)
async def login(body: Credentials): return token_out(await AuthService().login(body.email, body.password))
@router.get("/me", response_model=MeOut)
def me(user: AuthenticatedUser = Depends(get_current_user)): return MeOut(id=str(user.id), email=user.email)
