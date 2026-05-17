from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_reset_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    OtpResendRequest,
    OtpVerifyRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserPublic


router = APIRouter(prefix="/auth", tags=["auth"])


# v1 stub: with no SMS/email provider, this OTP always succeeds.
# Frontend already hard-codes a similar test flow.
DEV_OTP = "123456"


def _build_token_response(user: User) -> TokenResponse:
    access_token = create_access_token(subject=str(user.id), role=user.role)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user=UserPublic.model_validate(user),
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RegisterResponse:
    # Reject duplicates
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email.lower(),
        phone_number=payload.phone_number,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=payload.role or "student",
        school=payload.school,
        # v1: no real SMS/email — auto-verify so users can log in immediately.
        # The OTP endpoint still works as a no-op for the existing frontend flow.
        is_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        message="Account created successfully.",
        user=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """OAuth2 password flow — accepts form-encoded `username` and `password`.
    The frontend sends `username` = email."""
    identifier = form_data.username.strip().lower()
    user = db.query(User).filter(User.email == identifier).first()

    # Generic error message — don't leak whether the email exists.
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    return _build_token_response(user)


@router.post("/logout", response_model=MessageResponse)
def logout(_: Annotated[User, Depends(get_current_user)]) -> MessageResponse:
    """Stateless JWT — no server-side invalidation. Frontend drops the token."""
    return MessageResponse(message="Logged out.")


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(
    payload: OtpVerifyRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """v1 stub: accepts the dev OTP and returns a fresh token + user object.

    The frontend calls this right after signup. We look up the user by email
    (or phone if email wasn't given) and return a login-style payload.
    """
    if payload.otp.strip() != DEV_OTP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. (Dev OTP is {DEV_OTP}.)",
        )

    user: User | None = None
    if payload.email:
        user = db.query(User).filter(User.email == payload.email.lower()).first()
    elif payload.phone:
        user = db.query(User).filter(User.phone_number == payload.phone).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching account found.",
        )

    user.is_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)

    return _build_token_response(user)


@router.post("/resend-otp", response_model=MessageResponse)
def resend_otp(payload: OtpResendRequest) -> MessageResponse:
    """v1 stub. Without an SMS provider this is a no-op — we just remind the
    caller of the dev OTP. Don't surface whether the account exists."""
    if not payload.email and not payload.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email or phone is required.",
        )
    return MessageResponse(message=f"OTP sent. (Dev OTP is {DEV_OTP}.)")


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ForgotPasswordResponse:
    """Generate a reset token. In v1 we return it in the response (only in
    non-prod) since there's no email provider wired up. Even when the email
    doesn't exist, we return the same generic success message to avoid
    leaking account existence."""
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user:
        return ForgotPasswordResponse(
            message="If an account with that email exists, a reset link has been sent."
        )

    token = generate_reset_token()
    reset = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset)
    db.commit()

    response = ForgotPasswordResponse(
        message="If an account with that email exists, a reset link has been sent.",
    )
    # Dev-only convenience: surface the token so it can be tested without email.
    if settings.ENV != "prod":
        response.reset_token = token
    return response


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    reset = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == payload.token)
        .first()
    )
    if not reset or reset.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already-used reset token.",
        )
    # Compare in UTC. expires_at is stored timezone-aware.
    if reset.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired.",
        )

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account no longer exists.",
        )

    user.hashed_password = hash_password(payload.password)
    reset.used = True
    db.add(user)
    db.add(reset)
    db.commit()

    return MessageResponse(message="Password reset successful. Please log in.")
