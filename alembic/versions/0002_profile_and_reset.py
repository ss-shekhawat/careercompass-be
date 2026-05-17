"""add_profile_fields_and_password_reset

Revision ID: 0002_profile_and_reset
Revises: 0001_users
Create Date: 2026-05-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_profile_and_reset"
down_revision: Union[str, None] = "0001_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend users with profile fields
    op.add_column("users", sa.Column("first_name", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("class_grade", sa.String(length=16), nullable=True))
    op.add_column("users", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("state", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("city", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("parent_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("parent_occupation", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("parent_education", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("parent_relation", sa.String(length=64), nullable=True))

    # password_reset_tokens
    op.create_table(
        "password_reset_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "used",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_password_reset_tokens_token",
        "password_reset_tokens",
        ["token"],
        unique=True,
    )
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_token", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_column("users", "parent_relation")
    op.drop_column("users", "parent_education")
    op.drop_column("users", "parent_occupation")
    op.drop_column("users", "parent_name")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "city")
    op.drop_column("users", "state")
    op.drop_column("users", "date_of_birth")
    op.drop_column("users", "class_grade")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
