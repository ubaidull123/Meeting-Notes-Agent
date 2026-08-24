"""Authenticated user settings endpoints."""
from __future__ import annotations

from typing import Annotated
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status

from meeting_notes_agent.auth.dependencies import (
    get_current_configuration_manager_id,
    get_current_user_id,
)
from meeting_notes_agent.config.providers import PROVIDER_CATALOG
from meeting_notes_agent.database import get_db
from meeting_notes_agent.database.models import Meeting, UserUsage
from meeting_notes_agent.database.models_ai_config import UsageRecord
from meeting_notes_agent.schemas.settings import (
    AISettingsResponse,
    AISettingsUpdate,
    CredentialPublic,
    CredentialSaveRequest,
    CredentialTestRequest,
    CredentialTestResponse,
    CreditBalanceResponse,
    CreditTransactionResponse,
    EmailSettingsResponse,
    EmailSettingsUpdate,
    MeetingOverrideRequest,
    MeetingOverrideResponse,
    MeetingDefaultsResponse,
    MeetingDefaultsUpdate,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    PrivacySettingsResponse,
    PrivacySettingsUpdate,
    ProfileSettingsResponse,
    ProfileSettingsUpdate,
    TranscriptionSettingsResponse,
    TranscriptionSettingsUpdate,
    UsageRecordResponse,
    UsageSummaryResponse,
)
from meeting_notes_agent.services.ai_settings_service import AISettingsService
from meeting_notes_agent.services.credits_service import CreditsService
from meeting_notes_agent.services.email_settings_service import EmailSettingsService
from meeting_notes_agent.services.meeting_override_service import MeetingOverrideService
from meeting_notes_agent.services.product_settings_service import ProductSettingsService
from meeting_notes_agent.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/profile", response_model=ProfileSettingsResponse)
async def get_profile_settings(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    db=Depends(get_db),
):
    return ProductSettingsService(db).get_profile(current_user_id)


@router.put("/profile", response_model=ProfileSettingsResponse)
async def update_profile_settings(
    data: ProfileSettingsUpdate,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    db=Depends(get_db),
):
    profile = ProductSettingsService(db).update_profile(current_user_id, **data.model_dump())
    db.commit()
    return profile


def _credential_public(credential, service: AISettingsService | None = None) -> CredentialPublic:
    return CredentialPublic(
        provider=credential.provider.value if hasattr(credential.provider, "value") else credential.provider,
        has_api_key=bool(credential.api_key_encrypted),
        api_key_hint=credential.api_key_hint,
        is_valid=credential.is_valid,
        last_tested_at=credential.last_tested_at,
        last_test_error=credential.last_test_error,
        configuration=service.get_public_credential_config(credential) if service else {},
    )


@router.get("/providers")
async def providers(
    _current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)],
):
    return PROVIDER_CATALOG


@router.get("/ai", response_model=AISettingsResponse)
async def get_ai_settings(current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    service = AISettingsService(db)
    config = service.get_ai_config(current_user_id)
    advanced = ProductSettingsService(db).get_ai_advanced(current_user_id)
    return AISettingsResponse(
        llm_usage_mode=config.llm_usage_mode.value,
        llm_provider=config.llm_provider.value,
        llm_model=config.llm_model,
        transcription_usage_mode=config.transcription_usage_mode.value,
        transcription_provider=config.transcription_provider.value,
        transcription_model=config.transcription_model,
        **advanced,
        credentials=[_credential_public(c, service) for c in service.list_credentials(current_user_id)],
    )


@router.put("/ai", response_model=AISettingsResponse)
async def update_ai_settings(data: AISettingsUpdate, current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    service = AISettingsService(db)
    values = data.model_dump()
    advanced = {
        "temperature": values.pop("temperature"),
        "max_output_tokens": values.pop("max_output_tokens"),
        "response_language": values.pop("response_language"),
    }
    service.update_ai_config(current_user_id, **values)
    ProductSettingsService(db).update_ai_advanced(current_user_id, **advanced)
    db.commit()
    return await get_ai_settings(current_user_id, db)


@router.get("/transcription", response_model=TranscriptionSettingsResponse)
async def get_transcription_settings(
    current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)],
    db=Depends(get_db),
):
    service = AISettingsService(db)
    config = service.get_ai_config(current_user_id)
    preferences = ProductSettingsService(db).get_transcription_preferences(current_user_id)
    return TranscriptionSettingsResponse(
        usage_mode=config.transcription_usage_mode.value,
        provider=config.transcription_provider.value,
        model=config.transcription_model,
        language=preferences["language"],
        credentials=[_credential_public(c, service) for c in service.list_credentials(current_user_id)],
    )


