"""Tenant isolation, role separation, and IDOR regression tests."""

from dataclasses import dataclass
from datetime import date
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from meeting_notes_agent.auth.security import create_access_token, hash_password
from meeting_notes_agent.database.models import (
    Attendee,
    Meeting,
    MeetingEmailRecipient,
    MeetingStatus,
    PlatformRole,
    Project,
    ProjectMembership,
    Task,
    TaskPriority,
    TaskStatus,
    Team,
    TeamMembership,
    TeamInvitation,
    TeamRole,
    User,
    UserRole,
)
from meeting_notes_agent.services.processing_service import ProcessingService


PASSWORD_HASH = hash_password("TenantTestPass123!")


@dataclass
class TenantScenario:
    users: SimpleNamespace
    teams: SimpleNamespace
    projects: SimpleNamespace
    meetings: SimpleNamespace
    tasks: SimpleNamespace
    headers: dict[str, dict[str, str]]


def _new_user(db_session, label: str, *, legacy_admin=False, platform_admin=False):
    user = User(
        email=f"{label}-{uuid4().hex[:10]}@example.com",
        password_hash=PASSWORD_HASH,
        full_name=label.replace("_", " ").title(),
        role=UserRole.ADMIN if legacy_admin else UserRole.USER,
        platform_role=(
            PlatformRole.PLATFORM_ADMIN if platform_admin else PlatformRole.USER
        ),
    )
    db_session.add(user)
    db_session.flush()
    return user


