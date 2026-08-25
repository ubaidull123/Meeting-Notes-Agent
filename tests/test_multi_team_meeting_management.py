"""Regression coverage for multi-workspace context and managed meeting drafts."""

from datetime import date
from uuid import UUID, uuid4

from meeting_notes_agent.auth.security import create_access_token, hash_password
from meeting_notes_agent.database.models import (
    Attendee,
    Meeting,
    MeetingEmailRecipient,
    MeetingStatus,
    ProjectMembership,
    Task,
    TaskPriority,
    TaskStatus,
    Team,
    TeamMembership,
    TeamRole,
    User,
    UserRole,
)


def _headers(user: User, team_id=None) -> dict[str, str]:
    token = create_access_token(subject=user.email, user_id=user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    if team_id is not None:
        headers["X-Team-ID"] = str(team_id)
    return headers


def _uuid(value) -> UUID:
    return UUID(str(value))


def _create_project(client, headers, team_id, name):
    response = client.post(
        f"/api/v1/teams/{team_id}/projects",
        headers=headers,
        json={"name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_meeting(client, headers, team_id, project_id, participant_ids, **values):
    payload = {
        "title": values.pop("title", "Managed draft meeting"),
        "meeting_date": date.today().isoformat(),
        "team_id": str(team_id),
        "project_id": str(project_id) if project_id else None,
        "participant_user_ids": participant_ids,
        **values,
    }
    response = client.post("/api/v1/meetings", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_one_user_can_create_and_isolate_multiple_workspaces(
    client, db_session, test_user, auth_headers
):
    initial_team = client.get("/api/v1/teams", headers=auth_headers).json()[0]
    second = client.post(
        "/api/v1/teams",
        headers={**auth_headers, "X-Team-ID": initial_team["id"]},
        json={"name": "Independent Workspace B", "description": "Second workspace"},
    )
    assert second.status_code == 201
    second = second.json()
    assert second["role"] == "owner"

    teams = client.get("/api/v1/teams", headers=auth_headers).json()
    assert {item["id"] for item in teams} >= {initial_team["id"], second["id"]}

    project_a = _create_project(
        client,
        {**auth_headers, "X-Team-ID": initial_team["id"]},
        initial_team["id"],
        "Workspace A Project",
    )
    project_b = _create_project(
        client,
        {**auth_headers, "X-Team-ID": second["id"]},
        second["id"],
        "Workspace B Project",
    )
    meeting_a = _create_meeting(
        client,
        {**auth_headers, "X-Team-ID": initial_team["id"]},
        initial_team["id"],
        project_a["id"],
        [test_user.id],
    )
    task = Task(
        id=uuid4().hex[:8],
        meeting_id=_uuid(meeting_a["id"]),
        team_id=_uuid(initial_team["id"]),
        project_id=_uuid(project_a["id"]),
        assigned_user_id=test_user.id,
        meeting_title=meeting_a["title"],
        title="Workspace A task",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        action_item_index=0,
    )
    db_session.add(task)
    db_session.commit()

    b_headers = {**auth_headers, "X-Team-ID": second["id"]}
    assert client.get(f"/api/v1/projects/{project_a['id']}", headers=b_headers).status_code == 404
    assert client.get(f"/api/v1/meetings/{meeting_a['id']}", headers=b_headers).status_code == 404
    assert client.get(f"/api/v1/tasks/{task.id}", headers=b_headers).status_code == 404
    assert client.patch(
        f"/api/v1/projects/{project_a['id']}",
        headers=b_headers,
        json={"name": "Cross-workspace mutation"},
    ).status_code == 404

    b_projects = client.get(
        f"/api/v1/teams/{second['id']}/projects", headers=b_headers
    ).json()
    assert [item["id"] for item in b_projects] == [project_b["id"]]
    assert client.get(
        f"/api/v1/meetings?team_id={second['id']}", headers=b_headers
    ).json() == []
    assert client.get(
        f"/api/v1/tasks?team_id={second['id']}", headers=b_headers
    ).json()["tasks"] == []


def test_one_user_has_independent_roles_in_different_workspaces(
    client, db_session, test_user, auth_headers
):
    owned_team = client.get("/api/v1/teams", headers=auth_headers).json()[0]
    other_owner = User(
        email=f"other-owner-{uuid4().hex[:10]}@example.com",
        password_hash=hash_password("OtherOwnerPass123!"),
        full_name="Other Workspace Owner",
        role=UserRole.USER,
    )
    db_session.add(other_owner)
    db_session.flush()
    member_team = Team(name="Member Workspace", created_by=other_owner.id)
    db_session.add(member_team)
    db_session.flush()
    db_session.add_all([
        TeamMembership(team_id=member_team.id, user_id=other_owner.id, role=TeamRole.OWNER),
        TeamMembership(team_id=member_team.id, user_id=test_user.id, role=TeamRole.MEMBER),
    ])
    db_session.commit()

    roles = {
        item["id"]: item["role"]
        for item in client.get("/api/v1/teams", headers=auth_headers).json()
    }
    assert roles[owned_team["id"]] == "owner"
    assert roles[str(member_team.id)] == "member"
    assert client.post(
        f"/api/v1/teams/{member_team.id}/projects",
        headers={**auth_headers, "X-Team-ID": str(member_team.id)},
        json={"name": "Forbidden member project"},
    ).status_code == 403
    assert client.get(
        "/api/v1/settings/providers",
        headers={**auth_headers, "X-Team-ID": owned_team["id"]},
    ).status_code == 200
    assert client.get(
        "/api/v1/settings/providers",
        headers={**auth_headers, "X-Team-ID": str(member_team.id)},
    ).status_code == 403


def test_meeting_draft_edit_rules_project_validation_and_participant_access(
    client, db_session, test_user, auth_headers
):
    team = client.get("/api/v1/teams", headers=auth_headers).json()[0]
    headers = {**auth_headers, "X-Team-ID": team["id"]}
    project_a = _create_project(client, headers, team["id"], "Editable Project A")
    project_b = _create_project(client, headers, team["id"], "Editable Project B")

    member = User(
        email=f"meeting-member-{uuid4().hex[:10]}@example.com",
        password_hash=hash_password("MeetingMemberPass123!"),
        full_name="Meeting Member",
        role=UserRole.USER,
    )
    db_session.add(member)
    db_session.flush()
    db_session.add(TeamMembership(team_id=_uuid(team["id"]), user_id=member.id, role=TeamRole.MEMBER))
    db_session.add(ProjectMembership(project_id=_uuid(project_a["id"]), user_id=member.id))
    db_session.commit()

    meeting = _create_meeting(
        client,
        headers,
        team["id"],
        project_a["id"],
        [test_user.id, member.id],
    )
    assert meeting["status"] == "draft"
    assert meeting["audio_file_path"] is None
    assert meeting["transcript_file_path"] is None
    assert meeting["transcript_text"] is None
    assert meeting["created_by_name"] == test_user.full_name

    member_headers = _headers(member, team["id"])
    assert client.get(f"/api/v1/meetings/{meeting['id']}", headers=member_headers).status_code == 200
    assert client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        headers=member_headers,
        json={"title": "Forbidden edit"},
    ).status_code in {403, 404}
    assert client.delete(
        f"/api/v1/meetings/{meeting['id']}", headers=member_headers
    ).status_code in {403, 404}

    invalid_move = client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        headers=headers,
        json={"project_id": project_b["id"]},
    )
    assert invalid_move.status_code == 400
    assert "participant" in invalid_move.text.lower()

    updated = client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        headers=headers,
        json={
            "title": "Updated draft title",
            "project_id": project_b["id"],
            "participant_user_ids": [test_user.id],
            "transcript_text": "Replacement draft transcript",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["project_id"] == project_b["id"]
    assert updated.json()["transcript_text"] == "Replacement draft transcript"
    assert client.get(
        f"/api/v1/meetings/{meeting['id']}", headers=member_headers
    ).status_code == 404

    meeting_row = db_session.query(Meeting).filter(Meeting.id == _uuid(meeting["id"])).one()
    meeting_row.status = MeetingStatus.QUEUED
    db_session.commit()
    assert client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        headers=headers,
        json={"title": "Locked while queued"},
    ).status_code == 400
    assert client.delete(f"/api/v1/meetings/{meeting['id']}", headers=headers).status_code == 400

    meeting_row.status = MeetingStatus.COMPLETED
    db_session.commit()
    metadata = client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        headers=headers,
        json={"title": "Completed descriptive edit", "notes": "Safe metadata"},
    )
    assert metadata.status_code == 200
    assert client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        headers=headers,
        json={"participant_user_ids": [test_user.id]},
    ).status_code == 400