@router.put("/transcription", response_model=TranscriptionSettingsResponse)
async def update_transcription_settings(
    data: TranscriptionSettingsUpdate,
    current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)],
    db=Depends(get_db),
):
    ai_service = AISettingsService(db)
    config = ai_service.get_ai_config(current_user_id)
    ai_service.update_ai_config(
        current_user_id,
        llm_usage_mode=config.llm_usage_mode.value,
        llm_provider=config.llm_provider.value,
        llm_model=config.llm_model,
        transcription_usage_mode=data.usage_mode,
        transcription_provider=data.provider,
        transcription_model=data.model,
    )
    ProductSettingsService(db).update_transcription_preferences(
        current_user_id,
        language=data.language,
    )
    db.commit()
    return await get_transcription_settings(current_user_id, db)


@router.get("/meetings", response_model=MeetingDefaultsResponse)
async def get_meeting_defaults(
    current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)],
    db=Depends(get_db),
):
    return ProductSettingsService(db).get_meeting_defaults(current_user_id)


@router.put("/meetings", response_model=MeetingDefaultsResponse)
async def update_meeting_defaults(
    data: MeetingDefaultsUpdate,
    current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)],
    db=Depends(get_db),
):
    result = ProductSettingsService(db).update_meeting_defaults(current_user_id, **data.model_dump())
    db.commit()
    return result


@router.get("/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    db=Depends(get_db),
):
    return ProductSettingsService(db).get_notifications(current_user_id)


@router.put("/notifications", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    data: NotificationSettingsUpdate,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    db=Depends(get_db),
):
    result = ProductSettingsService(db).update_notifications(current_user_id, **data.model_dump())
    db.commit()
    return result


@router.get("/privacy", response_model=PrivacySettingsResponse)
async def get_privacy_settings(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    db=Depends(get_db),
):
    return ProductSettingsService(db).get_privacy(current_user_id)


@router.put("/privacy", response_model=PrivacySettingsResponse)
async def update_privacy_settings(
    data: PrivacySettingsUpdate,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    db=Depends(get_db),
):
    result = ProductSettingsService(db).update_privacy(current_user_id, **data.model_dump())
    db.commit()
    return result


