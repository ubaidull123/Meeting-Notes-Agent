"""Admin service."""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import func, and_, or_
from meeting_notes_agent.database import (
    UserRepository,
    UserQuotaRepository,
    UserCreditsRepository,
    UserUsageRepository,
    MeetingRepository,
    TaskRepository,
    get_db,
)
from meeting_notes_agent.database.models import UserRole, MeetingStatus, User
from meeting_notes_agent.config.core.exceptions import NotFoundError, ValidationError
from meeting_notes_agent.schemas.admin import (
    AdminStatsResponse,
    AdminUserListItem,
    AdminUserDetail,
    AdminUserUpdate,
    AdminMeetingListItem,
    AdminMeetingStatusResponse,
)
from meeting_notes_agent.schemas.user import UserQuotaResponse, UserCreditsResponse, UserUsageResponse


class AdminService:
    """Service for admin operations."""

    def __init__(self, db=None):
        self.db = db

    def _get_db(self):
        """Get database session."""
        if self.db:
            return self.db
        return next(get_db())

    def get_stats(self) -> AdminStatsResponse:
        """Get admin dashboard statistics."""
        db = self._get_db()
        user_repo = UserRepository(db)
        meeting_repo = MeetingRepository(db)

        # Total users
        total_users = user_repo.count()
        active_users = user_repo.count(is_active=True)

        # Meetings stats
        total_meetings = meeting_repo.count()

        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        meetings_today = meeting_repo.count(
            MeetingStatus.COMPLETED,
            date_from=today,
            date_to=today,
        )
        meetings_this_week = meeting_repo.count(
            MeetingStatus.COMPLETED,
            date_from=week_ago,
            date_to=today,
        )
        meetings_this_month = meeting_repo.count(
            MeetingStatus.COMPLETED,
            date_from=month_ago,
            date_to=today,
        )

        successful_meetings = meeting_repo.count(MeetingStatus.COMPLETED)
        failed_meetings = meeting_repo.count(MeetingStatus.FAILED)
        processing_meetings = meeting_repo.count(MeetingStatus.PROCESSING)

        # Tokens used
        total_tokens = meeting_repo.sum_tokens()

        # Emails sent
        emails_sent = meeting_repo.count_emails_sent()

        # Credits
        credits_repo = UserCreditsRepository(db)
        total_credits_issued = credits_repo.sum_credits_issued()
        total_credits_consumed = credits_repo.sum_credits_consumed()

        return AdminStatsResponse(
            total_users=total_users,
            active_users=active_users,
            total_meetings=total_meetings,
            meetings_today=meetings_today,
            meetings_this_week=meetings_this_week,
            meetings_this_month=meetings_this_month,
            successful_meetings=successful_meetings,
            failed_meetings=failed_meetings,
            processing_meetings=processing_meetings,
            total_tokens_used=total_tokens,
            emails_sent=emails_sent,
            total_credits_issued=total_credits_issued,
            total_credits_consumed=total_credits_consumed,
        )

    def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[AdminUserListItem], int]:
        """List users with filters."""
        db = self._get_db()
        user_repo = UserRepository(db)
        quota_repo = UserQuotaRepository(db)
        credits_repo = UserCreditsRepository(db)
        meeting_repo = MeetingRepository(db)

        users, total = user_repo.list_users(
            page=page,
            page_size=page_size,
            search=search,
            role=role,
            is_active=is_active,
        )

        items = []
        for user in users:
            quota = quota_repo.get_by_user_id(user.id)
            credits = credits_repo.get_by_user_id(user.id)
            meetings_this_month = meeting_repo.count_user_meetings_this_month(user.id)

            items.append(AdminUserListItem(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                quota_limit=quota.monthly_meeting_limit if quota else 0,
                credits_balance=credits.balance if credits else 0,
                meetings_this_month=meetings_this_month,
            ))

        return items, total

    def get_user(self, user_id: int) -> AdminUserDetail:
        """Get user detail."""
        db = self._get_db()
        user_repo = UserRepository(db)
        quota_repo = UserQuotaRepository(db)
        credits_repo = UserCreditsRepository(db)
        usage_repo = UserUsageRepository(db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        quota = quota_repo.get_by_user_id(user_id)
        credits = credits_repo.get_by_user_id(user_id)
        usage = usage_repo.get_by_user_id(user_id)

        return AdminUserDetail(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            quota=UserQuotaResponse.model_validate(quota) if quota else None,
            credits=UserCreditsResponse.model_validate(credits) if credits else None,
            usage=[UserUsageResponse.model_validate(u) for u in usage] if usage else None,
        )

    def update_user(self, user_id: int, data: AdminUserUpdate) -> AdminUserDetail:
        """Update user (admin)."""
        db = self._get_db()
        user_repo = UserRepository(db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        update_data = data.model_dump(exclude_unset=True)
        if "role" in update_data:
            update_data["role"] = update_data["role"].value if hasattr(update_data["role"], 'value') else update_data["role"]

        user_repo.update(user, **update_data)
        db.commit()
        db.refresh(user)

        return self.get_user(user_id)

    def delete_user(self, user_id: int, current_admin_id: int | None = None) -> None:
        """Delete user (admin)."""
        db = self._get_db()
        user_repo = UserRepository(db)

        if current_admin_id is not None and user_id == current_admin_id:
            raise ValidationError("You cannot delete your own admin account")

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        user_repo.delete(user)
        db.commit()

    def adjust_credits(self, user_id: int, amount: int, reason: str) -> UserCreditsResponse:
        """Adjust user credits (admin)."""
        db = self._get_db()
        user_repo = UserRepository(db)
        credits_repo = UserCreditsRepository(db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        credits = credits_repo.get_or_create(user_id)

        if amount > 0:
            credits_repo.add_credits(credits, amount, reason)
        else:
            credits_repo.deduct_credits(credits, abs(amount), reason)

        db.commit()
        db.refresh(credits)

        return UserCreditsResponse.model_validate(credits)

    def adjust_quota(self, user_id: int, monthly_limit: int) -> UserQuotaResponse:
        """Adjust user quota (admin)."""
        db = self._get_db()
        user_repo = UserRepository(db)
        quota_repo = UserQuotaRepository(db)

        user = user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        quota = quota_repo.get_or_create(user_id)
        quota_repo.update_quota(quota, monthly_limit)

        db.commit()
        db.refresh(quota)

        return UserQuotaResponse.model_validate(quota)

    def list_meetings(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[MeetingStatus] = None,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Tuple[List[AdminMeetingListItem], int]:
        """List all meetings (admin)."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meetings, total = meeting_repo.list_all(
            page=page,
            page_size=page_size,
            status=status,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )

        items = []
        for meeting in meetings:
            items.append(AdminMeetingListItem(
                id=meeting.id,
                user_id=meeting.user_id,
                user_email=meeting.user.email if meeting.user else "",
                user_name=meeting.user.full_name if meeting.user else "",
                title=meeting.title,
                meeting_date=meeting.meeting_date,
                status=meeting.status,
                tokens_used=meeting.tokens_used,
                created_at=meeting.created_at,
                updated_at=meeting.updated_at,
            ))

        return items, total

    def get_meeting_status(self, meeting_id: UUID) -> AdminMeetingStatusResponse:
        """Get meeting status (admin)."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id_admin(meeting_id)
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
            MeetingStatus.FAILED: "failed",
            MeetingStatus.CANCELLED: "cancelled",
        }

        return AdminMeetingStatusResponse(
            meeting_id=meeting.id,
            user_id=meeting.user_id,
            user_email=meeting.user.email if meeting.user else "",
            title=meeting.title,
            status=meeting.status,
            current_stage=stage_map.get(meeting.status),
            error_code=meeting.error_code,
            error_message=meeting.error_message,
            tokens_used=meeting.tokens_used,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at,
            thread_id=meeting.thread_id,
        )

    def cancel_meeting(self, meeting_id: UUID) -> None:
        """Cancel meeting (admin)."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id_admin(meeting_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if meeting.status in [MeetingStatus.PROCESSING, MeetingStatus.AWAITING_REVIEW, MeetingStatus.AWAITING_EMAIL_REVIEW]:
            raise ValidationError("Cannot cancel meeting while processing")

        meeting_repo.update(meeting, status=MeetingStatus.CANCELLED)
        db.commit()

    def retry_meeting(self, meeting_id: UUID) -> None:
        """Retry failed meeting (admin)."""
        db = self._get_db()
        meeting_repo = MeetingRepository(db)

        meeting = meeting_repo.get_by_id_admin(meeting_id)
        if not meeting:
            raise NotFoundError("Meeting not found")

        if meeting.status != MeetingStatus.FAILED:
            raise ValidationError("Only failed meetings can be retried")

        meeting_repo.update(
            meeting,
            status=MeetingStatus.QUEUED,
            error_code=None,
            error_message=None,
        )
        db.commit()
