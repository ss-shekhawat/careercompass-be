from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Date, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Identity
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(20), index=True, nullable=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Name — full_name is primary, split fields are for profile editing
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Role: 'student' | 'admin' | 'counsellor' | 'super_admin'
    role: Mapped[str] = mapped_column(
        String(32), default="student", nullable=False, index=True
    )

    # Student profile fields (all optional)
    school: Mapped[str | None] = mapped_column(String(255), nullable=True)
    class_grade: Mapped[str | None] = mapped_column(String(16), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Parent info
    parent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_education: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_relation: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Status flags
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"