def _headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=user.email,
        user_id=user.id,
        role=user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tenant_scenario(db_session) -> TenantScenario:
    users = SimpleNamespace(
        a_owner=_new_user(db_session, "team_a_owner"),
        a_admin=_new_user(db_session, "team_a_admin", legacy_admin=True),
        a_member=_new_user(db_session, "team_a_member"),
        a_unassigned=_new_user(db_session, "team_a_unassigned"),
        b_owner=_new_user(db_session, "team_b_owner"),
        b_member=_new_user(db_session, "team_b_member"),
        platform_admin=_new_user(
            db_session,
            "platform_admin",
            legacy_admin=True,
            platform_admin=True,
        ),
        candidate=_new_user(db_session, "candidate"),
    )

    teams = SimpleNamespace(
        a=Team(name="Tenant Test Team A", created_by=users.a_owner.id),
        b=Team(name="Tenant Test Team B", created_by=users.b_owner.id),
    )
    db_session.add_all([teams.a, teams.b])
    db_session.flush()
    db_session.add_all(
        [
            TeamMembership(
                team_id=teams.a.id, user_id=users.a_owner.id, role=TeamRole.OWNER
            ),
            TeamMembership(
                team_id=teams.a.id, user_id=users.a_admin.id, role=TeamRole.ADMIN
            ),
            TeamMembership(
                team_id=teams.a.id, user_id=users.a_member.id, role=TeamRole.MEMBER
            ),
            TeamMembership(
                team_id=teams.a.id,
                user_id=users.a_unassigned.id,
                role=TeamRole.MEMBER,
            ),
            TeamMembership(
                team_id=teams.b.id, user_id=users.b_owner.id, role=TeamRole.OWNER
            ),
            TeamMembership(
                team_id=teams.b.id, user_id=users.b_member.id, role=TeamRole.MEMBER
            ),
        ]
    )

    projects = SimpleNamespace(
        a1=Project(
            team_id=teams.a.id,
            name="Project A1",
            normalized_name="project a1",
            context="Only Team A Project A1 context",
            created_by=users.a_owner.id,
        ),
        a2=Project(
            team_id=teams.a.id,
            name="Project A2",
            normalized_name="project a2",
            created_by=users.a_owner.id,
        ),
        b1=Project(
            team_id=teams.b.id,
            name="Project B1",
            normalized_name="project b1",
            created_by=users.b_owner.id,
        ),
    )
    db_session.add_all([projects.a1, projects.a2, projects.b1])
    db_session.flush()
    db_session.add_all(
        [
            ProjectMembership(project_id=projects.a1.id, user_id=users.a_member.id),
            ProjectMembership(project_id=projects.b1.id, user_id=users.b_member.id),
        ]
    )

    meetings = SimpleNamespace(
        a1=Meeting(
            user_id=users.a_owner.id,
            team_id=teams.a.id,
            project_id=projects.a1.id,
            created_by=users.a_owner.id,
            title="Authorized A1 Meeting",
            meeting_date=date.today(),
            project_name=projects.a1.name,
            transcript_text="A1 transcript",
            summary="A1 summary",
            decisions=["A1 decision"],
            status=MeetingStatus.COMPLETED,
        ),
        a2=Meeting(
            user_id=users.a_owner.id,
            team_id=teams.a.id,
            project_id=projects.a2.id,
            created_by=users.a_owner.id,
            title="Restricted A2 Meeting",
            meeting_date=date.today(),
            project_name=projects.a2.name,
            transcript_text="A2 transcript",
            status=MeetingStatus.COMPLETED,
        ),
        b1=Meeting(
            user_id=users.b_owner.id,
            team_id=teams.b.id,
            project_id=projects.b1.id,
            created_by=users.b_owner.id,
            title="Other Tenant B1 Meeting",
            meeting_date=date.today(),
            project_name=projects.b1.name,
            transcript_text="B1 transcript",
            status=MeetingStatus.COMPLETED,
        ),
    )
    db_session.add_all([meetings.a1, meetings.a2, meetings.b1])
    db_session.flush()
    db_session.add_all(
        [
            Attendee(meeting_id=meeting.id, name="Attendee", email="attendee@example.com")
            for meeting in (meetings.a1, meetings.a2, meetings.b1)
        ]
    )

    tasks = SimpleNamespace(
        assigned=Task(
            id=uuid4().hex[:8],
            meeting_id=meetings.a1.id,
            team_id=teams.a.id,
            project_id=projects.a1.id,
            assigned_user_id=users.a_member.id,
            meeting_title=meetings.a1.title,
            title="Assigned A1 task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            action_item_index=0,
        ),
        project=Task(
            id=uuid4().hex[:8],
            meeting_id=meetings.a1.id,
            team_id=teams.a.id,
            project_id=projects.a1.id,
            assigned_user_id=None,
            meeting_title=meetings.a1.title,
            title="Visible project task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            action_item_index=1,
        ),
        a2=Task(
            id=uuid4().hex[:8],
            meeting_id=meetings.a2.id,
            team_id=teams.a.id,
            project_id=projects.a2.id,
            assigned_user_id=users.a_unassigned.id,
            meeting_title=meetings.a2.title,
            title="Restricted A2 task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            action_item_index=0,
        ),
        b1=Task(
            id=uuid4().hex[:8],
            meeting_id=meetings.b1.id,
            team_id=teams.b.id,
            project_id=projects.b1.id,
            assigned_user_id=users.b_member.id,
            meeting_title=meetings.b1.title,
            title="Other tenant task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            action_item_index=0,
        ),
    )
    db_session.add_all([tasks.assigned, tasks.project, tasks.a2, tasks.b1])
    db_session.commit()

    headers = {
        name: _headers(user)
        for name, user in vars(users).items()
        if isinstance(user, User)
    }
    return TenantScenario(users, teams, projects, meetings, tasks, headers)


def test_member_sees_only_assigned_team_projects(client, tenant_scenario):
    s = tenant_scenario
    headers = s.headers["a_member"]

    teams = client.get("/api/v1/teams", headers=headers)
    assert teams.status_code == 200
    assert {item["id"] for item in teams.json()} == {str(s.teams.a.id)}
    assert client.get(f"/api/v1/teams/{s.teams.a.id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/teams/{s.teams.b.id}", headers=headers).status_code == 403

    projects = client.get(f"/api/v1/teams/{s.teams.a.id}/projects", headers=headers)
    assert projects.status_code == 200
    assert {item["id"] for item in projects.json()} == {str(s.projects.a1.id)}
    assert client.get(f"/api/v1/projects/{s.projects.a1.id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/projects/{s.projects.a2.id}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/projects/{s.projects.b1.id}", headers=headers).status_code == 404


