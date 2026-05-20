"""Seed an admin user.

Usage:
    python -m scripts.seed_admin
"""
from __future__ import annotations

import getpass
import os
import re
import sys

from email_validator import EmailNotValidError, validate_email

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


PASSWORD_PATTERN = re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,72}$"
)


def _prompt(label: str, default: str | None = None, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = (getpass.getpass if secret else input)(f"{label}{suffix}: ").strip()
        if not value and default:
            return default
        if value:
            return value
        print("  (required)")


def main() -> int:
    email = os.getenv("SEED_ADMIN_EMAIL") or _prompt("Admin email")
    name = os.getenv("SEED_ADMIN_NAME") or _prompt("Admin full name", "Admin")
    password = os.getenv("SEED_ADMIN_PASSWORD") or _prompt("Admin password", secret=True)

    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError as e:
        print(f"ERROR: invalid email — {e}", file=sys.stderr)
        return 1

    if not PASSWORD_PATTERN.match(password):
        print(
            "ERROR: password must be 8-72 chars and include uppercase, "
            "lowercase, digit, and special character.",
            file=sys.stderr,
        )
        return 1

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.full_name = name
            existing.hashed_password = hash_password(password)
            existing.role = "admin"
            existing.is_verified = True
            existing.is_active = True
            db.add(existing)
            db.commit()
            print(f"Updated existing admin: {email}")
        else:
            admin = User(
                email=email,
                full_name=name,
                hashed_password=hash_password(password),
                role="admin",
                is_verified=True,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"Created admin: {email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())