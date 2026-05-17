from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import PasswordChange, ProfileUpdate, UserPublic


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/profile", response_model=UserPublic)
def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.put("/profile", response_model=UserPublic)
def update_profile(
    payload: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserPublic:
    """Partial update. Only fields explicitly provided in the request body
    are written — anything left out (or sent as `null` only when None is a
    valid clear) preserves the existing value.

    Frontend can also send `first_name`/`last_name`; if so we recompute
    `full_name` to keep both in sync.
    """
    data = payload.model_dump(exclude_unset=True)

    # Email change — must remain unique.
    if "email" in data and data["email"]:
        new_email = data["email"].lower()
        if new_email != current_user.email:
            clash = (
                db.query(User)
                .filter(User.email == new_email, User.id != current_user.id)
                .first()
            )
            if clash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email is already in use.",
                )
            current_user.email = new_email
        data.pop("email")

    # Apply remaining fields verbatim.
    for field, value in data.items():
        setattr(current_user, field, value)

    # Keep full_name in sync if first/last were touched.
    if "first_name" in data or "last_name" in data:
        first = (current_user.first_name or "").strip()
        last = (current_user.last_name or "").strip()
        composed = f"{first} {last}".strip()
        if composed:
            current_user.full_name = composed

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserPublic.model_validate(current_user)


@router.put("/profile/password", response_model=MessageResponse)
def change_password(
    payload: PasswordChange,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()
    return MessageResponse(message="Password updated successfully.")
