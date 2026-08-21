"""Tests for task endpoints."""
from datetime import date
import pytest
from uuid import uuid4

from meeting_notes_agent.database.models import Meeting, MeetingStatus, TaskStatus
from meeting_notes_agent.database.repositories import TaskRepository
from meeting_notes_agent.services.processing_service import ProcessingService


class TestTaskEndpoints:
    """Test task endpoints."""

    def test_list_tasks_empty(self, client, auth_headers, test_user):
        """Test listing tasks when none exist."""
        response = client.get("/api/v1/tasks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["tasks"], list)

    def test_list_tasks_pagination(self, client, auth_headers):
        """Test tasks pagination."""
        response = client.get("/api/v1/tasks?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_tasks_filter_by_status(self, client, auth_headers):
        """Test filtering tasks by status."""
        response = client.get("/api/v1/tasks?status=todo", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    def test_list_tasks_filter_by_meeting(self, client, auth_headers):
        """Test filtering tasks by meeting."""
        fake_meeting_id = uuid4()
        response = client.get(f"/api/v1/tasks?meeting_id={fake_meeting_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    def test_get_task_not_found(self, client, auth_headers):
        """Test getting nonexistent task."""
        fake_task_id = uuid4()
        response = client.get(f"/api/v1/tasks/{fake_task_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_task_not_found(self, client, auth_headers):
        """Test updating nonexistent task."""
        fake_task_id = uuid4()
        response = client.patch(f"/api/v1/tasks/{fake_task_id}", json={
            "status": "done"
        }, headers=auth_headers)
        assert response.status_code == 404

    def test_delete_task_not_found(self, client, auth_headers):
        """Test deleting nonexistent task."""
        fake_task_id = uuid4()
        response = client.delete(f"/api/v1/tasks/{fake_task_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_generated_meeting_tasks_are_visible(self, client, auth_headers, db_session, test_user):
        """Test meeting action items are persisted as SQL tasks."""
        meeting = Meeting(
            id=uuid4(),
            user_id=test_user.id,
            title="Task Sync Meeting",
            meeting_date=date.today(),
            transcript_text="Transcript",
            action_items=["Ubaid will prepare the launch checklist by Friday."],
            status=MeetingStatus.COMPLETED,
        )
        db_session.add(meeting)
        db_session.flush()

        ProcessingService._sync_tasks_from_meeting(db_session, meeting)
        db_session.commit()

        response = client.get(f"/api/v1/tasks?meeting_id={meeting.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["description"] == "Ubaid will prepare the launch checklist by Friday."

    def test_update_real_short_task_id(self, client, auth_headers, db_session, test_user):
        """Test 8-character generated task IDs can be updated by the API."""
        meeting = Meeting(
            id=uuid4(),
            user_id=test_user.id,
            title="Task Update Meeting",
            meeting_date=date.today(),
            transcript_text="Transcript",
            status=MeetingStatus.COMPLETED,
        )
        db_session.add(meeting)
        db_session.flush()
        task = TaskRepository(db_session).create(
            user_id=test_user.id,
            meeting_id=meeting.id,
            meeting_title=meeting.title,
            action_item_index=0,
            title="Prepare notes",
            description="Prepare notes",
        )
        db_session.commit()

        response = client.patch(f"/api/v1/tasks/{task.id}", json={"status": "done"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == TaskStatus.DONE.value
