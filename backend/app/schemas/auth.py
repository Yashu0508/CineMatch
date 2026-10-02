from pydantic import BaseModel, EmailStr, Field


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class RegisterOut(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    refresh_token: str | None = None
    confirmation_required: bool = False
    message: str | None = None


class MeOut(BaseModel):
    id: str
    email: str | None