def test_meeting_idor_is_blocked_across_project_and_team(client, tenant_scenario):
    s = tenant_scenario
    headers = s.headers["a_member"]

    assert client.get(f"/api/v1/meetings/{s.meetings.a1.id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/meetings/{s.meetings.a2.id}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/meetings/{s.meetings.b1.id}", headers=headers).status_code == 404

    listed = client.get("/api/v1/meetings", headers=headers)
    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()} == {str(s.meetings.a1.id)}


def test_member_cannot_manage_or_process_meetings(client, tenant_scenario):
    s = tenant_scenario
    headers = s.headers["a_member"]
    meeting_url = f"/api/v1/meetings/{s.meetings.a1.id}"
    payload = {
        "title": "Forbidden meeting",
        "meeting_date": date.today().isoformat(),
        "team_id": str(s.teams.a.id),
        "project_id": str(s.projects.a1.id),
        "attendees": [{"name": "Member", "email": "member@example.com"}],
        "transcript_text": "Forbidden",
    }

    # Project-management checks deliberately conceal the project with 404.
    assert client.post("/api/v1/meetings", json=payload, headers=headers).status_code == 404
    assert client.patch(meeting_url, json={"title": "Forbidden"}, headers=headers).status_code == 403
    assert client.delete(meeting_url, headers=headers).status_code == 403
    assert client.post(f"{meeting_url}/process", headers=headers).status_code == 403
    assert client.get(f"{meeting_url}/review", headers=headers).status_code == 403
    assert client.post(f"{meeting_url}/review", json={"decision": "approve"}, headers=headers).status_code == 403
    assert client.get(f"{meeting_url}/email-review", headers=headers).status_code == 403
    assert client.post(f"{meeting_url}/email-review", json={"decision": "approve"}, headers=headers).status_code == 403
    assert client.post(
        f"{meeting_url}/transcript",
        files={"file": ("notes.txt", b"unauthorized", "text/plain")},
        headers=headers,
    ).status_code == 403