@router.get("/credentials", response_model=list[CredentialPublic])
async def list_credentials(current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    service = AISettingsService(db)
    return [_credential_public(c, service) for c in service.list_credentials(current_user_id)]


@router.post("/credentials", response_model=CredentialPublic, status_code=status.HTTP_201_CREATED)
async def save_credential(data: CredentialSaveRequest, current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    credential = AISettingsService(db).save_credential(current_user_id, data.provider, data.api_key, data.config)
    db.commit()
    return _credential_public(credential, AISettingsService(db))


@router.delete("/credentials/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(provider: str, current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    AISettingsService(db).delete_credential(current_user_id, provider)
    db.commit()


@router.post("/credentials/test", response_model=CredentialTestResponse)
async def test_credential(data: CredentialTestRequest, current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    result = AISettingsService(db).test_credential(data.provider, data.api_key, current_user_id, data.config)
    db.commit()
    return CredentialTestResponse(**result)


@router.get("/email", response_model=EmailSettingsResponse)
async def get_email_settings(current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    config = EmailSettingsService(db).get_email_config(current_user_id)
    domain = config.sender_email.rsplit("@", 1)[-1] if config.sender_email and "@" in config.sender_email else None
    return EmailSettingsResponse(
        email_mode=config.email_mode.value,
        provider=config.provider.value,
        sender_name=config.sender_name,
        sender_email=config.sender_email,
        reply_to_email=config.reply_to_email,
        sending_domain=domain,
        domain_status="configured" if domain else None,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_username=config.smtp_username,
        smtp_use_tls=config.smtp_use_tls,
    )


@router.put("/email", response_model=EmailSettingsResponse)
async def update_email_settings(data: EmailSettingsUpdate, current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    EmailSettingsService(db).update_email_config(current_user_id, **data.model_dump())
    db.commit()
    return await get_email_settings(current_user_id, db)


@router.get("/credits", response_model=CreditBalanceResponse)
async def credits(current_user_id: Annotated[int, Depends(get_current_user_id)], db=Depends(get_db)):
    return CreditBalanceResponse(balance=CreditsService(db).get_balance(current_user_id))


@router.get("/credits/transactions", response_model=list[CreditTransactionResponse])
async def transactions(current_user_id: Annotated[int, Depends(get_current_user_id)], db=Depends(get_db)):
    return CreditsService(db).list_transactions(current_user_id)


@router.get("/usage", response_model=list[UsageRecordResponse])
async def usage(current_user_id: Annotated[int, Depends(get_current_user_id)], db=Depends(get_db)):
    records = CreditsService(db).list_usage(current_user_id)
    meeting_ids = {record.meeting_id for record in records}
    titles = dict(db.query(Meeting.id, Meeting.title).filter(Meeting.id.in_(meeting_ids)).all()) if meeting_ids else {}
    return [
        UsageRecordResponse.model_validate(record).model_copy(
            update={"meeting_title": titles.get(record.meeting_id)}
        )
        for record in records
    ]


@router.get("/usage/summary", response_model=UsageSummaryResponse)
async def usage_summary(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    db=Depends(get_db),
):
    monthly = (
        db.query(UserUsage)
        .filter_by(user_id=current_user_id, month=date.today().replace(day=1))
        .first()
    )
    records = db.query(UsageRecord).filter_by(user_id=current_user_id).all()
    llm = [record for record in records if record.service_type == "llm"]
    transcription = [record for record in records if record.service_type == "transcription"]
    return UsageSummaryResponse(
        balance=CreditsService(db).get_balance(current_user_id),
        meetings_processed=monthly.meetings_processed if monthly else 0,
        tokens_used=monthly.tokens_used if monthly else 0,
        credits_consumed=monthly.credits_consumed if monthly else 0,
        llm_requests=len(llm),
        llm_credits=sum(record.credits_cost for record in llm),
        transcription_requests=len(transcription),
        transcription_credits=sum(record.credits_cost for record in transcription),
    )


@router.get("/meetings/{meeting_id}/override", response_model=MeetingOverrideResponse)
async def get_override(meeting_id: UUID, current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    meeting = AuthorizationService(db).require_meeting_admin(meeting_id, current_user_id)
    return MeetingOverrideService(db).to_dict(meeting_id, meeting.user_id) or {}


@router.put("/meetings/{meeting_id}/override", response_model=MeetingOverrideResponse)
async def set_override(meeting_id: UUID, data: MeetingOverrideRequest, current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    meeting = AuthorizationService(db).require_meeting_admin(meeting_id, current_user_id)
    MeetingOverrideService(db).set_override(meeting_id, meeting.user_id, **data.model_dump())
    db.commit()
    return MeetingOverrideService(db).to_dict(meeting_id, meeting.user_id) or {}


@router.delete("/meetings/{meeting_id}/override", status_code=status.HTTP_204_NO_CONTENT)
async def clear_override(meeting_id: UUID, current_user_id: Annotated[int, Depends(get_current_configuration_manager_id)], db=Depends(get_db)):
    meeting = AuthorizationService(db).require_meeting_admin(meeting_id, current_user_id)
    MeetingOverrideService(db).clear_override(meeting_id, meeting.user_id)
    db.commit()
