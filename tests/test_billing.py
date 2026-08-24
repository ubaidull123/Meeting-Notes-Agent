"""Regression tests for quota, credits, and terminal meeting usage."""
from datetime import date
from uuid import uuid4

import pytest

from meeting_notes_agent.config.core.exceptions import QuotaExceededError
from meeting_notes_agent.database.models import Meeting, MeetingStatus
from meeting_notes_agent.database.repositories import (
    UserCreditsRepository,
    UserQuotaRepository,
    UserUsageRepository,
)
from meeting_notes_agent.services.processing_service import ProcessingService


def test_terminal_meeting_charges_once_and_updates_usage(db_session, test_user):
    service = ProcessingService(db_session)
    service._ensure_processing_allowance(db_session, test_user.id)

    credits = UserCreditsRepository(db_session).get_by_user_id(test_user.id)
    usage = UserUsageRepository(db_session).get_current_month(test_user.id)
    assert credits.balance == 500
    assert usage.meetings_processed == 0

    meeting = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        title="Billing test",
        meeting_date=date.today(),
        transcript_text="Transcript",
        tokens_used=37,
        status=MeetingStatus.AWAITING_EMAIL_REVIEW,
    )
    db_session.add(meeting)
    db_session.flush()

    meeting.status = MeetingStatus.COMPLETED
    service._record_terminal_processing_usage(db_session, meeting)
    service._record_terminal_processing_usage(db_session, meeting)
    db_session.commit()
    db_session.refresh(meeting)
    db_session.refresh(credits)
    db_session.refresh(usage)

    assert meeting.credits_charged is True
    assert credits.balance == 499
    assert usage.meetings_processed == 1
    assert usage.credits_consumed == 1
    assert usage.tokens_used == 37


@pytest.mark.parametrize("terminal_status", [MeetingStatus.REJECTED, MeetingStatus.CANCELLED])
def test_rejected_and_cancelled_meetings_spend_credit(db_session, test_user, terminal_status):
    service = ProcessingService(db_session)
    service._ensure_processing_allowance(db_session, test_user.id)
    credits = UserCreditsRepository(db_session).get_by_user_id(test_user.id)
    usage = UserUsageRepository(db_session).get_current_month(test_user.id)

    meeting = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        title=f"{terminal_status.value} billing test",
        meeting_date=date.today(),
        transcript_text="Transcript",
        tokens_used=12,
        status=terminal_status,
    )
    db_session.add(meeting)
    db_session.flush()

    service._record_terminal_processing_usage(db_session, meeting)
    db_session.commit()
    db_session.refresh(credits)
    db_session.refresh(usage)

    assert meeting.credits_charged is True
    assert credits.balance == 499
    assert usage.meetings_processed == 1
    assert usage.credits_consumed == 1


def test_quota_blocks_next_processing_attempt(db_session, test_user):
    service = ProcessingService(db_session)
    service._ensure_processing_allowance(db_session, test_user.id)
    quota = UserQuotaRepository(db_session).get_by_user_id(test_user.id)
    usage = UserUsageRepository(db_session).get_current_month(test_user.id)
    quota.monthly_meeting_limit = 1
    usage.meetings_processed = 1
    db_session.commit()

    with pytest.raises(QuotaExceededError):
        service._ensure_processing_allowance(db_session, test_user.id)