def test_member_task_access_and_status_boundary(client, tenant_scenario):
    s = tenant_scenario
    headers = s.headers["a_member"]

    assigned_url = f"/api/v1/tasks/{s.tasks.assigned.id}"
    assert client.get(assigned_url, headers=headers).status_code == 200
    updated = client.patch(assigned_url, json={"status": "in_progress"}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"
    assert client.patch(assigned_url, json={"title": "Forbidden edit"}, headers=headers).status_code == 403

    project_url = f"/api/v1/tasks/{s.tasks.project.id}"
    assert client.get(project_url, headers=headers).status_code == 200
    assert client.patch(project_url, json={"status": "done"}, headers=headers).status_code == 403
    assert client.get(f"/api/v1/tasks/{s.tasks.a2.id}", headers=headers).status_code == 404
    assert client.patch(f"/api/v1/tasks/{s.tasks.b1.id}", json={"status": "done"}, headers=headers).status_code == 404


def test_team_admin_can_manage_own_team_not_another_team(client, tenant_scenario):
    s = tenant_scenario
    headers = s.headers["a_admin"]

    created_project = client.post(
        f"/api/v1/teams/{s.teams.a.id}/projects",
        json={"name": f"Admin Project {uuid4().hex[:6]}"},
        headers=headers,
    )
    assert created_project.status_code == 201
    assert client.post(
        f"/api/v1/teams/{s.teams.b.id}/projects",
        json={"name": "Cross tenant project"},
        headers=headers,
    ).status_code == 403
    assert client.get(f"/api/v1/teams/{s.teams.b.id}/members", headers=headers).status_code == 403
    assert client.delete(f"/api/v1/projects/{s.projects.b1.id}", headers=headers).status_code == 404

    added = client.post(
        f"/api/v1/teams/{s.teams.a.id}/members",
        json={"user_id": s.users.candidate.id, "role": "member"},
        headers=headers,
    )
    assert added.status_code == 201

    meeting = client.post(
        "/api/v1/meetings",
        json={
            "title": "Admin-created meeting",
            "meeting_date": date.today().isoformat(),
            "team_id": str(s.teams.a.id),
            "project_id": str(s.projects.a1.id),
            "attendees": [{"name": "Admin", "email": "admin@example.com"}],
            "transcript_text": "Admin transcript",
        },
        headers=headers,
    )
    assert meeting.status_code == 201
    assert meeting.json()["team_id"] == str(s.teams.a.id)


def test_task_assignment_must_match_team_and_project(client, tenant_scenario):
    s = tenant_scenario
    headers = s.headers["a_admin"]
    payload = {
        "meeting_id": str(s.meetings.a1.id),
        "meeting_title": s.meetings.a1.title,
        "action_item_index": 9,
        "title": "Assignment validation",
        "assigned_user_id": s.users.a_unassigned.id,
    }
    assert client.post("/api/v1/tasks", json=payload, headers=headers).status_code == 400
    payload["assigned_user_id"] = s.users.b_member.id
    assert client.post("/api/v1/tasks", json=payload, headers=headers).status_code == 400
    payload["assigned_user_id"] = s.users.a_member.id
    assert client.post("/api/v1/tasks", json=payload, headers=headers).status_code == 201


def test_platform_admin_and_team_admin_roles_are_separate(client, tenant_scenario):
    s = tenant_scenario

    # A legacy global ADMIN flag does not grant platform authority anymore.
    assert client.get("/api/v1/admin/stats", headers=s.headers["a_admin"]).status_code == 403
    assert client.get("/api/v1/admin/stats", headers=s.headers["platform_admin"]).status_code == 200

    # Platform authority does not silently grant customer-team access.
    assert client.get(
        f"/api/v1/teams/{s.teams.a.id}",
        headers=s.headers["platform_admin"],
    ).status_code == 403
    assert client.get(
        f"/api/v1/meetings/{s.meetings.a1.id}",
        headers=s.headers["platform_admin"],
    ).status_code == 404


def test_provider_configuration_requires_team_management_role(client, tenant_scenario):
    s = tenant_scenario
    member_headers = s.headers["a_member"]

    for path in (
        "/api/v1/settings/providers",
        "/api/v1/settings/ai",
        "/api/v1/settings/transcription",
        "/api/v1/settings/meetings",
        "/api/v1/settings/credentials",
        "/api/v1/settings/email",
    ):
        assert client.get(path, headers=member_headers).status_code == 403

    # Personal account settings remain available to ordinary members.
    assert client.get("/api/v1/settings/profile", headers=member_headers).status_code == 200
    assert client.get("/api/v1/settings/notifications", headers=member_headers).status_code == 200

    override_url = f"/api/v1/settings/meetings/{s.meetings.a1.id}/override"
    assert client.get(override_url, headers=member_headers).status_code == 403
    assert client.get(override_url, headers=s.headers["a_admin"]).status_code == 200

    # A Team A admin cannot use a valid Team B meeting ID to manage overrides.
    assert client.get(
        f"/api/v1/settings/meetings/{s.meetings.b1.id}/override",
        headers=s.headers["a_admin"],
    ).status_code == 404

    assert client.get(
        "/api/v1/settings/providers",
        headers=s.headers["platform_admin"],
    ).status_code == 200


def test_team_admin_processing_keeps_legacy_owner_billing(
    tenant_scenario,
    db_session,
    monkeypatch,
):
    s = tenant_scenario
    captured: dict[str, int] = {}

    def capture_allowance(_db, billing_user_id, _meeting=None):
        captured["billing_user_id"] = billing_user_id

    monkeypatch.setattr(
        ProcessingService,
        "_ensure_processing_allowance",
        staticmethod(capture_allowance),
    )
    s.meetings.a1.status = MeetingStatus.DRAFT
    db_session.commit()

    ProcessingService(db_session).queue_processing(
        s.meetings.a1.id,
        s.users.a_admin.id,
    )

    assert captured["billing_user_id"] == s.users.a_owner.id
    assert captured["billing_user_id"] != s.users.a_admin.id


def test_owner_safety_and_team_member_cleanup(client, tenant_scenario, db_session):
    s = tenant_scenario
    owner_headers = s.headers["a_owner"]

    assert client.delete(
        f"/api/v1/teams/{s.teams.a.id}/members/{s.users.a_owner.id}",
        headers=owner_headers,
    ).status_code == 422
    assert client.patch(
        f"/api/v1/teams/{s.teams.a.id}/members/{s.users.a_owner.id}",
        json={"role": "member"},
        headers=owner_headers,
    ).status_code == 422

    removed_id = s.users.a_member.id
    assert client.delete(
        f"/api/v1/teams/{s.teams.a.id}/members/{removed_id}",
        headers=owner_headers,
    ).status_code == 204
    db_session.expire_all()
    assert db_session.query(ProjectMembership).filter_by(user_id=removed_id).count() == 0
    assert db_session.query(Task).filter_by(id=s.tasks.assigned.id).one().assigned_user_id == removed_id


def test_email_member_add_and_pending_invitation_reconciliation(
    client, tenant_scenario, db_session
):
    s = tenant_scenario
    existing = client.post(
        f"/api/v1/teams/{s.teams.a.id}/members",
        headers=s.headers["a_owner"],
        json={
            "full_name": "Candidate Person",
            "email": s.users.candidate.email,
            "title": "Backend Developer",
            "department": "Engineering",
            "role": "member",
        },
    )
    assert existing.status_code == 201
    assert existing.json()["user_id"] == s.users.candidate.id
    assert existing.json()["status"] == "active"
    assert existing.json()["title"] == "Backend Developer"

    duplicate = client.post(
        f"/api/v1/teams/{s.teams.a.id}/members",
        headers=s.headers["a_owner"],
        json={"full_name": "Candidate Person", "email": s.users.candidate.email},
    )
    assert duplicate.status_code == 409

    invited_email = f"invited-{uuid4().hex[:10]}@example.com"
    invited = client.post(
        f"/api/v1/teams/{s.teams.a.id}/members",
        headers=s.headers["a_owner"],
        json={
            "full_name": "Invited Engineer",
            "email": invited_email,
            "title": "AI Engineer",
        },
    )
    assert invited.status_code == 201
    assert invited.json()["status"] == "pending"
    assert invited.json()["user_id"] is None
    assert client.post(
        f"/api/v1/teams/{s.teams.a.id}/members",
        headers=s.headers["a_member"],
        json={"full_name": "Forbidden", "email": f"forbidden-{uuid4().hex}@example.com"},
    ).status_code == 403

    registered = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Invited Engineer",
            "email": invited_email,
            "password": "InvitationPass123!",
        },
    )
    assert registered.status_code == 201
    invited_user_id = registered.json()["id"]
    membership = db_session.query(TeamMembership).filter_by(
        team_id=s.teams.a.id, user_id=invited_user_id
    ).one()
    assert membership.title == "AI Engineer"
    invitation = db_session.query(TeamInvitation).filter_by(
        team_id=s.teams.a.id, email=invited_email
    ).one()
    assert invitation.status == "accepted"
    assert invitation.accepted_by == invited_user_id


