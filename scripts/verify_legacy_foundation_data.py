"""Assert representative legacy records survive schema migrations unchanged."""

from __future__ import annotations

import argparse
import json
import os
from uuid import UUID

from sqlalchemy import text

from meeting_notes_agent.auth.security import verify_password
from meeting_notes_agent.database.models import Meeting, MeetingStatus, Task, User, UserRole
from meeting_notes_agent.database.models_ai_config import (
    UserAIConfig,
    UserCredential,
    UserEmailConfig,
    UserProductSettings,
)
from meeting_notes_agent.database.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--meeting-id", type=UUID, required=True)
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args()

    expected_password = os.environ.get("LEGACY_TEST_PASSWORD")
    if not expected_password:
        raise RuntimeError("LEGACY_TEST_PASSWORD is required")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == args.user_id).one()
        meeting = db.query(Meeting).filter(Meeting.id == args.meeting_id).one()
        task = db.query(Task).filter(Task.id == args.task_id).one()
        settings = (
            db.query(UserProductSettings)
            .filter(UserProductSettings.user_id == user.id)
            .one()
        )

        assert verify_password(expected_password, user.password_hash)
        assert user.role == UserRole.ADMIN
        assert user.is_active is True
        assert user.quotas.monthly_meeting_limit == 20
        assert user.quotas.monthly_credits == 500
        assert user.credits.balance == 500

        assert meeting.user_id == user.id
        assert meeting.project_name == "  Migration   Foundation  "
        assert meeting.status == MeetingStatus.AWAITING_EMAIL_REVIEW
        assert meeting.thread_id is not None
        assert meeting.summary == "Persisted human-review summary"
        assert meeting.decisions == ["Keep legacy ownership unchanged"]
        assert meeting.action_items == [
            "Legacy Assignee will verify PostgreSQL persistence tomorrow."
        ]
        assert meeting.email_draft == "Persisted email-review draft"
        assert meeting.email_sent is False
        assert meeting.tokens_used == 0
        assert meeting.credits_charged is False

        assert task.meeting_id == meeting.id
        assert task.meeting_title == meeting.title
        assert task.action_item_index == 0
        assert task.description == meeting.action_items[0]
        assert settings.timezone == "Asia/Karachi"
        assert settings.organization == "Staging Verification"

        provider_rows = {
            "ai_config": db.query(UserAIConfig).filter_by(user_id=user.id).count(),
            "credentials": db.query(UserCredential).filter_by(user_id=user.id).count(),
            "email_config": db.query(UserEmailConfig).filter_by(user_id=user.id).count(),
        }
        alembic_revision = db.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    finally:
        db.close()

    print(
        json.dumps(
            {
                "legacy_foundation_data": "preserved",
                "user_id": args.user_id,
                "meeting_id": str(args.meeting_id),
                "task_id": args.task_id,
                "password_auth_valid": True,
                "meeting_owner_unchanged": True,
                "processing_state_unchanged": True,
                "human_review_state_unchanged": True,
                "email_review_state_unchanged": True,
                "task_unchanged": True,
                "billing_unchanged": True,
                "provider_rows": provider_rows,
                "alembic_revision": alembic_revision,
            }
        )
    )


if __name__ == "__main__":
    main()
