"""LangGraph processing service."""
import uuid
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timezone
from uuid import UUID
from langgraph.types import Command

from meeting_notes_agent.graph import build_graph
from meeting_notes_agent.state_schema import MeetingState, Attendee
from meeting_notes_agent.database import (
    MeetingRepository,
    AttendeeRepository,
    TaskRepository,
    UserQuotaRepository,
    UserCreditsRepository,
    UserUsageRepository,
    SessionLocal,
    get_db,
)
from meeting_notes_agent.database.models import Meeting, MeetingStatus, Task, TaskStatus, TaskPriority
from meeting_notes_agent.core.exceptions import (
    InsufficientCreditsError,
    NotFoundError,
    ProcessingCancelled,
    ProcessingError,
    QuotaExceededError,
    ValidationError,
)
from meeting_notes_agent.schemas.meeting import (
    MeetingCreate,
    MeetingUpdate,
    AttendeeBase,
    AudioUploadResponse,
    TranscriptUploadResponse,
    ProcessingStartResponse,
    ReviewContentResponse,
    ReviewRequest,
    ReviewResponse,
    EmailDraftResponse,
    EmailReviewRequest,
    EmailSendResponse,
    MeetingResultResponse,
    MeetingStatusResponse,
    TaskResponse,
)


logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for meeting processing operations."""

    def __init__(self, db=None):
        self.db = db
        self._graph = None

    def _get_db(self):
        """Get database session."""
        if self.db:
            return self.db
        return next(get_db())

    @property
    def graph(self):
        """Get or build the LangGraph graph."""
        if self._graph is None:
            self._graph = build_graph()
        return self._graph

    def _map_meeting_to_state(self, meeting: Meeting) -> MeetingState:
        """Map database meeting to MeetingState."""
        attendees = [
            Attendee(name=a.name, email=a.email)
            for a in meeting.attendees
        ]

        # Determine input source - prefer file paths over text if both exist
        audio_file_path = meeting.audio_file_path
        transcript_file_path = meeting.transcript_file_path
        transcript_text = meeting.transcript_text

        # If file paths exist, they take precedence over transcript_text
        if audio_file_path:
            transcript_text = None
        elif transcript_file_path:
            transcript_text = None

        state = MeetingState(
            meeting_id=str(meeting.id),
            user_id=meeting.user_id,
            meeting_title=meeting.title,
            meeting_date=meeting.meeting_date,
            meeting_time=meeting.meeting_time,
            project_name=meeting.project_name,
            audio_file_path=audio_file_path,
            transcript_file_path=transcript_file_path,
            transcript_text=transcript_text,
            attendees=attendees,
            agenda=meeting.agenda or [],
            notes=meeting.notes,
            # Include existing outputs if resuming
            raw_transcription=meeting.raw_transcription,
            cleaned_transcription=meeting.cleaned_transcription,
            summary=meeting.summary,
            decisions=meeting.decisions or [],
            action_items=meeting.action_items or [],
            redacted_transcription=meeting.redacted_transcription,
            redacted_summary=meeting.redacted_summary,
            redacted_decisions=meeting.redacted_decisions or [],
            redacted_action_items=meeting.redacted_action_items or [],
            email_draft=meeting.email_draft,
            email_sent=meeting.email_sent,
            email_response=meeting.email_response,
            status=meeting.status.value if hasattr(meeting.status, 'value') else meeting.status,
            thread_id=meeting.thread_id,
        )
        return state

    def _map_state_to_meeting(self, meeting: Meeting, state: Dict[str, Any]) -> Meeting:
        """Update meeting from state dict."""
        meeting.raw_transcription = state.get("raw_transcription")
        meeting.cleaned_transcription = state.get("cleaned_transcription")
        meeting.summary = state.get("summary")
        meeting.decisions = state.get("decisions", [])
        meeting.action_items = state.get("action_items", [])
        meeting.redacted_transcription = state.get("redacted_transcription")
        meeting.redacted_summary = state.get("redacted_summary")
        meeting.redacted_decisions = state.get("redacted_decisions", [])
        meeting.redacted_action_items = state.get("redacted_action_items", [])
        meeting.email_draft = state.get("email_draft")
        meeting.email_sent = state.get("email_sent", False)
        meeting.email_response = state.get("email_response")
        meeting.tokens_used = state.get("tokens_used_accrued", 0)
        meeting.status = state.get("status", meeting.status)
        meeting.thread_id = state.get("thread_id", meeting.thread_id)
        meeting.error_code = state.get("error_code")
        meeting.error_message = state.get("error_message")
        return meeting

    @staticmethod
    def _task_title(action_item: str, index: int) -> str:
        """Return a compact task title from a generated action item."""
        text = " ".join(str(action_item).split())
        if not text:
            return f"Action item {index + 1}"
        title = text.split(". ", 1)[0].strip()
        return title[:100] or f"Action item {index + 1}"

    @staticmethod
    def _sync_tasks_from_meeting(db, meeting: Meeting) -> None:
        """Persist generated action items into the SQL tasks table."""
        action_items = meeting.action_items or meeting.redacted_action_items or []
        task_repo = TaskRepository(db)

        seen_indexes = set()
        for index, action_item in enumerate(action_items):
            if not str(action_item).strip():
                continue
            seen_indexes.add(index)
            existing = task_repo.get_by_meeting_and_action_item(meeting.id, index)
            fields = {
                "title": ProcessingService._task_title(action_item, index),
                "description": str(action_item).strip(),
                "status": TaskStatus.TODO,
                "priority": TaskPriority.MEDIUM,
                "labels": ["meeting-action-item"],
            }
            if existing:
                task_repo.update(existing, **fields)
            else:
                task_repo.create(
                    user_id=meeting.user_id,
                    meeting_id=meeting.id,
                    meeting_title=meeting.title,
                    action_item_index=index,
                    **fields,
                )

        for task in task_repo.get_by_meeting_id(meeting.id):
            if task.action_item_index not in seen_indexes:
                task_repo.delete(task)

    def _persist_checkpoint_state(self, db, meeting: Meeting, config: Dict[str, Any]) -> None:
        """Copy the latest graph checkpoint into the persisted meeting.

        LangGraph returns an interrupt marker rather than the full state at a
        human checkpoint. Reading the checkpoint is therefore essential: it
        preserves the generated review artefacts for the review API and UI.
        """
        snapshot = self.graph.get_state(config)
        values = getattr(snapshot, "values", None)
        if values:
            self._map_state_to_meeting(meeting, values)
            self._sync_tasks_from_meeting(db, meeting)

    def _ensure_pending_checkpoint(
        self,
        meeting: Meeting,
        config: Dict[str, Any],
        db,
        meeting_repo: MeetingRepository,
    ) -> None:
        """Fail cleanly when a review thread has no resumable checkpoint."""
        snapshot = self.graph.get_state(config)
        if getattr(snapshot, "next", ()):
            return

        meeting_repo.update(
            meeting,
            status=MeetingStatus.FAILED,
            error_code="CHECKPOINT_NOT_FOUND",
            error_message=(
                "The saved review checkpoint is unavailable. Retry processing "
                "to create a fresh persistent checkpoint."
            ),
        )
        db.commit()
        raise ValidationError(
            "The review checkpoint is unavailable. Retry processing and submit the review again."
        )

    @staticmethod
    def _ensure_processing_allowance(db, user_id: int) -> None:
        """Initialize monthly billing records and enforce limits before work starts."""
        quota_repo = UserQuotaRepository(db)
        credits_repo = UserCreditsRepository(db)
        usage_repo = UserUsageRepository(db)

        quota = quota_repo.get_or_create(user_id)
        credits = credits_repo.get_by_user_id(user_id)
        if credits is None:
            credits = credits_repo.get_or_create(user_id)
            credits.balance = quota.monthly_credits

        current_usage = usage_repo.get_current_month(user_id)
        if current_usage is None:
            previous_usage = usage_repo.get_by_user_id(user_id, limit=1)
            current_usage = usage_repo.get_or_create_current_month(user_id)
            # Monthly credits reset when the user begins a new billing month.
            if previous_usage and previous_usage[0].month < current_usage.month:
                credits.balance = quota.monthly_credits

        if current_usage.meetings_processed >= quota.monthly_meeting_limit:
            raise QuotaExceededError(
                f"Monthly meeting quota ({quota.monthly_meeting_limit}) exceeded.",
                details={
                    "limit": quota.monthly_meeting_limit,
                    "used": current_usage.meetings_processed,
                },
            )
        if credits.balance <= 0:
            raise InsufficientCreditsError(
                "Insufficient credits. Please contact an administrator.",
                details={"balance": credits.balance},
            )

    @staticmethod
    def _record_terminal_processing_usage(db, meeting: Meeting) -> None:
        """Deduct one credit and add monthly usage exactly once per terminal run."""
        if meeting.credits_charged:
            return

        usage_repo = UserUsageRepository(db)
        credits_repo = UserCreditsRepository(db)
        usage = usage_repo.get_or_create_current_month(meeting.user_id)

        credits = credits_repo.get_or_create(meeting.user_id)
        credits_repo.deduct_credits(credits, 1, "Meeting processing")
        usage.meetings_processed += 1
        usage.tokens_used += meeting.tokens_used or 0
        usage.credits_consumed += 1
        usage.updated_at = datetime.now(timezone.utc)
        meeting.credits_charged = True

    @staticmethod
    def _interrupt_type(result: Dict[str, Any]) -> Optional[str]:
        interrupts = result.get("__interrupt__", [])
        if not interrupts:
            return None
        value = getattr(interrupts[0], "value", {}) or {}
        return value.get("type") if isinstance(value, dict) else None

    def create_meeting(self, user_id: int, data: MeetingCreate) -> Meeting:
        """Create a new meeting."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)
        attendee_repo = AttendeeRepository(db)

        # A pasted transcript is supplied at creation time. File-based inputs
        # are uploaded immediately after a draft is created, so a draft may
        # legitimately have no source yet.
        input_count = sum([
            bool(data.audio_file_path),
            bool(data.transcript_file_path),
            bool(data.transcript_text),
        ])
        if input_count > 1:
            raise ValidationError("Provide only one of: audio_file_path, transcript_file_path, or transcript_text")

        # Create meeting
        meeting = Meeting(
            user_id=user_id,
            title=data.title,
            meeting_date=data.meeting_date,
            meeting_time=data.meeting_time,
            project_name=data.project_name,
            audio_file_path=data.audio_file_path,
            transcript_file_path=data.transcript_file_path,
            transcript_text=data.transcript_text,
            agenda=data.agenda or [],
            notes=data.notes,
            status=MeetingStatus.DRAFT,
        )

        meeting = meeting_repo.create(meeting)

        # Create attendees
        attendees_data = [{"name": a.name, "email": a.email} for a in data.attendees]
        attendee_repo.create_batch(meeting.id, attendees_data)

        db.commit()
        db.refresh(meeting)
        return meeting

    def update_meeting(self, meeting_id: UUID, user_id: int, data: MeetingUpdate) -> Meeting:
        """Update meeting metadata."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)
        attendee_repo = AttendeeRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        # Only allow updates if in draft or uploaded state
        if meeting.status not in [MeetingStatus.DRAFT, MeetingStatus.UPLOADED]:
            raise ValidationError(f"Cannot update meeting in {meeting.status.value} state")

        update_data = data.model_dump(exclude_unset=True)
        attendees_data = update_data.pop("attendees", None)

        if update_data:
            meeting_repo.update(meeting, **update_data)

        if attendees_data is not None:
            # Validate attendees
            if len(attendees_data) == 0:
                raise ValidationError("At least one attendee is required")
            attendee_repo.delete_by_meeting_id(meeting.id)
            attendee_repo.create_batch(meeting.id, [a.model_dump() for a in attendees_data])

        db.commit()
        db.refresh(meeting)
        return meeting

    def upload_audio(self, meeting_id: UUID, user_id: int, file_path: str, file_size: int) -> AudioUploadResponse:
        """Upload audio file for meeting."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if meeting.status not in [MeetingStatus.DRAFT, MeetingStatus.UPLOADED]:
            raise ValidationError(f"Cannot upload audio for meeting in {meeting.status.value} state")

        # Validate file type
        from pathlib import Path
        suffix = Path(file_path).suffix.lower()
        if suffix not in [".mp3", ".wav", ".m4a"]:
            raise ValidationError("Unsupported audio format. Supported formats: MP3, WAV, M4A")

        meeting_repo.update(meeting, audio_file_path=file_path, status=MeetingStatus.UPLOADED)
        db.commit()

        return AudioUploadResponse(
            meeting_id=meeting.id,
            file_path=file_path,
            file_size=file_size,
            status="uploaded",
        )

    def upload_transcript(self, meeting_id: UUID, user_id: int, file_path: str) -> TranscriptUploadResponse:
        """Upload transcript file for meeting."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if meeting.status not in [MeetingStatus.DRAFT, MeetingStatus.UPLOADED]:
            raise ValidationError(f"Cannot upload transcript for meeting in {meeting.status.value} state")

        # Validate file type
        from pathlib import Path
        suffix = Path(file_path).suffix.lower()
        if suffix not in [".txt", ".md", ".text", ".transcript"]:
            raise ValidationError("Unsupported transcript format. Use TXT, MD, or a text transcript file.")

        meeting_repo.update(meeting, transcript_file_path=file_path, status=MeetingStatus.UPLOADED)
        db.commit()

        return TranscriptUploadResponse(
            meeting_id=meeting.id,
            file_path=file_path,
            status="uploaded",
        )

    def queue_processing(self, meeting_id: UUID, user_id: int) -> ProcessingStartResponse:
        """Validate a meeting and persist a queued job for background execution."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if meeting.status not in [
            MeetingStatus.DRAFT,
            MeetingStatus.UPLOADED,
            MeetingStatus.FAILED,
            MeetingStatus.CANCELLED,
        ]:
            raise ValidationError(f"Cannot process meeting in {meeting.status.value} state")

        # Validate input source exists
        if not any([meeting.audio_file_path, meeting.transcript_file_path, meeting.transcript_text]):
            raise ValidationError("No input source provided. Upload audio, transcript file, or provide transcript text.")

        self._ensure_processing_allowance(db, user_id)

        # Failed processing is safe to retry: discard its terminal error and
        # execute a new graph run with a fresh checkpoint thread.
        if meeting.status in [MeetingStatus.FAILED, MeetingStatus.CANCELLED]:
            meeting_repo.update(
                meeting,
                error_code=None,
                error_message=None,
                thread_id=None,
            )

        # Generate thread_id for checkpointing
        thread_id = str(uuid.uuid4())
        meeting_repo.update(meeting, status=MeetingStatus.QUEUED, thread_id=thread_id)
        db.commit()

        return ProcessingStartResponse(
            meeting_id=meeting.id,
            thread_id=thread_id,
            status=MeetingStatus.QUEUED.value,
            message="Processing queued",
        )

    def process_queued(self, meeting_id: UUID, user_id: int, thread_id: str) -> ProcessingStartResponse:
        """Execute a previously queued meeting and persist its checkpoint or result."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)
        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")
        if meeting.status == MeetingStatus.CANCELLED and meeting.thread_id == thread_id:
            return ProcessingStartResponse(
                meeting_id=meeting.id,
                thread_id=thread_id,
                status=MeetingStatus.CANCELLED.value,
                message="Processing was cancelled",
            )
        if meeting.status != MeetingStatus.QUEUED or meeting.thread_id != thread_id:
            raise ValidationError("Meeting is no longer queued for this processing run")

        try:
            meeting_repo.update(meeting, status=MeetingStatus.PROCESSING)
            db.commit()

            state = self._map_meeting_to_state(meeting)
            config = {"configurable": {"thread_id": thread_id}}

            # Invoke the graph
            result = self.graph.invoke(state.model_dump(), config=config)

            # Interrupt responses only contain an interrupt marker. Persist
            # the checkpoint before setting a review status so summaries and
            # redacted artefacts are available to the reviewer.
            if "__interrupt__" in result:
                self._persist_checkpoint_state(db, meeting, config)
                interrupt_type = self._interrupt_type(result)
                meeting.status = (
                    MeetingStatus.AWAITING_EMAIL_REVIEW
                    if interrupt_type == "email_review"
                    else MeetingStatus.AWAITING_REVIEW
                )
            else:
                # Update meeting with final results
                self._map_state_to_meeting(meeting, result)
                self._sync_tasks_from_meeting(db, meeting)
                meeting.status = MeetingStatus.COMPLETED
                self._record_terminal_processing_usage(db, meeting)

            db.commit()
            db.refresh(meeting)

        except ProcessingCancelled:
            db.rollback()
            db.expire_all()
            meeting = meeting_repo.get_by_id(meeting_id, user_id)
            if meeting and meeting.status != MeetingStatus.CANCELLED:
                meeting_repo.update(
                    meeting,
                    status=MeetingStatus.CANCELLED,
                    error_code=None,
                    error_message=None,
                )
                self._record_terminal_processing_usage(db, meeting)
                db.commit()
            return ProcessingStartResponse(
                meeting_id=meeting_id,
                thread_id=thread_id,
                status=MeetingStatus.CANCELLED.value,
                message="Processing was cancelled",
            )
        except Exception as e:
            meeting_repo.update(
                meeting,
                status=MeetingStatus.FAILED,
                error_code="PROCESSING_ERROR",
                error_message=str(e),
            )
            db.commit()
            raise ProcessingError(f"Processing failed: {str(e)}")

        return ProcessingStartResponse(
            meeting_id=meeting.id,
            thread_id=thread_id,
            status=meeting.status.value if hasattr(meeting.status, 'value') else meeting.status,
            message="Processing reached its next checkpoint",
        )

    def start_processing(self, meeting_id: UUID, user_id: int) -> ProcessingStartResponse:
        """Queue and execute processing synchronously for CLI and service callers."""
        queued = self.queue_processing(meeting_id, user_id)
        return self.process_queued(meeting_id, user_id, queued.thread_id)

    def resume_processing(self, meeting_id: UUID, user_id: int, review_data: ReviewRequest) -> ReviewResponse:
        """Resume processing after human review."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if not meeting.thread_id:
            raise ValidationError("No active processing thread found")

        if meeting.status not in [MeetingStatus.AWAITING_REVIEW, MeetingStatus.REVISION_REQUESTED]:
            raise ValidationError(f"Meeting not awaiting review. Current status: {meeting.status.value}")

        # Map the public review action to the payload consumed by the paused
        # human-review node, then resume the exact interrupted graph thread.
        if review_data.decision == "approve":
            resume_payload = {"decision": "approve", "instructions": ""}
        elif review_data.decision == "revise" and review_data.instructions:
            resume_payload = {
                "decision": "reject_with_instructions",
                "instructions": review_data.instructions,
            }
        else:
            resume_payload = {"decision": "reject_no_instructions", "instructions": ""}

        config = {"configurable": {"thread_id": meeting.thread_id}}
        self._ensure_pending_checkpoint(meeting, config, db, meeting_repo)

        try:
            result = self.graph.invoke(Command(resume=resume_payload), config=config)

            if "__interrupt__" in result:
                self._persist_checkpoint_state(db, meeting, config)
                interrupt_type = self._interrupt_type(result)
                if interrupt_type == "email_review":
                    meeting.status = MeetingStatus.AWAITING_EMAIL_REVIEW
                else:
                    meeting.status = (
                        MeetingStatus.REVISION_REQUESTED
                        if review_data.decision == "revise"
                        else MeetingStatus.AWAITING_REVIEW
                    )
            else:
                self._map_state_to_meeting(meeting, result)
                self._sync_tasks_from_meeting(db, meeting)
                meeting.status = (
                    MeetingStatus.REJECTED
                    if review_data.decision == "reject"
                    else MeetingStatus.COMPLETED
                )
                if meeting.status in [MeetingStatus.COMPLETED, MeetingStatus.REJECTED]:
                    self._record_terminal_processing_usage(db, meeting)

            db.commit()
            db.refresh(meeting)

        except Exception as e:
            meeting_repo.update(
                meeting,
                status=MeetingStatus.FAILED,
                error_code="RESUME_ERROR",
                error_message=str(e),
            )
            db.commit()
            raise ProcessingError(f"Resume failed: {str(e)}")

        next_status = meeting.status.value if hasattr(meeting.status, 'value') else meeting.status
        return ReviewResponse(
            meeting_id=meeting.id,
            decision=review_data.decision,
            message=f"Review {review_data.decision}d",
            next_status=next_status,
        )

    def get_review_content(self, meeting_id: UUID, user_id: int) -> ReviewContentResponse:
        """Get content for human review."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if meeting.status not in [MeetingStatus.AWAITING_REVIEW, MeetingStatus.REVISION_REQUESTED]:
            raise ValidationError(f"Meeting not awaiting review. Current status: {meeting.status.value}")

        return ReviewContentResponse(
            meeting_id=meeting.id,
            meeting_title=meeting.title,
            # Redaction may intentionally leave a field unchanged. The
            # reviewer should always see the generated artefacts, never an
            # empty panel just because no redaction replacement was needed.
            redacted_transcription=meeting.redacted_transcription or meeting.cleaned_transcription or meeting.raw_transcription or "",
            redacted_summary=meeting.redacted_summary or meeting.summary or "",
            redacted_decisions=meeting.redacted_decisions or meeting.decisions or [],
            redacted_action_items=meeting.redacted_action_items or meeting.action_items or [],
        )

    def get_email_draft(self, meeting_id: UUID, user_id: int) -> EmailDraftResponse:
        """Get email draft for review."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if meeting.status not in [MeetingStatus.AWAITING_EMAIL_REVIEW]:
            raise ValidationError(f"Meeting not awaiting email review. Current status: {meeting.status.value}")

        return EmailDraftResponse(
            meeting_id=meeting.id,
            meeting_title=meeting.title,
            email_draft=meeting.email_draft or "",
            redacted_summary=meeting.redacted_summary or "",
            redacted_decisions=meeting.redacted_decisions or [],
            redacted_action_items=meeting.redacted_action_items or [],
            delivery_error=(
                meeting.email_response.get("error")
                if isinstance(meeting.email_response, dict)
                else None
            ),
        )

    def review_email(self, meeting_id: UUID, user_id: int, review_data: EmailReviewRequest) -> EmailSendResponse:
        """Review and optionally send email."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if not meeting.thread_id:
            raise ValidationError("No active processing thread found")

        if meeting.status not in [MeetingStatus.AWAITING_EMAIL_REVIEW]:
            raise ValidationError(f"Meeting not awaiting email review. Current status: {meeting.status.value}")

        if review_data.decision == "approve":
            resume_payload = {"decision": "approve", "instructions": ""}
        elif review_data.decision == "revise" and review_data.instructions:
            resume_payload = {"decision": "reject_with_instructions", "instructions": review_data.instructions}
        else:
            resume_payload = {"decision": "reject_no_instructions", "instructions": ""}

        config = {"configurable": {"thread_id": meeting.thread_id}}
        self._ensure_pending_checkpoint(meeting, config, db, meeting_repo)

        try:
            result = self.graph.invoke(Command(resume=resume_payload), config=config)

            if "__interrupt__" in result:
                self._persist_checkpoint_state(db, meeting, config)
                meeting.status = MeetingStatus.AWAITING_EMAIL_REVIEW
            else:
                self._map_state_to_meeting(meeting, result)
                self._sync_tasks_from_meeting(db, meeting)
                meeting.status = MeetingStatus.REJECTED if review_data.decision == "reject" else MeetingStatus.COMPLETED
                if meeting.status in [MeetingStatus.COMPLETED, MeetingStatus.REJECTED]:
                    self._record_terminal_processing_usage(db, meeting)

            db.commit()
            db.refresh(meeting)

        except Exception as e:
            meeting_repo.update(
                meeting,
                status=MeetingStatus.FAILED,
                error_code="EMAIL_REVIEW_ERROR",
                error_message=str(e),
            )
            db.commit()
            raise ProcessingError(f"Email review failed: {str(e)}")

        if meeting.email_sent:
            return EmailSendResponse(
                meeting_id=meeting.id,
                sent=True,
                response=meeting.email_response,
                message="Email sent successfully",
            )
        else:
            delivery_response = meeting.email_response if isinstance(meeting.email_response, dict) else None
            delivery_error = delivery_response.get("error") if delivery_response else None
            return EmailSendResponse(
                meeting_id=meeting.id,
                sent=False,
                response=delivery_response,
                message=delivery_error or f"Email review {review_data.decision}d",
            )

    def get_meeting_results(self, meeting_id: UUID, user_id: int) -> MeetingResultResponse:
        """Get meeting results for frontend."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)
        task_repo = TaskRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        tasks = task_repo.get_by_meeting_id(meeting_id, user_id)

        return MeetingResultResponse(
            meeting_id=meeting.id,
            title=meeting.title,
            meeting_date=meeting.meeting_date,
            summary=meeting.summary,
            decisions=meeting.decisions or [],
            action_items=meeting.action_items or [],
            redacted_summary=meeting.redacted_summary,
            redacted_decisions=meeting.redacted_decisions or [],
            redacted_action_items=meeting.redacted_action_items or [],
            email_draft=meeting.email_draft,
            email_sent=meeting.email_sent,
            tasks=[TaskResponse.model_validate(t) for t in tasks],
            status=meeting.status.value if hasattr(meeting.status, 'value') else meeting.status,
            tokens_used=meeting.tokens_used,
        )

    def get_meeting_status(self, meeting_id: UUID, user_id: int) -> MeetingStatusResponse:
        """Get meeting processing status."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        # Map status to stage
        stage_map = {
            MeetingStatus.QUEUED: "queued",
            MeetingStatus.PROCESSING: "processing",
            MeetingStatus.AWAITING_REVIEW: "awaiting_review",
            MeetingStatus.REVISION_REQUESTED: "revision_requested",
            MeetingStatus.AWAITING_EMAIL_REVIEW: "awaiting_email_review",
            MeetingStatus.COMPLETED: "completed",
            MeetingStatus.REJECTED: "rejected",
            MeetingStatus.FAILED: "failed",
            MeetingStatus.CANCELLED: "cancelled",
        }

        return MeetingStatusResponse(
            meeting_id=meeting.id,
            status=meeting.status.value if hasattr(meeting.status, 'value') else meeting.status,
            current_stage=stage_map.get(meeting.status),
            error=meeting.error_message,
            progress_percentage=self._calculate_progress(meeting.status),
        )

    def cancel_processing(self, meeting_id: UUID, user_id: int) -> MeetingStatusResponse:
        """Cancel an active or paused meeting workflow owned by the user."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)
        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        cancellable_statuses = {
            MeetingStatus.QUEUED,
            MeetingStatus.PROCESSING,
            MeetingStatus.AWAITING_REVIEW,
            MeetingStatus.REVISION_REQUESTED,
            MeetingStatus.AWAITING_EMAIL_REVIEW,
        }
        if meeting.status not in cancellable_statuses:
            raise ValidationError(f"Cannot stop meeting in {meeting.status.value} state")

        meeting_repo.update(
            meeting,
            status=MeetingStatus.CANCELLED,
            error_code=None,
            error_message=None,
        )
        self._record_terminal_processing_usage(db, meeting)
        db.commit()
        db.refresh(meeting)

        return MeetingStatusResponse(
            meeting_id=meeting.id,
            status=MeetingStatus.CANCELLED.value,
            current_stage="cancelled",
            error=None,
            progress_percentage=0,
        )

    def _calculate_progress(self, status: MeetingStatus) -> int:
        """Calculate progress percentage based on status."""
        progress_map = {
            MeetingStatus.DRAFT: 0,
            MeetingStatus.UPLOADED: 10,
            MeetingStatus.QUEUED: 15,
            MeetingStatus.PROCESSING: 50,
            MeetingStatus.AWAITING_REVIEW: 60,
            MeetingStatus.REVISION_REQUESTED: 50,
            MeetingStatus.AWAITING_EMAIL_REVIEW: 80,
            MeetingStatus.COMPLETED: 100,
            MeetingStatus.REJECTED: 100,
            MeetingStatus.FAILED: 0,
            MeetingStatus.CANCELLED: 0,
        }
        return progress_map.get(status, 0)

    def list_meetings(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[MeetingStatus] = None,
    ) -> tuple[List[Meeting], int]:
        """List user's meetings."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)
        return meeting_repo.get_user_meetings(user_id, page, page_size, status)

    def get_meeting(self, meeting_id: UUID, user_id: int) -> Meeting:
        """Get meeting by ID."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)
        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")
        return meeting

    def delete_meeting(self, meeting_id: UUID, user_id: int) -> None:
        """Delete a meeting."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id(meeting_id, user_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if meeting.status in [MeetingStatus.PROCESSING, MeetingStatus.AWAITING_REVIEW, MeetingStatus.AWAITING_EMAIL_REVIEW]:
            raise ValidationError("Cannot delete meeting while processing")

        meeting_repo.delete(meeting)
        db.commit()


def process_meeting_in_background(meeting_id: UUID, user_id: int, thread_id: str) -> None:
    """Run a queued graph job with an isolated database session."""
    db = SessionLocal()
    try:
        ProcessingService(db).process_queued(meeting_id, user_id, thread_id)
    except Exception:
        # process_queued persists a FAILED state for graph/provider failures.
        # Logging here keeps background-task exceptions from being swallowed.
        logger.exception("Background meeting processing failed for meeting %s", meeting_id)
    finally:
        db.close()
