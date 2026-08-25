"""Compare Alembic-managed tables across two PostgreSQL schemas."""

from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any

from sqlalchemy import create_engine, inspect

from meeting_notes_agent.database.models import Base
from meeting_notes_agent.database import models_ai_config  # noqa: F401


def normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return "postgresql://" + value.removeprefix("postgres://")
    return value


def type_signature(type_: object) -> dict[str, Any]:
    return {
        "class": type(type_).__name__,
        "display": str(type_),
        "enum_values": list(getattr(type_, "enums", []) or []),
    }


def default_signature(value: object) -> object:
    """Ignore only schema qualification on equivalent owned sequences."""
    if not isinstance(value, str):
        return value
    return re.sub(
        r"nextval\('(?:[^']+\.)?([^'.]+)'::regclass\)",
        r"nextval('\1'::regclass)",
        value,
    )


def schema_signature(inspector, schema: str) -> dict[str, Any]:
    managed_tables = sorted(Base.metadata.tables)
    existing_tables = set(inspector.get_table_names(schema=schema))
    missing_tables = sorted(set(managed_tables) - existing_tables)
    if missing_tables:
        raise RuntimeError(
            f"Schema {schema!r} is missing managed tables: {missing_tables}"
        )

    signature: dict[str, Any] = {}
    for table in managed_tables:
        columns = []
        for column in inspector.get_columns(table, schema=schema):
            columns.append(
                {
                    "name": column["name"],
                    "type": type_signature(column["type"]),
                    "nullable": column["nullable"],
                    "default": default_signature(column.get("default")),
                    "identity": column.get("identity"),
                }
            )

        foreign_keys = []
        for foreign_key in inspector.get_foreign_keys(table, schema=schema):
            foreign_keys.append(
                {
                    "constrained_columns": foreign_key["constrained_columns"],
                    "referred_table": foreign_key["referred_table"],
                    "referred_columns": foreign_key["referred_columns"],
                    "options": foreign_key.get("options", {}),
                }
            )

        indexes = []
        for index in inspector.get_indexes(table, schema=schema):
            indexes.append(
                {
                    "name": index["name"],
                    "column_names": index["column_names"],
                    "unique": index["unique"],
                }
            )

        unique_constraints = []
        for constraint in inspector.get_unique_constraints(table, schema=schema):
            unique_constraints.append(
                {
                    "name": constraint["name"],
                    "column_names": constraint["column_names"],
                }
            )

        signature[table] = {
            "columns": columns,
            "primary_key": inspector.get_pk_constraint(table, schema=schema)[
                "constrained_columns"
            ],
            "foreign_keys": sorted(
                foreign_keys,
                key=lambda item: (
                    item["constrained_columns"],
                    item["referred_table"],
                ),
            ),
            "indexes": sorted(indexes, key=lambda item: item["name"]),
            "unique_constraints": sorted(
                unique_constraints, key=lambda item: item["name"] or ""
            ),
        }
    return signature


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left_schema")
    parser.add_argument("right_schema")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    engine = create_engine(normalize_database_url(database_url))
    try:
        inspector = inspect(engine)
        left = schema_signature(inspector, args.left_schema)
        right = schema_signature(inspector, args.right_schema)
    finally:
        engine.dispose()

    if left != right:
        differing_tables = [
            table for table in sorted(left) if left[table] != right[table]
        ]
        print(
            json.dumps(
                {
                    "equivalent": False,
                    "left_schema": args.left_schema,
                    "right_schema": args.right_schema,
                    "differing_tables": differing_tables,
                }
            )
        )
        return 1

    print(
        json.dumps(
            {
                "equivalent": True,
                "left_schema": args.left_schema,
                "right_schema": args.right_schema,
                "managed_table_count": len(left),
                "managed_tables": sorted(left),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
