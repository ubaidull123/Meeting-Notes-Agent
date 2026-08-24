"""Tests for meeting endpoints."""
import pytest
from datetime import date
from uuid import UUID


class TestMeetingCRUD:
    """Test meeting CRUD operations."""

    def test_create_meeting_with_transcript_text(self, client, auth_headers):
        """Test creating meeting with transcript_text."""
        response = client.post("/api/v1/meetings", json={
            "title": "Test Meeting",
            "meeting_date": "2026-08-20",
            "project_name": "Test Project",
            "transcript_text": "This is a test transcript.",
            "attendees": [{"name": "John Doe", "email": "john@example.com"}]
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Meeting"
        assert data["project_name"] == "Test Project"
        assert data["transcript_text"] == "This is a test transcript."
        assert len(data["attendees"]) == 1
        assert "id" in data
        # Verify UUID format
        UUID(data["id"])

    def test_create_meeting_allows_upload_draft_but_rejects_multiple_sources(self, client, auth_headers):
        """File uploads begin with a source-less draft; text still permits one source only."""
        # Draft is valid because its audio/transcript is uploaded next.
        response = client.post("/api/v1/meetings", json={
            "title": "Test Meeting",
            "meeting_date": "2026-08-20",
            "attendees": [{"name": "John Doe", "email": "john@example.com"}]
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["status"] == "draft"

        # Multiple sources
        response = client.post("/api/v1/meetings", json={
            "title": "Test Meeting",
            "meeting_date": "2026-08-20",
            "transcript_text": "Text",
            "audio_file_path": "/path/to/audio.mp3",
            "attendees": [{"name": "John Doe", "email": "john@example.com"}]
        }, headers=auth_headers)
        assert response.status_code == 400

    def test_list_meetings(self, client, auth_headers):
        """Test listing meetings."""
        # Create a meeting first
        client.post("/api/v1/meetings", json={
            "title": "Meeting 1",
            "meeting_date": "2026-08-20",
            "transcript_text": "Transcript 1",
            "attendees": [{"name": "John", "email": "john@example.com"}]
        }, headers=auth_headers)

        response = client.get("/api/v1/meetings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_meetings_pagination(self, client, auth_headers):
        """Test meetings pagination."""
        response = client.get("/api/v1/meetings?page=1&page_size=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_meeting(self, client, auth_headers):
        """Test getting a specific meeting."""
        # Create meeting
        create_resp = client.post("/api/v1/meetings", json={
            "title": "Get Test Meeting",
            "meeting_date": "2026-08-20",
            "transcript_text": "Test transcript",
            "attendees": [{"name": "Jane", "email": "jane@example.com"}]
        }, headers=auth_headers)
        meeting_id = create_resp.json()["id"]

        # Get meeting
        response = client.get(f"/api/v1/meetings/{meeting_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meeting_id
        assert data["title"] == "Get Test Meeting"

    def test_get_nonexistent_meeting(self, client, auth_headers):
        """Test getting nonexistent meeting returns 404."""
        from uuid import uuid4
        fake_id = uuid4()
        response = client.get(f"/api/v1/meetings/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_meeting(self, client, auth_headers):
        """Test updating meeting metadata."""
        # Create meeting
        create_resp = client.post("/api/v1/meetings", json={
            "title": "Original Title",
            "meeting_date": "2026-08-20",
            "transcript_text": "Test transcript",
            "attendees": [{"name": "Jane", "email": "jane@example.com"}]
        }, headers=auth_headers)
        meeting_id = create_resp.json()["id"]

        # Update meeting
        response = client.patch(f"/api/v1/meetings/{meeting_id}", json={
            "title": "Updated Title",
            "project_name": "New Project"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["project_name"] == "New Project"

    def test_update_completed_meeting_metadata_and_attendees(self, client, auth_headers, db_session):
        """Completed meetings remain editable without restarting the workflow."""
        from meeting_notes_agent.database.models import Meeting, MeetingStatus

        create_resp = client.post("/api/v1/meetings", json={
            "title": "Completed meeting",
            "meeting_date": "2026-08-20",
            "transcript_text": "Test transcript",
            "attendees": [{"name": "Jane", "email": "jane@example.com"}]
        }, headers=auth_headers)
        meeting_id = UUID(create_resp.json()["id"])
        stored = db_session.query(Meeting).filter(Meeting.id == meeting_id).one()
        stored.status = MeetingStatus.COMPLETED
        db_session.commit()

        response = client.patch(f"/api/v1/meetings/{meeting_id}", json={
            "title": "Corrected title",
            "notes": "Corrected notes",
            "attendees": [{"name": "Alex Smith", "email": "alex@example.com"}],
        }, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Corrected title"
        assert data["notes"] == "Corrected notes"
        assert data["status"] == "completed"
        assert [(item["name"], item["email"]) for item in data["attendees"]] == [
            ("Alex Smith", "alex@example.com")
        ]

    def test_delete_meeting(self, client, auth_headers):
        """Test deleting a meeting."""
        # Create meeting
        create_resp = client.post("/api/v1/meetings", json={
            "title": "To Delete",
            "meeting_date": "2026-08-20",
            "transcript_text": "Test transcript",
            "attendees": [{"name": "Jane", "email": "jane@example.com"}]
        }, headers=auth_headers)
        meeting_id = create_resp.json()["id"]

        # Delete meeting
        response = client.delete(f"/api/v1/meetings/{meeting_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(f"/api/v1/meetings/{meeting_id}", headers=auth_headers)
        assert get_resp.status_code == 404


class TestMeetingUpload:
    """Test file upload endpoints."""

    def test_upload_audio(self, client, auth_headers):
        """Test audio file upload."""
        # Create meeting first
        create_resp = client.post("/api/v1/meetings", json={
            "title": "Audio Upload Test",
            "meeting_date": "2026-08-20",
            "attendees": [{"name": "John", "email": "john@example.com"}]
        }, headers=auth_headers)
        meeting_id = create_resp.json()["id"]

        # Upload audio file
        files = {"file": ("test.mp3", b"dummy audio content", "audio/mpeg")}
        response = client.post(
            f"/api/v1/meetings/{meeting_id}/audio",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == meeting_id
        assert data["status"] == "uploaded"
        assert data["file_path"].endswith(".mp3")

    def test_upload_audio_invalid_format(self, client, auth_headers):
        """Test audio upload with invalid format."""
        create_resp = client.post("/api/v1/meetings", json={
            "title": "Invalid Audio",
            "meeting_date": "2026-08-20",
            "attendees": [{"name": "John", "email": "john@example.com"}]
        }, headers=auth_headers)
        meeting_id = create_resp.json()["id"]

        files = {"file": ("test.txt", b"not audio", "text/plain")}
        response = client.post(
            f"/api/v1/meetings/{meeting_id}/audio",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_upload_transcript(self, client, auth_headers):
        """Test transcript file upload."""
        create_resp = client.post("/api/v1/meetings", json={
            "title": "Transcript Upload Test",
            "meeting_date": "2026-08-20",
            "attendees": [{"name": "John", "email": "john@example.com"}]
        }, headers=auth_headers)
        meeting_id = create_resp.json()["id"]

        files = {"file": ("test.txt", b"transcript content", "text/plain")}
        response = client.post(
            f"/api/v1/meetings/{meeting_id}/transcript",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == meeting_id
        assert data["status"] == "uploaded"


class TestMeetingProcessing:
    """Test meeting processing endpoints."""

    def test_start_processing_with_transcript_text(self, client, auth_headers, monkeypatch):
        """Test starting processing with transcript_text."""
        create_resp = client.post("/api/v1/meetings", json={
            "title": "Processing Test",
            "meeting_date": "2026-08-20",
            "transcript_text": "This is a test transcript for processing.",
            "attendees": [{"name": "John", "email": "john@example.com"}]
        }, headers=auth_headers)
        meeting_id = create_resp.json()["id"]

        monkeypatch.setattr(
            "meeting_notes_agent.api.v1.meetings.process_meeting_in_background",
            lambda *args, **kwargs: None,
        )

        response = client.post(f"/api/v1/meetings/{meeting_id}/process", headers=auth_headers)
        assert response.status_code == 202
        assert response.json()["status"] == "queued"

        response = client.post(f"/api/v1/meetings/{meeting_id}/cancel", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

        # Cancelled runs can be started again with a fresh checkpoint thread.
        response = client.post(f"/api/v1/meetings/{meeting_id}/process", headers=auth_headers)
        assert response.status_code == 202
        assert response.json()["status"] == "queued"

    def test_get_meeting_status(self, client, auth_headers):
        """Test getting meeting status."""
        create_resp = client.post("/api/v1/meetings", json={
            "title": "Status Test",
            "meeting_date": "2026-08-20",
            "transcript_text": "Test transcript",
            "attendees": [{"name": "John", "email": "john@example.com"}]
        }, headers=auth_headers)
        meeting_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/meetings/{meeting_id}/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == meeting_id
        assert "status" in data
        assert "current_stage" in data
        assert "progress_percentage" in data


class TestMeetingOwnership:
    """Test meeting ownership enforcement."""

    def test_cannot_access_other_user_meeting(self, client, auth_headers, db_session, admin_user):
        """Test users cannot access other users' meetings."""
        from meeting_notes_agent.database.models import Meeting, MeetingStatus, Attendee
        from uuid import uuid4

        # Create a meeting owned by admin user (different from test_user)
        other_meeting = Meeting(
            id=uuid4(),
            user_id=admin_user.id,
            team_id=admin_user.team_memberships[0].team_id,
            created_by=admin_user.id,
            title="Other User's Meeting",
            meeting_date=date.today(),
            transcript_text="Other transcript",
            status=MeetingStatus.DRAFT,
        )
        db_session.add(other_meeting)
        attendee = Attendee(meeting_id=other_meeting.id, name="Other", email="other@example.com")
        db_session.add(attendee)
        db_session.commit()

        # Try to access as test_user
        response = client.get(f"/api/v1/meetings/{other_meeting.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_cannot_update_other_user_meeting(self, client, auth_headers, db_session, admin_user):
        """Test users cannot update other users' meetings."""
        from meeting_notes_agent.database.models import Meeting, MeetingStatus
        from uuid import uuid4

        other_meeting = Meeting(
            id=uuid4(),
            user_id=admin_user.id,
            team_id=admin_user.team_memberships[0].team_id,
            created_by=admin_user.id,
            title="Other User's Meeting",
            meeting_date=date.today(),
            transcript_text="Other transcript",
            status=MeetingStatus.DRAFT,
        )
        db_session.add(other_meeting)
        db_session.commit()

        response = client.patch(f"/api/v1/meetings/{other_meeting.id}", json={
            "title": "Hacked Title"
        }, headers=auth_headers)
        assert response.status_code == 404
