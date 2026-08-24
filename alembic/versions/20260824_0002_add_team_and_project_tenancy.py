"""add team and project tenancy

Revision ID: 20260824_0002
Revises: 20260824_0001
Create Date: 2026-08-24 14:57:38.977941
"""

from __future__ import annotations

import re
from typing import Sequence, Union
from uuid import UUID, uuid5

from alembic import op
import sqlalchemy as sa


revision: str = "20260824_0002"
down_revision: Union[str, Sequence[str], None] = "20260824_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TEAM_NAMESPACE = UUID("28e3b9aa-398c-4e75-95e5-1d3c30ed0f26")
TEAM_MEMBERSHIP_NAMESPACE = UUID("83928140-8b1d-4720-9e53-835ec2f84f74")
PROJECT_NAMESPACE = UUID("ac9f8336-fbc6-47b2-b25f-52e9591cb8d8")
PROJECT_MEMBERSHIP_NAMESPACE = UUID("47b6f514-bec8-48ac-b62d-6960ee85af87")


def stable_id(namespace: UUID, *parts: object) -> UUID:
    return uuid5(namespace, "\x1f".join(str(part) for part in parts))


def normalize_project_name(value: str | None) -> tuple[str, str] | None:
    if value is None:
        return None
    display_name = re.sub(r"\s+", " ", value.strip())
    if not display_name:
        return None
    return display_name, display_name.casefold()


def require_zero(connection, query: str, message: str) -> None:
    count = connection.execute(sa.text(query)).scalar_one()
    if count != 0:
        raise RuntimeError(f"{message}: {count}")


