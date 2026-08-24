"""Create an isolated PostgreSQL schema for non-destructive verification."""

from __future__ import annotations

import argparse
import os
import re

import psycopg2
from psycopg2 import sql


SAFE_SCHEMA = re.compile(r"^(?:alembic|postgres)_verification_[a-z0-9_]+$")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("schema")
    args = parser.parse_args()
    if not SAFE_SCHEMA.fullmatch(args.schema):
        raise ValueError(
            "Verification schema must start with alembic_verification_ or "
            "postgres_verification_ and contain lowercase letters, digits, or underscores"
        )

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    connection = psycopg2.connect(database_url)
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(args.schema)
                )
            )
    finally:
        connection.close()

    print(f"VERIFICATION_SCHEMA_READY={args.schema}")


if __name__ == "__main__":
    main()
