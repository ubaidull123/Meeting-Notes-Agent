"""Deterministic owner-to-member team workflow without external provider calls."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from langgraph.types import Command

from meeting_notes_agent.services.processing_service import ProcessingService


class StagingWorkflowGraph:
    """Small shared graph that exercises both review checkpoints safely."""

    def __init__(self):
        self.stage = "initial"
        self.values = {
            "raw_transcription": "Owner supplied transcript",
            "cleaned_transcription": "Owner supplied transcript",
            "summary": "The team approved the staged project plan.",
            "decisions": ["Ship the staged team architecture"],
            "action_items": ["Member will verify the staged task workflow."],
            "redacted_summary": "The team approved the staged project plan.",
            "redacted_decisions": ["Ship the staged team architecture"],
            "redacted_action_items": ["Member will verify the staged task workflow."],
            "email_draft": "The staged meeting workflow is ready for verification.",
            "email_sent": False,
            "tokens_used_accrued": 12,
        }

    def invoke(self, payload, config):
        if not isinstance(payload, Command):
            self.stage = "human_review"
            return {"__interrupt__": [SimpleNamespace(value={"type": "human_review"})]}
        if self.stage == "human_review":
            self.stage = "email_review"
            return {"__interrupt__": [SimpleNamespace(value={"type": "email_review"})]}
        self.stage = "completed"
        self.values["email_sent"] = True
        self.values["email_response"] = {"id": "deterministic-staging-delivery"}
        return dict(self.values)

    def get_state(self, config):
        next_nodes = {
            "human_review": ("HumanReview",),
            "email_review": ("EmailReview",),
        }.get(self.stage, ())
        return SimpleNamespace(values=dict(self.values), next=next_nodes)


def _register_and_login(client, label: str):
    suffix = uuid4().hex[:10]
    email = f"{label.lower().replace(' ', '-')}-{suffix}@example.com"
    password = "StagingE2EPass123!"
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": label},
    )
    assert registered.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return registered.json(), {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


def test_owner_to_member_staging_workflow(client, monkeypatch):
    graph = StagingWorkflowGraph()
    monkeypatch.setattr(
        ProcessingService,
        "graph",
        property(lambda _service: graph),
    )

    owner, owner_headers = _register_and_login(client, "Staging Team Owner")
    member, member_headers = _register_and_login(client, "Staging Team Member")

    owner_team = client.get("/api/v1/teams", headers=owner_headers).json()[0]
    member_personal_team = client.get("/api/v1/teams", headers=member_headers).json()[0]

    added = client.post(
        f"/api/v1/teams/{owner_team['id']}/members",
        headers=owner_headers,
        json={"user_id": member["id"], "role": "member"},
    )
    assert added.status_code == 201

    project = client.post(
        f"/api/v1/teams/{owner_team['id']}/projects",
        headers=owner_headers,
        json={
            "name": "Staging E2E Project",
            "description": "Tenant workflow verification",
            "context": "Use only this staged project context.",
        },
    )
    assert project.status_code == 201
    project = project.json()
    assert client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=owner_headers,
        json={"user_id": member["id"]},
    ).status_code == 201

    restricted_project = client.post(
        f"/api/v1/teams/{owner_team['id']}/projects",
        headers=owner_headers,
        json={"name": "Staging Restricted Project"},
    )
    assert restricted_project.status_code == 201

    meeting = client.post(
        "/api/v1/meetings",
        headers=owner_headers,
        json={
            "title": "Staging Team Architecture Review",
            "meeting_date": date.today().isoformat(),
            "team_id": owner_team["id"],
            "project_id": project["id"],
            "attendees": [{"name": "Staging Member", "email": member["email"]}],
            "transcript_text": "A deterministic transcript for staging verification.",
        },
    )
    assert meeting.status_code == 201
    meeting = meeting.json()

    queued = client.post(
        f"/api/v1/meetings/{meeting['id']}/process",
        headers=owner_headers,
    )
    assert queued.status_code == 202
    assert client.get(
        f"/api/v1/meetings/{meeting['id']}/status",
        headers=owner_headers,
    ).json()["status"] == "awaiting_review"

    reviewed = client.post(
        f"/api/v1/meetings/{meeting['id']}/review",
        headers=owner_headers,
        json={"decision": "approve"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["next_status"] == "awaiting_email_review"

    email_reviewed = client.post(
        f"/api/v1/meetings/{meeting['id']}/email-review",
        headers=owner_headers,
        json={"decision": "approve"},
    )
    assert email_reviewed.status_code == 200
    assert email_reviewed.json()["sent"] is True

    task_list = client.get(
        f"/api/v1/tasks?meeting_id={meeting['id']}",
        headers=owner_headers,
    )
    assert task_list.status_code == 200
    task = task_list.json()["tasks"][0]
    assigned = client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=owner_headers,
        json={"assigned_user_id": member["id"]},
    )
    assert assigned.status_code == 200

    member_results = client.get(
        f"/api/v1/meetings/{meeting['id']}/results",
        headers=member_headers,
    )
    assert member_results.status_code == 200
    assert member_results.json()["summary"] == graph.values["summary"]
    assert member_results.json()["decisions"] == graph.values["decisions"]

    in_progress = client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=member_headers,
        json={"status": "in_progress"},
    )
    assert in_progress.status_code == 200
    assert client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=member_headers,
        json={"status": "done"},
    ).json()["status"] == "done"

    assert client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=member_headers,
        json={"title": "Forbidden member edit"},
    ).status_code == 403
    assert client.post(
        "/api/v1/meetings",
        headers=member_headers,
        json={
            "title": "Forbidden member meeting",
            "meeting_date": date.today().isoformat(),
            "team_id": owner_team["id"],
            "project_id": project["id"],
            "attendees": [{"name": "Member", "email": member["email"]}],
            "transcript_text": "Forbidden",
        },
    ).status_code == 404
    assert client.post(
        f"/api/v1/meetings/{meeting['id']}/process",
        headers=member_headers,
    ).status_code == 403
    assert client.post(
        f"/api/v1/meetings/{meeting['id']}/review",
        headers=member_headers,
        json={"decision": "approve"},
    ).status_code == 403
    assert client.post(
        f"/api/v1/meetings/{meeting['id']}/email-review",
        headers=member_headers,
        json={"decision": "approve"},
    ).status_code == 403
    assert client.get(
        f"/api/v1/projects/{restricted_project.json()['id']}",
        headers=member_headers,
    ).status_code == 404
    assert client.get(
        f"/api/v1/teams/{member_personal_team['id']}",
        headers=owner_headers,
    ).status_code == 403
    assert client.get(
        "/api/v1/settings/providers",
        headers={**member_headers, "X-Team-ID": owner_team["id"]},
    ).status_code == 403
    # The same account is still owner of its personal team; authority follows
    # the explicitly selected team rather than becoming a global user role.
    assert client.get(
        "/api/v1/settings/providers",
        headers={**member_headers, "X-Team-ID": member_personal_team["id"]},
    ).status_code == 200
