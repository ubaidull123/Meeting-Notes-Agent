"""Regression tests for non-mutating application startup."""

from sqlalchemy import create_engine, inspect

from meeting_notes_agent.database import session as database_session


def test_init_db_only_verifies_connectivity(monkeypatch) -> None:
    empty_engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(database_session, "engine", empty_engine)

    database_session.init_db()

    assert inspect(empty_engine).get_table_names() == []
    empty_engine.dispose()
