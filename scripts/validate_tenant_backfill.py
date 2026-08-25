"""Validate tenant backfill counts and cross-scope invariants."""

from __future__ import annotations

import json
import os

import psycopg2


COUNT_QUERIES = {
    "users": "SELECT count(*) FROM users",
    "teams": "SELECT count(*) FROM teams",
    "team_memberships": "SELECT count(*) FROM team_memberships",
    "projects": "SELECT count(*) FROM projects",
    "project_memberships": "SELECT count(*) FROM project_memberships",
    "meetings": "SELECT count(*) FROM meetings",
    "tasks": "SELECT count(*) FROM tasks",
}

VIOLATION_QUERIES = {
    "meetings_missing_team": (
        "SELECT count(*) FROM meetings WHERE team_id IS NULL"
    ),
    "meetings_missing_creator": (
        "SELECT count(*) FROM meetings WHERE created_by IS NULL"
    ),
    "meetings_invalid_project_relationship": (
        "SELECT count(*) FROM meetings m JOIN projects p ON p.id = m.project_id "
        "WHERE p.team_id <> m.team_id"
    ),
    "tasks_missing_meeting": (
        "SELECT count(*) FROM tasks t LEFT JOIN meetings m ON m.id = t.meeting_id "
        "WHERE m.id IS NULL"
    ),
    "tasks_missing_team": "SELECT count(*) FROM tasks WHERE team_id IS NULL",
    "tasks_team_differs_from_meeting": (
        "SELECT count(*) FROM tasks t JOIN meetings m ON m.id = t.meeting_id "
        "WHERE t.team_id <> m.team_id"
    ),
    "tasks_project_differs_from_meeting": (
        "SELECT count(*) FROM tasks t JOIN meetings m ON m.id = t.meeting_id "
        "WHERE t.project_id IS DISTINCT FROM m.project_id"
    ),
    "project_members_missing_team_membership": (
        "SELECT count(*) FROM project_memberships pm "
        "JOIN projects p ON p.id = pm.project_id "
        "LEFT JOIN team_memberships tm "
        "ON tm.team_id = p.team_id AND tm.user_id = pm.user_id "
        "WHERE tm.id IS NULL"
    ),
    "duplicate_team_memberships": (
        "SELECT count(*) FROM (SELECT team_id, user_id FROM team_memberships "
        "GROUP BY team_id, user_id HAVING count(*) > 1) duplicates"
    ),
    "duplicate_project_memberships": (
        "SELECT count(*) FROM (SELECT project_id, user_id FROM project_memberships "
        "GROUP BY project_id, user_id HAVING count(*) > 1) duplicates"
    ),
    "teams_without_owner": (
        "SELECT count(*) FROM teams t LEFT JOIN team_memberships tm "
        "ON tm.team_id = t.id AND tm.role = 'OWNER' WHERE tm.id IS NULL"
    ),
    "assigned_users_outside_team": (
        "SELECT count(*) FROM tasks t LEFT JOIN team_memberships tm "
        "ON tm.team_id = t.team_id AND tm.user_id = t.assigned_user_id "
        "WHERE t.assigned_user_id IS NOT NULL AND tm.id IS NULL"
    ),
    "assigned_users_outside_project": (
        "SELECT count(*) FROM tasks t LEFT JOIN project_memberships pm "
        "ON pm.project_id = t.project_id AND pm.user_id = t.assigned_user_id "
        "WHERE t.assigned_user_id IS NOT NULL AND t.project_id IS NOT NULL "
        "AND pm.id IS NULL"
    ),
}


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    connection = psycopg2.connect(database_url)
    try:
        connection.set_session(readonly=True)
        with connection.cursor() as cursor:
            counts = {}
            for name, query in COUNT_QUERIES.items():
                cursor.execute(query)
                counts[name] = cursor.fetchone()[0]

            violations = {}
            for name, query in VIOLATION_QUERIES.items():
                cursor.execute(query)
                violations[name] = cursor.fetchone()[0]
    finally:
        connection.rollback()
        connection.close()

    failed = {name: count for name, count in violations.items() if count != 0}
    print(
        json.dumps(
            {
                "counts": counts,
                "violations": violations,
                "valid": not failed,
            }
        )
    )
    if failed:
        raise RuntimeError(f"Tenant validation failed: {failed}")


if __name__ == "__main__":
    main()
