from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserPublic(BaseModel):
    """Shape returned to the frontend in login/profile responses.

    Field names match what the frontend reads (snake_case).
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    phone_number: Optional[str] = None
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    school: Optional[str] = None
    class_grade: Optional[str] = None
    date_of_birth: Optional[date] = None
    state: Optional[str] = None
    city: Optional[str] = None
    avatar_url: Optional[str] = None
    parent_name: Optional[str] = None
    parent_occupation: Optional[str] = None
    parent_education: Optional[str] = None
    parent_relation: Optional[str] = None
    is_verified: bool
    is_active: bool
    created_at: datetime


class ProfileUpdate(BaseModel):
    """All-optional payload for PUT /profile/profile. Frontend sends partial
    updates (e.g. just `avatar_url`), so every field is optional."""
    first_name: Optional[str] = Field(default=None, max_length=128)
    last_name: Optional[str] = Field(default=None, max_length=128)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(default=None, max_length=20)
    school: Optional[str] = Field(default=None, max_length=255)
    class_grade: Optional[str] = Field(default=None, max_length=16)
    date_of_birth: Optional[date] = None
    state: Optional[str] = Field(default=None, max_length=128)
    city: Optional[str] = Field(default=None, max_length=128)
    avatar_url: Optional[str] = Field(default=None, max_length=512)
    parent_name: Optional[str] = Field(default=None, max_length=255)
    parent_occupation: Optional[str] = Field(default=None, max_length=255)
    parent_education: Optional[str] = Field(default=None, max_length=255)
    parent_relation: Optional[str] = Field(default=None, max_length=64)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)