def test_structured_meeting_participants_restrict_project_access(
    client, tenant_scenario, db_session
):
    s = tenant_scenario
    db_session.add(
        ProjectMembership(project_id=s.projects.a1.id, user_id=s.users.a_unassigned.id)
    )
    db_session.commit()

    created = client.post(
        "/api/v1/meetings",
        headers=s.headers["a_owner"],
        json={
            "title": "Participant restricted review",
            "meeting_date": date.today().isoformat(),
            "team_id": str(s.teams.a.id),
            "project_id": str(s.projects.a1.id),
            "participant_user_ids": [s.users.a_member.id],
            "transcript_text": "A participant-restricted transcript.",
        },
    )
    assert created.status_code == 201
    meeting = created.json()
    assert meeting["restrict_to_participants"] is True
    assert meeting["attendees"][0]["user_id"] == s.users.a_member.id
    assert client.get(
        f"/api/v1/meetings/{meeting['id']}", headers=s.headers["a_member"]
    ).status_code == 200
    assert client.get(
        f"/api/v1/meetings/{meeting['id']}", headers=s.headers["a_unassigned"]
    ).status_code == 404
    assert client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        headers=s.headers["a_member"],
        json={"participant_user_ids": [s.users.a_member.id]},
    ).status_code == 403

    invalid = client.post(
        "/api/v1/meetings",
        headers=s.headers["a_owner"],
        json={
            "title": "Invalid participant",
            "meeting_date": date.today().isoformat(),
            "team_id": str(s.teams.a.id),
            "project_id": str(s.projects.a1.id),
            "participant_user_ids": [s.users.b_member.id],
            "transcript_text": "Invalid",
        },
    )
    assert invalid.status_code == 400


