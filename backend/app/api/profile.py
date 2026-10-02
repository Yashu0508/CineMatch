from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import AuthenticatedUser, get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.profile import PresetAvatarIn, ProfileOut
from app.services.profile_avatar import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_PRESET_AVATARS,
    MAX_AVATAR_BYTES,
    AvatarStorageError,
    avatar_path,
    has_valid_image_signature,
    signed_avatar_url,
    upload_avatar,
)


router = APIRouter(prefix="/users", tags=["profile"])


async def profile_out(user: User) -> ProfileOut:
    avatar_url = None
    if user.avatar_type == "upload" and user.avatar_ref:
        try:
            avatar_url = await signed_avatar_url(user.avatar_ref)
        except AvatarStorageError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
    return ProfileOut(id=str(user.id), email=user.email, avatar_type=user.avatar_type, avatar_id=user.avatar_ref if user.avatar_type == "preset" else None, avatar_url=avatar_url, has_uploaded_avatar=bool(user.avatar_upload_ref))


def _user(db: Session, auth_user: AuthenticatedUser) -> User:
    user = db.get(User, auth_user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return user


@router.get("/profile", response_model=ProfileOut)
async def get_profile(db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    return await profile_out(_user(db, user))


@router.post("/avatar/upload", response_model=ProfileOut)
async def upload_profile_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    extension = ALLOWED_CONTENT_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP images are supported")
    content = await file.read(MAX_AVATAR_BYTES + 1)
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="Profile image must be 5 MB or smaller")
    if not has_valid_image_signature(file.content_type or "", content):
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid JPEG, PNG, or WebP image")
    path = avatar_path(str(user.id), extension)
    try:
        await upload_avatar(path, content, file.content_type or "application/octet-stream")
    except AvatarStorageError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    profile = _user(db, user)
    profile.avatar_type, profile.avatar_ref, profile.avatar_upload_ref = "upload", path, path
    db.commit()
    db.refresh(profile)
    return await profile_out(profile)


@router.put("/avatar/preset", response_model=ProfileOut)
async def select_preset_avatar(body: PresetAvatarIn, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    if body.avatar_id not in ALLOWED_PRESET_AVATARS:
        raise HTTPException(status_code=400, detail="Unknown CineMatch avatar")
    profile = _user(db, user)
    profile.avatar_type, profile.avatar_ref = "preset", body.avatar_id
    db.commit()
    db.refresh(profile)
    return await profile_out(profile)


@router.put("/avatar/upload/activate", response_model=ProfileOut)
async def activate_uploaded_avatar(db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    profile = _user(db, user)
    if not profile.avatar_upload_ref:
        raise HTTPException(status_code=404, detail="No uploaded profile image is available")
    profile.avatar_type, profile.avatar_ref = "upload", profile.avatar_upload_ref
    db.commit()
    db.refresh(profile)
    return await profile_out(profile)
