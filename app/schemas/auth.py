import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserPublic


# Frontend password rules (SignUpPage.jsx):
# min 8, at least one uppercase, lowercase, digit, special character.
# Mirroring server-side so error messages stay consistent.
_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,72}$"
)


def _validate_password_strength(v: str) -> str:
    if not _PASSWORD_PATTERN.match(v):
        raise ValueError(
            "Password must be 8-72 chars and include uppercase, lowercase, "
            "number, and special character."
        )
    return v


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str
    phone_number: str = Field(min_length=10, max_length=20)
    role: Optional[str] = None       # frontend may send "student" when org code is given
    school: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("phone_number")
    @classmethod
    def phone_digits(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) < 10:
            raise ValueError("Phone number must contain at least 10 digits.")
        return digits

    @field_validator("role")
    @classmethod
    def role_must_be_safe(cls, v: Optional[str]) -> Optional[str]:
        # Never accept self-assigned admin/super_admin via public register.
        if v is None:
            return None
        if v not in {"student", "counsellor"}:
            return "student"
        return v


class RegisterResponse(BaseModel):
    message: str
    user: UserPublic


class TokenResponse(BaseModel):
    """Shape consumed by frontend: { access_token, token_type, role, user }."""
    access_token: str
    token_type: str = "bearer"
    role: str
    user: UserPublic


class MessageResponse(BaseModel):
    message: str


class OtpVerifyRequest(BaseModel):
    otp: str = Field(min_length=4, max_length=8)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class OtpResendRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    # Only populated in non-prod environments since we have no email provider yet.
    reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=128)
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)
