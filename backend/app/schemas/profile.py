from pydantic import BaseModel, Field


class ProfileOut(BaseModel):
    id: str
    email: str | None = None
    avatar_type: str | None = None
    avatar_id: str | None = None
    avatar_url: str | None = None
    has_uploaded_avatar: bool = False


class PresetAvatarIn(BaseModel):
    avatar_id: str = Field(min_length=1, max_length=64)
