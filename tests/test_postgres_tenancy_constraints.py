"""PostgreSQL-only migration and tenant constraint checks."""

from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from meeting_notes_agent.database.models import (
    Attendee,
    Meeting,
    MeetingEmailRecipient,
    MeetingStatus,
    Project,
    ProjectMembership,
    Task,
    TaskPriority,
    TaskStatus,
    Team,
    TeamInvitation,
    TeamMembership,
    TeamRole,
)
from meeting_notes_agent.database.repositories import MeetingRepository


pytestmark = pytest.mark.usefixtures("test_engine")


@pytest.fixture(autouse=True)
def require_postgresql(test_engine):
    if test_engine.dialect.name != "postgresql":
        pytest.skip("PostgreSQL-specific constraint test")


def test_postgres_uses_uuid_and_timezone_aware_timestamps(db_session, test_user):
    membership = test_user.team_memberships[0]
    team = membership.team

    assert isinstance(team.id, UUID)
    assert isinstance(membership.id, UUID)
    assert team.created_at.tzinfo is not None
    assert membership.created_at.tzinfo is not None


def test_postgres_meeting_list_does_not_compare_json_columns(db_session, test_user):
    team_id = test_user.team_memberships[0].team_id
    meeting = Meeting(
        user_id=test_user.id,
        team_id=team_id,
        created_by=test_user.id,
        title="PostgreSQL meeting list",
        meeting_date=date.today(),
        transcript_text="Transcript",
        agenda=["Review JSON-backed fields"],
        decisions=["Use EXISTS for participant access"],
        restrict_to_participants=True,
    )
    db_session.add(meeting)
    db_session.flush()
    db_session.add(
        Attendee(
            meeting_id=meeting.id,
            user_id=test_user.id,
            name=test_user.full_name,
            email=test_user.email,
        )
    )
    db_session.commit()

    meetings, total = MeetingRepository(db_session).get_user_meetings(
        test_user.id,
        team_id=team_id,
    )

    assert total == 1
    assert [item.id for item in meetings] == [meeting.id]


def test_postgres_rejects_duplicate_team_and_project_memberships(
    db_session, test_user
):
    team_id = test_user.team_memberships[0].team_id
    db_session.add(
        TeamMembership(team_id=team_id, user_id=test_user.id, role=TeamRole.MEMBER)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    project = Project(
        team_id=team_id,
        name=f"Constraint Project {uuid4().hex[:8]}",
        normalized_name=f"constraint project {uuid4().hex[:8]}",
        created_by=test_user.id,
    )
    db_session.add(project)
    db_session.flush()
    db_session.add(ProjectMembership(project_id=project.id, user_id=test_user.id))
    db_session.commit()

    db_session.add(ProjectMembership(project_id=project.id, user_id=test_user.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_postgres_foreign_keys_and_project_delete_behavior(db_session, test_user):
    team_id = test_user.team_memberships[0].team_id
    project = Project(
        team_id=team_id,
        name=f"Cascade Project {uuid4().hex[:8]}",
        normalized_name=f"cascade project {uuid4().hex[:8]}",
        created_by=test_user.id,
    )
    db_session.add(project)
    db_session.flush()
    db_session.add(ProjectMembership(project_id=project.id, user_id=test_user.id))
    meeting = Meeting(
        user_id=test_user.id,
        team_id=team_id,
        project_id=project.id,
        created_by=test_user.id,
        title="PostgreSQL cascade meeting",
        meeting_date=date.today(),
        project_name=project.name,
        transcript_text="PostgreSQL transcript",
        status=MeetingStatus.COMPLETED,
    )
    db_session.add(meeting)
    db_session.flush()
    task = Task(
        id=uuid4().hex[:8],
        meeting_id=meeting.id,
        team_id=team_id,
        project_id=project.id,
        assigned_user_id=test_user.id,
        meeting_title=meeting.title,
        title="PostgreSQL cascade task",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        action_item_index=0,
    )
    db_session.add(task)
    db_session.commit()

    project_id = project.id
    meeting_id = meeting.id
    task_id = task.id
    db_session.delete(project)
    db_session.commit()
    db_session.expire_all()

    assert (
        db_session.query(ProjectMembership)
        .filter(ProjectMembership.project_id == project_id)
        .count()
        == 0
    )
    assert db_session.get(Meeting, meeting_id).project_id is None
    assert db_session.get(Task, task_id).project_id is None


def test_postgres_transaction_rollback_leaves_no_partial_team(db_session, test_user):
    team = Team(
        name=f"Rollback Team {uuid4().hex[:8]}",
        created_by=test_user.id,
    )
    db_session.add(team)
    db_session.flush()
    team_id = team.id
    db_session.add(
        TeamMembership(team_id=team_id, user_id=test_user.id, role=TeamRole.OWNER)
    )
    db_session.rollback()

    assert db_session.get(Team, team_id) is None
    assert (
        db_session.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id)
        .count()
        == 0
    )


def test_postgres_collaboration_uniqueness_constraints(db_session, test_user):
    team_id = test_user.team_memberships[0].team_id
    invitation_email = f"postgres-invite-{uuid4().hex[:8]}@example.com"
    db_session.add(
        TeamInvitation(
            team_id=team_id,
            email=invitation_email,
            full_name="Postgres Invite",
            role=TeamRole.MEMBER,
            status="pending",
            invited_by=test_user.id,
        )
    )
    db_session.commit()
    db_session.add(
        TeamInvitation(
            team_id=team_id,
            email=invitation_email,
            full_name="Duplicate Invite",
            role=TeamRole.MEMBER,
            status="pending",
            invited_by=test_user.id,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    meeting = Meeting(
        user_id=test_user.id,
        team_id=team_id,
        created_by=test_user.id,
        title="Postgres participant constraints",
        meeting_date=date.today(),
        transcript_text="Transcript",
        restrict_to_participants=True,
    )
    db_session.add(meeting)
    db_session.flush()
    participant = Attendee(
        meeting_id=meeting.id,
        user_id=test_user.id,
        name=test_user.full_name,
        email=test_user.email,
    )
    db_session.add(participant)
    db_session.flush()
    db_session.add(
        MeetingEmailRecipient(
            meeting_id=meeting.id,
            attendee_id=participant.id,
            user_id=test_user.id,
            email=test_user.email,
            status="pending",
            selected_by=test_user.id,
        )
    )
    db_session.commit()
    db_session.add(
        MeetingEmailRecipient(
            meeting_id=meeting.id,
            attendee_id=participant.id,
            user_id=test_user.id,
            email=test_user.email,
            status="pending",
            selected_by=test_user.id,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
