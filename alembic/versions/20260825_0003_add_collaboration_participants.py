"""add collaboration invitations, participants, and email recipients

Revision ID: 20260825_0003
Revises: 20260824_0002
Create Date: 2026-08-25
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260825_0003"
down_revision: Union[str, Sequence[str], None] = "20260824_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("team_memberships", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("team_memberships", sa.Column("department", sa.String(length=255), nullable=True))

    op.create_table(
        "team_invitations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.Enum("OWNER", "ADMIN", "MEMBER", name="teamrole", native_enum=False),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("invited_by", sa.Integer(), nullable=False),
        sa.Column("accepted_by", sa.Integer(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["accepted_by"], ["users.id"], name="fk_team_invitations_accepted_by_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], name="fk_team_invitations_invited_by_users", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name="fk_team_invitations_team_id_teams", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_team_invitations"),
        sa.UniqueConstraint("team_id", "email", name="uq_team_invitation_team_email"),
    )
    op.create_index("ix_team_invitations_team_id", "team_invitations", ["team_id"], unique=False)
    op.create_index("ix_team_invitations_email", "team_invitations", ["email"], unique=False)
    op.create_index("ix_team_invitations_status", "team_invitations", ["status"], unique=False)
    op.create_index("ix_team_invitations_invited_by", "team_invitations", ["invited_by"], unique=False)
    op.create_index("ix_team_invitations_accepted_by", "team_invitations", ["accepted_by"], unique=False)

    op.add_column("meetings", sa.Column("restrict_to_participants", sa.Boolean(), nullable=True))
    op.execute(sa.text("UPDATE meetings SET restrict_to_participants = false WHERE restrict_to_participants IS NULL"))
    op.alter_column("meetings", "restrict_to_participants", existing_type=sa.Boolean(), nullable=False)

    op.add_column("attendees", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("attendees", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("attendees", sa.Column("department", sa.String(length=255), nullable=True))
    op.create_foreign_key("fk_attendees_user_id_users", "attendees", "users", ["user_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_attendees_user_id", "attendees", ["user_id"], unique=False)
    op.create_unique_constraint("uq_attendee_meeting_user", "attendees", ["meeting_id", "user_id"])

    # Link only unambiguous legacy attendees to an active account in the same
    # Team and Project. Legacy meetings remain project-visible because their
    # restriction flag is false; new structured meetings opt into participant
    # restriction explicitly through the API.
    op.execute(sa.text("""
        UPDATE attendees
        SET user_id = (
            SELECT users.id
            FROM users
            JOIN meetings ON meetings.id = attendees.meeting_id
            JOIN team_memberships
              ON team_memberships.team_id = meetings.team_id
             AND team_memberships.user_id = users.id
            WHERE lower(users.email) = lower(attendees.email)
              AND (
                meetings.project_id IS NULL
                OR EXISTS (
                    SELECT 1 FROM project_memberships
                    WHERE project_memberships.project_id = meetings.project_id
                      AND project_memberships.user_id = users.id
                )
              )
            ORDER BY users.id
            LIMIT 1
        )
        WHERE user_id IS NULL
    """))

    op.create_table(
        "meeting_email_recipients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("meeting_id", sa.UUID(), nullable=False),
        sa.Column("attendee_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("selected_by", sa.Integer(), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_error", sa.Text(), nullable=True),
        sa.Column("delivery_response", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["attendee_id"], ["attendees.id"], name="fk_meeting_email_recipients_attendee_id_attendees", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], name="fk_meeting_email_recipients_meeting_id_meetings", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["selected_by"], ["users.id"], name="fk_meeting_email_recipients_selected_by_users", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_meeting_email_recipients_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_meeting_email_recipients"),
        sa.UniqueConstraint("meeting_id", "attendee_id", name="uq_meeting_email_recipient_participant"),
    )
    for column in ("meeting_id", "attendee_id", "user_id", "status", "selected_by"):
        op.create_index(f"ix_meeting_email_recipients_{column}", "meeting_email_recipients", [column], unique=False)


def downgrade() -> None:
    op.drop_table("meeting_email_recipients")
    op.drop_constraint("uq_attendee_meeting_user", "attendees", type_="unique")
    op.drop_index("ix_attendees_user_id", table_name="attendees")
    op.drop_constraint("fk_attendees_user_id_users", "attendees", type_="foreignkey")
    op.drop_column("attendees", "department")
    op.drop_column("attendees", "title")
    op.drop_column("attendees", "user_id")
    op.drop_column("meetings", "restrict_to_participants")
    op.drop_table("team_invitations")
    op.drop_column("team_memberships", "department")
    op.drop_column("team_memberships", "title")
