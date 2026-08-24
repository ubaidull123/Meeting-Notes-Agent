"""Set a user's role from the command line.

Usage:
    python scripts/set_user_role.py user@example.com ADMIN
    python scripts/set_user_role.py user@example.com USER
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from meeting_notes_agent.database.models import User, UserRole  # noqa: E402
from meeting_notes_agent.database.session import SessionLocal, engine, init_db  # noqa: E402


ROLE_CONSTRAINT_SQL = """
DO $$
DECLARE
    constraint_name text;
BEGIN
    SELECT conname
    INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'users'::regclass
      AND contype = 'c'
      AND pg_get_constraintdef(oid) ILIKE '%role%'
    LIMIT 1;

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE users DROP CONSTRAINT %I', constraint_name);
    END IF;

    ALTER TABLE users
        ALTER COLUMN role SET DEFAULT 'USER';

    ALTER TABLE users
        ADD CONSTRAINT users_role_check CHECK (role IN ('ADMIN', 'USER'));
END $$;
"""


def normalize_legacy_roles() -> None:
    """Convert old lowercase role values/constraints to the API enum values."""
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text(ROLE_CONSTRAINT_SQL))
        connection.execute(text("UPDATE users SET role = 'USER' WHERE role = 'user'"))
        connection.execute(text("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'"))


def set_user_role(email: str, role: UserRole) -> User:
    init_db()
    normalize_legacy_roles()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower()).first()
        if user is None:
            raise SystemExit(f"User not found: {email}")

        user.role = role
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as exc:
        db.rollback()
        raise SystemExit(f"Could not update role because the database rejected the value: {exc}") from exc
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Change a Meeting Notes user role.")
    parser.add_argument("email", help="User email address")
    parser.add_argument(
        "role",
        choices=[role.value for role in UserRole],
        type=str.upper,
        help="Target role: ADMIN or USER",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    user = set_user_role(args.email, UserRole(args.role))
    print(f"Updated {user.email} to {user.role.value}")


if __name__ == "__main__":
    main()
