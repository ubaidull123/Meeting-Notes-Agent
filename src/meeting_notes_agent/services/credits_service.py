"""Credit ledger and usage service."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from meeting_notes_agent.config.core.exceptions import InsufficientCreditsError
from meeting_notes_agent.database.models import UserCredits, UserUsage
from meeting_notes_agent.database.models_ai_config import AIUsageMode, CreditTransaction, UsageRecord


class CreditsService:
    def __init__(self, db: Session):
        self.db = db

    def get_balance(self, user_id: int) -> int:
        account = self.db.query(UserCredits).filter_by(user_id=user_id).first()
        if not account:
            account = UserCredits(user_id=user_id, balance=500)
            self.db.add(account)
            self.db.flush()
        return account.balance

    def deduct_credits(
        self,
        user_id: int,
        amount: int,
        *,
        meeting_id: UUID | None,
        service_type: str,
        provider: str,
        model: str,
        usage_mode: str,
        description: str,
        usage_metadata: dict | None = None,
    ) -> CreditTransaction:
        account = self.db.query(UserCredits).filter_by(user_id=user_id).first()
        if not account:
            account = UserCredits(user_id=user_id, balance=0)
            self.db.add(account)
            self.db.flush()
        if account.balance < amount:
            raise InsufficientCreditsError("You do not have enough credits to process this meeting.", details={"balance": account.balance, "required": amount})
        account.balance -= amount
        account.updated_at = datetime.now(timezone.utc)
        tx = CreditTransaction(
            user_id=user_id,
            meeting_id=meeting_id,
            amount=-amount,
            balance_after=account.balance,
            transaction_type="meeting_processing",
            service_type=service_type,
            provider=provider,
            model=model,
            usage_mode=AIUsageMode(usage_mode),
            usage_metadata=usage_metadata or {},
            description=description,
        )
        self.db.add(tx)
        self.db.flush()
        return tx

    def record_usage(
        self,
        user_id: int,
        meeting_id: UUID,
        *,
        service_type: str,
        provider: str,
        model: str,
        usage_mode: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        audio_duration_seconds: int = 0,
        credits_cost: int = 0,
        status: str = "completed",
        error_message: str | None = None,
    ) -> UsageRecord:
        record = UsageRecord(
            user_id=user_id,
            meeting_id=meeting_id,
            service_type=service_type,
            provider=provider,
            model=model,
            usage_mode=AIUsageMode(usage_mode),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            audio_duration_seconds=audio_duration_seconds,
            credits_cost=credits_cost,
            status=status,
            error_message=error_message,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def list_transactions(self, user_id: int, limit: int = 50) -> list[CreditTransaction]:
        return (
            self.db.query(CreditTransaction)
            .filter_by(user_id=user_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_usage(self, user_id: int, limit: int = 50) -> list[UsageRecord]:
        return (
            self.db.query(UsageRecord)
            .filter_by(user_id=user_id)
            .order_by(UsageRecord.created_at.desc())
            .limit(limit)
            .all()
        )

