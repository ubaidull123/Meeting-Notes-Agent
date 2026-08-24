"""Alembic environment for the Meeting Notes Agent schema."""

from __future__ import annotations

from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import create_engine, pool

from meeting_notes_agent.config.core.config import settings
from meeting_notes_agent.database.models import Base
from meeting_notes_agent.database import models_ai_config  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
database_url = settings.database_url
verification_schema = os.environ.get("ALEMBIC_SCHEMA") or None
unmanaged_tables = {
    "alembic_version",
    "checkpoint_blobs",
    "checkpoint_migrations",
    "checkpoint_writes",
    "checkpoints",
}


def include_object(
    object_: object,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: object | None,
) -> bool:
    """Exclude Alembic and LangGraph-owned infrastructure tables."""
    if type_ == "table" and reflected and name in unmanaged_tables:
        return False
    return True


def migration_options() -> dict[str, object]:
    """Return consistent comparison and version-table options."""
    options: dict[str, object] = {
        "target_metadata": target_metadata,
        "compare_type": True,
        "compare_server_default": True,
        "include_object": include_object,
        "transaction_per_migration": True,
    }
    if verification_schema:
        options["version_table_schema"] = verification_schema
    return options


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""
    context.configure(
        url=database_url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **migration_options(),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with the environment-provided database connection."""
    connect_args: dict[str, str] = {}
    if verification_schema:
        connect_args["options"] = f"-csearch_path={verification_schema}"

    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, **migration_options())

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
