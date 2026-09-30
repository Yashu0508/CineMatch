from fastapi import APIRouter, Depends
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.auth import Credentials, MeOut, TokenOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

def token_out(payload: dict) -> TokenOut: return TokenOut(access_token=payload["access_token"], refresh_token=payload.get("refresh_token"))
@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: Credentials): return token_out(await AuthService().register(body.email, body.password))
@router.post("/login", response_model=TokenOut)
async def login(body: Credentials): return token_out(await AuthService().login(body.email, body.password))
@router.get("/me", response_model=MeOut)
def me(user: AuthenticatedUser = Depends(get_current_user)): return MeOut(id=str(user.id), email=user.email)