def test_email_recipients_are_a_subset_of_meeting_participants(
    client, tenant_scenario, db_session, monkeypatch
):
    s = tenant_scenario
    db_session.add_all(
        [
            TeamMembership(
                team_id=s.teams.a.id,
                user_id=s.users.candidate.id,
                role=TeamRole.MEMBER,
            ),
            ProjectMembership(
                project_id=s.projects.a1.id,
                user_id=s.users.candidate.id,
            ),
            ProjectMembership(
                project_id=s.projects.a1.id,
                user_id=s.users.a_unassigned.id,
            ),
        ]
    )
    db_session.commit()
    created = client.post(
        "/api/v1/meetings",
        headers=s.headers["a_owner"],
        json={
            "title": "Recipient selection review",
            "meeting_date": date.today().isoformat(),
            "team_id": str(s.teams.a.id),
            "project_id": str(s.projects.a1.id),
            "participant_user_ids": [s.users.a_member.id, s.users.candidate.id],
            "transcript_text": "Recipient selection transcript.",
        },
    )
    assert created.status_code == 201
    meeting_id = created.json()["id"]
    meeting = db_session.query(Meeting).filter_by(id=UUID(meeting_id)).one()
    meeting.status = MeetingStatus.AWAITING_EMAIL_REVIEW
    meeting.thread_id = f"email-{uuid4()}"
    meeting.email_draft = "Reviewed follow-up"
    meeting.redacted_summary = "Reviewed summary"
    db_session.commit()

    class EmailGraph:
        def get_state(self, config):
            return SimpleNamespace(values={}, next=("EmailReview",))

        def invoke(self, payload, config):
            return {
                "email_sent": True,
                "email_response": {"id": "selected-recipient-delivery"},
                "email_draft": "Reviewed follow-up",
                "redacted_summary": "Reviewed summary",
            }

    monkeypatch.setattr(
        ProcessingService,
        "graph",
        property(lambda _service: EmailGraph()),
    )

    draft = client.get(
        f"/api/v1/meetings/{meeting_id}/email-review",
        headers=s.headers["a_owner"],
    )
    assert draft.status_code == 200
    assert {item["user_id"] for item in draft.json()["participants"]} == {
        s.users.a_member.id,
        s.users.candidate.id,
    }
    assert client.post(
        f"/api/v1/meetings/{meeting_id}/email-review",
        headers=s.headers["a_owner"],
        json={
            "decision": "approve",
            "recipient_user_ids": [s.users.a_unassigned.id],
        },
    ).status_code == 400

    sent = client.post(
        f"/api/v1/meetings/{meeting_id}/email-review",
        headers=s.headers["a_owner"],
        json={
            "decision": "approve",
            "recipient_user_ids": [s.users.a_member.id],
        },
    )
    assert sent.status_code == 200
    recipients = db_session.query(MeetingEmailRecipient).filter_by(
        meeting_id=meeting.id
    ).all()
    assert [(recipient.user_id, recipient.status) for recipient in recipients] == [
        (s.users.a_member.id, "sent")
    ]