def upgrade() -> None:
    """Add tenancy relationships and backfill every legacy owner safely."""
    op.create_table(
        "teams",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_teams_created_by_users", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_teams"),
    )
    op.create_index("ix_teams_created_by", "teams", ["created_by"], unique=False)

    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_projects_created_by_users", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name="fk_projects_team_id_teams", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
        sa.UniqueConstraint("team_id", "normalized_name", name="uq_project_team_normalized_name"),
    )
    op.create_index("idx_projects_team_name", "projects", ["team_id", "name"], unique=False)
    op.create_index("ix_projects_created_by", "projects", ["created_by"], unique=False)
    op.create_index("ix_projects_team_id", "projects", ["team_id"], unique=False)

    op.create_table(
        "team_memberships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.Enum("OWNER", "ADMIN", "MEMBER", name="teamrole", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name="fk_team_memberships_team_id_teams", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_team_memberships_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_team_memberships"),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_membership_team_user"),
    )
    op.create_index("ix_team_memberships_team_id", "team_memberships", ["team_id"], unique=False)
    op.create_index("ix_team_memberships_user_id", "team_memberships", ["user_id"], unique=False)

    op.create_table(
        "project_memberships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_project_memberships_project_id_projects", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_project_memberships_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_project_memberships"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_membership_project_user"),
    )
    op.create_index("ix_project_memberships_project_id", "project_memberships", ["project_id"], unique=False)
    op.create_index("ix_project_memberships_user_id", "project_memberships", ["user_id"], unique=False)

    op.add_column("meetings", sa.Column("team_id", sa.UUID(), nullable=True))
    op.add_column("meetings", sa.Column("project_id", sa.UUID(), nullable=True))
    op.add_column("meetings", sa.Column("created_by", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("team_id", sa.UUID(), nullable=True))
    op.add_column("tasks", sa.Column("project_id", sa.UUID(), nullable=True))
    op.add_column("tasks", sa.Column("assigned_user_id", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column("platform_role", sa.Enum("USER", "PLATFORM_ADMIN", name="platformrole", native_enum=False), nullable=True),
    )

    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT id, full_name, role FROM users ORDER BY id")).mappings().all()
    meetings = connection.execute(
        sa.text("SELECT id, user_id, project_name FROM meetings ORDER BY user_id, created_at, id")
    ).mappings().all()

    team_by_user: dict[int, UUID] = {}
    for user in users:
        user_id = user["id"]
        team_id = stable_id(TEAM_NAMESPACE, user_id)
        membership_id = stable_id(TEAM_MEMBERSHIP_NAMESPACE, user_id)
        team_by_user[user_id] = team_id
        owner_name = (user["full_name"] or f"User {user_id}").strip()
        team_name = f"{owner_name[:248]}'s Team"
        connection.execute(
            sa.text("INSERT INTO teams (id, name, description, created_by) VALUES (:id, :name, :description, :created_by)"),
            {"id": team_id, "name": team_name, "description": "Default workspace created from legacy user ownership.", "created_by": user_id},
        )
        connection.execute(
            sa.text("INSERT INTO team_memberships (id, team_id, user_id, role) VALUES (:id, :team_id, :user_id, 'OWNER')"),
            {"id": membership_id, "team_id": team_id, "user_id": user_id},
        )
        platform_role = "PLATFORM_ADMIN" if str(user["role"]).upper() == "ADMIN" else "USER"
        connection.execute(
            sa.text("UPDATE users SET platform_role = :role WHERE id = :user_id"),
            {"role": platform_role, "user_id": user_id},
        )

    project_by_owner_name: dict[tuple[int, str], UUID] = {}
    meeting_scope: dict[UUID, tuple[UUID, UUID | None]] = {}
    for meeting in meetings:
        owner_id = meeting["user_id"]
        if owner_id not in team_by_user:
            raise RuntimeError(f"Meeting {meeting['id']} references missing legacy owner {owner_id}")
        team_id = team_by_user[owner_id]
        normalized = normalize_project_name(meeting["project_name"])
        project_id = None
        if normalized is not None:
            display_name, normalized_name = normalized
            project_key = (owner_id, normalized_name)
            project_id = project_by_owner_name.get(project_key)
            if project_id is None:
                project_id = stable_id(PROJECT_NAMESPACE, owner_id, normalized_name)
                project_by_owner_name[project_key] = project_id
                project_membership_id = stable_id(PROJECT_MEMBERSHIP_NAMESPACE, project_id, owner_id)
                connection.execute(
                    sa.text("INSERT INTO projects (id, team_id, name, normalized_name, created_by) VALUES (:id, :team_id, :name, :normalized_name, :created_by)"),
                    {"id": project_id, "team_id": team_id, "name": display_name, "normalized_name": normalized_name, "created_by": owner_id},
                )
                connection.execute(
                    sa.text("INSERT INTO project_memberships (id, project_id, user_id) VALUES (:id, :project_id, :user_id)"),
                    {"id": project_membership_id, "project_id": project_id, "user_id": owner_id},
                )

        connection.execute(
            sa.text("UPDATE meetings SET team_id = :team_id, project_id = :project_id, created_by = user_id WHERE id = :meeting_id"),
            {"team_id": team_id, "project_id": project_id, "meeting_id": meeting["id"]},
        )
        meeting_scope[meeting["id"]] = (team_id, project_id)

    tasks = connection.execute(sa.text("SELECT id, meeting_id FROM tasks ORDER BY id")).mappings().all()
    for task in tasks:
        scope = meeting_scope.get(task["meeting_id"])
        if scope is None:
            raise RuntimeError(f"Task {task['id']} references missing meeting {task['meeting_id']}")
        connection.execute(
            sa.text("UPDATE tasks SET team_id = :team_id, project_id = :project_id, assigned_user_id = NULL WHERE id = :task_id"),
            {"team_id": scope[0], "project_id": scope[1], "task_id": task["id"]},
        )

    user_count = connection.execute(sa.text("SELECT count(*) FROM users")).scalar_one()
    team_count = connection.execute(sa.text("SELECT count(*) FROM teams")).scalar_one()
    owner_count = connection.execute(sa.text("SELECT count(*) FROM team_memberships WHERE role = 'OWNER'")).scalar_one()
    project_count = connection.execute(sa.text("SELECT count(*) FROM projects")).scalar_one()
    project_member_count = connection.execute(sa.text("SELECT count(*) FROM project_memberships")).scalar_one()
    if team_count != user_count or owner_count != user_count:
        raise RuntimeError(f"Legacy team backfill count mismatch: users={user_count}, teams={team_count}, owners={owner_count}")
    if project_count != len(project_by_owner_name) or project_member_count != project_count:
        raise RuntimeError(
            "Legacy project backfill count mismatch: "
            f"expected={len(project_by_owner_name)}, projects={project_count}, memberships={project_member_count}"
        )

    require_zero(connection, "SELECT count(*) FROM users WHERE platform_role IS NULL", "Users missing platform role")
    require_zero(connection, "SELECT count(*) FROM meetings WHERE team_id IS NULL OR created_by IS NULL", "Meetings missing required tenancy")
    require_zero(connection, "SELECT count(*) FROM meetings m JOIN projects p ON p.id = m.project_id WHERE p.team_id <> m.team_id", "Meetings with a project from another team")
    require_zero(connection, "SELECT count(*) FROM tasks t LEFT JOIN meetings m ON m.id = t.meeting_id WHERE m.id IS NULL", "Tasks with missing meetings")
    require_zero(
        connection,
        "SELECT count(*) FROM tasks t JOIN meetings m ON m.id = t.meeting_id WHERE t.team_id IS NULL OR t.team_id <> m.team_id OR t.project_id IS DISTINCT FROM m.project_id",
        "Tasks whose scope differs from their meeting",
    )
    require_zero(
        connection,
        "SELECT count(*) FROM project_memberships pm JOIN projects p ON p.id = pm.project_id LEFT JOIN team_memberships tm ON tm.team_id = p.team_id AND tm.user_id = pm.user_id WHERE tm.id IS NULL",
        "Project members missing team membership",
    )
    require_zero(connection, "SELECT count(*) FROM (SELECT team_id, user_id FROM team_memberships GROUP BY team_id, user_id HAVING count(*) > 1) duplicates", "Duplicate team memberships")
    require_zero(connection, "SELECT count(*) FROM (SELECT project_id, user_id FROM project_memberships GROUP BY project_id, user_id HAVING count(*) > 1) duplicates", "Duplicate project memberships")

    op.create_index("ix_meetings_created_by", "meetings", ["created_by"], unique=False)
    op.create_index("ix_meetings_project_id", "meetings", ["project_id"], unique=False)
    op.create_index("ix_meetings_team_id", "meetings", ["team_id"], unique=False)
    op.create_foreign_key("fk_meetings_created_by_users", "meetings", "users", ["created_by"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_meetings_team_id_teams", "meetings", "teams", ["team_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_meetings_project_id_projects", "meetings", "projects", ["project_id"], ["id"], ondelete="SET NULL")

    op.create_index("ix_tasks_assigned_user_id", "tasks", ["assigned_user_id"], unique=False)
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"], unique=False)
    op.create_index("ix_tasks_team_id", "tasks", ["team_id"], unique=False)
    op.create_foreign_key("fk_tasks_assigned_user_id_users", "tasks", "users", ["assigned_user_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_tasks_project_id_projects", "tasks", "projects", ["project_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_tasks_team_id_teams", "tasks", "teams", ["team_id"], ["id"], ondelete="CASCADE")

    op.alter_column("users", "platform_role", existing_type=sa.String(length=14), nullable=False)
    op.alter_column("meetings", "team_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("meetings", "created_by", existing_type=sa.Integer(), nullable=False)
    op.alter_column("tasks", "team_id", existing_type=sa.UUID(), nullable=False)


def downgrade() -> None:
    """Remove additive tenancy structures while retaining every legacy field."""
    op.drop_column("users", "platform_role")
    op.drop_constraint("fk_tasks_team_id_teams", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_project_id_projects", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_assigned_user_id_users", "tasks", type_="foreignkey")
    op.drop_index("ix_tasks_team_id", table_name="tasks")
    op.drop_index("ix_tasks_project_id", table_name="tasks")
    op.drop_index("ix_tasks_assigned_user_id", table_name="tasks")
    op.drop_column("tasks", "assigned_user_id")
    op.drop_column("tasks", "project_id")
    op.drop_column("tasks", "team_id")

    op.drop_constraint("fk_meetings_project_id_projects", "meetings", type_="foreignkey")
    op.drop_constraint("fk_meetings_team_id_teams", "meetings", type_="foreignkey")
    op.drop_constraint("fk_meetings_created_by_users", "meetings", type_="foreignkey")
    op.drop_index("ix_meetings_team_id", table_name="meetings")
    op.drop_index("ix_meetings_project_id", table_name="meetings")
    op.drop_index("ix_meetings_created_by", table_name="meetings")
    op.drop_column("meetings", "created_by")
    op.drop_column("meetings", "project_id")
    op.drop_column("meetings", "team_id")

    op.drop_table("project_memberships")
    op.drop_table("team_memberships")
    op.drop_table("projects")
    op.drop_table("teams")