def test_meeting_delete_cascades_collaboration_records(
    client, db_session, test_user, auth_headers
):
    team = client.get("/api/v1/teams", headers=auth_headers).json()[0]
    headers = {**auth_headers, "X-Team-ID": team["id"]}
    project = _create_project(client, headers, team["id"], "Deletion Project")
    meeting = _create_meeting(
        client, headers, team["id"], project["id"], [test_user.id]
    )
    attendee = db_session.query(Attendee).filter(Attendee.meeting_id == _uuid(meeting["id"])).one()
    recipient = MeetingEmailRecipient(
        meeting_id=_uuid(meeting["id"]),
        attendee_id=attendee.id,
        user_id=test_user.id,
        email=test_user.email,
        selected_by=test_user.id,
    )
    task = Task(
        id=uuid4().hex[:8],
        meeting_id=_uuid(meeting["id"]),
        team_id=_uuid(team["id"]),
        project_id=_uuid(project["id"]),
        assigned_user_id=test_user.id,
        meeting_title=meeting["title"],
        title="Delete with meeting",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        action_item_index=0,
    )
    db_session.add_all([recipient, task])
    db_session.commit()

    assert client.delete(f"/api/v1/meetings/{meeting['id']}", headers=headers).status_code == 204
    assert db_session.query(Attendee).filter(Attendee.meeting_id == _uuid(meeting["id"])).count() == 0
    assert db_session.query(MeetingEmailRecipient).filter(MeetingEmailRecipient.meeting_id == _uuid(meeting["id"])).count() == 0
    assert db_session.query(Task).filter(Task.meeting_id == _uuid(meeting["id"])).count() == 0
